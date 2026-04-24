# routes.py - Debtor Portal (Read-Only Access)
debtor_portal_bp = Blueprint('debtor_portal', __name__, url_prefix='/api/debtor-portal')

@debtor_portal_bp.route('/my-cases', methods=['GET'])
@token_required
def debtor_get_cases():
    """Debtor can only see their own cases"""
    try:
        if request.role != 'debtor':
            return jsonify({'error': 'Access denied'}), 403
        
        # Find debtor by user_id
        from models import Debtor
        debtor = Debtor.query.filter_by(user_id=request.user_id).first()
        
        if not debtor:
            return jsonify({'error': 'Debtor profile not found'}), 404
        
        cases = Case.query.filter_by(debtor_id=debtor.debtor_id).all()
        
        cases_data = [{
            'case_id': c.case_id,
            'case_number': c.case_number,
            'total_amount': float(c.total_amount),
            'remaining_amount': float(c.remaining_amount),
            'status': c.status,
            'created_at': c.created_at.isoformat()
        } for c in cases]
        
        return jsonify({'cases': cases_data}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@debtor_portal_bp.route('/case/<case_id>/payments', methods=['GET'])
@token_required
def debtor_get_payments(case_id):
    """Debtor can only see payments for their own cases"""
    try:
        if request.role != 'debtor':
            return jsonify({'error': 'Access denied'}), 403
        
        from models import Debtor
        debtor = Debtor.query.filter_by(user_id=request.user_id).first()
        
        case = Case.query.filter_by(
            case_id=case_id,
            debtor_id=debtor.debtor_id
        ).first()
        
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        payments = Payment.query.filter_by(case_id=case_id).all()
        
        payments_data = [{
            'payment_id': p.payment_id,
            'amount': float(p.amount),
            'payment_method': p.payment_method,
            'payment_date': p.payment_date.isoformat(),
            'transaction_ref': p.transaction_ref
        } for p in payments]
        
        return jsonify({'payments': payments_data}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500