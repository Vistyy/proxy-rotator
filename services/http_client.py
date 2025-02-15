import aiohttp
import logging
from typing import Optional
from abc import ABC, abstractmethod

class HttpClientInterface(ABC):
    @abstractmethod
    async def get(self, url: str, timeout: int = 10, **kwargs) -> Optional[str]:
        pass

class AiohttpClient(HttpClientInterface):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    async def get(self, url: str, timeout: int = 10, **kwargs) -> Optional[str]:
        """Fetch URL content with timeout using aiohttp"""
        try:
            async with aiohttp.ClientSession(headers=self.default_headers) as session:
                async with session.get(url, timeout=timeout, **kwargs) as response:
                    return await response.text()
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None 