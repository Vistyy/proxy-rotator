from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from settings.db_settings import DB_CONFIG
from db.models import Base, Proxy, ProxyStats, ProxySource
import logging
from typing import List, Optional


class ProxyDatabase:
    def __init__(self):
        self.setup_logging()
        self.setup_database()

    def setup_logging(self):
        self.logger = logging.getLogger(__name__)

    def setup_database(self):
        """Setup database connection and tables"""
        url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

        # Create engine with connection pool
        self.engine = create_engine(
            url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_pre_ping=True
        )

        # Create session factory
        self.Session = sessionmaker(bind=self.engine)

    def add_proxies_batch(self, proxy_urls):
        """Add multiple proxies in a single transaction"""
        session = self.Session()
        try:
            # Create proxy objects
            proxies = [
                Proxy(
                    proxy_url=url,
                    stats=ProxyStats(last_check=datetime.now())
                )
                for url in proxy_urls
            ]

            # Bulk insert with ignore conflicts
            session.bulk_save_objects(
                proxies,
                update_changed_only=True,
                preserve_order=False
            )
            session.commit()
        except SQLAlchemyError as e:
            self.logger.error(f"Error adding proxies: {e}")
            session.rollback()
        finally:
            session.close()

    def update_proxy_stats_batch(self, proxy_results):
        """Update statistics for multiple proxies at once"""
        try:
            with self.Session() as session:
                for result in proxy_results:
                    proxy_id = result['proxy_id']
                    proxy = session.get(Proxy, proxy_id)
                    if proxy:
                        proxy.last_checked = datetime.utcnow()

                        # Initialize counts if they are None
                        if proxy.success_count is None:
                            proxy.success_count = 0
                        if proxy.failure_count is None:
                            proxy.failure_count = 0

                        if result['success']:
                            proxy.last_successful = datetime.utcnow()
                            proxy.success_count += 1
                        else:
                            proxy.failure_count += 1

                        total = proxy.success_count + proxy.failure_count
                        proxy.success_rate = proxy.success_count / total if total > 0 else 0

                session.commit()
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating proxy stats: {e}")
            session.rollback()

    def get_working_proxies(self, max_age_hours, max_failures, min_success_rate):
        """Get list of working proxies based on criteria"""
        session = self.Session()
        try:
            min_check_time = datetime.now() - timedelta(hours=max_age_hours)

            stmt = select(Proxy.proxy_url).join(ProxyStats).where(
                Proxy.is_active == True,
                ProxyStats.last_check >= min_check_time,
                ProxyStats.failure_count <= max_failures,
                (ProxyStats.success_count * 1.0 /
                    func.nullif(ProxyStats.success_count + ProxyStats.failure_count, 0)
                 ) >= min_success_rate
            ).order_by(
                (ProxyStats.success_count * 1.0 /
                    func.nullif(ProxyStats.success_count + ProxyStats.failure_count, 0)
                 ).desc(),
                ProxyStats.last_check.desc()
            ).limit(1000)

            result = session.execute(stmt)
            return [row[0] for row in result]
        finally:
            session.close()

    def cleanup_old_data(self, days_old=30):
        """Archive or delete old proxy data"""
        try:
            with self.Session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=days_old)

                # Delete old stats using delete()
                session.query(ProxyStats).filter(
                    ProxyStats.last_check < cutoff_date
                ).delete(synchronize_session=False)

                session.commit()
        except SQLAlchemyError as e:
            self.logger.error(f"Error cleaning up old data: {e}")
            session.rollback()

    def get_proxies_to_test(self, max_age_hours: int, limit: int = 50) -> List[str]:
        """Get proxies that need testing"""
        session = self.Session()
        try:
            min_check_time = datetime.now() - timedelta(hours=max_age_hours)

            stmt = select(Proxy.proxy_url).join(ProxyStats).where(
                Proxy.is_active == True,
                (ProxyStats.last_check <= min_check_time) |
                (ProxyStats.last_check == None)
            ).limit(limit)

            result = session.execute(stmt)
            return [row[0] for row in result]
        finally:
            session.close()

    def get_sources(self, enabled_only: bool = True) -> List[ProxySource]:
        """Get all proxy sources from the database"""
        try:
            with self.Session() as session:
                query = select(ProxySource)
                if enabled_only:
                    query = query.where(ProxySource.enabled == True)
                return list(session.scalars(query))
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting proxy sources: {e}")
            return []

    def add_source(self, name: str, url: str, fetch_interval: int = 3600) -> Optional[ProxySource]:
        """Add a new proxy source to the database"""
        try:
            with self.Session() as session:
                source = ProxySource(
                    name=name,
                    url=url,
                    fetch_interval=fetch_interval
                )
                session.add(source)
                session.commit()
                return source
        except SQLAlchemyError as e:
            self.logger.error(f"Error adding proxy source: {e}")
            return None

    def update_source_fetch_time(self, source_id: int):
        """Update the last fetch time for a proxy source"""
        try:
            with self.Session() as session:
                source = session.get(ProxySource, source_id)
                if source:
                    source.last_fetch = datetime.utcnow()
                    session.commit()
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating source fetch time: {e}")

    def get_sources_to_fetch(self) -> List[ProxySource]:
        """Get sources that need to be fetched based on their fetch interval"""
        try:
            with self.Session() as session:
                query = select(ProxySource).where(
                    ProxySource.enabled == True,
                    (ProxySource.last_fetch == None) |
                    (func.extract('epoch', datetime.utcnow() - ProxySource.last_fetch) > ProxySource.fetch_interval)
                )
                return list(session.scalars(query))
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting sources to fetch: {e}")
            return []

    def add_proxies(self, proxies: List[dict], source_id: Optional[int] = None):
        """Add new proxies to the database"""
        try:
            with self.Session() as session:
                # Prepare all proxy objects
                proxy_objects = [
                    Proxy(
                        address=proxy_data['address'],
                        protocol=proxy_data['protocol'],
                        source_id=source_id,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    for proxy_data in proxies
                ]

                # Bulk insert with ON CONFLICT DO NOTHING
                stmt = text("""
                    INSERT INTO proxies (address, protocol, source_id, created_at, updated_at)
                    VALUES (:address, :protocol, :source_id, :created_at, :updated_at)
                    ON CONFLICT (address) DO NOTHING
                """)

                # Execute bulk insert
                session.execute(stmt, [
                    {
                        'address': proxy.address,
                        'protocol': proxy.protocol,
                        'source_id': proxy.source_id,
                        'created_at': proxy.created_at,
                        'updated_at': proxy.updated_at
                    }
                    for proxy in proxy_objects
                ])

                session.commit()
                self.logger.info(f"Added proxies to database (duplicates ignored)")
        except SQLAlchemyError as e:
            self.logger.error(f"Error adding proxies: {e}")
            session.rollback()

    def get_proxies_for_testing(self, max_age_hours: int = 1, batch_size: int = 50) -> List[dict]:
        """Get a batch of proxies that need testing"""
        try:
            with self.Session() as session:
                min_check_time = datetime.utcnow() - timedelta(hours=max_age_hours)
                query = select(Proxy).where(
                    (Proxy.last_checked == None) |
                    (datetime.utcnow() - Proxy.last_checked >
                     timedelta(minutes=5))  # Test interval from config
                ).limit(batch_size)

                proxies = list(session.scalars(query))
                return [
                    {
                        'id': proxy.id,
                        'url': f"{proxy.protocol}://{proxy.address}"
                    }
                    for proxy in proxies
                ]
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting proxies for testing: {e}")
            return []

    def update_proxy_stats(self, proxy_id: int, success: bool, response_time: Optional[float] = None):
        """Update proxy statistics after a test"""
        try:
            with self.Session() as session:
                proxy = session.get(Proxy, proxy_id)
                if proxy:
                    proxy.last_checked = datetime.utcnow()

                    # Initialize counts if they are None
                    if proxy.success_count is None:
                        proxy.success_count = 0
                    if proxy.failure_count is None:
                        proxy.failure_count = 0

                    if success:
                        proxy.last_successful = datetime.utcnow()
                        proxy.success_count += 1
                    else:
                        proxy.failure_count += 1

                    total = proxy.success_count + proxy.failure_count
                    proxy.success_rate = proxy.success_count / total if total > 0 else 0

                    if response_time is not None:
                        proxy.response_time = response_time

                    session.commit()
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating proxy stats: {e}")

    def initialize_default_sources(self):
        """Initialize default proxy sources if none exist"""
        try:
            with self.Session() as session:
                if session.scalar(select(ProxySource).limit(1)) is None:
                    default_sources = [
                        {
                            'name': 'Free Proxy List',
                            'url': 'https://free-proxy-list.net/',
                            'fetch_interval': 3600
                        },
                        {
                            'name': 'Spys.me',
                            'url': 'https://spys.me/proxy.txt',
                            'fetch_interval': 3600
                        }
                    ]
                    for source in default_sources:
                        session.add(ProxySource(**source))
                    session.commit()
                    self.logger.info("Initialized default proxy sources")
        except SQLAlchemyError as e:
            self.logger.error(f"Error initializing default sources: {e}")
