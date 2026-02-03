# Deployment Guide - Railway.app

Complete guide for deploying Chemical Equipment Parameter Visualizer to Railway.app production platform.

---

## 🚀 Quick Deploy

```bash
# 1. Push to GitHub
git add .
git commit -m "Update for production"
git push origin master

# 2. Railway auto-deploys (watch dashboard)
# Frontend: https://chemical-visualizer-production-2f4c.up.railway.app
# Backend: https://chemical-backend-production-dd2c.up.railway.app
```

---

## 📋 Prerequisites

- GitHub repository with git initialized
- Railway.app account (free tier available)
- Docker knowledge (basic)
- Environment variables documented

---

## 🔑 Production Environment Variables

| Variable | Frontend | Backend | Purpose |
|----------|----------|---------|---------|
| REACT_APP_API_URL | ✅ | - | API endpoint for frontend |
| DEBUG | - | ✅ | Django debug mode (False) |
| ALLOWED_HOSTS | - | ✅ | Allowed domains |
| SECRET_KEY | - | ✅ | Django secret for CSRF |
| PORT | - | ✅ | Server port (Railway injects) |

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] `DEBUG = False` in settings.py
- [ ] `SECRET_KEY` is secure and unique
- [ ] All migrations applied locally
- [ ] Docker builds successfully locally
- [ ] Tests pass locally
- [ ] Git repository is clean (no uncommitted changes)

### GitHub Setup
- [ ] Repository is public (or Railway has access)
- [ ] main/master branch is default
- [ ] .gitignore includes `*.pyc`, `node_modules/`, `.env`

### Railway Setup
- [ ] Railway.app account created
- [ ] GitHub connected
- [ ] Project created
- [ ] Both services added (frontend, backend)
- [ ] Environment variables set
- [ ] Dockerfile paths correct

### Post-Deployment
- [ ] Frontend healthcheck passes: `curl https://frontend-url/`
- [ ] Backend healthcheck passes: `curl https://backend-url/api/health/`
- [ ] Login endpoint works
- [ ] Frontend can make API calls
- [ ] No CORS errors in console
- [ ] Charts load and display data

---

## 📊 Monitoring Production

### Railway Dashboard
```
https://railway.app/dashboard
├─ Deployments tab: See build history
├─ Logs tab: Real-time service logs
├─ Metrics tab: CPU, memory, network
└─ Settings: Environment variables
```

### Health Endpoints
```bash
# Frontend
curl https://chemical-visualizer-production-2f4c.up.railway.app/

# Backend
curl https://chemical-backend-production-dd2c.up.railway.app/api/health/
```

---

## 🔐 Production Security

### Django Settings
```python
DEBUG = False
ALLOWED_HOSTS = ['*.railway.app']
SECURE_SSL_REDIRECT = True
```

### CORS Configuration
```python
CORS_ALLOWED_ORIGINS = [
    'https://chemical-visualizer-production-2f4c.up.railway.app',
    'https://*.railway.app'
]
```

---

**Version**: 1.0.0  
**Status**: Production-Ready ✅
defang compose logs frontend
```

### 4. Get Service URLs
After deployment, Defang will provide URLs like:
- Backend: `https://backend-<random>.defang.dev`
- Frontend: `https://frontend-<random>.defang.dev`

## Environment Configuration

The deployment uses these environment variables:
- `DEBUG=False` - Production mode for Django
- `ALLOWED_HOSTS=*` - Allows all hosts (can be restricted later)
- `CORS_ALLOWED_ORIGINS` - Auto-configured for frontend URL

## Post-Deployment

### Create Django Superuser (Optional)
```bash
defang compose exec backend python manage.py createsuperuser
```

### Update Frontend API URL
After deployment, update the frontend to use the production backend URL:
1. Note the backend URL from Defang
2. Update `frontend/src/components/Dashboard.jsx` API_URL if needed

## Useful Commands

```bash
# Stop services
defang compose down

# View service details
defang service list

# Update after code changes
defang compose up

# View service logs (real-time)
defang compose logs -f backend
```

## Troubleshooting

### Backend not responding
```bash
defang compose logs backend
```
Check for migration or startup errors.

### Frontend can't connect to backend
1. Verify backend URL in frontend environment
2. Check CORS configuration in Django settings
3. Ensure backend health check is passing

### Database issues
The deployment uses SQLite (stored in Docker volume). For production, consider:
- PostgreSQL
- MySQL
- Cloud database service

## Production Recommendations

1. **Database**: Switch from SQLite to PostgreSQL
2. **Secret Key**: Use environment variables for Django SECRET_KEY
3. **Static Files**: Configure proper static file serving (AWS S3, CloudFlare)
4. **HTTPS**: Defang provides HTTPS by default
5. **Monitoring**: Set up application monitoring (Sentry, DataDog)

## Cost Estimation

Run this to estimate cloud costs:
```bash
defang estimate --provider aws
```

## Support

- Defang Documentation: https://docs.defang.io
- GitHub Issues: https://github.com/Ashwini-169/app/issues
