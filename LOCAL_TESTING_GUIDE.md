# Local Testing Guide - Frontend with Production Backend

This guide explains how to test the frontend locally (localhost) while connecting to the Railway-hosted backend.

## Quick Start

### 1. Switch to Production Backend URL

Edit `frontend/.env`:
```bash
# Change from:
REACT_APP_API_URL=http://localhost:8000

# To:
REACT_APP_API_URL=https://chemical-backend-production-dd2c.up.railway.app
```

### 2. Start Frontend Dev Server

```bash
cd frontend
npm start
```

Your browser will open automatically at: `http://localhost:3000`

### 3. Test the Application

- Login with your credentials
- Upload CSV files
- Export data
- View charts and analytics

The frontend will run on **localhost:3000** but all API calls will go to the **production Railway backend**.

---

## Environment Configuration

### Available Configurations

**Option A: Local Development (Both frontend and backend local)**
```
REACT_APP_API_URL=http://localhost:8000
```
Requirements:
- Backend running on `python manage.py runserver 0.0.0.0:8000`
- Frontend running on `npm start`

**Option B: Local Frontend + Production Backend (Current Setup)**
```
REACT_APP_API_URL=https://chemical-backend-production-dd2c.up.railway.app
```
Requirements:
- Backend deployed on Railway
- Frontend running locally on `npm start`
- ✅ CORS already configured in Django settings

**Option C: Production Frontend + Production Backend**
```
# No environment variable needed (Docker build arg)
ARG REACT_APP_API_URL=https://chemical-backend-production-dd2c.up.railway.app
```

---

## CORS Configuration Status

✅ **CORS is properly configured** in Django settings:

- `CORS_ALLOW_ALL_ORIGINS = True` - Allows requests from any origin
- `http://localhost:3000` - Explicitly added to CSRF_TRUSTED_ORIGINS
- `https://chemical-backend-production-dd2c.up.railway.app` - Self-reference allowed
- All standard HTTP methods and headers allowed

No additional CORS configuration needed.

---

## Troubleshooting

### Issue: "API is not responding" or 404 errors

**Solution 1:** Verify the correct backend URL
```bash
curl -X GET https://chemical-backend-production-dd2c.up.railway.app/api/health/
```

**Solution 2:** Check environment variable loaded
```bash
# In frontend browser console:
console.log(process.env.REACT_APP_API_URL)
```

**Solution 3:** Clear React dev server cache
```bash
# Stop the dev server (Ctrl+C)
npm start
```

### Issue: 401 Unauthorized errors

**Solution:** Clear localStorage and login again
```javascript
// In browser console:
localStorage.clear()
// Refresh page and login
```

### Issue: CORS errors in browser console

The current setup should not have CORS errors because:
- Django CORS is configured to allow all origins
- Your requests include proper Authorization headers
- Credentials are handled correctly

If you still see CORS errors:
1. Check that `REACT_APP_API_URL` is set correctly in `.env`
2. Restart the dev server: `npm start`
3. Hard refresh in browser: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)

---

## Backend Health Check

Before testing, verify the backend is running:

```bash
curl -X GET https://chemical-backend-production-dd2c.up.railway.app/api/health/ \
  -H "Content-Type: application/json"
```

Expected response:
```json
{
  "status": "healthy",
  "service": "chemical-backend"
}
```

---

## Notes

- **Frontend Port:** 3000
- **Backend URL:** https://chemical-backend-production-dd2c.up.railway.app
- **API Base Path:** `/api/`
- **Authentication:** JWT tokens (24hr access, 7-day refresh)
- **Database:** Railway PostgreSQL (for production backend)

## API Endpoints Reference

- `GET /api/health/` - Health check
- `POST /api/register/` - User registration
- `POST /api/upload/` - Upload CSV dataset
- `GET /api/summary/latest/` - Get latest dataset summary
- `GET /api/history/` - Get upload history
- `GET /api/dataset/<id>/` - Get specific dataset
- `GET /api/export/csv/<id>/` - Export dataset as CSV
- `GET /api/report/pdf/<id>/` - Generate PDF report
