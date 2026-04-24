# routes.py - Cases (Data Isolation)
from flask import Blueprint, request, jsonify
from models import db, Case, Debtor, Payment, Document, Notification
from auth import token_required, client_only, log_audit
from file_handler import FileHandler, OneDriveHandler
from datetime import datetime

cases_bp = Blueprint('cases', __name__, url_prefix='/api/cases')

@cases_bp.route('/create', methods=['POST'])
@token_required
@client_only
def create_case():
    """Create new case - FIXED TO ALLOW INSERTS"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['debtor_id', 'case_number', 'total_amount']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Verify debtor belongs to client
        debtor = Debtor.query.filter_by(
            debtor_id=data['debtor_id'],
            client_id=request.client_id
        ).first()
        
        if not debtor:
            return jsonify({'error': 'Debtor not found or does not belong to your organization'}), 404
        
        # Check if case number already exists
        if Case.query.filter_by(case_number=data['case_number']).first():
            return jsonify({'error': 'Case number already exists'}), 409
        
        # Create case
        case = Case(
            client_id=request.client_id,  # IMPORTANT: Set client_id from token
            debtor_id=data['debtor_id'],
            case_number=data['case_number'],
            total_amount=data['total_amount'],
            remaining_amount=data['total_amount'],
            currency=data.get('currency', 'USD'),
            status=data.get('status', 'active'),
            priority=data.get('priority', 'medium'),
            created_by=request.user_id
        )
        
        db.session.add(case)
        db.session.commit()
        
        log_audit('INSERT', 'cases', case.case_id, new_values=data)
        
        return jsonify({
            'message': 'Case created successfully',
            'case_id': case.case_id,
            'case_number': case.case_number
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@cases_bp.route('/my-cases', methods=['GET'])
@token_required
@client_only
def get_my_cases():
    """Get all cases for the logged-in client"""
    try:
        cases = Case.query.filter_by(client_id=request.client_id).all()
        
        cases_data = [{
            'case_id': c.case_id,
            'case_number': c.case_number,
            'debtor_name': f"{c.debtor.first_name} {c.debtor.last_name}",
            'total_amount': float(c.total_amount),
            'remaining_amount': float(c.remaining_amount),
            'status': c.status,
            'priority': c.priority,
            'created_at': c.created_at.isoformat()
        } for c in cases]
        
        return jsonify({'cases': cases_data}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cases_bp.route('/<case_id>/add-payment', methods=['POST'])
@token_required
@client_only
def add_payment(case_id):
    """Add payment to case"""
    try:
        # Verify case belongs to client
        case = Case.query.filter_by(
            case_id=case_id,
            client_id=request.client_id
        ).first()
        
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        data = request.get_json()
        if not all(k in data for k in ['amount', 'payment_method']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({'error': 'Amount must be greater than 0'}), 400
        
        if amount > float(case.remaining_amount):
            return jsonify({'error': 'Payment exceeds remaining amount'}), 400
        
        # Create payment
        payment = Payment(
            case_id=case_id,
            amount=amount,
            payment_method=data['payment_method'],
            transaction_ref=data.get('transaction_ref'),
            recorded_by=request.user_id,
            notes=data.get('notes')
        )
        
        # Update case remaining amount
        case.remaining_amount = float(case.remaining_amount) - amount
        
        # Update case status if fully paid
        if float(case.remaining_amount) <= 0:
            case.status = 'paid'
            case.remaining_amount = 0
        
        case.updated_at = datetime.utcnow()
        
        db.session.add(payment)
        db.session.commit()
        
        log_audit('INSERT', 'payments', payment.payment_id, new_values=data)
        
        return jsonify({
            'message': 'Payment recorded successfully',
            'payment_id': payment.payment_id,
            'remaining_amount': float(case.remaining_amount)
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500