from datetime import datetime, timedelta
from typing import Dict, Optional

class ProxyCache:
    def __init__(self, cache_duration: timedelta = timedelta(minutes=10)):
        self.cache_duration = cache_duration
        self.last_fetch_time: Dict[str, datetime] = {}

    def is_valid(self, key: str) -> bool:
        """Check if cached item is still valid"""
        if key not in self.last_fetch_time:
            return False
        return datetime.now() - self.last_fetch_time[key] < self.cache_duration

    def set(self, key: str, time: Optional[datetime] = None):
        """Set cache time for a key"""
        self.last_fetch_time[key] = time or datetime.now()

    def clear(self):
        """Clear all cache entries"""
        self.last_fetch_time.clear() 