from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .device_service import DeviceService
from ..device_communication.phototherapy_light import PhototherapyLight
from ..device_communication.base_device import ConnectionType
import asyncio

class PhototherapyManager:
    def __init__(self):
        self.device_service = DeviceService()
        self._active_sessions = {}
        self._monitoring_tasks = {}
        self.session_alert_threshold = timedelta(minutes=15)  # Alert when 15 minutes remaining

    async def register_phototherapy_light(self,
                                        name: str,
                                        serial_number: str,
                                        location: str) -> Optional[Dict]:
        """Register a new phototherapy light"""
        device = await self.device_service.register_device(
            name=name,
            model='PhototherapyLight',
            serial_number=serial_number,
            device_type='PhototherapyLight',
            location=location
        )
        return device

    async def connect_light(self, device_id: int) -> bool:
        """Connect to a phototherapy light and start monitoring"""
        connected = await self.device_service.connect_device(device_id, ConnectionType.SERIAL)
        if connected:
            self._start_session_monitoring(device_id)
        return connected

    def _start_session_monitoring(self, device_id: int):
        """Start background session monitoring"""
        if str(device_id) not in self._monitoring_tasks:
            task = asyncio.create_task(self._monitor_session(device_id))
            self._monitoring_tasks[str(device_id)] = task

    async def _monitor_session(self, device_id: int):
        """Background task to monitor therapy session"""
        while True:
            try:
                status = await self.device_service.get_device_status(device_id)
                if status and 'parameters' in status:
                    params = status['parameters']
                    
                    # Check active session
                    if params.get('session_active'):
                        session_info = params.get('session_info', {})
                        
                        # Monitor light intensity and session duration
                        current_intensity = params.get('current_intensity')
                        start_time = datetime.fromisoformat(session_info['start_time'])
                        planned_duration = timedelta(minutes=session_info['planned_duration_minutes'])
                        elapsed_time = datetime.utcnow() - start_time
                        remaining_time = planned_duration - elapsed_time
                        
                        # Alert when session is nearly complete
                        if remaining_time <= self.session_alert_threshold:
                            await self._handle_session_alert(
                                device_id,
                                'session_ending',
                                remaining_time.total_seconds() / 60
                            )
                        
                        # Monitor intensity stability
                        if current_intensity is not None:
                            target_intensity = session_info.get('light_intensity', 100)
                            if abs(current_intensity - target_intensity) > 5:  # 5% deviation threshold
                                await self._handle_session_alert(
                                    device_id,
                                    'intensity_deviation',
                                    current_intensity
                                )
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                # Log error and continue monitoring
                print(f"Error monitoring phototherapy light {device_id}: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _handle_session_alert(self, device_id: int, alert_type: str, value: float):
        """Handle session alerts"""
        device = self.device_service.get_device_by_id(device_id)
        if device:
            alert_details = {
                'device_id': device_id,
                'device_name': device.name,
                'alert_type': alert_type,
                'value': value,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if alert_type == 'session_ending':
                alert_details['minutes_remaining'] = value
                alert_details['severity'] = 'low'
            elif alert_type == 'intensity_deviation':
                alert_details['current_intensity'] = value
                alert_details['severity'] = 'medium'
            
            # Log alert in activity log
            await self.device_service.record_device_alert(device_id, alert_type, alert_details)

    async def start_therapy_session(self,
                                  device_id: int,
                                  patient_id: str,
                                  duration_minutes: int) -> bool:
        """Start a new therapy session"""
        device = await self.device_service.get_device_status(device_id)
        if device and isinstance(device.get('device'), PhototherapyLight):
            light = device['device']
            return await light.start_session(patient_id, duration_minutes)
        return False

    async def end_therapy_session(self, device_id: int) -> bool:
        """End the current therapy session"""
        device = await self.device_service.get_device_status(device_id)
        if device and isinstance(device.get('device'), PhototherapyLight):
            light = device['device']
            return await light.end_session()
        return False

    async def set_light_intensity(self, device_id: int, intensity: float) -> bool:
        """Set light intensity percentage"""
        return await self.device_service.set_device_parameter(
            device_id, 'light_intensity', intensity)

    async def get_session_history(self,
                                device_id: int,
                                patient_id: Optional[str] = None) -> List[Dict]:
        """Get therapy session history"""
        device = await self.device_service.get_device_status(device_id)
        if device and isinstance(device.get('device'), PhototherapyLight):
            light = device['device']
            return light.get_session_history(patient_id)
        return []

    async def get_lamp_status(self, device_id: int) -> Dict[str, Any]:
        """Get detailed lamp status information"""
        device = await self.device_service.get_device_status(device_id)
        if device and isinstance(device.get('device'), PhototherapyLight):
            light = device['device']
            return light.get_lamp_status()
        return {}

    async def stop_monitoring(self, device_id: int):
        """Stop session monitoring"""
        str_id = str(device_id)
        if str_id in self._monitoring_tasks:
            self._monitoring_tasks[str_id].cancel()
            del self._monitoring_tasks[str_id]

    async def disconnect_light(self, device_id: int) -> bool:
        """Disconnect from a phototherapy light and stop monitoring"""
        await self.stop_monitoring(device_id)
        return await self.device_service.disconnect_device(device_id)

    def get_monitored_lights(self) -> List[str]:
        """Get list of currently monitored light IDs"""
        return list(self._monitoring_tasks.keys())

    async def check_maintenance_status(self, device_id: int) -> Dict[str, Any]:
        """Check maintenance requirements based on lamp hours"""
        lamp_status = await self.get_lamp_status(device_id)
        if lamp_status:
            needs_replacement = lamp_status.get('replacement_needed', False)
            hours_remaining = lamp_status.get('hours_remaining', 0)
            
            if needs_replacement:
                await self._handle_session_alert(
                    device_id,
                    'lamp_replacement_needed',
                    hours_remaining
                )
            
        return lamp_status