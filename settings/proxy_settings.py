# Proxy configuration
PROXY_CONFIG = {
    'MAX_AGE_HOURS': 24,
    'MIN_SUCCESS_RATE': 0.3,
    'MAX_FAILURES': 3,
    'CHECK_INTERVAL': 300,  # 5 minutes
}

# Proxy testing settings
PROXY_TEST = {
    'TEST_URL': 'https://httpbin.org/ip',  # Generic test URL
    'TEST_TIMEOUT': 10,
    'MAX_TEST_RETRIES': 2,
}

# Proxy sources
PROXY_SOURCES = [
    'https://free-proxy-list.net/',
    'https://spys.me/proxy.txt',
]
