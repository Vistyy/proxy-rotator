import asyncio
import logging
from services.http_client import AiohttpClient
from services.proxy_validator import ProxyValidator
from services.proxy_cache import ProxyCache
from services.proxy_retriever import ProxyRetriever
from db.proxy_db import ProxyDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting proxy retriever service")
    # Initialize shared services
    http_client = AiohttpClient()
    proxy_validator = ProxyValidator()
    proxy_cache = ProxyCache()
    db = ProxyDatabase()
    logger.info("Initialized all services")

    # Initialize retriever
    retriever = ProxyRetriever(
        http_client=http_client,
        proxy_validator=proxy_validator,
        proxy_cache=proxy_cache,
        db=db
    )

    try:
        logger.info("Starting proxy retrieval loop")
        await retriever.run()
    except asyncio.CancelledError:
        logger.info("Received cancellation signal, shutting down")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}", exc_info=True)
    finally:
        logger.info("Proxy retriever service shutting down")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
