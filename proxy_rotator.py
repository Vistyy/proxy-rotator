import requests
from typing import List, Optional
from urllib.parse import urlparse
import logging
from settings.proxy_settings import PROXY_CONFIG, PROXY_TEST
from proxy_fetcher import ProxyFetcher


class ProxyRotator:
    def __init__(self, proxy_list: List[str] = None, test_url: str = None):
        """
        Initialize the ProxyRotator with a list of proxies.

        Args:
            proxy_list (List[str], optional): List of proxy URLs. If None, fetches from sources.
            test_url (str): Optional URL to test proxy connectivity
        """
        self.setup_logging()

        # Initialize database
        from db.proxy_db import ProxyDatabase
        self.db = ProxyDatabase()

        # Initialize proxy list
        if proxy_list is None:
            self.logger.info("Fetching proxies from configured sources...")
            fetcher = ProxyFetcher()
            proxy_list = fetcher.fetch_all()
            self.logger.info(f"Fetched {len(proxy_list)} proxies")

        self.proxy_list = proxy_list
        self.current_index = 0
        self.working_proxies = []
        self.test_url = test_url or PROXY_TEST['TEST_URL']

        # Add proxies in batch
        self.db.add_proxies_batch(proxy_list)

        self.validate_proxies()

    def setup_logging(self):
        """Configure basic logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def validate_proxy(self, proxy: str) -> bool:
        """
        Test if a proxy is working.

        Args:
            proxy (str): Proxy URL to test

        Returns:
            bool: True if proxy is working, False otherwise
        """
        for attempt in range(PROXY_TEST['MAX_TEST_RETRIES']):
            try:
                proxies = {
                    'http': proxy,
                    'https': proxy
                }
                response = requests.get(
                    self.test_url,
                    proxies=proxies,
                    timeout=PROXY_TEST['TEST_TIMEOUT']
                )
                if response.status_code == 200:
                    self.db.update_proxy_stats(proxy, success=True)
                    return True

            except Exception as e:
                self.logger.warning(f"Proxy {proxy} failed validation attempt {attempt + 1}: {str(e)}")

        self.db.update_proxy_stats(proxy, success=False)
        return False

    def validate_proxies(self):
        """Validate all proxies in the list and keep only working ones"""
        self.logger.info("Validating proxies...")

        # Get working proxies from database based on criteria
        self.working_proxies = self.db.get_working_proxies(
            max_age_hours=PROXY_CONFIG['MAX_AGE_HOURS'],
            max_failures=PROXY_CONFIG['MAX_FAILURES'],
            min_success_rate=PROXY_CONFIG['MIN_SUCCESS_RATE']
        )

        # Test proxies in batches
        batch_size = 50  # Adjust based on your needs
        to_test = [p for p in self.proxy_list if p not in self.working_proxies]

        for i in range(0, len(to_test), batch_size):
            batch = to_test[i:i + batch_size]
            results = []

            for proxy in batch:
                success = self.validate_proxy(proxy)
                results.append({
                    'proxy': proxy,
                    'success': success
                })
                if success:
                    self.working_proxies.append(proxy)

            # Update stats in batch
            self.db.update_proxy_stats_batch(results)

        self.logger.info(f"Found {len(self.working_proxies)} working proxies")

    def get_next_proxy(self) -> Optional[str]:
        """
        Get the next working proxy in the rotation.

        Returns:
            Optional[str]: Next working proxy or None if no working proxies
        """
        if not self.working_proxies:
            self.logger.error("No working proxies available")
            return None

        proxy = self.working_proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.working_proxies)
        return proxy

    def make_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Make a request using the next proxy in rotation.

        Args:
            url (str): URL to make request to
            **kwargs: Additional arguments to pass to requests.get()

        Returns:
            Optional[requests.Response]: Response object or None if request fails
        """
        proxy = self.get_next_proxy()
        if not proxy:
            return None

        try:
            proxies = {
                'http': proxy,
                'https': proxy
            }
            kwargs['proxies'] = proxies
            response = requests.get(url, **kwargs)
            return response
        except Exception as e:
            self.logger.error(f"Request failed with proxy {proxy}: {str(e)}")
            return None
