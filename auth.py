# auth.py
from flask import request, jsonify, current_app
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from models import db, User, Client, AuditLog

def create_token(user_id, client_id, role):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'client_id': client_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )
    return token

def token_required(f):
    """Decorator to verify JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Missing token'}), 401
        
        try:
            token = token.split(' ')[1]  # Remove 'Bearer '
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            request.user_id = payload['user_id']
            request.client_id = payload['client_id']
            request.role = payload['role']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except (jwt.InvalidTokenError, IndexError):
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def client_only(f):
    """Ensure user belongs to a client (not super admin)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not request.client_id:
            return jsonify({'error': 'Client access required'}), 403
        return f(*args, **kwargs)
    return decorated

def log_audit(action, table_name, record_id, old_values=None, new_values=None, status='success'):
    """Log all database changes"""
    audit = AuditLog(
        user_id=request.user_id if hasattr(request, 'user_id') else None,
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=request.remote_addr,
        status=status
    )
    db.session.add(audit)
    db.session.commit()