# Chemical Equipment Parameter Visualizer

A complete **Hybrid Web + Desktop Application** for analyzing and visualizing chemical equipment parameters from CSV files.

## 🏭 Architecture Overview

### Technology Stack
- **Backend**: Django 5.2 + Django REST Framework
- **Database**: SQLite3 (file-based)
- **Frontend (Web)**: React 19 + Chart.js
- **Frontend (Desktop)**: PyQt5 + Matplotlib (To be implemented)
- **Data Processing**: Pandas
- **Authentication**: JWT (Simple JWT)
- **PDF Generation**: ReportLab

### System Architecture
```
┌─────────────────┐
│  React Web App   │
│  (Port 3000)     │
└────────┬────────┘
         │
         │ REST API
         │
┌────────┴────────┐
│  Django Backend  │
│  (Port 8002)     │
│                  │
│  • REST APIs     │
│  • Pandas        │
│  • ReportLab     │
└────────┬────────┘
         │
┌────────┴────────┐
│  SQLite Database │
│  (db.sqlite3)    │
└─────────────────┘
```

---

## 📁 Project Structure

```
/app/
├── django_backend/           # Django Backend
│   ├── chemical_visualizer/   # Django Project
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── api/                   # Django App
│   │   ├── models.py          # Dataset model
│   │   ├── serializers.py     # DRF serializers
│   │   ├── views.py           # API views
│   │   └── urls.py            # API routes
│   ├── uploads/               # CSV file storage
│   ├── db.sqlite3             # SQLite database
│   ├── manage.py
│   ├── venv/                  # Python virtual env
│   └── sample_data.csv        # Test CSV file
│
└── frontend/                 # React Frontend
    ├── src/
    │   ├── components/
    │   │   ├── Login.jsx
    │   │   ├── Register.jsx
    │   │   └── Dashboard.jsx
    │   ├── App.js
    │   ├── App.css
    │   └── index.js
    ├── package.json
    └── .env
```

---

## 📦 Features Implemented

### Backend Features
1. **CSV Upload & Processing**
   - Validates CSV structure (required columns)
   - Parses CSV using Pandas
   - Computes summary statistics
   - Stores metadata in SQLite

2. **Dataset Management**
   - Automatically maintains last 5 datasets
   - Auto-deletes older datasets
   - Tracks upload timestamp and user

3. **Summary Statistics**
   - Total equipment count
   - Average flowrate, pressure, temperature
   - Equipment type distribution (JSON)

4. **REST APIs**
   - `POST /api/upload/` - Upload CSV
   - `GET /api/summary/latest/` - Get latest dataset summary
   - `GET /api/history/` - Get last 5 datasets
   - `GET /api/export/csv/` - Export dataset as CSV
   - `GET /api/report/pdf/` - Generate PDF report
   - `POST /api/register/` - User registration
   - `POST /api/token/` - JWT login

5. **Authentication**
   - JWT-based authentication
   - Token-based API access
   - User registration and login

6. **PDF Report Generation**
   - Professional PDF reports using ReportLab
   - Summary statistics tables
   - Equipment type distribution

### Frontend Features
1. **Authentication Pages**
   - Login page
   - Registration page
   - JWT token management

2. **Dashboard**
   - CSV file upload form
   - Summary statistics cards
   - Interactive charts (Chart.js)
     - Pie chart: Equipment type distribution
     - Bar chart: Parameter comparison
   - Data table (first 50 rows)
   - Export CSV and PDF buttons

3. **Visualizations**
   - Equipment type distribution (Pie chart)
   - Parameter comparison (Bar chart)
   - Responsive design
   - Dark theme with glassmorphism

---

## 🚀 Setup Instructions

### Backend Setup

1. **Navigate to Django backend**
```bash
cd /app/django_backend
```

2. **Activate virtual environment**
```bash
source venv/bin/activate
```

3. **Install dependencies** (Already done)
```bash
pip install django djangorestframework djangorestframework-simplejwt pandas reportlab Pillow django-cors-headers
```

4. **Run migrations** (Already done)
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Create superuser** (Already created: admin/admin123)
```bash
python manage.py createsuperuser
```

6. **Start Django server**
```bash
python manage.py runserver 0.0.0.0:8002
```

Or use supervisor:
```bash
sudo supervisorctl restart django_backend
```

