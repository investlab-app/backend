#!/usr/bin/env python3
"""
Database connection diagnostic script for Kubernetes environment.
This script helps identify PostgreSQL connection issues.
"""

import os
import socket
import sys
import logging
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_dns_resolution(hostname):
    """Test if hostname can be resolved."""
    try:
        ip_address = socket.gethostbyname(hostname)
        logger.info(f"✓ DNS resolution successful: {hostname} -> {ip_address}")
        return True, ip_address
    except socket.gaierror as e:
        logger.error(f"✗ DNS resolution failed: {hostname} - {e}")
        return False, str(e)

def test_port_connection(hostname, port):
    """Test if port is open on hostname."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((hostname, int(port)))
        sock.close()
        
        if result == 0:
            logger.info(f"✓ Port connection successful: {hostname}:{port}")
            return True
        else:
            logger.error(f"✗ Port connection failed: {hostname}:{port} - Error code: {result}")
            return False
    except Exception as e:
        logger.error(f"✗ Port connection error: {hostname}:{port} - {e}")
        return False

def test_django_db_connection():
    """Test Django database connection."""
    try:
        import django
        from django.conf import settings
        
        # Configure Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        django.setup()
        
        from django.db import connection
        
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        if result and result[0] == 1:
            logger.info("✓ Django database connection successful")
            return True
        else:
            logger.error("✗ Django database connection failed - unexpected result")
            return False
            
    except Exception as e:
        logger.error(f"✗ Django database connection error: {e}")
        return False

def main():
    """Main diagnostic function."""
    logger.info("=== Database Connection Diagnostic ===")
    
    # Get database configuration from environment
    db_host = os.environ.get('POSTGRES_HOST', 'postgresql')
    db_port = os.environ.get('POSTGRES_PORT', '5432')
    db_name = os.environ.get('POSTGRES_DB', 'template_db')
    db_user = os.environ.get('POSTGRES_USER', 'user')
    
    logger.info(f"Database Configuration:")
    logger.info(f"  Host: {db_host}")
    logger.info(f"  Port: {db_port}")
    logger.info(f"  Database: {db_name}")
    logger.info(f"  User: {db_user}")
    logger.info("")
    
    # Test 1: DNS Resolution
    logger.info("Test 1: DNS Resolution")
    dns_success, dns_result = test_dns_resolution(db_host)
    logger.info("")
    
    # Test 2: Port Connection
    logger.info("Test 2: Port Connection")
    port_success = test_port_connection(db_host, db_port)
    logger.info("")
    
    # Test 3: Django Database Connection
    logger.info("Test 3: Django Database Connection")
    django_success = test_django_db_connection()
    logger.info("")
    
    # Summary
    logger.info("=== Diagnostic Summary ===")
    logger.info(f"DNS Resolution: {'✓ PASS' if dns_success else '✗ FAIL'}")
    logger.info(f"Port Connection: {'✓ PASS' if port_success else '✗ FAIL'}")
    logger.info(f"Django DB Connection: {'✓ PASS' if django_success else '✗ FAIL'}")
    
    if not dns_success:
        logger.error("")
        logger.error("🔍 ROOT CAUSE IDENTIFIED:")
        logger.error(f"The hostname '{db_host}' cannot be resolved.")
        logger.error("")
        logger.error("Possible solutions:")
        logger.error("1. Check if the PostgreSQL service name is correct")
        logger.error("2. Verify the service is in the same namespace")
        logger.error("3. Check Kubernetes DNS configuration")
        logger.error("4. Verify service discovery is working")
        
    elif not port_success:
        logger.error("")
        logger.error("🔍 ROOT CAUSE IDENTIFIED:")
        logger.error(f"Port {db_port} is not accessible on {db_host}.")
        logger.error("")
        logger.error("Possible solutions:")
        logger.error("1. Check if PostgreSQL is running")
        logger.error("2. Verify firewall rules")
        logger.error("3. Check service configuration")
        
    elif not django_success:
        logger.error("")
        logger.error("🔍 ROOT CAUSE IDENTIFIED:")
        logger.error("Django cannot connect to PostgreSQL despite network connectivity.")
        logger.error("")
        logger.error("Possible solutions:")
        logger.error("1. Check database credentials")
        logger.error("2. Verify database exists")
        logger.error("3. Check user permissions")
    
    return dns_success and port_success and django_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)