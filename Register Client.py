# 1. Register Client
curl -X POST http://localhost:5000/api/auth/register-client \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "ABC Collections",
    "email": "admin@abccollections.com",
    "password": "SecurePass123",
    "phone": "+1234567890"
  }'

# 2. Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@abccollections.com",
    "password": "SecurePass123"
  }'

# 3. Create Debtor
curl -X POST http://localhost:5000/api/debtors/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+1987654321"
  }'

# 4. Create Case
curl -X POST http://localhost:5000/api/cases/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "debtor_id": "DEBTOR_ID",
    "case_number": "CASE-001",
    "total_amount": 5000.00,
    "priority": "high"
  }'

# 5. Upload Document (Local)
curl -X POST http://localhost:5000/api/cases/CASE_ID/upload-document-local \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "document_type=invoice" \
  -F "description=Monthly Invoice"

# 6. Upload Document (OneDrive)
curl -X POST http://localhost:5000/api/cases/CASE_ID/upload-document-onedrive \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "document_type=court_order"

# 7. Add Payment
curl -X POST http://localhost:5000/api/cases/CASE_ID/add-payment \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1000.00,
    "payment_method": "bank_transfer",
    "transaction_ref": "TXN-12345"
  }'

# 8. Get My Cases
curl -X GET http://localhost:5000/api/cases/my-cases \
  -H "Authorization: Bearer YOUR_TOKEN"

# 9. Debtor Login & View Own Cases
curl -X GET http://localhost:5000/api/debtor-portal/my-cases \
  -H "Authorization: Bearer DEBTOR_TOKEN"