# Chemical Equipment Parameter Visualizer - API Documentation

## Base URL
```
http://localhost:8002
```

## Authentication

All protected endpoints require JWT Bearer token authentication.

**Header Format:**
```
Authorization: Bearer <access_token>
```

---

## Endpoints

### 1. User Registration

**Endpoint:** `POST /api/register/`

**Description:** Register a new user account

**Authentication:** Not required

**Request Body:**
```json
{
  "username": "string" (required),
  "password": "string" (required),
  "email": "string" (optional)
}
```

**Success Response (201 Created):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "Username already exists"
}
```

---

### 2. Login (Obtain JWT Token)

**Endpoint:** `POST /api/token/`

**Description:** Get access and refresh tokens

**Authentication:** Not required

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Success Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Token Lifetime:**
- Access Token: 24 hours
- Refresh Token: 7 days

---

### 3. Refresh Token

**Endpoint:** `POST /api/token/refresh/`

**Description:** Get new access token using refresh token

**Authentication:** Not required

**Request Body:**
```json
{
  "refresh": "string"
}
```

**Success Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

### 4. Upload CSV

**Endpoint:** `POST /api/upload/`

**Description:** Upload and process a CSV file containing equipment data

**Authentication:** Required

**Request:**
- Content-Type: `multipart/form-data`
- Form Fields:
  - `file`: CSV file (required)
  - `name`: Dataset name (optional, defaults to filename)

**CSV Required Columns:**
- Equipment Name
- Equipment Type
- Flowrate
- Pressure
- Temperature

**Success Response (201 Created):**
```json
{
  "message": "File uploaded successfully",
  "dataset": {
    "id": 1,
    "name": "sample_data.csv",
    "upload_timestamp": "2025-01-28T10:30:00.123456Z",
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
    },
    "file_path": "/path/to/uploads/20250128_103000_sample_data.csv"
  },
  "raw_data": [
    {
      "Equipment Name": "Reactor-A1",
      "Equipment Type": "Reactor",
      "Flowrate": 150.5,
      "Pressure": 45.2,
      "Temperature": 120.3
    },
    // ... first 100 rows
  ]
}
```

**Error Responses:**

400 Bad Request - No file provided:
```json
{
  "error": "No file provided"
}
```

400 Bad Request - Invalid file type:
```json
{
  "error": "Only CSV files are allowed"
}
```

400 Bad Request - Missing columns:
```json
{
  "error": "Missing required columns: Flowrate, Pressure"
}
```

400 Bad Request - No valid data:
```json
{
  "error": "No valid data rows found"
}
```

---

### 5. Get Latest Summary

**Endpoint:** `GET /api/summary/latest/`

**Description:** Get summary and raw data of the most recently uploaded dataset

**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "summary": {
    "id": 1,
    "name": "sample_data.csv",
    "upload_timestamp": "2025-01-28T10:30:00.123456Z",
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
  "raw_data": [
    // All rows from the CSV
  ]
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "No datasets found"
}
```

---

### 6. Get History

**Endpoint:** `GET /api/history/`

**Description:** Get list of last 5 uploaded datasets

**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "history": [
    {
      "id": 5,
      "name": "dataset_5.csv",
      "upload_timestamp": "2025-01-28T12:00:00.123456Z",
      "total_equipment_count": 25,
      "avg_flowrate": 195.2,
      "avg_pressure": 62.1,
      "avg_temperature": 108.5,
      "equipment_type_distribution": { ... },
      "file_path": "/path/to/file"
    },
    {
      "id": 4,
      "name": "dataset_4.csv",
      "upload_timestamp": "2025-01-28T11:30:00.123456Z",
      // ...
    },
    // ... up to 5 datasets
  ]
}
```

---

### 7. Export CSV

**Endpoint:** `GET /api/export/csv/` or `GET /api/export/csv/<dataset_id>/`

**Description:** Download dataset as CSV file

**Authentication:** Required

**Parameters:**
- `dataset_id` (optional): Specific dataset ID. If not provided, exports latest dataset

**Success Response (200 OK):**
- Content-Type: `text/csv`
- Content-Disposition: `attachment; filename="<dataset_name>.csv"`
- Body: CSV file content

**Error Response (404 Not Found):**
```json
{
  "error": "Dataset not found"
}
```

---

### 8. Generate PDF Report

**Endpoint:** `GET /api/report/pdf/` or `GET /api/report/pdf/<dataset_id>/`

**Description:** Generate and download PDF report for a dataset

**Authentication:** Required

**Parameters:**
- `dataset_id` (optional): Specific dataset ID. If not provided, generates report for latest dataset

**Report Contents:**
1. Title and dataset information
2. Summary statistics table
3. Equipment type distribution table

**Success Response (200 OK):**
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename="<dataset_name>_report.pdf"`
- Body: PDF file content

**Error Response (404 Not Found):**
```json
{
  "error": "Dataset not found"
}
```

---

## Error Responses

### 401 Unauthorized
Returned when authentication token is missing or invalid.

```json
{
  "detail": "Authentication credentials were not provided."
}
```

or

```json
{
  "detail": "Given token not valid for any token type"
}
```

### 500 Internal Server Error
Returned when an unexpected server error occurs.

```json
{
  "error": "<error message>"
}
```

---

## cURL Examples

### Register User
```bash
curl -X POST http://localhost:8002/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123",
    "email": "test@example.com"
  }'
```

### Login
```bash
curl -X POST http://localhost:8002/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

### Upload CSV
```bash
TOKEN="your_access_token_here"

curl -X POST http://localhost:8002/api/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/your/data.csv" \
  -F "name=My Equipment Data"
```

### Get Latest Summary
```bash
curl -X GET http://localhost:8002/api/summary/latest/ \
  -H "Authorization: Bearer $TOKEN"
```

### Get History
```bash
curl -X GET http://localhost:8002/api/history/ \
  -H "Authorization: Bearer $TOKEN"
```

### Export CSV
```bash
curl -X GET http://localhost:8002/api/export/csv/ \
  -H "Authorization: Bearer $TOKEN" \
  --output dataset.csv
```

### Generate PDF Report
```bash
curl -X GET http://localhost:8002/api/report/pdf/ \
  -H "Authorization: Bearer $TOKEN" \
  --output report.pdf
```

---

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider adding:
- Django REST Framework throttling
- Rate limiting per user/IP
- Request quotas

---

## CORS Configuration

Currently configured to allow all origins for development:
```python
CORS_ALLOW_ALL_ORIGINS = True
```

**Production recommendation:**
```python
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://app.yourdomain.com",
]
```

---

## Data Retention

The system automatically maintains only the **last 5 datasets**. When a 6th dataset is uploaded, the oldest dataset is automatically deleted.

This behavior is implemented in the `Dataset.maintain_dataset_limit()` method.

---

## File Storage

Uploaded CSV files are stored in:
```
/app/django_backend/uploads/
```

File naming format:
```
<timestamp>_<original_filename>
```

Example:
```
20250128_103000_sample_data.csv
```
