# file_handler.py
import os
import secrets
from werkzeug.utils import secure_filename
from config import Config
from models import db, Document
import requests
from msal import PublicClientApplication

class FileHandler:
    
    @staticmethod
    def allowed_file(filename):
        """Validate file extension"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    
    @staticmethod
    def save_local_file(file, case_id, user_id, doc_type, description=''):
        """Save file to local storage"""
        if not FileHandler.allowed_file(file.filename):
            return {'success': False, 'error': 'File type not allowed'}
        
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{secrets.token_hex(16)}.{ext}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        try:
            file.save(file_path)
            file_size = os.path.getsize(file_path)
            
            # Save document record
            document = Document(
                case_id=case_id,
                document_type=doc_type,
                file_name=file.filename,
                file_extension=ext,
                file_size=file_size,
                storage_type='local',
                file_path=file_path,
                uploaded_by=user_id,
                description=description
            )
            db.session.add(document)
            db.session.commit()
            
            return {
                'success': True,
                'document_id': document.document_id,
                'file_path': file_path
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}

class OneDriveHandler:
    """Handle OneDrive integration via Microsoft Graph API"""
    
    def __init__(self):
        self.tenant_id = Config.ONEDRIVE_TENANT_ID
        self.client_id = Config.ONEDRIVE_CLIENT_ID
        self.client_secret = Config.ONEDRIVE_CLIENT_SECRET
        self.graph_url = "https://graph.microsoft.com/v1.0"
    
    def get_access_token(self):
        """Get OneDrive access token using Client Credentials flow"""
        try:
            app = PublicClientApplication(
                client_id=self.client_id,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            
            result = app.acquire_token_for_client(
                scopes=["https://graph.microsoft.com/.default"]
            )
            
            if 'access_token' in result:
                return result['access_token']
            return None
        except Exception as e:
            print(f"Token Error: {str(e)}")
            return None
    
    def upload_file(self, file, case_id, user_id, doc_type, description=''):
        """Upload file to OneDrive"""
        token = self.get_access_token()
        if not token:
            return {'success': False, 'error': 'OneDrive authentication failed'}
        
        try:
            # Prepare file
            file_name = secure_filename(file.filename)
            file_content = file.read()
            file_size = len(file_content)
            ext = file_name.rsplit('.', 1)[1].lower() if '.' in file_name else ''
            
            # Upload to OneDrive
            headers = {'Authorization': f'Bearer {token}'}
            upload_url = f"{self.graph_url}/me/drive/root:/DebtManager/{file_name}:/content"
            
            response = requests.put(
                upload_url,
                headers=headers,
                data=file_content
            )
            
            if response.status_code == 201:
                file_data = response.json()
                
                # Save document record
                document = Document(
                    case_id=case_id,
                    document_type=doc_type,
                    file_name=file_name,
                    file_extension=ext,
                    file_size=file_size,
                    storage_type='onedrive',
                    onedrive_item_id=file_data.get('id'),
                    onedrive_web_url=file_data.get('webUrl'),
                    uploaded_by=user_id,
                    description=description
                )
                db.session.add(document)
                db.session.commit()
                
                return {
                    'success': True,
                    'document_id': document.document_id,
                    'onedrive_url': file_data.get('webUrl')
                }
            else:
                return {'success': False, 'error': f'OneDrive upload failed: {response.text}'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}