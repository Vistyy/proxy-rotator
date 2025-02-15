import asyncio
from services.http_client import AiohttpClient
from services.proxy_validator import ProxyValidator
from services.proxy_cache import ProxyCache
from services.proxy_retriever import ProxyRetriever
from services.proxy_tester import ProxyTester
from db.proxy_db import ProxyDatabase


async def main():
    # Initialize shared services
    http_client = AiohttpClient()
    proxy_validator = ProxyValidator()
    proxy_cache = ProxyCache()
    db = ProxyDatabase()

    # Initialize retriever and tester
    retriever = ProxyRetriever(
        http_client=http_client,
        proxy_validator=proxy_validator,
        proxy_cache=proxy_cache,
        db=db
    )

    tester = ProxyTester(
        http_client=http_client,
        db=db
    )

    # Start proxy tester in background
    tester_task = asyncio.create_task(tester.run())

    try:
        while True:
            # Fetch new proxies every hour
            await retriever.fetch_and_save()
            await asyncio.sleep(3600)  # 1 hour
    finally:
        tester.stop()
        await tester_task

if __name__ == "__main__":
    asyncio.run(main())
