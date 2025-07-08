#!/bin/bash

# Clean VPS Deployment Script for Beautiland
# Ubuntu 22.04 LTS

set -e

echo "🚀 Beautiland VPS Deployment - Clean Version"

# Update system
echo "📦 Updating system..."
apt update && apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
apt install -y \
    python3 python3-pip python3-venv python3-dev \
    build-essential git nginx supervisor \
    postgresql postgresql-contrib libpq-dev \
    redis-server \
    libcairo2-dev libpango1.0-dev libgdk-pixbuf2.0-dev \
    libffi-dev shared-mime-info libglib2.0-dev \
    libfontconfig1-dev libfreetype6-dev libharfbuzz-dev \
    libjpeg-dev libpng-dev zlib1g-dev \
    libxml2-dev libxslt1-dev libssl-dev

# Create application user
echo "👤 Creating application user..."
useradd --system --shell /bin/bash --home /opt/beautiland --create-home beautiland
mkdir -p /opt/beautiland/app
chown beautiland:beautiland /opt/beautiland/app

# Clone repository
echo "📥 Cloning repository..."
cd /opt/beautiland
sudo -u beautiland git clone https://github.com/QuantumLeap-us/beautiland.git app

# Setup Python environment
echo "🐍 Setting up Python environment..."
cd /opt/beautiland/app
sudo -u beautiland python3 -m venv venv
sudo -u beautiland ./venv/bin/pip install --upgrade pip
sudo -u beautiland ./venv/bin/pip install -r requirements.txt

# Setup PostgreSQL
echo "🗄️ Setting up PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql
sudo -u postgres createdb beautiland
sudo -u postgres createuser beautiland
sudo -u postgres psql -c "ALTER USER beautiland WITH PASSWORD 'beautiland123';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE beautiland TO beautiland;"

# Create environment file
echo "⚙️ Creating environment configuration..."
sudo -u beautiland tee .env > /dev/null <<EOF
DEBUG=False
SECRET_KEY=django-secret-$(openssl rand -hex 32)
DATABASE_URL=postgresql://beautiland:beautiland123@localhost:5432/beautiland
ALLOWED_HOSTS=178.128.100.99,*
ASSETS_ROOT=/static/assets
DJANGO_SETTINGS_MODULE=core.settings_production
EOF

# Run Django setup
echo "🔧 Running Django setup..."
sudo -u beautiland ./venv/bin/python manage.py collectstatic --noinput --settings=core.settings_production
sudo -u beautiland ./venv/bin/python manage.py migrate --settings=core.settings_production

# Create superuser
echo "👑 Creating superuser..."
sudo -u beautiland ./venv/bin/python manage.py shell --settings=core.settings_production <<PYEOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
PYEOF

echo "✅ Deployment completed!"
echo "🔗 Next: Run configure_services.sh to setup Nginx and Supervisor"
