FROM python:3.11-slim

# Install nginx and supervisor
RUN apt-get update && apt-get install -y nginx supervisor && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Copy nginx configuration
COPY nginx.conf /etc/nginx/sites-available/default

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Remove default nginx config and create log directories
RUN rm -f /etc/nginx/sites-enabled/default && \
    ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/ && \
    mkdir -p /var/log/supervisor

EXPOSE 80

ENV SECRET_KEY=change-this-in-production
ENV DATABASE=/app/data/workout_tracker.db

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]