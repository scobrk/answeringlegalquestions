#!/usr/bin/env python3
"""
Startup script for NSW Revenue AI Assistant
Handles environment setup and graceful startup
"""

import os
import sys
import logging
from pathlib import Path

# Set up environment
os.environ.setdefault('PYTHONPATH', '.')
os.environ.setdefault('PYTHONUNBUFFERED', '1')

# Add current directory to Python path
current_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(current_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main startup function"""
    try:
        logger.info("🚀 Starting NSW Revenue AI Assistant...")
        logger.info(f"Python path: {sys.path[:3]}...")
        logger.info(f"Working directory: {os.getcwd()}")

        # Check environment
        port = int(os.getenv("PORT", 8080))
        logger.info(f"Starting on port: {port}")

        # Import and run FastAPI app
        import uvicorn
        from fastapi_app import app

        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()