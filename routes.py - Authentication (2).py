# routes.py - Authentication
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Client, AuditLog
from auth import create_token, log_audit
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register-client', methods=['POST'])
def register_client():
    """Register a new client organization"""
    try:
        data = request.get_json()
        
        # Validate input
        if not all(k in data for k in ['company_name', 'email', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if len(data['password']) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        # Check if client exists
        if Client.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Client already registered'}), 409
        
        # Create client
        client = Client(
            name=data['company_name'],
            email=data['email'],
            phone=data.get('phone')
        )
        db.session.add(client)
        db.session.flush()
        
        # Create admin user
        user = User(
            client_id=client.client_id,
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            first_name=data.get('first_name', 'Admin'),
            role='client_admin',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        
        log_audit('INSERT', 'clients', client.client_id, new_values=data)
        
        return jsonify({
            'message': 'Client registered successfully',
            'client_id': client.client_id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'User account is inactive'}), 403
        
        # Update last login
        user.last_login = db.func.now()
        db.session.commit()
        
        log_audit('LOGIN', 'users', user.user_id, status='success')
        
        token = create_token(user.user_id, user.client_id, user.role)
        
        return jsonify({
            'token': token,
            'user': {
                'user_id': user.user_id,
                'email': user.email,
                'role': user.role,
                'client_id': user.client_id
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """Change user password"""
    from auth import token_required
    
    @token_required
    def _change_password():
        try:
            data = request.get_json()
            
            user = User.query.get(request.user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if not check_password_hash(user.password_hash, data.get('old_password')):
                return jsonify({'error': 'Old password incorrect'}), 401
            
            if len(data.get('new_password', '')) < 8:
                return jsonify({'error': 'New password must be at least 8 characters'}), 400
            
            user.password_hash = generate_password_hash(data['new_password'])
            db.session.commit()
            
            log_audit('UPDATE', 'users', user.user_id, status='success')
            
            return jsonify({'message': 'Password changed successfully'}), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return _change_password()