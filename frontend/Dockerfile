FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including devDependencies for build)
RUN npm ci

# Copy application code
COPY . .

# Build the React app
RUN npm run build

# Install serve to run the production build
RUN npm install -g serve

# Railway provides PORT automatically
ENV PORT=3000

# Serve the build folder on Railway's PORT
CMD serve -s build -l $PORT
