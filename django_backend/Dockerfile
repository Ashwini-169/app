FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8002

# Railway provides PORT automatically
ENV PORT=8002

# Start Gunicorn (PRODUCTION SERVER)
CMD gunicorn chemical_visualizer.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 3 \
    --timeout 120
