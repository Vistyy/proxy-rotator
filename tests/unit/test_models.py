import pytest
from datetime import datetime, UTC
from proxy_rotator.core.models import Proxy


@pytest.mark.unit
class TestProxyModel:
    def test_proxy_str_representation(self):
        """Test the string representation of a proxy."""
        proxy = Proxy(
            address="192.168.1.1:8080",
            protocol="http"
        )
        assert str(proxy) == "http://192.168.1.1:8080"

    def test_proxy_to_dict(self):
        """Test converting a proxy to dictionary."""
        now = datetime.now(UTC)
        proxy = Proxy(
            id=1,
            address="192.168.1.1:8080",
            protocol="http",
            source_id=1,
            created_at=now,
            updated_at=now,
            last_checked=now
        )
        proxy_dict = proxy.to_dict()

        assert proxy_dict == {
            'id': 1,
            'address': "192.168.1.1:8080",
            'protocol': "http",
            'source_id': 1,
            'created_at': now,
            'updated_at': now,
            'last_checked': now
        }

    def test_proxy_default_protocol(self):
        """Test that protocol defaults to 'http' when not specified."""
        proxy = Proxy(address="192.168.1.1:8080")  # Only specify required fields
        assert proxy.protocol == "http"

    def test_proxy_custom_protocol(self):
        """Test that we can set a custom protocol."""
        proxy = Proxy(
            address="192.168.1.1:8080",
            protocol="socks5"
        )
        assert proxy.protocol == "socks5"
