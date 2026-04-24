# routes.py - Documents & File Upload
@cases_bp.route('/<case_id>/upload-document-local', methods=['POST'])
@token_required
@client_only
def upload_document_local(case_id):
    """Upload document to local storage"""
    try:
        # Verify case belongs to client
        case = Case.query.filter_by(
            case_id=case_id,
            client_id=request.client_id
        ).first()
        
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        doc_type = request.form.get('document_type', 'other')
        description = request.form.get('description', '')
        
        result = FileHandler.save_local_file(
            file, case_id, request.user_id, doc_type, description
        )
        
        if result['success']:
            log_audit('INSERT', 'documents', result['document_id'], new_values={'case_id': case_id})
            return jsonify({
                'message': 'Document uploaded successfully',
                'document_id': result['document_id']
            }), 201
        else:
            return jsonify({'error': result['error']}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cases_bp.route('/<case_id>/upload-document-onedrive', methods=['POST'])
@token_required
@client_only
def upload_document_onedrive(case_id):
    """Upload document to OneDrive"""
    try:
        # Verify case belongs to client
        case = Case.query.filter_by(
            case_id=case_id,
            client_id=request.client_id
        ).first()
        
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        doc_type = request.form.get('document_type', 'other')
        description = request.form.get('description', '')
        
        handler = OneDriveHandler()
        result = handler.upload_file(
            file, case_id, request.user_id, doc_type, description
        )
        
        if result['success']:
            log_audit('INSERT', 'documents', result['document_id'], new_values={'case_id': case_id})
            return jsonify({
                'message': 'Document uploaded to OneDrive successfully',
                'document_id': result['document_id'],
                'onedrive_url': result['onedrive_url']
            }), 201
        else:
            return jsonify({'error': result['error']}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cases_bp.route('/<case_id>/documents', methods=['GET'])
@token_required
@client_only
def get_case_documents(case_id):
    """Get all documents for a case"""
    try:
        case = Case.query.filter_by(
            case_id=case_id,
            client_id=request.client_id
        ).first()
        
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        documents = Document.query.filter_by(
            case_id=case_id,
            is_active=True
        ).all()
        
        docs_data = [{
            'document_id': d.document_id,
            'file_name': d.file_name,
            'document_type': d.document_type,
            'storage_type': d.storage_type,
            'onedrive_url': d.onedrive_web_url,
            'created_at': d.created_at.isoformat()
        } for d in documents]
        
        return jsonify({'documents': docs_data}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500