import asyncio
import logging
from proxy_rotator.services.http.client import AiohttpClient
from proxy_rotator.services.proxy.tester import ProxyTester
from proxy_rotator.core.database import ProxyDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting proxy tester service")
    # Initialize shared services
    http_client = AiohttpClient()
    db = ProxyDatabase()
    logger.info("Initialized database and HTTP client")

    # Initialize tester
    tester = ProxyTester(
        http_client=http_client,
        db=db
    )

    try:
        logger.info("Starting proxy testing loop")
        await tester.run()
    except asyncio.CancelledError:
        logger.info("Received cancellation signal, shutting down")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}", exc_info=True)
    finally:
        logger.info("Proxy tester service shutting down")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
