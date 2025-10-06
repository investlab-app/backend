#!/usr/bin/env python3
"""
Simple database connection test for Kubernetes debugging.
"""

import os
import socket

def test_connection():
    """Test database connection parameters."""
    
    # Get environment variables
    db_host = os.environ.get('POSTGRES_HOST', 'postgresql')
    db_port = os.environ.get('POSTGRES_PORT', '5432')
    
    print(f"Testing connection to PostgreSQL at {db_host}:{db_port}")
    print(f"Environment variables:")
    print(f"  POSTGRES_HOST: {db_host}")
    print(f"  POSTGRES_PORT: {db_port}")
    print(f"  POSTGRES_DB: {os.environ.get('POSTGRES_DB', 'not_set')}")
    print(f"  POSTGRES_USER: {os.environ.get('POSTGRES_USER', 'not_set')}")
    print()
    
    # Test DNS resolution
    print("Testing DNS resolution...")
    try:
        ip = socket.gethostbyname(db_host)
        print(f"✓ DNS resolution successful: {db_host} -> {ip}")
    except socket.gaierror as e:
        print(f"✗ DNS resolution failed: {e}")
        return False
    
    # Test port connection
    print("Testing port connection...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((db_host, int(db_port)))
        sock.close()
        
        if result == 0:
            print(f"✓ Port {db_port} is open on {db_host}")
        else:
            print(f"✗ Port {db_port} is not accessible on {db_host} (error code: {result})")
            return False
    except Exception as e:
        print(f"✗ Port connection error: {e}")
        return False
    
    print("✓ All network tests passed")
    return True

if __name__ == "__main__":
    success = test_connection()
    if not success:
        print("\n🔍 DIAGNOSIS: Network connectivity issue detected")
        print("The backend cannot reach the PostgreSQL service.")
        exit(1)
    else:
        print("\n✓ Network connectivity is working")
        exit(0)