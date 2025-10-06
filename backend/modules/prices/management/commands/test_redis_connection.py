import asyncio
import logging
import os
import base64

from channels.layers import get_channel_layer
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test Redis connection and channel layer functionality'

    def handle(self, *args, **options):
        logger.error("=== Testing Redis Connection ===")
        
        # Test basic Redis connection
        asyncio.run(self.test_redis_connection())
        
        # Test channel layer
        asyncio.run(self.test_channel_layer())
    
    async def test_redis_connection(self):
        """Test basic Redis connection"""
        try:
            import redis.asyncio as redis
            
            redis_host = os.environ.get("REDIS_HOST", "redis-master")
            redis_port = int(os.environ.get("REDIS_PORT", "6379"))
            redis_password = os.environ.get("REDIS_PASSWORD", "")
            
            # Decode base64 password if needed
            try:
                redis_password = base64.b64decode(redis_password).decode('utf-8')
                logger.error(f"Redis password decoded from base64")
            except Exception:
                logger.error(f"Redis password used as-is")
            
            logger.error(f"Connecting to Redis at {redis_host}:{redis_port}")
            
            client = redis.Redis(host=redis_host, port=redis_port, password=redis_password)
            await client.ping()
            logger.error("✅ SUCCESS: Basic Redis connection works")
            await client.close()
            
        except Exception as e:
            logger.error(f"❌ FAILED: Basic Redis connection failed: {e}")
    
    async def test_channel_layer(self):
        """Test Django channels Redis connection"""
        try:
            logger.error("Testing channel layer connection...")
            channel_layer = get_channel_layer()
            
            # Try to add to a test group
            await channel_layer.group_add("test_group", "test_channel")
            logger.error("✅ SUCCESS: Channel layer group_add works")
            
            # Try to send a message
            await channel_layer.group_send("test_group", {
                "type": "test.message",
                "data": {"test": "hello"}
            })
            logger.error("✅ SUCCESS: Channel layer group_send works")
            
            # Clean up
            await channel_layer.group_discard("test_group", "test_channel")
            logger.error("✅ SUCCESS: Channel layer group_discard works")
            
        except Exception as e:
            logger.error(f"❌ FAILED: Channel layer test failed: {e}")