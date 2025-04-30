from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..database.db_manager import DatabaseManager
from ..database.models import Device, DeviceCategory, MaintenanceRecord, UsageHistory, SparePart
from ..device_communication.base_device import BaseDevice, DeviceFactory, DeviceStatus, ConnectionType

class DeviceService:
    def __init__(self):
        self.db = DatabaseManager()
        self._active_devices: Dict[str, BaseDevice] = {}

    async def register_device(self, 
                            name: str,
                            model: str,
                            serial_number: str,
                            device_type: str,
                            location: str,
                            category_ids: List[int] = None) -> Optional[Device]:
        """Register a new medical device in the system"""
        # Check if device already exists
        existing = self.db.query(Device, serial_number=serial_number)
        if existing:
            return None

        # Create new device record
        device = Device(
            name=name,
            model=model,
            serial_number=serial_number,
            status=DeviceStatus.DISCONNECTED.value,
            location=location,
            purchase_date=datetime.utcnow()
        )

        # Add categories if provided
        if category_ids:
            categories = []
            for cat_id in category_ids:
                category = self.db.get_by_id(DeviceCategory, cat_id)
                if category:
                    categories.append(category)
            device.categories = categories

        return self.db.add(device)

    async def connect_device(self, device_id: int, connection_type: ConnectionType) -> bool:
        """Connect to a physical device"""
        device_record = self.db.get_by_id(Device, device_id)
        if not device_record:
            return False

        # Create device instance if not already connected
        if device_id not in self._active_devices:
            try:
                device_instance = DeviceFactory.create_device(
                    device_record.model,
                    str(device_id),
                    connection_type
                )
                connected = await device_instance.connect()
                if connected:
                    self._active_devices[str(device_id)] = device_instance
                    device_record.status = DeviceStatus.CONNECTED.value
                    self.db.update(device_record)
                    await device_instance.start_monitoring()
                    return True
            except Exception as e:
                # Log error here
                return False
        return False

    async def disconnect_device(self, device_id: int) -> bool:
        """Disconnect from a physical device"""
        device_str_id = str(device_id)
        if device_str_id in self._active_devices:
            device = self._active_devices[device_str_id]
            await device.stop_monitoring()
            disconnected = await device.disconnect()
            if disconnected:
                del self._active_devices[device_str_id]
                device_record = self.db.get_by_id(Device, device_id)
                if device_record:
                    device_record.status = DeviceStatus.DISCONNECTED.value
                    self.db.update(device_record)
                return True
        return False

    async def get_device_status(self, device_id: int) -> Optional[Dict[str, Any]]:
        """Get current device status and parameters"""
        device_str_id = str(device_id)
        if device_str_id in self._active_devices:
            device = self._active_devices[device_str_id]
            status = await device.get_status()
            parameters = await device.get_parameters()
            return {
                'status': status.value,
                'parameters': parameters,
                'last_update': device.last_update.isoformat()
            }
        return None

    def get_device_by_id(self, device_id: int) -> Optional[Device]:
        """Get device record by ID"""
        return self.db.get_by_id(Device, device_id)

    def search_devices(self, **filters) -> List[Device]:
        """Search devices with filters"""
        return self.db.query(Device, **filters)

    def update_device(self, device_id: int, **updates) -> bool:
        """Update device information"""
        device = self.get_device_by_id(device_id)
        if not device:
            return False

        for key, value in updates.items():
            if hasattr(device, key):
                setattr(device, key, value)

        return self.db.update(device)

    async def set_device_parameter(self, device_id: int, parameter: str, value: Any) -> bool:
        """Set a specific parameter on the device"""
        device_str_id = str(device_id)
        if device_str_id in self._active_devices:
            device = self._active_devices[device_str_id]
            return await device.set_parameter(parameter, value)
        return False

    def record_usage(self, device_id: int, user_id: int, start_time: datetime, 
                    end_time: datetime = None, notes: str = None) -> Optional[UsageHistory]:
        """Record device usage"""
        device = self.get_device_by_id(device_id)
        if not device:
            return None

        usage = UsageHistory(
            device_id=device_id,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            notes=notes
        )

        if end_time:
            duration = (end_time - start_time).total_seconds() / 60  # Convert to minutes
            usage.duration = duration

        return self.db.add(usage)

    def schedule_maintenance(self, device_id: int, task_description: str,
                           scheduled_date: datetime) -> Optional[MaintenanceRecord]:
        """Schedule device maintenance"""
        device = self.get_device_by_id(device_id)
        if not device:
            return None

        maintenance = MaintenanceRecord(
            device_id=device_id,
            description=task_description,
            next_maintenance=scheduled_date
        )

        if self.db.add(maintenance):
            device.next_maintenance_due = scheduled_date
            self.db.update(device)
            return maintenance
        return None

    def get_maintenance_history(self, device_id: int) -> List[MaintenanceRecord]:
        """Get maintenance history for a device"""
        return self.db.query(MaintenanceRecord, device_id=device_id)

    def get_usage_history(self, device_id: int, 
                         start_date: datetime = None,
                         end_date: datetime = None) -> List[UsageHistory]:
        """Get usage history for a device"""
        filters = {'device_id': device_id}
        # Implementation for date filtering would go here
        return self.db.query(UsageHistory, **filters)

    def get_devices_due_maintenance(self, days_threshold: int = 7) -> List[Device]:
        """Get devices due for maintenance within the specified days"""
        threshold_date = datetime.utcnow() + timedelta(days=days_threshold)
        devices = self.db.get_all(Device)
        return [device for device in devices 
                if device.next_maintenance_due 
                and device.next_maintenance_due <= threshold_date]

    def get_warranty_expiring_devices(self, days_threshold: int = 30) -> List[Device]:
        """Get devices with warranty expiring soon"""
        threshold_date = datetime.utcnow() + timedelta(days=days_threshold)
        devices = self.db.get_all(Device)
        return [device for device in devices 
                if device.warranty_expiry 
                and device.warranty_expiry <= threshold_date]

    def manage_spare_parts(self, action: str, part_id: int = None, 
                          **part_details) -> Optional[SparePart]:
        """Manage spare parts inventory"""
        if action == "add":
            part = SparePart(**part_details)
            return self.db.add(part)
        elif action == "update" and part_id:
            part = self.db.get_by_id(SparePart, part_id)
            if part:
                for key, value in part_details.items():
                    if hasattr(part, key):
                        setattr(part, key, value)
                if self.db.update(part):
                    return part
        return None

    def get_low_stock_parts(self) -> List[SparePart]:
        """Get spare parts with stock below minimum quantity"""
        parts = self.db.get_all(SparePart)
        return [part for part in parts if part.quantity <= part.minimum_quantity]

    async def run_device_diagnostic(self, device_id: int) -> Optional[Dict[str, Any]]:
        """Run diagnostic on a device"""
        device_str_id = str(device_id)
        if device_str_id in self._active_devices:
            device = self._active_devices[device_str_id]
            return await device.run_diagnostic()
        return None