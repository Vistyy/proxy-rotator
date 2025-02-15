from abc import ABC, abstractmethod
import aiohttp
from typing import Optional
import logging


class HttpClientInterface(ABC):
    @abstractmethod
    async def get(self, url: str, timeout: int = 10, proxy: Optional[str] = None) -> Optional[str]:
        """Make a GET request"""
        pass


class AiohttpClient(HttpClientInterface):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    async def get(self, url: str, timeout: int = 10, proxy: Optional[str] = None) -> Optional[str]:
        """Make a GET request using aiohttp"""
        try:
            async with aiohttp.ClientSession(headers=self.default_headers) as session:
                async with session.get(url, proxy=proxy, timeout=timeout) as response:
                    if response.status == 200:
                        return await response.text()
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None
        return None
