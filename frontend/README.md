# React Frontend - Production Guide

React 19 single-page application for Chemical Equipment Parameter Visualization with TailwindCSS and Chart.js.

## 🚀 Quick Start

### Production (Railway)
```bash
# Automatically deployed via Docker
# Frontend running at: https://chemical-visualizer-production-2f4c.up.railway.app
# Backend API: https://chemical-backend-production-dd2c.up.railway.app
```

### Local Development
```bash
cd frontend

# Install dependencies
npm install

# Set backend API URL (required)
export REACT_APP_API_URL=http://localhost:8002

```

**Frontend running at**: http://localhost:3000  
**Requires backend at**: `$REACT_APP_API_URL`

---

## 🏗️ Project Structure

```
frontend/
├── Dockerfile                      # Production container
├── package.json                    # Dependencies
└── src/
    ├── api.js                      # Centralized API client
    ├── components/
    │   ├── Dashboard.jsx
    │   ├── Login.jsx
    │   └── Register.jsx
    └── hooks/
        └── use-toast.js
```

---

## 🔧 Environment Variables

**Required at build time**:
```bash
REACT_APP_API_URL=https://chemical-backend-production-dd2c.up.railway.app
```

---

## 📦 Development

```bash
npm install
REACT_APP_API_URL=http://localhost:8002 npm start
npm run build
```

---

## 🚀 Production

### Docker Build
```bash
docker build --build-arg REACT_APP_API_URL=https://your-backend-url -t chemical-frontend .
```

### Railway
```bash
git push origin master  # Auto-deploys with env vars
```

---

## 🔐 Security

- Centralized API client (api.js) with validation
- Throws error if REACT_APP_API_URL missing
- JWT token management
- CORS configured on backend

---

## 📞 Support

See [django_backend/README.md](../django_backend/README.md) for API details and [README.md](../README.md) for project overview.

---

**Version**: 1.0.0 | **Status**: Production-Ready ✅

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can't go back!**

If you aren't satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you're on your own.

You don't have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn't feel obligated to use this feature. However we understand that this tool wouldn't be useful if you couldn't customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

### Code Splitting

This section has moved here: [https://facebook.github.io/create-react-app/docs/code-splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### Analyzing the Bundle Size

This section has moved here: [https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### Making a Progressive Web App

This section has moved here: [https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### Advanced Configuration

This section has moved here: [https://facebook.github.io/create-react-app/docs/advanced-configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### Deployment

This section has moved here: [https://facebook.github.io/create-react-app/docs/deployment](https://facebook.github.io/create-react-app/docs/deployment)

### `npm run build` fails to minify

This section has moved here: [https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)
