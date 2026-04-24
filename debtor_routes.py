# routes.py - Debtors
debtors_bp = Blueprint('debtors', __name__, url_prefix='/api/debtors')

@debtors_bp.route('/create', methods=['POST'])
@token_required
@client_only
def create_debtor():
    """Create new debtor"""
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['first_name', 'last_name']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        debtor = Debtor(
            client_id=request.client_id,  # IMPORTANT: Set client_id
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            city=data.get('city'),
            country=data.get('country'),
            id_number=data.get('id_number')
        )
        
        db.session.add(debtor)
        db.session.commit()
        
        log_audit('INSERT', 'debtors', debtor.debtor_id, new_values=data)
        
        return jsonify({
            'message': 'Debtor created successfully',
            'debtor_id': debtor.debtor_id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@debtors_bp.route('/my-debtors', methods=['GET'])
@token_required
@client_only
def get_my_debtors():
    """Get all debtors for client"""
    try:
        debtors = Debtor.query.filter_by(
            client_id=request.client_id,
            is_active=True
        ).all()
        
        debtors_data = [{
            'debtor_id': d.debtor_id,
            'name': f"{d.first_name} {d.last_name}",
            'email': d.email,
            'phone': d.phone,
            'created_at': d.created_at.isoformat()
        } for d in debtors]
        
        return jsonify({'debtors': debtors_data}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
