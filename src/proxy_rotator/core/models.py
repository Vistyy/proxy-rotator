from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, UTC

Base = declarative_base()


class ProxySource(Base):
    """Model for storing proxy source information"""
    __tablename__ = 'proxy_sources'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    enabled = Column(Boolean, default=True)
    last_fetch = Column(DateTime, nullable=True)
    fetch_interval = Column(Integer, default=3600)  # Default 1 hour in seconds
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class Proxy(Base):
    """Model for storing proxy information"""
    __tablename__ = 'proxies'

    id = Column(Integer, primary_key=True)
    address = Column(String, nullable=False)
    protocol = Column(String, nullable=False, default='http', server_default='http')
    source_id = Column(Integer, ForeignKey('proxy_sources.id'))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    last_checked = Column(DateTime, nullable=True)

    source = relationship("ProxySource", backref="proxies")

    def __init__(self, **kwargs):
        """Initialize a proxy with default values."""
        kwargs.setdefault('protocol', 'http')
        super().__init__(**kwargs)

    def __str__(self):
        """Return string representation of proxy."""
        return f"{self.protocol}://{self.address}"

    def to_dict(self):
        """Convert proxy to dictionary."""
        return {
            'id': self.id,
            'address': self.address,
            'protocol': self.protocol,
            'source_id': self.source_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_checked': self.last_checked
        }


class ProxyStats(Base):
    """Model for storing proxy statistics"""
    __tablename__ = 'proxy_stats'

    id = Column(Integer, primary_key=True)
    proxy_id = Column(Integer, ForeignKey('proxies.id'))
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_success = Column(DateTime, nullable=True)
    last_failure = Column(DateTime, nullable=True)
    last_check = Column(DateTime, nullable=True)
    average_response_time = Column(Float, nullable=True)

    proxy = relationship("Proxy", backref="stats")

    @property
    def success_rate(self):
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0
