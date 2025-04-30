from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Table
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Association tables for many-to-many relationships
device_category_association = Table(
    'device_category_association',
    Base.metadata,
    Column('device_id', Integer, ForeignKey('devices.id')),
    Column('category_id', Integer, ForeignKey('device_categories.id'))
)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), nullable=False)
    name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Device(Base):
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    model = Column(String(100))
    serial_number = Column(String(50), unique=True)
    status = Column(String(20))
    location = Column(String(100))
    purchase_date = Column(DateTime)
    warranty_expiry = Column(DateTime)
    last_maintenance = Column(DateTime)
    next_maintenance_due = Column(DateTime)
    categories = relationship("DeviceCategory", secondary=device_category_association)

class DeviceCategory(Base):
    __tablename__ = 'device_categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))

class MaintenanceRecord(Base):
    __tablename__ = 'maintenance_records'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'))
    performed_by = Column(Integer, ForeignKey('users.id'))
    date = Column(DateTime, default=datetime.utcnow)
    description = Column(String(500))
    cost = Column(Float)
    next_maintenance = Column(DateTime)

class UsageHistory(Base):
    __tablename__ = 'usage_history'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration = Column(Float)  # in minutes
    notes = Column(String(200))

class SparePart(Base):
    __tablename__ = 'spare_parts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    part_number = Column(String(50), unique=True)
    quantity = Column(Integer, default=0)
    minimum_quantity = Column(Integer, default=1)
    location = Column(String(100))
    device_model = Column(String(100))  # Compatible device model

class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String(50))
    details = Column(String(500))
    ip_address = Column(String(45))  # IPv6 compatible