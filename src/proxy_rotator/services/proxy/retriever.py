import logging
import asyncio
from typing import List, Set, Dict
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from proxy_rotator.services.http.client import HttpClientInterface
from proxy_rotator.services.proxy.validator import ProxyValidatorInterface
from proxy_rotator.services.proxy.cache import ProxyCache
from proxy_rotator.core.database import ProxyDatabase


class ProxyRetriever:
    """Service responsible for retrieving proxies from various sources and saving to DB"""

    def __init__(
        self,
        http_client: HttpClientInterface,
        proxy_validator: ProxyValidatorInterface,
        proxy_cache: ProxyCache,
        db: ProxyDatabase
    ):
        self.logger = logging.getLogger(__name__)
        self.http_client = http_client
        self.validator = proxy_validator
        self.cache = proxy_cache
        self.db = db

        # Initialize default sources if none exist
        self.db.initialize_default_sources()

        self.source_handlers = {
            'free-proxy-list.net': self.fetch_from_free_proxy_list,
            'spys.me': self.fetch_from_spys_me
        }

    async def run(self):
        """Main loop that continuously fetches proxies from sources"""
        self.logger.info("Starting proxy retriever service")
        while True:
            try:
                await self.fetch_and_save()
                self.logger.info("Waiting for next fetch cycle")
                await asyncio.sleep(60)  # Check every minute for sources that need updating
            except asyncio.CancelledError:
                self.logger.info("Received cancellation signal")
                break
            except Exception as e:
                self.logger.error(f"Error in proxy retrieval loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait a minute before retrying on error

    async def fetch_and_save(self):
        """Fetch proxies from sources that need updating and save valid ones to database"""
        self.logger.info("Checking for sources that need updating")
        sources = self.db.get_sources_to_fetch()

        if not sources:
            self.logger.info("No sources need updating at this time")
            return

        for source in sources:
            try:
                handler = self._get_source_handler(source.url)
                if handler:
                    self.logger.info(f"Fetching proxies from {source.name} ({source.url})")
                    proxies = await handler(source.url)

                    # Convert proxies to the format expected by add_proxies
                    proxy_data = [
                        {
                            'address': proxy.split('://')[1],
                            'protocol': proxy.split('://')[0]
                        }
                        for proxy in proxies
                    ]

                    if proxy_data:
                        self.logger.info(f"Found {len(proxy_data)} proxies from {source.name}")
                        self.db.add_proxies(proxy_data, source.id)
                    else:
                        self.logger.warning(f"No proxies found from {source.name}")

                    # Update the last fetch time
                    self.db.update_source_fetch_time(source.id)
                else:
                    self.logger.warning(f"No handler found for source: {source.url}")
            except Exception as e:
                self.logger.error(f"Error fetching from {source.name}: {e}", exc_info=True)

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