### Frontend Setup

1. **Navigate to frontend**
```bash
cd /app/frontend
```

2. **Install dependencies** (Already done)
```bash
yarn add chart.js react-chartjs-2
```

3. **Start React app**
```bash
yarn start
```

Or use supervisor:
```bash
sudo supervisorctl restart frontend
```

---

## 📋 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/register/
Content-Type: application/json

{
  "username": "testuser",
  "password": "password123",
  "email": "test@example.com"
}

Response: 201 Created
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com"
  }
}
```

#### Login (Get JWT Token)
```http
POST /api/token/
Content-Type: application/json

{
  "username": "testuser",
  "password": "password123"
}

Response: 200 OK
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOi...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOi..."
}
```

### Dataset Endpoints (Requires Authentication)

All requests must include:
```
Authorization: Bearer <access_token>
```

#### Upload CSV
```http
POST /api/upload/
Content-Type: multipart/form-data
Authorization: Bearer <token>

Form Data:
  file: <csv_file>
  name: "My Dataset" (optional)

Response: 201 Created
{
  "message": "File uploaded successfully",
  "dataset": {
    "id": 1,
    "name": "sample_data.csv",
    "upload_timestamp": "2025-01-28T10:30:00Z",
    "total_equipment_count": 20,
    "avg_flowrate": 188.55,
    "avg_pressure": 58.73,
    "avg_temperature": 104.32,
    "equipment_type_distribution": {
      "Reactor": 4,
      "Pump": 5,
      "Heat Exchanger": 5,
      "Distillation Column": 2,
      "Compressor": 2,
      "Mixer": 2,
      "Separator": 2
    }
  },
  "raw_data": [ ... ] // First 100 rows
}
```

#### Get Latest Summary
```http
GET /api/summary/latest/
Authorization: Bearer <token>

Response: 200 OK
{
  "summary": {
    "id": 1,
    "name": "sample_data.csv",
    "upload_timestamp": "2025-01-28T10:30:00Z",
    "total_equipment_count": 20,
    "avg_flowrate": 188.55,
    "avg_pressure": 58.73,
    "avg_temperature": 104.32,
    "equipment_type_distribution": { ... }
  },
  "raw_data": [ ... ] // All rows
}
```

#### Get History
```http
GET /api/history/
Authorization: Bearer <token>

Response: 200 OK
{
  "history": [
    { ... dataset 1 ... },
    { ... dataset 2 ... },
    ...
  ]
}
```

#### Export CSV
```http
GET /api/export/csv/
GET /api/export/csv/<dataset_id>/
Authorization: Bearer <token>

Response: 200 OK (CSV file download)
```

#### Generate PDF Report
```http
GET /api/report/pdf/
GET /api/report/pdf/<dataset_id>/
Authorization: Bearer <token>

Response: 200 OK (PDF file download)
```

---

## 📊 CSV File Format

Required columns:
```
Equipment Name,Equipment Type,Flowrate,Pressure,Temperature
```

Example:
```csv
Equipment Name,Equipment Type,Flowrate,Pressure,Temperature
Reactor-A1,Reactor,150.5,45.2,120.3
Pump-B2,Pump,200.0,60.5,85.7
Heat Exchanger-C3,Heat Exchanger,180.3,55.0,95.2
```

**Sample file available at**: `/app/django_backend/sample_data.csv`

---

## 🔑 Default Credentials

**Admin User:**
- Username: `admin`
- Password: `admin123`

**Test User** (create via registration):
- Username: `testuser`
- Password: `password123`

---

## 🧪 Testing the Application

### 1. Test Backend APIs

**Login and get token:**
```bash
curl -X POST http://localhost:8002/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Upload CSV:**
```bash
TOKEN="<your_access_token>"
curl -X POST http://localhost:8002/api/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/app/django_backend/sample_data.csv" \
  -F "name=Sample Dataset"
```

**Get latest summary:**
```bash
curl -X GET http://localhost:8002/api/summary/latest/ \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Test Frontend

1. Open browser: `http://localhost:3000`
2. Register a new user or login with admin credentials
3. Upload the sample CSV file
4. View statistics, charts, and data table
5. Export CSV or PDF report

---

## 🔧 Technology Details

### Backend (Django)

