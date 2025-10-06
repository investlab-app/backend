import os
import base64
import asyncio
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)

async def test_redis_connection():
    """Test Redis connection with different authentication methods"""
    
    redis_host = os.environ.get("REDIS_HOST", "redis-master")
    redis_port = int(os.environ.get("REDIS_PORT", "6379"))
    redis_password = os.environ.get("REDIS_PASSWORD", "")
    
    logger.error("=== Redis Connection Diagnostic ===")
    logger.error(f"Host: {redis_host}")
    logger.error(f"Port: {redis_port}")
    logger.error(f"Password (raw): {redis_password}")
    
    # Test 1: Try without password
    logger.error("\n--- Test 1: Connection without password ---")
    try:
        client = redis.Redis(host=redis_host, port=redis_port, password=None)
        await client.ping()
        logger.error("SUCCESS: Connected without password")
        await client.close()
    except Exception as e:
        logger.error(f"FAILED: {e}")
    
    # Test 2: Try with raw password
    logger.error("\n--- Test 2: Connection with raw password ---")
    try:
        client = redis.Redis(host=redis_host, port=redis_port, password=redis_password)
        await client.ping()
        logger.error("SUCCESS: Connected with raw password")
        await client.close()
    except Exception as e:
        logger.error(f"FAILED: {e}")
    
    # Test 3: Try with base64 decoded password
    logger.error("\n--- Test 3: Connection with base64 decoded password ---")
    try:
        decoded_password = base64.b64decode(redis_password).decode('utf-8')
        logger.error(f"Decoded password: {decoded_password}")
        client = redis.Redis(host=redis_host, port=redis_port, password=decoded_password)
        await client.ping()
        logger.error("SUCCESS: Connected with decoded password")
        await client.close()
    except Exception as e:
        logger.error(f"FAILED: {e}")
    
    # Test 4: Try connection with URL format
    logger.error("\n--- Test 4: Connection with URL format ---")
    try:
        redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}"
        logger.error(f"Redis URL: {redis_url}")
        client = redis.from_url(redis_url)
        await client.ping()
        logger.error("SUCCESS: Connected with URL format")
        await client.close()
    except Exception as e:
        logger.error(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_redis_connection())