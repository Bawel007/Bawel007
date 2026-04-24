# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from app import app; app.app_context().push(); from models import db; db.create_all()"

# Run Flask
python app.py