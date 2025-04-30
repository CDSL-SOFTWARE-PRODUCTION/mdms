from datetime import datetime, UTC
from typing import Dict, Any
import uuid
from .base_device import BaseDevice, DeviceStatus, ConnectionType

class Sterilizer(BaseDevice):
    def __init__(self, device_id: str, location: str, connection_type: ConnectionType = ConnectionType.TCP):
        super().__init__(device_id, connection_type)
        self.location = location
        self.active_cycles = {}
        self._cycle_types = {
            'standard': {'temp': 134, 'duration': 20},
            'quick': {'temp': 134, 'duration': 10},
            'delicate': {'temp': 121, 'duration': 30}
        }

    async def connect(self) -> bool:
        """Connect to the device"""
        self.status = DeviceStatus.CONNECTED
        return True

    async def start_cycle(self, temperature: float = None, duration: int = None, cycle_type: str = 'standard') -> str:
        """Start a sterilization cycle"""
        if self.status != DeviceStatus.CONNECTED:
            raise RuntimeError("Device not connected")

        cycle_params = self._cycle_types.get(cycle_type, {}).copy()
        if temperature is not None:
            cycle_params['temp'] = temperature
        if duration is not None:
            cycle_params['duration'] = duration

        if not cycle_params:
            raise ValueError(f"Invalid cycle type and no parameters provided")

        cycle_id = str(uuid.uuid4())
        self.active_cycles[cycle_id] = {
            'cycle_type': cycle_type,
            'temperature': cycle_params['temp'],
            'duration': cycle_params['duration'],
            'start_time': datetime.now(UTC),
            'status': 'running'
        }
        return cycle_id

    async def get_cycle_status(self, cycle_id: str) -> str:
        """Get status of a sterilization cycle"""
        if cycle_id not in self.active_cycles:
            raise ValueError("Invalid cycle ID")
        return self.active_cycles[cycle_id]['status']

    async def abort_cycle(self, cycle_id: str) -> None:
        """Abort an active sterilization cycle"""
        if cycle_id not in self.active_cycles:
            raise ValueError("Invalid cycle ID")
        self.active_cycles[cycle_id]['status'] = 'aborted'

    async def run_diagnostic(self) -> Dict[str, Any]:
        """Run device diagnostics"""
        diagnostic_result = {
            'status': 'pass',  # or 'fail' or 'warning'
            'temperature_control': 'operational',
            'pressure_control': 'operational',
            'door_seal': 'operational',
            'safety_systems': 'operational',
            'last_calibration': datetime.now(UTC).isoformat(),
            'errors': []
        }
        return diagnostic_result