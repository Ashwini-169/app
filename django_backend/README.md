# Django Backend API - Production Guide

Django REST Framework backend for Chemical Equipment Parameter Visualizer with Gunicorn production server.

## 🚀 Quick Start

### Production (Railway)
```bash
# Automatically deployed via Docker
# Backend running at: https://chemical-backend-production-dd2c.up.railway.app
```

### Local Development
```bash
cd django_backend

# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Run development server
python manage.py runserver 0.0.0.0:8002
```

**Backend running at**: http://localhost:8002

---

## 🏗️ Project Structure

```
django_backend/
├── Dockerfile                      # Production container
├── start.sh                        # Startup script (migrations + Gunicorn)
├── requirements.txt                # Python dependencies
├── manage.py                       # Django management
├── db.sqlite3                      # SQLite database
├── railway.json                    # Railway deployment config
│
├── chemical_visualizer/            # Django project
│   ├── settings.py                 # CORS, CSRF, JWT, DATABASES
│   ├── urls.py                     # URL routing
│   ├── wsgi.py                     # WSGI application
│   └── asgi.py                     # ASGI (async support)
│
├── api/                            # REST API app
│   ├── models.py                   # Dataset model
│   ├── views.py                    # API endpoint handlers
│   ├── serializers.py              # DRF serializers
│   ├── urls.py                     # API routes
│   ├── admin.py                    # Django admin
│   └── migrations/                 # Database migrations
│
└── uploads/                        # CSV file storage
```

---

## 🔧 Configuration

### settings.py - Key Settings

#### Database
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

#### JWT Authentication
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ALGORITHM': 'HS256',
}
```

#### CORS & CSRF
```python
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    'https://chemical-backend-production-dd2c.up.railway.app',
    'https://*.railway.app',
    'http://localhost:3000',
    'http://localhost:8000',
]
```

---

## 📚 API Endpoints

### Authentication

#### Login
```http
POST /api/token/
Content-Type: application/json

{
  "username": "testuser",
  "password": "testpass123"
}

Response (200):
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Refresh Token
```http
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response (200):
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Register
```http
POST /api/register/
Content-Type: application/json

{
  "username": "newuser",
  "password": "securepass123",
  "email": "user@example.com"
}

Response (201):
{
  "id": 1,
  "username": "newuser",
  "email": "user@example.com"
}
```

#### Health Check
```http
GET /api/health/

Response (200):
{
  "status": "healthy",
  "service": "chemical-backend"
}
```

### Data Operations

#### Upload CSV
```http
POST /api/upload/
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <csv_file>
name: "Dataset Name"

Response (201):
{
  "message": "File uploaded successfully",
  "dataset": {
    "id": 1,
    "name": "Dataset Name",
    "total_equipment_count": 100,
    "avg_flowrate": 45.5,
    "avg_pressure": 30.2,
    "avg_temperature": 25.0
  },
  "raw_data": [...]
}
```

#### Get Latest Summary
```http
GET /api/summary/latest/
Authorization: Bearer <token>

Response (200):
{
  "summary": {
    "id": 1,
    "name": "Dataset Name",
    "total_equipment_count": 100,
    "avg_flowrate": 45.5,
    "avg_pressure": 30.2,
    "avg_temperature": 25.0
  },
  "raw_data": [...]
}
```

#### Get History
```http
GET /api/history/
Authorization: Bearer <token>

Response (200):
{
  "history": [
    {
      "id": 1,
      "name": "Dataset 1",
      "upload_timestamp": "2026-02-03T10:30:00Z",
      "total_equipment_count": 100
    },
    ...
  ]
}
```

#### Export CSV
```http
GET /api/export/csv/
Authorization: Bearer <token>

Response (200):
Content-Type: text/csv

<csv_data>
```

#### Generate PDF Report
```http
GET /api/report/pdf/
Authorization: Bearer <token>

Response (200):
Content-Type: application/pdf

<pdf_data>
```

---

## 🚀 Production Deployment

### Docker Build
```bash
docker build -t chemical-backend ./django_backend
```

### Run Container
```bash
docker run \
  -e PORT=8000 \
  -e DEBUG=False \
  -e ALLOWED_HOSTS=* \
  -p 8000:8000 \
  chemical-backend
```

### Railway Deployment
```bash
# Push to GitHub - Railway auto-deploys
git push origin master

# Monitor: https://railway.app
```

### Startup Process
1. `start.sh` runs on container start
2. Applies pending migrations
3. Starts Gunicorn (3 workers)
4. Health check validates `/api/health/`

---

## 🔐 Security Features

### Authentication
- JWT tokens (24hr access, 7-day refresh)
- Secure password hashing (PBKDF2)
- User registration validation

### Authorization
- `@permission_classes([AllowAny])` for public endpoints
- `@permission_classes([IsAuthenticated])` for protected endpoints

### CORS/CSRF
- CorsMiddleware positioned first (critical)
- CSRF tokens for all form submissions
- Trusted origins for Railway domains

### Data Protection
- SQLite database (file-based)
- Uploaded files stored in `/uploads/`
- File validation on upload

---

## 🧪 Testing

### Unit Tests
```bash
python manage.py test api
```

### Manual API Tests
```bash
# Login
curl -X POST http://localhost:8002/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Get token from response, then:
curl -X GET http://localhost:8002/api/summary/latest/ \
  -H "Authorization: Bearer <token>"

# Health check (no auth needed)
curl http://localhost:8002/api/health/
```

---

## 🔧 Troubleshooting

### Database Errors
```bash
# Check migrations
python manage.py showmigrations

# Apply pending migrations
python manage.py migrate

# Create new migration
python manage.py makemigrations
python manage.py migrate
```

### Import Errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Permission Errors (CORS)
1. Verify `CorsMiddleware` is first in MIDDLEWARE
2. Check `CORS_ALLOWED_ORIGINS` includes your domain
3. Check `CSRF_TRUSTED_ORIGINS` for POST requests

### Port Already in Use
```bash
# Use different port
python manage.py runserver 0.0.0.0:8003
```

---

## 📦 Dependencies

See `requirements.txt`:
```
Django>=4.2.0
djangorestframework>=3.14.0
djangorestframework-simplejwt>=5.2.0
pandas>=2.0.0
reportlab>=4.0.0
matplotlib>=3.7.0
django-cors-headers>=4.0.0
gunicorn>=21.2.0
```

---

## 🚀 Performance Optimization

### Gunicorn Settings
- **Workers**: 2-3 per CPU core
- **Timeout**: 120s for long operations
- **Access logging**: Enabled for monitoring

### Database
- SQLite sufficient for single-instance deployment
- For production scale: migrate to PostgreSQL
- Backup database regularly

### Caching
- Redis ready (add to requirements.txt if needed)
- Static files collected in `staticfiles/`

---

## 📝 Deployment Checklist

Before production deploy:
- [ ] `DEBUG = False`
- [ ] `SECRET_KEY` changed
- [ ] `ALLOWED_HOSTS` configured
- [ ] HTTPS enforced
- [ ] CORS origins validated
- [ ] Database backed up
- [ ] Static files collected
- [ ] Migrations tested locally

---

## 📞 Support

- Check [API_DOCUMENTATION.md](../API_DOCUMENTATION.md) for detailed API specs
- See main [README.md](../README.md) for system overview
- Django docs: https://docs.djangoproject.com/

---

**Version**: 1.0.0  
**Last Updated**: February 3, 2026  
**Status**: Production-Ready ✅
