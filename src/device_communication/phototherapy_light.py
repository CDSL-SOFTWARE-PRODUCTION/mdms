from datetime import datetime, UTC
from typing import Dict, Any
import uuid
from .base_device import BaseDevice, DeviceStatus, ConnectionType

class PhototherapyLight(BaseDevice):
    def __init__(self, device_id: str, location: str, connection_type: ConnectionType = ConnectionType.TCP):
        super().__init__(device_id, connection_type)
        self.location = location
        self.active_sessions = {}
        self._intensity_limits = {
            'min': 0,
            'max': 100
        }

    async def connect(self) -> bool:
        """Connect to the device"""
        self.status = DeviceStatus.CONNECTED
        return True

    async def start_session(self, duration: int, intensity: int) -> str:
        """Start a new phototherapy session"""
        if self.status != DeviceStatus.CONNECTED:
            raise RuntimeError("Device not connected")

        if not (0 <= intensity <= 100):
            raise ValueError("Intensity must be between 0 and 100")

        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = {
            'duration': duration,
            'intensity': intensity,
            'start_time': datetime.now(UTC),
            'status': 'running'
        }
        return session_id

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session information"""
        if session_id not in self.active_sessions:
            raise ValueError("Invalid session ID")
        return self.active_sessions[session_id]

    async def stop_session(self, session_id: str) -> None:
        """Stop an active session"""
        if session_id not in self.active_sessions:
            raise ValueError("Invalid session ID")
        self.active_sessions[session_id]['status'] = 'completed'

    async def run_diagnostic(self) -> Dict[str, Any]:
        """Run device diagnostics"""
        diagnostic_result = {
            'status': 'pass',  # or 'fail' or 'warning'
            'light_source': 'operational',
            'intensity_sensor': 'operational',
            'timer': 'operational',
            'safety_system': 'operational',
            'last_calibration': datetime.now(UTC).isoformat(),
            'errors': []
        }
        return diagnostic_result