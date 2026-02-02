# Testing Guide - Chemical Equipment Visualizer

## Quick Start Testing

### Prerequisites
- Django backend running on port 8002
- React frontend running on port 3000
- Sample CSV file at /app/django_backend/sample_data.csv

---

## 1. Backend API Testing (Django)

### Test Authentication

Register:
```bash
curl -X POST http://localhost:8002/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123", "email": "test@example.com"}'
```

Login:
```bash
curl -X POST http://localhost:8002/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Test CSV Upload

```bash
TOKEN=$(curl -s -X POST http://localhost:8002/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access'])")

curl -X POST http://localhost:8002/api/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/app/django_backend/sample_data.csv" \
  -F "name=Sample Equipment Data"
```

### Test Other Endpoints

Get Summary:
```bash
curl -X GET http://localhost:8002/api/summary/latest/ -H "Authorization: Bearer $TOKEN"
```

Get History:
```bash
curl -X GET http://localhost:8002/api/history/ -H "Authorization: Bearer $TOKEN"
```

Export CSV:
```bash
curl -X GET http://localhost:8002/api/export/csv/ -H "Authorization: Bearer $TOKEN" --output exported.csv
```

Export PDF:
```bash
curl -X GET http://localhost:8002/api/report/pdf/ -H "Authorization: Bearer $TOKEN" --output report.pdf
```

## 2. Frontend Testing

1. Open http://localhost:3000
2. Login with admin/admin123
3. Upload sample CSV
4. Verify charts and data table
5. Test export buttons

## 3. Validation Checklist

Backend:
- [x] Django on port 8002
- [x] JWT authentication
- [x] CSV upload & processing
- [x] Summary statistics
- [x] Last 5 datasets retention
- [x] PDF generation
- [x] All APIs working

Frontend:
- [x] React on port 3000
- [x] Login/Register pages
- [x] Dashboard with charts
- [x] Data table
- [x] Export functionality
- [x] Responsive design

See API_DOCUMENTATION.md for detailed API specs.
