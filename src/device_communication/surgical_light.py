from typing import Dict, Any, Optional
from .base_device import BaseDevice, ConnectionType, DeviceStatus
import asyncio

class SurgicalLight(BaseDevice):
    def __init__(self, device_id: str, connection_type: ConnectionType):
        super().__init__(device_id, connection_type)
        self.light_intensity = 0
        self.focus_position = 0
        self.camera_active = False
        self._supported_parameters = {
            'light_intensity': (0, 100),  # min, max percentage
            'focus_position': (0, 100),   # min, max percentage
            'camera_active': (False, True) # allowed values
        }

    async def connect(self) -> bool:
        """Establish connection with the surgical light"""
        try:
            # Implementation would depend on actual hardware protocol
            # This is a simulation
            await asyncio.sleep(1)
            self.status = DeviceStatus.CONNECTED
            return True
        except Exception:
            self.status = DeviceStatus.ERROR
            return False

    async def disconnect(self) -> bool:
        """Disconnect from the surgical light"""
        try:
            # Implementation would depend on actual hardware protocol
            await asyncio.sleep(0.5)
            self.status = DeviceStatus.DISCONNECTED
            return True
        except Exception:
            return False

    async def get_status(self) -> DeviceStatus:
        """Get current device status"""
        # In real implementation, would query actual device
        return self.status

    async def get_parameters(self) -> Dict[str, Any]:
        """Get current device parameters"""
        return {
            'light_intensity': self.light_intensity,
            'focus_position': self.focus_position,
            'camera_active': self.camera_active
        }

    async def set_parameter(self, parameter: str, value: Any) -> bool:
        """Set a specific device parameter"""
        if parameter not in self._supported_parameters:
            return False

        min_val, max_val = self._supported_parameters[parameter]
        
        try:
            if parameter == 'light_intensity':
                if 0 <= float(value) <= 100:
                    self.light_intensity = float(value)
                    return True
            elif parameter == 'focus_position':
                if 0 <= float(value) <= 100:
                    self.focus_position = float(value)
                    return True
            elif parameter == 'camera_active':
                self.camera_active = bool(value)
                return True
        except (ValueError, TypeError):
            return False
        
        return False

    async def run_diagnostic(self) -> Dict[str, Any]:
        """Run device self-diagnostic"""
        # In real implementation, would run actual diagnostic
        return {
            'light_functional': True,
            'focus_system': 'OK',
            'camera_status': 'OK' if self.camera_active else 'Inactive',
            'connection_quality': 'Good'
        }

    async def get_error_log(self) -> list:
        """Get device error log"""
        # In real implementation, would fetch from device
        return []

# Register with device factory
from .base_device import device_factory
device_factory.register('SurgicalLight', SurgicalLight)