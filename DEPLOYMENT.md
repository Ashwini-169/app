# Defang Deployment Guide

This guide will help you deploy the Chemical Equipment Visualizer to the cloud using Defang.

## Prerequisites

1. Install Defang CLI:
   ```bash
   # Windows (PowerShell)
   iwr https://s.defang.io/install.ps1 -useb | iex
   
   # macOS/Linux
   curl -fsSL https://s.defang.io/install.sh | sh
   ```

2. Authenticate with Defang:
   ```bash
   defang login
   ```

## Project Structure

- `django_backend/` - Django REST API backend
- `frontend/` - React frontend
- `compose.yaml` - Defang deployment configuration

## Deployment Steps

### 1. Navigate to project root
```bash
cd d:\ASHWINI\project\fossdjweb\app
```

### 2. Deploy to Defang
```bash
defang compose up
```

This command will:
- Build Docker images for both frontend and backend
- Deploy services to Defang cloud
- Provide you with public URLs for your services

### 3. Monitor Deployment
```bash
# Check service status
defang compose ps

# View logs
defang compose logs backend
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
