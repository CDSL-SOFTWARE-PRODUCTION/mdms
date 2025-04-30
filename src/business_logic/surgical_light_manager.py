from typing import Dict, List, Optional, Any
from datetime import datetime
from .device_service import DeviceService
from ..device_communication.surgical_light import SurgicalLight
from ..device_communication.base_device import ConnectionType
import asyncio

class SurgicalLightManager:
    def __init__(self):
        self.device_service = DeviceService()
        self._monitoring_tasks = {}

    async def register_surgical_light(self,
                                    name: str,
                                    serial_number: str,
                                    location: str) -> Optional[Dict]:
        """Register a new surgical light"""
        device = await self.device_service.register_device(
            name=name,
            model='SurgicalLight',
            serial_number=serial_number,
            device_type='SurgicalLight',
            location=location
        )
        return device

    async def connect_light(self, device_id: int) -> bool:
        """Connect to a surgical light and start monitoring"""
        connected = await self.device_service.connect_device(device_id, ConnectionType.ETHERNET)
        if connected:
            self._start_monitoring(device_id)
        return connected

    def _start_monitoring(self, device_id: int):
        """Start background monitoring"""
        if str(device_id) not in self._monitoring_tasks:
            task = asyncio.create_task(self._monitor_light(device_id))
            self._monitoring_tasks[str(device_id)] = task

    async def _monitor_light(self, device_id: int):
        """Background task to monitor light parameters"""
        while True:
            try:
                status = await self.device_service.get_device_status(device_id)
                if status and 'parameters' in status:
                    params = status['parameters']
                    
                    # Monitor light intensity stability
                    current_intensity = params.get('light_intensity')
                    if current_intensity is not None and current_intensity < 10:
                        await self._handle_alert(
                            device_id,
                            'low_intensity',
                            current_intensity
                        )
                    
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                print(f"Error monitoring surgical light {device_id}: {str(e)}")
                await asyncio.sleep(30)  # Wait longer on error

    async def _handle_alert(self, device_id: int, alert_type: str, value: float):
        """Handle monitoring alerts"""
        # In real implementation, would integrate with alert system
        print(f"Alert for surgical light {device_id}: {alert_type} = {value}")

    async def set_light_intensity(self, device_id: int, intensity: float) -> bool:
        """Set light intensity percentage"""
        return await self.device_service.set_device_parameter(
            device_id, 'light_intensity', intensity)

    async def set_focus_position(self, device_id: int, position: float) -> bool:
        """Set focus position percentage"""
        return await self.device_service.set_device_parameter(
            device_id, 'focus_position', position)

    async def toggle_camera(self, device_id: int, active: bool) -> bool:
        """Toggle camera on/off"""
        return await self.device_service.set_device_parameter(
            device_id, 'camera_active', active)

    async def stop_monitoring(self, device_id: int):
        """Stop light monitoring"""
        str_id = str(device_id)
        if str_id in self._monitoring_tasks:
            self._monitoring_tasks[str_id].cancel()
            del self._monitoring_tasks[str_id]

    async def disconnect_light(self, device_id: int) -> bool:
        """Disconnect from a surgical light and stop monitoring"""
        await self.stop_monitoring(device_id)
        return await self.device_service.disconnect_device(device_id)

    def get_monitored_lights(self) -> List[str]:
        """Get list of currently monitored light IDs"""
        return list(self._monitoring_tasks.keys())