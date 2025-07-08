#!/bin/bash

# Configure services for Beautiland VPS deployment

echo "🔧 Configuring services..."

# Configure Nginx
echo "📝 Setting up Nginx..."
cat > /etc/nginx/sites-available/beautiland << 'EOF'
server {
    listen 80;
    server_name 178.128.100.99;
    
    client_max_body_size 100M;
    
    location /static/ {
        alias /opt/beautiland/app/staticfiles/;
        expires 30d;
    }
    
    location /media/ {
        alias /opt/beautiland/app/media/;
        expires 30d;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/beautiland /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
systemctl enable nginx

# Configure Supervisor
echo "📝 Setting up Supervisor..."
cat > /etc/supervisor/conf.d/beautiland.conf << 'EOF'
[program:beautiland]
command=/opt/beautiland/app/venv/bin/gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 120 core.wsgi:application
directory=/opt/beautiland/app
user=beautiland
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/beautiland.log
environment=DJANGO_SETTINGS_MODULE="core.settings_production"
EOF

# Start services
supervisorctl reread
supervisorctl update
supervisorctl start beautiland

# Start Redis
systemctl start redis-server
systemctl enable redis-server

# Check status
echo "📊 Service Status:"
echo "Nginx: $(systemctl is-active nginx)"
echo "PostgreSQL: $(systemctl is-active postgresql)"
echo "Redis: $(systemctl is-active redis-server)"
echo "Beautiland: $(supervisorctl status beautiland | awk '{print $2}')"

echo ""
echo "✅ Services configured!"
echo "🌐 Access: http://178.128.100.99"
echo "👑 Admin: http://178.128.100.99/admin (admin/admin123)"
echo "📋 Logs: tail -f /var/log/beautiland.log"
