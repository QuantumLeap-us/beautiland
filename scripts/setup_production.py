#!/usr/bin/env python3
"""
Production Setup Script for Beautiland Django Application
This script sets up the production environment including WeasyPrint dependencies
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(command, check=True):
    """Run a shell command and return the result"""
    logger.info(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=check, 
                              capture_output=True, text=True)
        if result.stdout:
            logger.info(f"Output: {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        if e.stderr:
            logger.error(f"Error: {e.stderr.strip()}")
        if check:
            raise
        return e

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        logger.error("Python 3.7 or higher is required")
        sys.exit(1)
    logger.info(f"Python version: {version.major}.{version.minor}.{version.micro}")

def install_python_dependencies():
    """Install Python dependencies"""
    logger.info("Installing Python dependencies...")
    
    # Upgrade pip first
    run_command("python3 -m pip install --upgrade pip")
    
    # Install wheel and setuptools
    run_command("python3 -m pip install --upgrade wheel setuptools")
    
    # Install requirements
    if os.path.exists("requirements_clean.txt"):
        run_command("python3 -m pip install -r requirements_clean.txt")
    elif os.path.exists("requirements.txt"):
        run_command("python3 -m pip install -r requirements.txt")
    else:
        logger.error("No requirements file found!")
        sys.exit(1)

def test_weasyprint():
    """Test WeasyPrint functionality"""
    logger.info("Testing WeasyPrint functionality...")
    
    test_script = '''
import sys
try:
    from weasyprint import HTML, CSS
    print("WeasyPrint import successful!")
    
    # Test basic HTML to PDF conversion
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Test Document</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            .chinese { font-family: "Noto Sans CJK SC", "SimSun", sans-serif; }
        </style>
    </head>
    <body>
        <h1>WeasyPrint Test</h1>
        <p>This is a test document to verify WeasyPrint functionality.</p>
        <p class="chinese">中文字体测试</p>
        <p>Date: $(date)</p>
    </body>
    </html>
    """
    
    html_doc = HTML(string=html_content)
    pdf_bytes = html_doc.write_pdf()
    
    print(f"PDF generation successful! Size: {len(pdf_bytes)} bytes")
    
    # Save test PDF
    with open("/tmp/weasyprint_test.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("Test PDF saved to /tmp/weasyprint_test.pdf")
    
except ImportError as e:
    print(f"WeasyPrint import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"WeasyPrint test failed: {e}")
    sys.exit(1)
'''
    
    result = run_command(f"python3 -c '{test_script}'", check=False)
    if result.returncode != 0:
        logger.error("WeasyPrint test failed!")
        return False
    
    logger.info("WeasyPrint test passed!")
    return True

def setup_django():
    """Setup Django application"""
    logger.info("Setting up Django application...")
    
    # Set Django settings module for production
    os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings_prod'
    
    # Collect static files
    run_command("python3 manage.py collectstatic --noinput")
    
    # Run migrations
    run_command("python3 manage.py migrate")
    
    logger.info("Django setup completed!")

def create_directories():
    """Create necessary directories"""
    directories = [
        "/home/dev/logs",
        "staticfiles",
        "media",
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")

def main():
    """Main setup function"""
    logger.info("Starting production setup...")
    
    # Check Python version
    check_python_version()
    
    # Create necessary directories
    create_directories()
    
    # Install Python dependencies
    install_python_dependencies()
    
    # Test WeasyPrint
    if not test_weasyprint():
        logger.error("WeasyPrint test failed. Please check system dependencies.")
        logger.info("Run: bash scripts/install_weasyprint_deps.sh")
        sys.exit(1)
    
    # Setup Django
    setup_django()
    
    logger.info("Production setup completed successfully!")
    logger.info("You can now start the application with:")
    logger.info("  gunicorn --config gunicorn-cfg.py core.wsgi:application")

if __name__ == "__main__":
    main()
