# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from uuid import uuid4
import uuid

db = SQLAlchemy()

class Client(db.Model):
    __tablename__ = 'clients'
    client_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    users = db.relationship('User', backref='client', cascade='all, delete-orphan')
    debtors = db.relationship('Debtor', backref='client', cascade='all, delete-orphan')
    cases = db.relationship('Case', backref='client', cascade='all, delete-orphan')


class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.client_id'))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    role = db.Column(db.String(50), nullable=False)  # super_admin, client_admin, client_user, debtor
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Debtor(db.Model):
    __tablename__ = 'debtors'
    debtor_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.client_id'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    id_number = db.Column(db.String(50))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    cases = db.relationship('Case', backref='debtor', cascade='all, delete-orphan')


class Case(db.Model):
    __tablename__ = 'cases'
    case_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.client_id'), nullable=False)
    debtor_id = db.Column(db.String(36), db.ForeignKey('debtors.debtor_id'), nullable=False)
    case_number = db.Column(db.String(100), unique=True, nullable=False)
    total_amount = db.Column(db.Numeric(15, 2), nullable=False)
    remaining_amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(50), default='active')
    priority = db.Column(db.String(20), default='medium')
    created_by = db.Column(db.String(36), db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    payments = db.relationship('Payment', backref='case', cascade='all, delete-orphan')
    documents = db.relationship('Document', backref='case', cascade='all, delete-orphan')
    installments = db.relationship('InstallmentPlan', backref='case', cascade='all, delete-orphan')


class Payment(db.Model):
    __tablename__ = 'payments'
    payment_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey('cases.case_id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    transaction_ref = db.Column(db.String(100))
    recorded_by = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class InstallmentPlan(db.Model):
    __tablename__ = 'installment_plans'
    plan_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey('cases.case_id'), nullable=False)
    total_amount = db.Column(db.Numeric(15, 2), nullable=False)
    installment_count = db.Column(db.Integer, nullable=False)
    frequency = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='active')
    created_by = db.Column(db.String(36), db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Document(db.Model):
    __tablename__ = 'documents'
    document_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey('cases.case_id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_extension = db.Column(db.String(10), nullable=False)
    file_size = db.Column(db.BigInteger)
    storage_type = db.Column(db.String(20), nullable=False)  # local, onedrive
    file_path = db.Column(db.Text)
    onedrive_item_id = db.Column(db.Text)
    onedrive_web_url = db.Column(db.Text)
    uploaded_by = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    log_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'))
    action = db.Column(db.String(50), nullable=False)
    table_name = db.Column(db.String(50))
    record_id = db.Column(db.String(36))
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    status = db.Column(db.String(20), default='success')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = 'notifications'
    notification_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey('cases.case_id'))
    recipient_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    channel = db.Column(db.String(20), nullable=False)  # email, sms, in_app
    subject = db.Column(db.Text)
    message_body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    sent_at = db.Column(db.DateTime)
    read_at = db.Column(db.DateTime)
    retry_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)