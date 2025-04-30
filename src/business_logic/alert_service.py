from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import logging
from .user_service import UserService
from .performance_monitor import PerformanceMonitor
from .device_service import DeviceService

class AlertService:
    def __init__(self):
        self.user_service = UserService()
        self.performance_monitor = PerformanceMonitor()
        self.device_service = DeviceService()
        self._active_alerts: Dict[str, Dict] = {}
        self._monitor_task = None

    async def start_monitoring(self):
        """Start alert monitoring"""
        if not self._monitor_task:
            self._monitor_task = asyncio.create_task(self._alert_monitor())
            logging.info("Alert monitoring started")

    async def stop_monitoring(self):
        """Stop alert monitoring"""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
            logging.info("Alert monitoring stopped")

    async def _alert_monitor(self):
        """Monitor various system components for alerts"""
        while True:
            try:
                # Check system performance
                perf_metrics = self.performance_monitor.get_system_performance()
                await self._check_performance_alerts(perf_metrics)

                # Check slow operations
                slow_ops = self.performance_monitor.get_slow_operations()
                if slow_ops:
                    await self._handle_slow_operations(slow_ops)

                # Check device maintenance
                due_devices = self.device_service.get_devices_due_maintenance()
                await self._check_maintenance_alerts(due_devices)

                # Check warranty expiry
                warranty_devices = self.device_service.get_warranty_expiring_devices()
                await self._check_warranty_alerts(warranty_devices)

                # Check spare parts inventory
                low_stock = self.device_service.get_low_stock_parts()
                await self._check_inventory_alerts(low_stock)

                await asyncio.sleep(300)  # Check every 5 minutes
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logging.error(f"Error in alert monitor: {str(e)}")
                await asyncio.sleep(60)

    async def _check_performance_alerts(self, metrics: Dict):
        """Check and handle performance alerts"""
        alert_id = 'system_performance'
        if metrics['cpu_usage'] > 80 or metrics['memory_usage'] > 80 or metrics['disk_usage'] > 80:
            if alert_id not in self._active_alerts:
                self._active_alerts[alert_id] = {
                    'type': 'performance',
                    'timestamp': datetime.utcnow(),
                    'details': metrics,
                    'severity': 'high'
                }
                await self._notify_admins(
                    "High System Resource Usage",
                    f"CPU: {metrics['cpu_usage']}%\n"
                    f"Memory: {metrics['memory_usage']}%\n"
                    f"Disk: {metrics['disk_usage']}%"
                )
        else:
            self._active_alerts.pop(alert_id, None)

    async def _check_maintenance_alerts(self, due_devices: List[Any]):
        """Check and handle maintenance alerts"""
        for device in due_devices:
            alert_id = f'maintenance_{device.id}'
            if alert_id not in self._active_alerts:
                self._active_alerts[alert_id] = {
                    'type': 'maintenance',
                    'timestamp': datetime.utcnow(),
                    'device_id': device.id,
                    'severity': 'medium'
                }
                await self._notify_maintenance(
                    f"Maintenance Due for {device.name}",
                    f"Device {device.name} is due for maintenance on {device.next_maintenance_due}"
                )

    async def _check_warranty_alerts(self, warranty_devices: List[Any]):
        """Check and handle warranty expiry alerts"""
        for device in warranty_devices:
            alert_id = f'warranty_{device.id}'
            if alert_id not in self._active_alerts:
                self._active_alerts[alert_id] = {
                    'type': 'warranty',
                    'timestamp': datetime.utcnow(),
                    'device_id': device.id,
                    'severity': 'low'
                }
                await self._notify_maintenance(
                    f"Warranty Expiring for {device.name}",
                    f"Device warranty expires on {device.warranty_expiry}"
                )

    async def _check_inventory_alerts(self, low_stock_parts: List[Any]):
        """Check and handle inventory alerts"""
        for part in low_stock_parts:
            alert_id = f'inventory_{part.id}'
            if alert_id not in self._active_alerts:
                self._active_alerts[alert_id] = {
                    'type': 'inventory',
                    'timestamp': datetime.utcnow(),
                    'part_id': part.id,
                    'severity': 'medium'
                }
                await self._notify_maintenance(
                    f"Low Stock Alert: {part.name}",
                    f"Current quantity ({part.quantity}) is below minimum ({part.minimum_quantity})"
                )

    async def _handle_slow_operations(self, slow_ops: List[Dict]):
        """Handle slow operation alerts"""
        alert_id = 'slow_operations'
        if slow_ops and alert_id not in self._active_alerts:
            self._active_alerts[alert_id] = {
                'type': 'performance',
                'timestamp': datetime.utcnow(),
                'details': slow_ops,
                'severity': 'medium'
            }
            await self._notify_admins(
                "Slow Operations Detected",
                f"Found {len(slow_ops)} operations exceeding 2-second threshold"
            )

    async def _notify_admins(self, title: str, message: str):
        """Notify system administrators"""
        # In real implementation, would integrate with notification system
        logging.warning(f"Admin Alert - {title}: {message}")

    async def _notify_maintenance(self, title: str, message: str):
        """Notify maintenance staff"""
        # In real implementation, would integrate with notification system
        logging.warning(f"Maintenance Alert - {title}: {message}")

    def get_active_alerts(self) -> List[Dict]:
        """Get list of currently active alerts"""
        return [
            {**alert, 'id': alert_id}
            for alert_id, alert in self._active_alerts.items()
        ]

    def clear_alert(self, alert_id: str):
        """Clear a specific alert"""
        self._active_alerts.pop(alert_id, None)