import re
from typing import Optional
from abc import ABC, abstractmethod

class ProxyValidatorInterface(ABC):
    @abstractmethod
    def is_valid_format(self, proxy: str) -> bool:
        pass

    @abstractmethod
    def add_protocol(self, proxy: str) -> str:
        pass

class ProxyValidator(ProxyValidatorInterface):
    def __init__(self):
        self._proxy_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}:\d{1,5}$')

    def is_valid_format(self, proxy: str) -> bool:
        """Validate proxy format using regex"""
        try:
            proxy = proxy.replace('http://', '').replace('https://', '')
            return bool(self._proxy_pattern.match(proxy))
        except:
            return False

    def add_protocol(self, proxy: str) -> str:
        """Add http protocol if missing"""
        if not proxy.startswith(('http://', 'https://')):
            return f"http://{proxy}"
        return proxy 