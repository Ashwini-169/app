# Alternative Deployment Options (No CLI Required)

## Option 1: Render.com (Recommended - Web UI Only)

### Steps:
1. Go to https://render.com and sign up
2. Click "New +" → "Web Service"
3. Connect your GitHub repository: https://github.com/Ashwini-169/app
4. Configure Backend Service:
   - **Name**: chemical-backend
   - **Root Directory**: django_backend
   - **Environment**: Docker
   - **Dockerfile Path**: django_backend/Dockerfile
   - **Add Environment Variables**:
     ```
     DEBUG=False
     ALLOWED_HOSTS=*
     SECRET_KEY=your-secret-key-here
     ```
5. Click "Create Web Service"

6. Create Frontend Service:
   - Click "New +" → "Web Service"
   - **Name**: chemical-frontend
   - **Root Directory**: frontend
   - **Environment**: Docker
   - **Dockerfile Path**: frontend/Dockerfile
   - **Add Environment Variable**:
     ```
     REACT_APP_API_URL=https://chemical-backend.onrender.com
     ```
7. Click "Create Web Service"

**URLs**: Render will provide URLs like:
- Backend: `https://chemical-backend.onrender.com`
- Frontend: `https://chemical-frontend.onrender.com`

---

## Option 2: Railway.app (Web UI + GitHub Integration)

### Steps:
1. Go to https://railway.app and sign up
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect services from compose.yaml
5. Configure environment variables in the Railway dashboard
6. Deploy both services

**URLs**: Railway provides URLs automatically.

---

## Option 3: Heroku (Web UI Deployment)

### Backend Setup:
1. Create `heroku.yml` in django_backend/:
```yaml
build:
  docker:
    web: Dockerfile
run:
  web: python manage.py migrate && python manage.py runserver 0.0.0.0:$PORT
```

2. Go to https://heroku.com → Dashboard → New → Create new app
3. App name: `chemical-backend`
4. Deploy method: GitHub → Connect repository
5. In Settings → Buildpacks → Add buildpack: `heroku/python`
6. Manual deploy → Deploy Branch

### Frontend Setup:
1. Create new app: `chemical-frontend`
2. Follow same steps
3. Update API URL in environment

---

## Option 4: Local Docker Compose (Development)

### Prerequisites:
- Install Docker Desktop for Windows

### Steps:
1. Open Docker Desktop
2. Navigate to project:
```powershell
cd d:\ASHWINI\project\fossdjweb\app
```

3. Build and run:
```powershell
docker-compose -f compose.yaml up --build
```

4. Access:
- Backend: http://localhost:8002
- Frontend: http://localhost:3000

5. Stop services:
```powershell
docker-compose -f compose.yaml down
```

---

## Option 5: Azure Container Instances (Web Portal)

### Steps:
1. Go to https://portal.azure.com
2. Create Container Instance for backend
3. Create Container Instance for frontend
4. Configure networking and environment variables
5. Services will be accessible via Azure URLs

---

## Option 6: AWS App Runner (Web Console)

### Steps:
1. Go to AWS Console → App Runner
2. Create Service from GitHub
3. Select repository and branch
4. Configure build settings (Dockerfile)
5. Set environment variables
6. Deploy

---

## Recommended: Render.com Setup

I'll create Render-specific configuration files for you.
