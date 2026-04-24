-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS uuid-ossp;

-- ==================== CORE TABLES ====================

-- 1. ClientsOrganizations Table
CREATE TABLE IF NOT EXISTS clients (
    client_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Users Table (Clients & Admin Staff)
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(client_id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) NOT NULL CHECK (role IN ('super_admin', 'client_admin', 'client_user', 'debtor')),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Debtors Table
CREATE TABLE IF NOT EXISTS debtors (
    debtor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    id_number VARCHAR(50),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL, -- Link if debtor can login
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(client_id, email)
);

-- 4. Cases Table
CREATE TABLE IF NOT EXISTS cases (
    case_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    debtor_id UUID NOT NULL REFERENCES debtors(debtor_id) ON DELETE CASCADE,
    case_number VARCHAR(100) UNIQUE NOT NULL,
    total_amount DECIMAL(15, 2) NOT NULL,
    remaining_amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'paid', 'defaulted', 'closed')),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Payments Table
CREATE TABLE IF NOT EXISTS payments (
    payment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    amount DECIMAL(15, 2) NOT NULL,
    payment_method VARCHAR(50) CHECK (payment_method IN ('bank_transfer', 'check', 'cash', 'card', 'other')),
    transaction_ref VARCHAR(100),
    recorded_by UUID NOT NULL REFERENCES users(user_id),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Installment Plans
CREATE TABLE IF NOT EXISTS installment_plans (
    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    total_amount DECIMAL(15, 2) NOT NULL,
    installment_count INTEGER NOT NULL CHECK (installment_count  0),
    frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('weekly', 'bi-weekly', 'monthly', 'quarterly')),
    start_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'defaulted')),
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Installment Schedules
CREATE TABLE IF NOT EXISTS installment_schedules (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES installment_plans(plan_id) ON DELETE CASCADE,
    installment_number INTEGER NOT NULL,
    due_date DATE NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    paid_amount DECIMAL(15, 2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'overdue', 'waived')),
    payment_id UUID REFERENCES payments(payment_id) ON DELETE SET NULL
);

-- 8. Documents Table (Local & OneDrive)
CREATE TABLE IF NOT EXISTS documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
    document_type VARCHAR(50) CHECK (document_type IN ('court_order', 'agreement', 'invoice', 'statement', 'id_copy', 'proof_of_address', 'other')),
    file_name VARCHAR(255) NOT NULL,
    file_extension VARCHAR(10) NOT NULL,
    file_size BIGINT,
    storage_type VARCHAR(20) NOT NULL CHECK (storage_type IN ('local', 'onedrive')),
    file_path TEXT, -- Local system path
    onedrive_item_id TEXT, -- OneDrive unique ID
    onedrive_web_url TEXT, -- Shared link
    uploaded_by UUID NOT NULL REFERENCES users(user_id),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'DOWNLOAD')),
    table_name VARCHAR(50),
    record_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    status VARCHAR(20) DEFAULT 'success',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. Notifications
CREATE TABLE IF NOT EXISTS notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(case_id) ON DELETE CASCADE,
    recipient_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('email', 'sms', 'in_app')),
    subject TEXT,
    message_body TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'read')),
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. Document Metadata
CREATE TABLE IF NOT EXISTS document_metadata (
    metadata_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    meta_key VARCHAR(100) NOT NULL,
    meta_value TEXT
);

-- 12. OneDrive Sync Log
CREATE TABLE IF NOT EXISTS onedrive_sync_logs (
    sync_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(document_id) ON DELETE SET NULL,
    action VARCHAR(50) CHECK (action IN ('upload', 'update', 'delete', 'sync')),
    status VARCHAR(20) CHECK (status IN ('success', 'failed', 'pending')),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==================== INDEXING ====================

CREATE INDEX idx_users_client ON users(client_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_debtors_client ON debtors(client_id);
CREATE INDEX idx_debtors_user ON debtors(user_id);
CREATE INDEX idx_cases_client ON cases(client_id);
CREATE INDEX idx_cases_debtor ON cases(debtor_id);
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_payments_case ON payments(case_id);
CREATE INDEX idx_payments_date ON payments(payment_date);
CREATE INDEX idx_installments_case ON installment_plans(case_id);
CREATE INDEX idx_documents_case ON documents(case_id);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_table ON audit_logs(table_name);
CREATE INDEX idx_notifications_recipient ON notifications(recipient_id);
CREATE INDEX idx_notifications_case ON notifications(case_id);

-- ==================== SECURE VIEWS ====================

-- View for client users to see only their cases
CREATE OR REPLACE VIEW v_client_cases AS
SELECT 
    c.case_id, c.case_number, c.client_id, c.debtor_id,
    CONCAT(d.first_name, ' ', d.last_name) AS debtor_name,
    d.email, d.phone,
    c.total_amount, c.remaining_amount, c.status, c.priority,
    c.created_at
FROM cases c
JOIN debtors d ON c.debtor_id = d.debtor_id;

-- View for debtors to see their own cases and payments
CREATE OR REPLACE VIEW v_debtor_cases AS
SELECT 
    c.case_id, c.case_number, c.total_amount, c.remaining_amount, c.status,
    c.created_at, p.payment_id, p.amount as paid_amount, p.payment_date
FROM cases c
LEFT JOIN payments p ON c.case_id = p.case_id
ORDER BY c.created_at DESC;