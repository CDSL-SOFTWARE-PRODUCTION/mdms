from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .device_service import DeviceService
from ..device_communication.heating_bed import HeatingBed
from ..device_communication.base_device import ConnectionType
import asyncio

class HeatingBedManager:
    def __init__(self):
        self.device_service = DeviceService()
        self._monitoring_tasks = {}
        self._temperature_alerts = {}

    async def register_heating_bed(self, 
                                 name: str,
                                 serial_number: str,
                                 location: str) -> Optional[Dict]:
        """Register a new heating bed"""
        device = await self.device_service.register_device(
            name=name,
            model='HeatingBed',
            serial_number=serial_number,
            device_type='HeatingBed',
            location=location
        )
        return device

    async def connect_bed(self, device_id: int) -> bool:
        """Connect to a heating bed and start monitoring"""
        connected = await self.device_service.connect_device(device_id, ConnectionType.SERIAL)
        if connected:
            # Start temperature monitoring for this bed
            self._start_temperature_monitoring(device_id)
        return connected

    def _start_temperature_monitoring(self, device_id: int):
        """Start background temperature monitoring for a bed"""
        if str(device_id) not in self._monitoring_tasks:
            task = asyncio.create_task(self._monitor_temperature(device_id))
            self._monitoring_tasks[str(device_id)] = task

    async def _monitor_temperature(self, device_id: int):
        """Background task to monitor temperature and trigger alerts"""
        while True:
            try:
                status = await self.device_service.get_device_status(device_id)
                if status and 'parameters' in status:
                    params = status['parameters']
                    current_temp = params.get('current_temperature')
                    target_temp = params.get('target_temperature')
                    
                    if current_temp is not None and target_temp is not None:
                        # Check for temperature deviation
                        if abs(current_temp - target_temp) > 1.0:  # 1°C deviation threshold
                            if str(device_id) not in self._temperature_alerts:
                                self._temperature_alerts[str(device_id)] = {
                                    'first_detected': datetime.utcnow(),
                                    'alert_sent': False
                                }
                            
                            alert = self._temperature_alerts[str(device_id)]
                            # If deviation persists for more than 5 minutes
                            if not alert['alert_sent'] and \
                               (datetime.utcnow() - alert['first_detected']) > timedelta(minutes=5):
                                # Trigger alert
                                await self._handle_temperature_alert(
                                    device_id, current_temp, target_temp)
                                alert['alert_sent'] = True
                        else:
                            # Clear alert if temperature is back to normal
                            if str(device_id) in self._temperature_alerts:
                                del self._temperature_alerts[str(device_id)]
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                # Log error and continue monitoring
                print(f"Error monitoring heating bed {device_id}: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _handle_temperature_alert(self, device_id: int, current_temp: float, target_temp: float):
        """Handle temperature deviation alert"""
        device = self.device_service.get_device_by_id(device_id)
        if device:
            alert_details = {
                'device_id': device_id,
                'device_name': device.name,
                'current_temperature': current_temp,
                'target_temperature': target_temp,
                'deviation': abs(current_temp - target_temp),
                'timestamp': datetime.utcnow().isoformat(),
                'severity': 'high' if abs(current_temp - target_temp) > 2.0 else 'medium'
            }
            # Log alert in activity log
            # In real implementation, would also send notifications
            await self.device_service.record_device_alert(device_id, 'temperature_deviation', alert_details)

    async def set_target_temperature(self, device_id: int, temperature: float) -> bool:
        """Set target temperature for a heating bed"""
        return await self.device_service.set_device_parameter(
            device_id, 'target_temperature', temperature)

    async def get_temperature_history(self, 
                                    device_id: int,
                                    hours: int = 24) -> List[Dict]:
        """Get temperature history for specified period"""
        device = await self.device_service.get_device_status(device_id)
        if device and isinstance(device.get('device'), HeatingBed):
            return device['device'].get_temperature_history(
                start_time=datetime.utcnow() - timedelta(hours=hours)
            )
        return []

    async def check_safety_status(self, device_id: int) -> Dict[str, Any]:
        """Check comprehensive safety status of a heating bed"""
        device = await self.device_service.get_device_status(device_id)
        if device and isinstance(device.get('device'), HeatingBed):
            return device['device'].check_safety_status()
        return {}

    async def reset_alarm(self, device_id: int) -> bool:
        """Reset alarm for a heating bed"""
        device = await self.device_service.get_device_status(device_id)
        if device and isinstance(device.get('device'), HeatingBed):
            return await device['device'].reset_alarm()
        return False

    async def stop_monitoring(self, device_id: int):
        """Stop temperature monitoring for a bed"""
        str_id = str(device_id)
        if str_id in self._monitoring_tasks:
            self._monitoring_tasks[str_id].cancel()
            del self._monitoring_tasks[str_id]
            if str_id in self._temperature_alerts:
                del self._temperature_alerts[str_id]

    async def disconnect_bed(self, device_id: int) -> bool:
        """Disconnect from a heating bed and stop monitoring"""
        await self.stop_monitoring(device_id)
        return await self.device_service.disconnect_device(device_id)

    def get_monitored_beds(self) -> List[str]:
        """Get list of currently monitored bed IDs"""
        return list(self._monitoring_tasks.keys())