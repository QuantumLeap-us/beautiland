#!/bin/bash
# Beautiland Django Application Deployment Script for DigitalOcean
# Server: 139.59.127.30
# User: root

set -e  # Exit on any error

echo "🚀 Starting Beautiland deployment on DigitalOcean..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Update system packages
print_status "Updating system packages..."
apt update && apt upgrade -y

# Step 2: Install basic software packages
print_status "Installing basic software packages..."
apt install -y python3 python3-pip python3-venv git nginx mysql-server redis-server supervisor curl wget

# Step 3: Install build dependencies
print_status "Installing build dependencies..."
apt install -y build-essential python3-dev libmysqlclient-dev pkg-config

# Step 4: Install WeasyPrint dependencies
print_status "Installing WeasyPrint dependencies..."
apt install -y libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 libffi-dev libcairo2-dev

# Step 5: Create project directory structure
print_status "Creating project directory structure..."
mkdir -p /home/dev
mkdir -p /home/dev/logs
chown -R root:root /home/dev

# Step 6: Clone project from GitHub
print_status "Cloning project from GitHub..."
cd /home/dev
if [ -d "beautiland" ]; then
    print_warning "Project directory exists, updating..."
    cd beautiland
    git pull origin main
else
    git clone https://github.com/QuantumLeap-us/beautiland.git
    cd beautiland
fi

# Step 7: Create Python virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv bvenv
source bvenv/bin/activate

# Step 8: Upgrade pip and install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 9: Configure environment variables
print_status "Configuring environment variables..."
cp .env.production .env

# Update .env with server-specific settings
sed -i "s/your-server-ip/139.59.127.30/g" .env
sed -i "s/your-domain.com/139.59.127.30/g" .env

print_status "Environment configuration completed!"

# Step 10: Configure MySQL (if needed)
print_status "Configuring MySQL service..."
systemctl start mysql
systemctl enable mysql

# Step 11: Configure Redis
print_status "Configuring Redis service..."
systemctl start redis-server
systemctl enable redis-server

# Step 12: Test database connection
print_status "Testing database connection..."
python manage.py check --database default

# Step 13: Run database migrations
print_status "Running database migrations..."
python manage.py migrate

# Step 14: Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput

# Step 15: Create logs directory with proper permissions
print_status "Setting up log directories..."
mkdir -p /home/dev/logs
touch /home/dev/logs/gunicorn_access.log
touch /home/dev/logs/gunicorn_error.log
touch /home/dev/logs/django.log
chmod 755 /home/dev/logs
chmod 644 /home/dev/logs/*.log

print_status "✅ Basic deployment completed!"
print_warning "Next steps:"
echo "1. Create Django superuser: python manage.py createsuperuser"
echo "2. Configure Nginx"
echo "3. Configure Gunicorn service"
echo "4. Test the application"

print_status "🎉 Deployment script finished!"
