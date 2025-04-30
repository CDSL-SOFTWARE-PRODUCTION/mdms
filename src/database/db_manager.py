from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from .models import Base

class DatabaseManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def initialize(self, connection_string: str):
        """Initialize database connection"""
        if not self._initialized:
            self.engine = create_engine(
                connection_string,
                poolclass=StaticPool,
                connect_args={'check_same_thread': False}
            )
            Base.metadata.create_all(self.engine)
            self.Session = scoped_session(sessionmaker(
                bind=self.engine,
                autoflush=True,
                expire_on_commit=False
            ))
            self._initialized = True

    def get_session(self):
        """Get a new session"""
        if not self._initialized:
            raise RuntimeError("DatabaseManager not initialized")
        return self.Session()

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
            self.Session.remove()