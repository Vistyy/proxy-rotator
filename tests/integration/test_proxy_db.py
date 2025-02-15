import pytest
from proxy_rotator.core.models import Proxy


@pytest.mark.integration
class TestProxyDatabase:
    @pytest.mark.asyncio
    async def test_create_proxy(self, db_session, sample_proxy):
        """Test creating a new proxy in the database."""
        proxy = Proxy(**sample_proxy)
        db_session.add(proxy)
        await db_session.commit()

        # Refresh the session to ensure we get the latest data
        await db_session.refresh(proxy)

        assert proxy.address == sample_proxy["address"]
        assert proxy.protocol == sample_proxy["protocol"]
        assert proxy.last_checked == sample_proxy["last_checked"]
        assert proxy.id is not None  # Check that ID was assigned

    @pytest.mark.asyncio
    async def test_update_proxy(self, db_session, sample_proxy):
        """Test updating a proxy in the database."""
        # Create proxy
        proxy = Proxy(**sample_proxy)
        db_session.add(proxy)
        await db_session.commit()

        # Update proxy
        new_address = "10.0.0.1:8080"
        proxy.address = new_address
        await db_session.commit()
        await db_session.refresh(proxy)

        assert proxy.address == new_address

    @pytest.mark.asyncio
    async def test_delete_proxy(self, db_session, sample_proxy):
        """Test deleting a proxy from the database."""
        # Create proxy
        proxy = Proxy(**sample_proxy)
        db_session.add(proxy)
        await db_session.commit()

        # Delete proxy
        await db_session.delete(proxy)
        await db_session.commit()

        # Try to find the proxy
        result = await db_session.get(Proxy, proxy.id)
        assert result is None
