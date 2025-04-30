from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QTableWidget, QTableWidgetItem, QPushButton, QLabel,
                            QDateEdit, QComboBox, QFrame, QFileDialog, QSpinBox,
                            QMessageBox)
from PyQt6.QtCore import Qt, QDate
from ..business_logic.report_service import ReportService
import gettext
from datetime import datetime, timedelta
import json
import csv
import os

class ReportsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_service = ReportService()
        self.setup_localization()
        self.setup_ui()
        
    def setup_localization(self):
        """Initialize localization support"""
        try:
            self.trans = gettext.translation('mdms', 'locale', languages=['vi'])
            self.trans.install()
            self._ = self.trans.gettext
        except FileNotFoundError:
            self._ = lambda x: x
            
    def setup_ui(self):
        """Initialize the reports UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel(self._("Reports"))
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)
        
        # Tab widget for different report types
        self.tab_widget = QTabWidget()
        
        # Device Status Report Tab
        self.tab_widget.addTab(self._create_device_status_tab(), 
                             self._("Device Status"))
        
        # Usage Report Tab
        self.tab_widget.addTab(self._create_usage_tab(),
                             self._("Usage Analysis"))
        
        # Maintenance Cost Report Tab
        self.tab_widget.addTab(self._create_maintenance_cost_tab(),
                             self._("Maintenance Costs"))
        
        # Incident Report Tab
        self.tab_widget.addTab(self._create_incident_tab(),
                             self._("Incidents"))
        
        # Inventory Report Tab
        self.tab_widget.addTab(self._create_inventory_tab(),
                             self._("Inventory"))
        
        layout.addWidget(self.tab_widget)
        
    def _create_device_status_tab(self) -> QWidget:
        """Create device status report tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controls
        controls = QHBoxLayout()
        
        # Date range selection
        self.device_status_start = QDateEdit()
        self.device_status_start.setCalendarPopup(True)
        self.device_status_start.setDate(QDate.currentDate().addMonths(-1))
        controls.addWidget(QLabel(self._("From:")))
        controls.addWidget(self.device_status_start)
        
        self.device_status_end = QDateEdit()
        self.device_status_end.setCalendarPopup(True)
        self.device_status_end.setDate(QDate.currentDate())
        controls.addWidget(QLabel(self._("To:")))
        controls.addWidget(self.device_status_end)
        
        # Generate button
        generate_btn = QPushButton(self._("Generate Report"))
        generate_btn.clicked.connect(self.generate_device_status_report)
        controls.addWidget(generate_btn)
        
        # Export button
        export_btn = QPushButton(self._("Export"))
        export_btn.clicked.connect(lambda: self.export_report('device_status'))
        controls.addWidget(export_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # Results area
        self.device_status_table = QTableWidget()
        self.device_status_table.setColumnCount(4)
        self.device_status_table.setHorizontalHeaderLabels([
            self._("Device"), self._("Status"), self._("Location"),
            self._("Last Maintenance")
        ])
        layout.addWidget(self.device_status_table)
        
        return widget
        
    def _create_usage_tab(self) -> QWidget:
        """Create usage analysis report tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controls
        controls = QHBoxLayout()
        
        # Device selection
        self.usage_device = QComboBox()
        self.usage_device.addItem(self._("All Devices"))
        controls.addWidget(QLabel(self._("Device:")))
        controls.addWidget(self.usage_device)
        
        # Date range selection
        self.usage_start = QDateEdit()
        self.usage_start.setCalendarPopup(True)
        self.usage_start.setDate(QDate.currentDate().addDays(-30))
        controls.addWidget(QLabel(self._("From:")))
        controls.addWidget(self.usage_start)
        
        self.usage_end = QDateEdit()
        self.usage_end.setCalendarPopup(True)
        self.usage_end.setDate(QDate.currentDate())
        controls.addWidget(QLabel(self._("To:")))
        controls.addWidget(self.usage_end)
        
        # Generate button
        generate_btn = QPushButton(self._("Generate Report"))
        generate_btn.clicked.connect(self.generate_usage_report)
        controls.addWidget(generate_btn)
        
        # Export button
        export_btn = QPushButton(self._("Export"))
        export_btn.clicked.connect(lambda: self.export_report('usage'))
        controls.addWidget(export_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # Results area
        self.usage_table = QTableWidget()
        self.usage_table.setColumnCount(4)
        self.usage_table.setHorizontalHeaderLabels([
            self._("Device"), self._("Total Hours"), 
            self._("Usage Count"), self._("Peak Usage Time")
        ])
        layout.addWidget(self.usage_table)
        
        return widget
        
    def _create_maintenance_cost_tab(self) -> QWidget:
        """Create maintenance cost report tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controls
        controls = QHBoxLayout()
        
        # Device selection
        self.maintenance_device = QComboBox()
        self.maintenance_device.addItem(self._("All Devices"))
        controls.addWidget(QLabel(self._("Device:")))
        controls.addWidget(self.maintenance_device)
        
        # Date range selection
        self.maintenance_start = QDateEdit()
        self.maintenance_start.setCalendarPopup(True)
        self.maintenance_start.setDate(QDate.currentDate().addMonths(-12))
        controls.addWidget(QLabel(self._("From:")))
        controls.addWidget(self.maintenance_start)
        
        self.maintenance_end = QDateEdit()
        self.maintenance_end.setCalendarPopup(True)
        self.maintenance_end.setDate(QDate.currentDate())
        controls.addWidget(QLabel(self._("To:")))
        controls.addWidget(self.maintenance_end)
        
        # Generate button
        generate_btn = QPushButton(self._("Generate Report"))
        generate_btn.clicked.connect(self.generate_maintenance_cost_report)
        controls.addWidget(generate_btn)
        
        # Export button
        export_btn = QPushButton(self._("Export"))
        export_btn.clicked.connect(lambda: self.export_report('maintenance'))
        controls.addWidget(export_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # Results area
        self.maintenance_table = QTableWidget()
        self.maintenance_table.setColumnCount(4)
        self.maintenance_table.setHorizontalHeaderLabels([
            self._("Device"), self._("Total Cost"), 
            self._("Maintenance Count"), self._("Last Maintenance")
        ])
        layout.addWidget(self.maintenance_table)
        
        return widget
        
    def _create_incident_tab(self) -> QWidget:
        """Create incident report tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controls
        controls = QHBoxLayout()
        
        # Severity selection
        self.incident_severity = QComboBox()
        self.incident_severity.addItems([
            self._("All Severities"), self._("High"), 
            self._("Medium"), self._("Low")
        ])
        controls.addWidget(QLabel(self._("Severity:")))
        controls.addWidget(self.incident_severity)
        
        # Date range selection
        self.incident_start = QDateEdit()
        self.incident_start.setCalendarPopup(True)
        self.incident_start.setDate(QDate.currentDate().addMonths(-1))
        controls.addWidget(QLabel(self._("From:")))
        controls.addWidget(self.incident_start)
        
        self.incident_end = QDateEdit()
        self.incident_end.setCalendarPopup(True)
        self.incident_end.setDate(QDate.currentDate())
        controls.addWidget(QLabel(self._("To:")))
        controls.addWidget(self.incident_end)
        
        # Generate button
        generate_btn = QPushButton(self._("Generate Report"))
        generate_btn.clicked.connect(self.generate_incident_report)
        controls.addWidget(generate_btn)
        
        # Export button
        export_btn = QPushButton(self._("Export"))
        export_btn.clicked.connect(lambda: self.export_report('incident'))
        controls.addWidget(export_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # Results area
        self.incident_table = QTableWidget()
        self.incident_table.setColumnCount(5)
        self.incident_table.setHorizontalHeaderLabels([
            self._("Device"), self._("Timestamp"), self._("Severity"),
            self._("Description"), self._("Status")
        ])
        layout.addWidget(self.incident_table)
        
        return widget
        
    def _create_inventory_tab(self) -> QWidget:
        """Create inventory report tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controls
        controls = QHBoxLayout()
        
        # Generate button
        generate_btn = QPushButton(self._("Generate Report"))
        generate_btn.clicked.connect(self.generate_inventory_report)
        controls.addWidget(generate_btn)
        
        # Export button
        export_btn = QPushButton(self._("Export"))
        export_btn.clicked.connect(lambda: self.export_report('inventory'))
        controls.addWidget(export_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # Results area
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(6)
        self.inventory_table.setHorizontalHeaderLabels([
            self._("Part Name"), self._("Part Number"), self._("Quantity"),
            self._("Min. Quantity"), self._("Location"), self._("Device Model")
        ])
        layout.addWidget(self.inventory_table)
        
        return widget
        
    def generate_device_status_report(self):
        """Generate and display device status report"""
        start_date = self.device_status_start.date().toPyDate()
        end_date = self.device_status_end.date().toPyDate()
        
        report = self.report_service.generate_device_status_report(start_date, end_date)
        self.current_device_status_report = report
        
        # Clear and update table
        self.device_status_table.setRowCount(0)
        row = 0
        
        # Add devices
        devices = []
        for status, count in report['status_summary'].items():
            for device in report.get('devices', []):
                if device['status'] == status:
                    devices.append(device)
                    
        for device in devices:
            self.device_status_table.insertRow(row)
            self.device_status_table.setItem(row, 0, QTableWidgetItem(device['name']))
            self.device_status_table.setItem(row, 1, QTableWidgetItem(device['status']))
            self.device_status_table.setItem(row, 2, QTableWidgetItem(device['location']))
            self.device_status_table.setItem(row, 3, 
                QTableWidgetItem(device['last_maintenance'].split('T')[0] 
                               if device.get('last_maintenance') else "N/A"))
            row += 1
            
    def generate_usage_report(self):
        """Generate and display usage report"""
        start_date = self.usage_start.date().toPyDate()
        end_date = self.usage_end.date().toPyDate()
        device_id = None  # Get selected device ID if not "All Devices"
        
        report = self.report_service.generate_usage_report(
            start_date, end_date, device_id)
        self.current_usage_report = report
        
        # Clear and update table
        self.usage_table.setRowCount(0)
        row = 0
        
        for device_id, usage in report['usage_by_device'].items():
            self.usage_table.insertRow(row)
            self.usage_table.setItem(row, 0, QTableWidgetItem(usage['device_name']))
            self.usage_table.setItem(row, 1, 
                QTableWidgetItem(f"{usage['total_hours']:.1f}"))
            self.usage_table.setItem(row, 2, 
                QTableWidgetItem(str(usage['usage_count'])))
            
            # Find peak usage time
            peak_hour = max(report['peak_usage_times'].items(), 
                          key=lambda x: x[1])[0]
            self.usage_table.setItem(row, 3, QTableWidgetItem(f"{peak_hour}:00"))
            row += 1
            
    def generate_maintenance_cost_report(self):
        """Generate and display maintenance cost report"""
        start_date = self.maintenance_start.date().toPyDate()
        end_date = self.maintenance_end.date().toPyDate()
        device_id = None  # Get selected device ID if not "All Devices"
        
        report = self.report_service.generate_maintenance_cost_report(
            start_date, end_date, device_id)
        self.current_maintenance_report = report
        
        # Clear and update table
        self.maintenance_table.setRowCount(0)
        row = 0
        
        for device_id, maintenance in report['maintenance_by_device'].items():
            self.maintenance_table.insertRow(row)
            self.maintenance_table.setItem(row, 0, 
                QTableWidgetItem(maintenance['device_name']))
            self.maintenance_table.setItem(row, 1, 
                QTableWidgetItem(f"${maintenance['total_cost']:.2f}"))
            self.maintenance_table.setItem(row, 2, 
                QTableWidgetItem(str(maintenance['maintenance_count'])))
            
            # Get last maintenance date
            if maintenance['maintenance_history']:
                last_date = maintenance['maintenance_history'][-1]['date'].split('T')[0]
                self.maintenance_table.setItem(row, 3, QTableWidgetItem(last_date))
            else:
                self.maintenance_table.setItem(row, 3, QTableWidgetItem("N/A"))
            row += 1
            
    def generate_incident_report(self):
        """Generate and display incident report"""
        start_date = self.incident_start.date().toPyDate()
        end_date = self.incident_end.date().toPyDate()
        severity = None if self.incident_severity.currentText() == self._("All Severities") \
                  else self.incident_severity.currentText().lower()
        
        report = self.report_service.generate_incident_report(
            start_date, end_date, severity)
        self.current_incident_report = report
        
        # Clear and update table
        self.incident_table.setRowCount(0)
        row = 0
        
        for incident in report['incident_timeline']:
            self.incident_table.insertRow(row)
            
            # Get device name from incident details
            device_id = incident['device_id']
            device_name = "Unknown"
            if device_id in report['incidents_by_device']:
                device_name = report['incidents_by_device'][device_id]['device_name']
                
            self.incident_table.setItem(row, 0, QTableWidgetItem(device_name))
            self.incident_table.setItem(row, 1, 
                QTableWidgetItem(incident['timestamp'].split('T')[0]))
            self.incident_table.setItem(row, 2, 
                QTableWidgetItem(incident['severity']))
            self.incident_table.setItem(row, 3, 
                QTableWidgetItem(str(incident['details'])))
            
            # Set status based on resolution field if available
            status = incident.get('resolution', 'Open')
            self.incident_table.setItem(row, 4, QTableWidgetItem(status))
            row += 1
            
    def generate_inventory_report(self):
        """Generate and display inventory report"""
        report = self.report_service.generate_inventory_report()
        self.current_inventory_report = report
        
        # Clear and update table
        self.inventory_table.setRowCount(0)
        row = 0
        
        # Add parts from all device models
        for device_model, parts in report['parts_by_device'].items():
            for part in parts:
                self.inventory_table.insertRow(row)
                self.inventory_table.setItem(row, 0, QTableWidgetItem(part['name']))
                self.inventory_table.setItem(row, 1, 
                    QTableWidgetItem(part['part_number']))
                self.inventory_table.setItem(row, 2, 
                    QTableWidgetItem(str(part['quantity'])))
                
                # Get minimum quantity from low stock alert if available
                min_qty = next((alert['minimum_quantity'] 
                              for alert in report['low_stock_parts']
                              if alert['part_id'] == part['part_id']), "N/A")
                self.inventory_table.setItem(row, 3, QTableWidgetItem(str(min_qty)))
                
                self.inventory_table.setItem(row, 4, 
                    QTableWidgetItem(part['location']))
                self.inventory_table.setItem(row, 5, 
                    QTableWidgetItem(device_model))
                
                # Highlight low stock items
                if str(min_qty) != "N/A" and part['quantity'] <= min_qty:
                    for col in range(self.inventory_table.columnCount()):
                        item = self.inventory_table.item(row, col)
                        if item:
                            item.setBackground(Qt.GlobalColor.yellow)
                            
                row += 1
                
    def export_report(self, report_type: str):
        """Export current report to JSON or CSV"""
        report_data = None
        if report_type == 'device_status':
            report_data = getattr(self, 'current_device_status_report', None)
        elif report_type == 'usage':
            report_data = getattr(self, 'current_usage_report', None)
        elif report_type == 'maintenance':
            report_data = getattr(self, 'current_maintenance_report', None)
        elif report_type == 'incident':
            report_data = getattr(self, 'current_incident_report', None)
        elif report_type == 'inventory':
            report_data = getattr(self, 'current_inventory_report', None)
            
        if not report_data:
            QMessageBox.warning(self, self._("Error"),
                              self._("Please generate a report first"))
            return
            
        # Get save location
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            self._("Export Report"),
            "",
            self._("JSON files (*.json);;CSV files (*.csv)")
        )
        
        if not file_name:
            return
            
        try:
            if file_name.endswith('.json'):
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, ensure_ascii=False, indent=2)
            else:  # CSV export
                self._export_to_csv(report_data, file_name, report_type)
                
            QMessageBox.information(
                self,
                self._("Success"),
                self._("Report exported successfully")
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                self._("Error"),
                self._("Failed to export report: ") + str(e)
            )
            
    def _export_to_csv(self, report_data: dict, file_name: str, report_type: str):
        """Export report data to CSV format"""
        with open(file_name, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if report_type == 'device_status':
                writer.writerow(['Device', 'Status', 'Location', 'Last Maintenance'])
                for status, devices in report_data['status_summary'].items():
                    for device in devices:
                        writer.writerow([
                            device['name'],
                            device['status'],
                            device['location'],
                            device.get('last_maintenance', 'N/A')
                        ])
            elif report_type == 'usage':
                writer.writerow(['Device', 'Total Hours', 'Usage Count', 'Peak Usage Time'])
                for device_id, usage in report_data['usage_by_device'].items():
                    peak_hour = max(report_data['peak_usage_times'].items(), 
                                  key=lambda x: x[1])[0]
                    writer.writerow([
                        usage['device_name'],
                        f"{usage['total_hours']:.1f}",
                        usage['usage_count'],
                        f"{peak_hour}:00"
                    ])
            # Add similar logic for other report types