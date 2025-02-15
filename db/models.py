from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Proxy(Base):
    __tablename__ = 'proxies'

    id = Column(Integer, primary_key=True)
    address = Column(String, nullable=False, unique=True)
    protocol = Column(String, nullable=False)
    last_checked = Column(DateTime, nullable=True)
    last_successful = Column(DateTime, nullable=True)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    response_time = Column(Float, nullable=True)  # in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source_id = Column(Integer, ForeignKey('proxy_sources.id'), nullable=True)

    stats = relationship("ProxyStats", back_populates="proxy", uselist=False)


class ProxyStats(Base):
    __tablename__ = 'proxy_stats'

    id = Column(Integer, primary_key=True)
    proxy_id = Column(Integer, ForeignKey('proxies.id'))
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_check = Column(DateTime(timezone=True))
    last_status = Column(Boolean)

    proxy = relationship("Proxy", back_populates="stats")

    @property
    def success_rate(self):
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0
