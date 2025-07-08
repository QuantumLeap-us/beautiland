#!/bin/bash
# Configure Nginx, Supervisor and other services for Beautiland
# Run this after deploy_to_digitalocean.sh

set -e

echo "🔧 Configuring services for Beautiland..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Step 1: Update Gunicorn configuration for production
print_status "Updating Gunicorn configuration..."
cd /home/dev/beautiland

# Update gunicorn-cfg.py for production
cat > gunicorn-cfg.py << 'EOF'
import multiprocessing
import os

# Server socket
bind = '127.0.0.1:5005'
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 2

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "/home/dev/logs/gunicorn_access.log"
errorlog = "/home/dev/logs/gunicorn_error.log"
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'beautiland'

# Server mechanics
daemon = False
pidfile = '/home/dev/logs/gunicorn.pid'
user = None
group = None

# Environment
raw_env = [
    'DJANGO_SETTINGS_MODULE=core.settings_prod',
]

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
preload_app = True
enable_stdio_inheritance = True
capture_output = True
EOF

# Step 2: Configure Nginx
print_status "Configuring Nginx..."

# Remove default Nginx site
rm -f /etc/nginx/sites-enabled/default

# Copy our Nginx configuration
cat > /etc/nginx/sites-available/beautiland << 'EOF'
server {
    listen 80;
    server_name 139.59.127.30;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss;

    # Static files
    location /static/ {
        alias /home/dev/beautiland/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /home/dev/beautiland/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Main application
    location / {
        proxy_pass http://127.0.0.1:5005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Logging
    access_log /var/log/nginx/beautiland_access.log;
    error_log /var/log/nginx/beautiland_error.log;
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/beautiland /etc/nginx/sites-enabled/

# Test Nginx configuration
nginx -t

# Step 3: Configure Supervisor
print_status "Configuring Supervisor..."

cat > /etc/supervisor/conf.d/beautiland.conf << 'EOF'
[program:beautiland]
command=/home/dev/beautiland/bvenv/bin/gunicorn --config /home/dev/beautiland/gunicorn-cfg.py core.wsgi:application
directory=/home/dev/beautiland
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/dev/logs/gunicorn_supervisor.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/home/dev/beautiland/bvenv/bin"

[program:beautiland_celery]
command=/home/dev/beautiland/bvenv/bin/celery -A core worker --loglevel=info
directory=/home/dev/beautiland
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/dev/logs/celery_worker.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/home/dev/beautiland/bvenv/bin"
EOF

# Step 4: Start services
print_status "Starting services..."

# Reload supervisor configuration
supervisorctl reread
supervisorctl update

# Start Beautiland services
supervisorctl start beautiland
supervisorctl start beautiland_celery

# Restart Nginx
systemctl restart nginx
systemctl enable nginx

# Step 5: Configure firewall
print_status "Configuring firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

print_status "✅ Service configuration completed!"
print_status "🌐 Your application should be available at: http://139.59.127.30"
print_warning "Next steps:"
echo "1. Create Django superuser: cd /home/dev/beautiland && source bvenv/bin/activate && python manage.py createsuperuser"
echo "2. Test the application in browser"
echo "3. Monitor logs: tail -f /home/dev/logs/gunicorn_supervisor.log"
EOF
