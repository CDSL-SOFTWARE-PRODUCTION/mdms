import pytest
import pytest_asyncio
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os
import sys
import tempfile
import shutil
from datetime import datetime

# Add source directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database.models import Base
from src.database.db_manager import DatabaseManager
from src.business_logic.config_manager import ConfigManager
from src.business_logic.user_service import UserService
from src.business_logic.device_service import DeviceService
from src.business_logic.backup_service import BackupService

@pytest_asyncio.fixture(scope='session')
async def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope='session')
def temp_dir():
    """Create a temporary directory for test files"""
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    shutil.rmtree(tmp_dir)

@pytest.fixture(scope='session')
def db_path(temp_dir):
    """Create a temporary database file"""
    return os.path.join(temp_dir, 'test.db')

@pytest.fixture(scope='session')
def config_path(temp_dir):
    """Create a temporary config directory"""
    config_dir = os.path.join(temp_dir, 'config')
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

@pytest.fixture(scope='session')
def test_db(db_path):
    """Setup test database"""
    connection_string = f'sqlite:///{db_path}'
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)
    
    # Setup DatabaseManager with test database
    db_manager = DatabaseManager()
    db_manager.initialize(connection_string)
    
    return db_manager

@pytest.fixture(scope='function')
def db_session(test_db):
    """Create a new database session for a test"""
    with test_db.session_scope() as session:
        yield session

@pytest.fixture(scope='session')
def config_manager(config_path):
    """Setup test configuration"""
    config = ConfigManager()
    config.config_file = os.path.join(config_path, 'config.json')
    return config

@pytest.fixture(scope='session')
def user_service(test_db, config_manager):
    """Setup UserService with test dependencies"""
    return UserService()

@pytest.fixture(scope='session')
def device_service(test_db, config_manager):
    """Setup DeviceService with test dependencies"""
    return DeviceService()

@pytest.fixture(scope='function')
def backup_service(temp_dir, config_manager):
    """Setup BackupService with test dependencies"""
    backup_dir = os.path.join(temp_dir, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    config_manager.set_setting('backup.backup_location', backup_dir)
    return BackupService()

@pytest.fixture(scope='function')
def sample_user(user_service):
    """Create a test user"""
    user = user_service.create_user(
        username='test_user',
        password='Test123!',
        role='user',
        name='Test User'
    )
    return user

@pytest.fixture(scope='function')
def admin_user(user_service):
    """Create a test admin user"""
    admin = user_service.create_user(
        username='admin',
        password='Admin123!',
        role='admin',
        name='Admin User'
    )
    return admin

@pytest.fixture(scope='function')
def test_device(device_service):
    """Create a test device"""
    device = asyncio.get_event_loop().run_until_complete(
        device_service.register_device(
            name='Test Device',
            model='TestModel',
            serial_number='TEST001',
            device_type='HeatingBed',
            location='Test Room'
        )
    )
    return device

@pytest.fixture(scope='function')
def backup_data(temp_dir):
    """Create test data for backup/restore testing"""
    data_dir = os.path.join(temp_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Create some test files
    test_files = {
        'config.json': '{"test": "data"}',
        'data.txt': 'Test content',
        'log.txt': 'Test log entry'
    }
    
    for filename, content in test_files.items():
        with open(os.path.join(data_dir, filename), 'w') as f:
            f.write(content)
    
    return data_dir

@pytest.fixture(scope='function')
def cleanup_logs():
    """Clean up log files after tests"""
    log_dir = Path('logs')
    if log_dir.exists():
        for log_file in log_dir.glob('*.log'):
            log_file.unlink()
    yield
    if log_dir.exists():
        for log_file in log_dir.glob('*.log'):
            log_file.unlink()