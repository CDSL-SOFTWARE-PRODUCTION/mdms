from datetime import datetime, UTC
from typing import Dict, Any
from .base_device import BaseDevice, DeviceStatus, ConnectionType

class HeatingBed(BaseDevice):
    def __init__(self, device_id: str, location: str, connection_type: ConnectionType = ConnectionType.TCP):
        super().__init__(device_id, connection_type)
        self.location = location
        self.target_temperature = 37.0  # Default temperature in Celsius
        self.current_temperature = 37.0  # Initialize to room temperature
        self.is_heating = False
        self.timestamp = datetime.now(UTC)
        self._safety_limits = {
            'min_temp': 20.0,
            'max_temp': 42.0
        }

    async def connect(self) -> bool:
        """Connect to the device"""
        # For testing, simulate successful connection
        self.status = DeviceStatus.CONNECTED
        return True

    async def get_temperature(self) -> float:
        """Get current temperature"""
        # For testing, simulate temperature reading
        if self.status != DeviceStatus.CONNECTED:
            raise RuntimeError("Device not connected")
        return self.current_temperature

    async def set_temperature(self, temp: float) -> None:
        """Set target temperature with safety checks"""
        if temp < self._safety_limits['min_temp'] or temp > self._safety_limits['max_temp']:
            raise ValueError(f"Temperature must be between {self._safety_limits['min_temp']} and {self._safety_limits['max_temp']}")
        self.target_temperature = temp

    async def reset(self) -> None:
        """Reset device to default state"""
        self.target_temperature = 37.0
        self.current_temperature = 37.0
        self.is_heating = False
        self.status = DeviceStatus.IDLE

    async def run_diagnostic(self) -> Dict[str, Any]:
        """Run device diagnostics"""
        diagnostic_result = {
            'status': 'pass',  # or 'fail' or 'warning'
            'temperature_sensor': 'operational',
            'heating_element': 'operational',
            'safety_system': 'operational',
            'last_calibration': datetime.now(UTC).isoformat(),
            'errors': []
        }
        return diagnostic_result

    async def _monitor_loop(self):
        """Background monitoring loop"""
        while self.status != DeviceStatus.ERROR:
            # Simulate temperature changes
            if self.is_heating and self.current_temperature < self.target_temperature:
                self.current_temperature += 0.1
            elif self.current_temperature > self.target_temperature:
                self.current_temperature -= 0.1
            await self._sleep(1)