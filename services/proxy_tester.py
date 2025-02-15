import asyncio
import logging
from datetime import datetime
from typing import List
from settings.proxy_settings import PROXY_CONFIG, PROXY_TEST
from services.http_client import HttpClientInterface
from db.proxy_db import ProxyDatabase


class ProxyTester:
    """Service responsible for continuously testing proxies in the database"""

    def __init__(
        self,
        http_client: HttpClientInterface,
        db: ProxyDatabase,
        batch_size: int = 50,
        test_interval: int = PROXY_CONFIG['CHECK_INTERVAL']
    ):
        self.logger = logging.getLogger(__name__)
        self.http_client = http_client
        self.db = db
        self.batch_size = batch_size
        self.test_interval = test_interval
        self.is_running = False

    async def test_proxy(self, proxy_data: dict) -> dict:
        """Test a single proxy"""
        response = await self.http_client.get(
            PROXY_TEST['TEST_URL'],
            timeout=PROXY_TEST['TEST_TIMEOUT'],
            proxy=proxy_data['url']
        )
        return {
            'proxy_id': proxy_data['id'],
            'success': response is not None
        }

    async def test_batch(self, proxies: List[dict]):
        """Test a batch of proxies and update their stats"""
        results = []
        for proxy in proxies:
            result = await self.test_proxy(proxy)
            results.append(result)

        # Update stats in database
        self.db.update_proxy_stats_batch(results)

        successes = sum(1 for r in results if r['success'])
        self.logger.info(f"Tested {len(results)} proxies, {successes} working")

    async def run(self):
        """Run continuous proxy testing"""
        self.is_running = True
        self.logger.info("Starting proxy tester service")

        while self.is_running:
            try:
                # Get untested/old proxies from database
                proxies = self.db.get_proxies_for_testing(
                    max_age_hours=PROXY_CONFIG['MAX_AGE_HOURS'],
                    batch_size=self.batch_size
                )

                if not proxies:
                    self.logger.info("No proxies need testing, waiting...")
                    await asyncio.sleep(self.test_interval)
                    continue

                await self.test_batch(proxies)

                # Clean up old data periodically
                self.db.cleanup_old_data()

            except Exception as e:
                self.logger.error(f"Error in proxy tester: {e}")
                await asyncio.sleep(self.test_interval)

    def stop(self):
        """Stop the proxy tester"""
        self.is_running = False