**Key Dependencies:**
- `django==5.2.10` - Web framework
- `djangorestframework==3.16.1` - REST API framework
- `djangorestframework-simplejwt==5.5.1` - JWT authentication
- `pandas==3.0.0` - Data processing
- `reportlab==4.4.9` - PDF generation
- `django-cors-headers==4.9.0` - CORS support

**Database Model:**
```python
class Dataset(models.Model):
    name = CharField(max_length=255)
    upload_timestamp = DateTimeField(auto_now_add=True)
    total_equipment_count = IntegerField()
    avg_flowrate = FloatField()
    avg_pressure = FloatField()
    avg_temperature = FloatField()
    equipment_type_distribution = JSONField()
    file_path = CharField(max_length=500)
    uploaded_by = ForeignKey(User)
```

### Frontend (React)

**Key Dependencies:**
- `react==19.0.0` - UI framework
- `react-router-dom==7.5.1` - Routing
- `chart.js==4.5.1` - Charting library
- `react-chartjs-2==5.3.1` - React wrapper for Chart.js
- `axios==1.8.4` - HTTP client

**Chart Types:**
1. **Pie Chart** - Equipment type distribution
2. **Bar Chart** - Parameter comparison (Flowrate, Pressure, Temperature)

---

## 🔐 Security Features

1. **JWT Authentication**
   - Secure token-based auth
   - 24-hour access token lifetime
   - 7-day refresh token lifetime

2. **Protected Routes**
   - All data endpoints require authentication
   - Frontend route protection

3. **CORS Configuration**
   - Configured for development (allow all origins)
   - Should be restricted in production

4. **Password Validation**
   - Django built-in validators
   - Minimum length, complexity checks

---

## 🚧 Future Enhancements

### Phase 2: Desktop Application (PyQt5)
- [ ] PyQt5 desktop interface
- [ ] File upload dialog
- [ ] Data table with QTableWidget
- [ ] Matplotlib charts integration
- [ ] Same REST API integration
- [ ] Local settings storage

### Additional Features
- [ ] Real-time data streaming
- [ ] Advanced filtering and search
- [ ] Custom report templates
- [ ] Email notifications
- [ ] Data export to Excel
- [ ] Chart customization options
- [ ] Multi-user collaboration
- [ ] Historical trend analysis
- [ ] Anomaly detection using ML

---

## 🐛 Troubleshooting

### Backend Issues

**Database locked error:**
```bash
cd /app/django_backend
rm db.sqlite3
python manage.py migrate
```

**Check Django logs:**
```bash
tail -f /var/log/supervisor/django_backend.*.log
```

**Restart Django:**
```bash
sudo supervisorctl restart django_backend
```

### Frontend Issues

**Clear cache and restart:**
```bash
cd /app/frontend
rm -rf node_modules/.cache
sudo supervisorctl restart frontend
```

**Check frontend logs:**
```bash
tail -f /var/log/supervisor/frontend.*.log
```

---

## 📝 Best Practices Implemented

1. **Clean Code Structure**
   - Modular Django app design
   - Reusable React components
   - Separation of concerns

2. **RESTful API Design**
   - Standard HTTP methods
   - Proper status codes
   - Consistent response format

3. **Error Handling**
   - Validation errors
   - Authentication errors
   - User-friendly error messages

4. **Data Validation**
   - CSV structure validation
   - Required column checks
   - Data type validation

5. **Responsive Design**
   - Mobile-friendly interface
   - Flexible grid layouts
   - Adaptive components

6. **Performance**
   - Efficient Pandas operations
   - Pagination for large datasets
   - Optimized queries

---

## 📞 Support

For issues or questions:
1. Check logs in `/var/log/supervisor/`
2. Review API responses for error details
3. Verify authentication tokens
4. Ensure CSV format is correct

---

## ✅ Project Status

**Completed:**
- ✅ Django backend with DRF
- ✅ SQLite database
- ✅ CSV upload and processing
- ✅ Summary statistics calculation
- ✅ REST APIs (all endpoints)
- ✅ JWT authentication
- ✅ PDF report generation
- ✅ React web frontend
- ✅ Chart.js visualizations
- ✅ Data table display
- ✅ Export functionality
- ✅ Responsive design

**Pending:**
- ⏳ PyQt5 desktop application
- ⏳ Matplotlib desktop charts

---

**Built with ❤️ using Django REST Framework + React + Chart.js**
