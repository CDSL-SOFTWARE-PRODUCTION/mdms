from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .device_service import DeviceService
from ..device_communication.sterilizer import Sterilizer
from ..device_communication.base_device import ConnectionType
import asyncio

class SterilizerManager:
    def __init__(self):
        self.device_service = DeviceService()
        self._active_cycles = {}
        self._monitoring_tasks = {}

    async def register_sterilizer(self,
                                name: str,
                                serial_number: str,
                                location: str) -> Optional[Dict]:
        """Register a new sterilizer"""
        device = await self.device_service.register_device(
            name=name,
            model='Sterilizer',
            serial_number=serial_number,
            device_type='Sterilizer',
            location=location
        )
        return device

    async def connect_sterilizer(self, device_id: int) -> bool:
        """Connect to a sterilizer and start monitoring"""
        connected = await self.device_service.connect_device(device_id, ConnectionType.ETHERNET)
        if connected:
            self._start_cycle_monitoring(device_id)
        return connected

    def _start_cycle_monitoring(self, device_id: int):
        """Start background cycle monitoring"""
        if str(device_id) not in self._monitoring_tasks:
            task = asyncio.create_task(self._monitor_cycle(device_id))
            self._monitoring_tasks[str(device_id)] = task

    async def _monitor_cycle(self, device_id: int):
        """Background task to monitor sterilization cycle"""
        while True:
            try:
                status = await self.device_service.get_device_status(device_id)
                if status and 'parameters' in status:
                    params = status['parameters']
                    
                    # Check cycle status
                    if params.get('cycle_active'):
                        cycle_info = params.get('cycle_info', {})
                        
                        # Monitor temperature and pressure
                        current_temp = cycle_info.get('current_temperature')
                        target_temp = cycle_info.get('target_temperature')
                        current_pressure = cycle_info.get('current_pressure')
                        target_pressure = cycle_info.get('target_pressure')
                        
                        if current_temp and target_temp and current_pressure and target_pressure:
                            # Check for deviations
                            temp_deviation = abs(current_temp - target_temp)
                            pressure_deviation = abs(current_pressure - target_pressure)
                            
                            if temp_deviation > 2.0 or pressure_deviation > 0.2:
                                await self._handle_cycle_alert(
                                    device_id,
                                    temp_deviation,
                                    pressure_deviation,
                                    cycle_info
                                )
                
                await asyncio.sleep(10)  # Check every 10 seconds during cycle
            except Exception as e:
                # Log error and continue monitoring
                print(f"Error monitoring sterilizer {device_id}: {str(e)}")
                await asyncio.sleep(30)  # Wait longer on error

    async def _handle_cycle_alert(self, device_id: int, temp_deviation: float, 
                                pressure_deviation: float, cycle_info: Dict):
        """Handle cycle parameter deviation alert"""
        device = self.device_service.get_device_by_id(device_id)
        if device:
            alert_details = {
                'device_id': device_id,
                'device_name': device.name,
                'cycle_id': cycle_info.get('id'),
                'temperature_deviation': temp_deviation,
                'pressure_deviation': pressure_deviation,
                'timestamp': datetime.utcnow().isoformat(),
                'severity': 'high' if (temp_deviation > 3.0 or pressure_deviation > 0.3) else 'medium'
            }
            # Log alert in activity log
            await self.device_service.record_device_alert(device_id, 'cycle_deviation', alert_details)

    async def start_sterilization_cycle(self, 
                                      device_id: int,
                                      items_list: List[str],
                                      cycle_type: str = "Standard") -> bool:
        """Start a new sterilization cycle"""
        device = await self.device_service.get_device_status(device_id)
        if device and isinstance(device.get('device'), Sterilizer):
            sterilizer = device['device']
            return await sterilizer.start_cycle(items_list, cycle_type)
        return False

    async def end_sterilization_cycle(self, device_id: int) -> bool:
        """End the current sterilization cycle"""
        device = await self.device_service.get_device_status(device_id)
        if device and isinstance(device.get('device'), Sterilizer):
            sterilizer = device['device']
            return await sterilizer.end_cycle()
        return False

    async def get_cycle_history(self, device_id: int) -> List[Dict]:
        """Get sterilization cycle history"""
        device = await self.device_service.get_device_status(device_id)
        if device and isinstance(device.get('device'), Sterilizer):
            sterilizer = device['device']
            return sterilizer.get_cycle_history()
        return []

    async def set_cycle_parameters(self, 
                                 device_id: int,
                                 temperature: Optional[float] = None,
                                 pressure: Optional[float] = None) -> bool:
        """Set sterilization cycle parameters"""
        success = True
        if temperature is not None:
            success &= await self.device_service.set_device_parameter(
                device_id, 'target_temperature', temperature)
        if pressure is not None:
            success &= await self.device_service.set_device_parameter(
                device_id, 'target_pressure', pressure)
        return success

    async def get_cycle_parameters(self, device_id: int) -> Dict[str, Any]:
        """Get current cycle parameters"""
        device = await self.device_service.get_device_status(device_id)
        if device and isinstance(device.get('device'), Sterilizer):
            return device['device'].get_parameters()
        return {}

    async def lock_door(self, device_id: int, lock: bool = True) -> bool:
        """Lock or unlock sterilizer door"""
        return await self.device_service.set_device_parameter(
            device_id, 'door_lock', lock)

    async def stop_monitoring(self, device_id: int):
        """Stop cycle monitoring"""
        str_id = str(device_id)
        if str_id in self._monitoring_tasks:
            self._monitoring_tasks[str_id].cancel()
            del self._monitoring_tasks[str_id]

    async def disconnect_sterilizer(self, device_id: int) -> bool:
        """Disconnect from a sterilizer and stop monitoring"""
        await self.stop_monitoring(device_id)
        return await self.device_service.disconnect_device(device_id)

    def get_monitored_sterilizers(self) -> List[str]:
        """Get list of currently monitored sterilizer IDs"""
        return list(self._monitoring_tasks.keys())