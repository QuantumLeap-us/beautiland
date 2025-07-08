#!/bin/bash

# WeasyPrint Dependencies Installation Script for Alibaba Cloud ECS
# This script installs system dependencies required for WeasyPrint

echo "Installing WeasyPrint system dependencies..."

# Update package manager
if command -v yum &> /dev/null; then
    # CentOS/RHEL/Alibaba Cloud Linux
    echo "Detected YUM package manager (CentOS/RHEL/Alibaba Cloud Linux)"
    
    # Install EPEL repository if not already installed
    sudo yum install -y epel-release
    
    # Install development tools
    sudo yum groupinstall -y "Development Tools"
    
    # Install WeasyPrint dependencies
    sudo yum install -y \
        python3-devel \
        python3-pip \
        cairo-devel \
        pango-devel \
        gdk-pixbuf2-devel \
        libffi-devel \
        shared-mime-info \
        glib2-devel \
        fontconfig-devel \
        freetype-devel \
        harfbuzz-devel \
        libjpeg-devel \
        libpng-devel \
        zlib-devel \
        gobject-introspection-devel
        
    # Install Chinese fonts for PDF generation
    sudo yum install -y \
        google-noto-cjk-fonts \
        google-noto-fonts \
        dejavu-fonts-common \
        dejavu-sans-fonts
        
elif command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    echo "Detected APT package manager (Ubuntu/Debian)"
    
    # Update package list
    sudo apt-get update
    
    # Install WeasyPrint dependencies
    sudo apt-get install -y \
        python3-dev \
        python3-pip \
        build-essential \
        libcairo2-dev \
        libpango1.0-dev \
        libgdk-pixbuf2.0-dev \
        libffi-dev \
        shared-mime-info \
        libglib2.0-dev \
        libfontconfig1-dev \
        libfreetype6-dev \
        libharfbuzz-dev \
        libjpeg-dev \
        libpng-dev \
        zlib1g-dev \
        libgirepository1.0-dev
        
    # Install Chinese fonts for PDF generation
    sudo apt-get install -y \
        fonts-noto-cjk \
        fonts-noto \
        fonts-dejavu-core \
        fonts-liberation
        
else
    echo "Unsupported package manager. Please install dependencies manually."
    exit 1
fi

echo "System dependencies installation completed!"

# Verify installation
echo "Verifying WeasyPrint installation..."
python3 -c "
try:
    import weasyprint
    print('WeasyPrint import successful!')
    
    # Test basic functionality
    from weasyprint import HTML
    html_doc = HTML(string='<html><body><h1>Test</h1></body></html>')
    pdf = html_doc.write_pdf()
    print('WeasyPrint PDF generation test successful!')
    print(f'Generated PDF size: {len(pdf)} bytes')
    
except ImportError as e:
    print(f'WeasyPrint import failed: {e}')
    print('Please install WeasyPrint: pip install weasyprint')
except Exception as e:
    print(f'WeasyPrint test failed: {e}')
    print('Some system dependencies might be missing.')
"

echo "WeasyPrint dependency installation and verification completed!"
