import logging
import asyncio
from typing import List, Set
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from settings.proxy_settings import PROXY_SOURCES, PROXY_TEST
from services.http_client import HttpClientInterface
from services.proxy_validator import ProxyValidatorInterface
from services.proxy_cache import ProxyCache


class ProxyFetcher:
    def __init__(
        self,
        http_client: HttpClientInterface,
        proxy_validator: ProxyValidatorInterface,
        proxy_cache: ProxyCache
    ):
        self.logger = logging.getLogger(__name__)
        self.http_client = http_client
        self.validator = proxy_validator
        self.cache = proxy_cache
        
        self.source_handlers = {
            'free-proxy-list.net': self.fetch_from_free_proxy_list,
            'spys.me': self.fetch_from_spys_me
        }

    async def fetch_from_free_proxy_list(self, url: str) -> Set[str]:
        """Fetch proxies from free-proxy-list.net"""
        if self.cache.is_valid(url):
            return set()

        proxies = set()
        content = await self.http_client.get(url)
        if not content:
            return proxies

        try:
            soup = BeautifulSoup(content, 'html.parser')
            table = soup.find('table')
            
            if table:
                for row in table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        ip = cols[0].text.strip()
                        port = cols[1].text.strip()
                        is_https = cols[6].text.strip() == 'yes'
                        
                        if ip and port:
                            proxy = f"{ip}:{port}"
                            if self.validator.is_valid_format(proxy):
                                protocol = 'https' if is_https else 'http'
                                proxies.add(f"{protocol}://{proxy}")

            self.cache.set(url)
            self.logger.info(f"Fetched {len(proxies)} proxies from {url}")
            
        except Exception as e:
            self.logger.error(f"Error parsing {url}: {e}")
        
        return proxies

    async def fetch_from_spys_me(self, url: str) -> Set[str]:
        """Fetch proxies from spys.me"""
        if self.cache.is_valid(url):
            return set()

        proxies = set()
        content = await self.http_client.get(url)
        if not content:
            return proxies

        try:
            for line in content.split('\n'):
                if ':' in line:
                    proxy = line.split()[0]
                    if self.validator.is_valid_format(proxy):
                        proxies.add(self.validator.add_protocol(proxy))

            self.cache.set(url)
            self.logger.info(f"Fetched {len(proxies)} proxies from {url}")
            
        except Exception as e:
            self.logger.error(f"Error parsing {url}: {e}")
        
        return proxies

    def _get_source_handler(self, url: str):
        """Get the appropriate handler for the source URL"""
        domain = urlparse(url).netloc
        for key, handler in self.source_handlers.items():
            if key in domain:
                return handler
        return None

    async def _quick_check_proxy(self, proxy: str) -> bool:
        """Quickly check if proxy responds"""
        response = await self.http_client.get(
            PROXY_TEST['TEST_URL'],
            timeout=PROXY_TEST['TEST_TIMEOUT'],
            proxy=proxy
        )
        return response is not None

    async def fetch_all(self) -> List[str]:
        """Fetch proxies from all configured sources"""
        all_proxies = set()
        fetch_tasks = []

        for url in PROXY_SOURCES:
            handler = self._get_source_handler(url)
            if handler:
                fetch_tasks.append(handler(url))
            else:
                self.logger.warning(f"No handler found for source: {url}")

        proxy_sets = await asyncio.gather(*fetch_tasks)
        for proxy_set in proxy_sets:
            all_proxies.update(proxy_set)

        valid_proxies = []
        async def check_proxy(proxy):
            if await self._quick_check_proxy(proxy):
                valid_proxies.append(proxy)

        check_tasks = [check_proxy(proxy) for proxy in all_proxies]
        await asyncio.gather(*check_tasks)

        self.logger.info(f"Found {len(valid_proxies)} working proxies out of {len(all_proxies)} total")
        return valid_proxies

    def fetch_all_sync(self) -> List[str]:
        """Synchronous wrapper for fetch_all"""
        return asyncio.run(self.fetch_all())
