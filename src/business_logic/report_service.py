from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..database.db_manager import DatabaseManager
from ..database.models import (
    Device, MaintenanceRecord, UsageHistory, 
    ActivityLog, SparePart
)

class ReportService:
    def __init__(self):
        self.db = DatabaseManager()

    def generate_device_status_report(self, 
                                    start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate comprehensive device status report"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        devices = self.db.get_all(Device)
        
        report = {
            'total_devices': len(devices),
            'status_summary': {},
            'maintenance_needed': [],
            'warranty_expiring': [],
            'status_by_category': {},
            'generated_at': datetime.utcnow().isoformat()
        }

        for device in devices:
            # Status summary
            status = device.status
            report['status_summary'][status] = report['status_summary'].get(status, 0) + 1

            # Check maintenance
            if device.next_maintenance_due and device.next_maintenance_due <= end_date:
                report['maintenance_needed'].append({
                    'device_id': device.id,
                    'name': device.name,
                    'model': device.model,
                    'due_date': device.next_maintenance_due.isoformat()
                })

            # Check warranty
            if device.warranty_expiry and device.warranty_expiry <= end_date:
                report['warranty_expiring'].append({
                    'device_id': device.id,
                    'name': device.name,
                    'model': device.model,
                    'expiry_date': device.warranty_expiry.isoformat()
                })

            # Status by category
            for category in device.categories:
                if category.name not in report['status_by_category']:
                    report['status_by_category'][category.name] = {}
                cat_status = report['status_by_category'][category.name]
                cat_status[status] = cat_status.get(status, 0) + 1

        return report

    def generate_usage_report(self,
                            start_date: datetime,
                            end_date: datetime,
                            device_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate usage frequency and duration report"""
        filters = {
            'start_time': {'$gte': start_date},
            'end_time': {'$lte': end_date}
        }
        if device_id:
            filters['device_id'] = device_id

        usage_records = self.db.query(UsageHistory, **filters)
        
        report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_usage_hours': 0,
            'usage_by_device': {},
            'peak_usage_times': {},
            'generated_at': datetime.utcnow().isoformat()
        }

        for record in usage_records:
            device_id = record.device_id
            if device_id not in report['usage_by_device']:
                device = self.db.get_by_id(Device, device_id)
                report['usage_by_device'][device_id] = {
                    'device_name': device.name,
                    'device_model': device.model,
                    'total_hours': 0,
                    'usage_count': 0
                }

            # Calculate duration
            if record.duration:
                hours = record.duration / 60  # Convert minutes to hours
                report['total_usage_hours'] += hours
                report['usage_by_device'][device_id]['total_hours'] += hours
                report['usage_by_device'][device_id]['usage_count'] += 1

            # Track peak usage times
            hour = record.start_time.hour
            report['peak_usage_times'][hour] = report['peak_usage_times'].get(hour, 0) + 1

        return report

    def generate_maintenance_cost_report(self,
                                      start_date: datetime,
                                      end_date: datetime,
                                      device_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate maintenance cost and history report"""
        filters = {
            'date': {'$gte': start_date, '$lte': end_date}
        }
        if device_id:
            filters['device_id'] = device_id

        maintenance_records = self.db.query(MaintenanceRecord, **filters)
        
        report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_cost': 0,
            'maintenance_by_device': {},
            'parts_used': {},
            'generated_at': datetime.utcnow().isoformat()
        }

        for record in maintenance_records:
            device_id = record.device_id
            if device_id not in report['maintenance_by_device']:
                device = self.db.get_by_id(Device, device_id)
                report['maintenance_by_device'][device_id] = {
                    'device_name': device.name,
                    'device_model': device.model,
                    'total_cost': 0,
                    'maintenance_count': 0,
                    'maintenance_history': []
                }

            # Add costs
            if record.cost:
                report['total_cost'] += record.cost
                report['maintenance_by_device'][device_id]['total_cost'] += record.cost
            
            report['maintenance_by_device'][device_id]['maintenance_count'] += 1
            report['maintenance_by_device'][device_id]['maintenance_history'].append({
                'date': record.date.isoformat(),
                'description': record.description,
                'cost': record.cost
            })

        return report

    def generate_incident_report(self,
                               start_date: datetime,
                               end_date: datetime,
                               severity: Optional[str] = None) -> Dict[str, Any]:
        """Generate incident and error report"""
        # Query activity logs for error events
        filters = {
            'timestamp': {'$gte': start_date, '$lte': end_date},
            'action': 'error'  # Assuming error events are logged with 'error' action
        }
        
        error_logs = self.db.query(ActivityLog, **filters)
        
        report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_incidents': len(error_logs),
            'incidents_by_severity': {},
            'incidents_by_device': {},
            'incident_timeline': [],
            'generated_at': datetime.utcnow().isoformat()
        }

        for log in error_logs:
            # Parse severity from log details
            if isinstance(log.details, dict):
                incident_severity = log.details.get('severity', 'unknown')
                device_id = log.details.get('device_id')
            else:
                incident_severity = 'unknown'
                device_id = None

            if severity and incident_severity != severity:
                continue

            # Count by severity
            report['incidents_by_severity'][incident_severity] = \
                report['incidents_by_severity'].get(incident_severity, 0) + 1

            # Count by device
            if device_id:
                if device_id not in report['incidents_by_device']:
                    device = self.db.get_by_id(Device, device_id)
                    report['incidents_by_device'][device_id] = {
                        'device_name': device.name if device else 'Unknown',
                        'incident_count': 0,
                        'incidents': []
                    }
                
                report['incidents_by_device'][device_id]['incident_count'] += 1
                report['incidents_by_device'][device_id]['incidents'].append({
                    'timestamp': log.timestamp.isoformat(),
                    'severity': incident_severity,
                    'details': log.details
                })

            # Add to timeline
            report['incident_timeline'].append({
                'timestamp': log.timestamp.isoformat(),
                'severity': incident_severity,
                'device_id': device_id,
                'details': log.details
            })

        # Sort timeline
        report['incident_timeline'].sort(key=lambda x: x['timestamp'])

        return report

    def generate_inventory_report(self) -> Dict[str, Any]:
        """Generate spare parts inventory report"""
        parts = self.db.get_all(SparePart)
        
        report = {
            'total_parts': len(parts),
            'low_stock_parts': [],
            'parts_by_device': {},
            'total_value': 0,
            'generated_at': datetime.utcnow().isoformat()
        }

        for part in parts:
            # Check low stock
            if part.quantity <= part.minimum_quantity:
                report['low_stock_parts'].append({
                    'part_id': part.id,
                    'name': part.name,
                    'current_quantity': part.quantity,
                    'minimum_quantity': part.minimum_quantity,
                    'device_model': part.device_model
                })

            # Group by device model
            if part.device_model not in report['parts_by_device']:
                report['parts_by_device'][part.device_model] = []
                
            report['parts_by_device'][part.device_model].append({
                'part_id': part.id,
                'name': part.name,
                'part_number': part.part_number,
                'quantity': part.quantity,
                'location': part.location
            })

        return report