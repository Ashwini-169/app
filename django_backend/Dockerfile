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

# Make startup script executable
RUN chmod +x start.sh

# Create uploads directory
RUN mkdir -p uploads

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Railway provides PORT automatically (defaults to 8000)
ENV PORT=8000

# Start server with migrations
CMD ["./start.sh"]
