from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QTableWidget, QTableWidgetItem, QPushButton, QLabel,
                            QDateEdit, QSpinBox, QLineEdit, QComboBox, QFrame,
                            QFormLayout, QMessageBox, QDialog)
from PyQt6.QtCore import Qt, QTimer, QDate
from ..business_logic.device_service import DeviceService
from datetime import datetime, timedelta
import gettext
import asyncio

class MaintenanceScheduleDialog(QDialog):
    def __init__(self, device_id: int, device_service: DeviceService, parent=None):
        super().__init__(parent)
        self.device_id = device_id
        self.device_service = device_service
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the maintenance schedule dialog UI"""
        layout = QFormLayout(self)
        
        # Date selection
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setMinimumDate(QDate.currentDate())
        layout.addRow("Date:", self.date_edit)
        
        # Description
        self.description_edit = QLineEdit()
        layout.addRow("Description:", self.description_edit)
        
        # Estimated cost
        self.cost_spin = QSpinBox()
        self.cost_spin.setRange(0, 1000000)
        self.cost_spin.setSuffix(" USD")
        layout.addRow("Estimated Cost:", self.cost_spin)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_maintenance)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)
        
    def save_maintenance(self):
        """Save the maintenance schedule"""
        date = self.date_edit.date().toPyDate()
        description = self.description_edit.text()
        if not description:
            QMessageBox.warning(self, "Error", "Please enter a description")
            return
            
        scheduled = self.device_service.schedule_maintenance(
            self.device_id,
            description,
            date
        )
        
        if scheduled:
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to schedule maintenance")

class SparePartDialog(QDialog):
    def __init__(self, device_service: DeviceService, part_id: int = None, parent=None):
        super().__init__(parent)
        self.device_service = device_service
        self.part_id = part_id
        self.setup_ui()
        if part_id:
            self.load_part_data()
        
    def setup_ui(self):
        """Initialize the spare part dialog UI"""
        layout = QFormLayout(self)
        
        # Part details
        self.name_edit = QLineEdit()
        layout.addRow("Name:", self.name_edit)
        
        self.part_number_edit = QLineEdit()
        layout.addRow("Part Number:", self.part_number_edit)
        
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(0, 10000)
        layout.addRow("Quantity:", self.quantity_spin)
        
        self.min_quantity_spin = QSpinBox()
        self.min_quantity_spin.setRange(0, 10000)
        layout.addRow("Minimum Quantity:", self.min_quantity_spin)
        
        self.location_edit = QLineEdit()
        layout.addRow("Storage Location:", self.location_edit)
        
        self.model_edit = QLineEdit()
        layout.addRow("Device Model:", self.model_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_part)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)
        
    def load_part_data(self):
        """Load existing part data for editing"""
        part = self.device_service.get_spare_part(self.part_id)
        if part:
            self.name_edit.setText(part.name)
            self.part_number_edit.setText(part.part_number)
            self.quantity_spin.setValue(part.quantity)
            self.min_quantity_spin.setValue(part.minimum_quantity)
            self.location_edit.setText(part.location)
            self.model_edit.setText(part.device_model)
            
    def save_part(self):
        """Save the spare part details"""
        details = {
            'name': self.name_edit.text(),
            'part_number': self.part_number_edit.text(),
            'quantity': self.quantity_spin.value(),
            'minimum_quantity': self.min_quantity_spin.value(),
            'location': self.location_edit.text(),
            'device_model': self.model_edit.text()
        }
        
        if self.part_id:
            success = self.device_service.manage_spare_parts(
                "update",
                self.part_id,
                **details
            )
        else:
            success = self.device_service.manage_spare_parts(
                "add",
                **details
            )
            
        if success:
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to save spare part")

class MaintenanceManagementWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.device_service = DeviceService()
        self.setup_localization()
        self.setup_ui()
        self.setup_refresh_timer()
        
    def setup_localization(self):
        """Initialize localization support"""
        try:
            self.trans = gettext.translation('mdms', 'locale', languages=['vi'])
            self.trans.install()
            self._ = self.trans.gettext
        except FileNotFoundError:
            self._ = lambda x: x
            
    def setup_ui(self):
        """Initialize the maintenance management UI"""
        layout = QVBoxLayout(self)
        
        # Tab widget for different maintenance views
        self.tab_widget = QTabWidget()
        
        # Schedule tab
        schedule_widget = QWidget()
        schedule_layout = QVBoxLayout(schedule_widget)
        
        # Upcoming maintenance table
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(5)
        self.schedule_table.setHorizontalHeaderLabels([
            self._("Device"), self._("Due Date"), self._("Description"),
            self._("Status"), self._("Actions")
        ])
        schedule_layout.addWidget(self.schedule_table)
        
        # Add new maintenance button
        add_maintenance_btn = QPushButton(self._("Schedule Maintenance"))
        add_maintenance_btn.clicked.connect(self.show_schedule_dialog)
        schedule_layout.addWidget(add_maintenance_btn)
        
        self.tab_widget.addTab(schedule_widget, self._("Maintenance Schedule"))
        
        # History tab
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        
        # History filters
        filter_layout = QHBoxLayout()
        
        self.device_filter = QComboBox()
        self.device_filter.addItem(self._("All Devices"))
        self.device_filter.currentIndexChanged.connect(self.refresh_history)
        filter_layout.addWidget(self.device_filter)
        
        self.date_range = QComboBox()
        self.date_range.addItems([
            self._("Last 30 days"),
            self._("Last 90 days"),
            self._("Last 12 months"),
            self._("All time")
        ])
        self.date_range.currentIndexChanged.connect(self.refresh_history)
        filter_layout.addWidget(self.date_range)
        
        history_layout.addLayout(filter_layout)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            self._("Device"), self._("Date"), self._("Description"),
            self._("Cost"), self._("Performed By"), self._("Next Due")
        ])
        history_layout.addWidget(self.history_table)
        
        self.tab_widget.addTab(history_widget, self._("Maintenance History"))
        
        # Spare Parts tab
        parts_widget = QWidget()
        parts_layout = QVBoxLayout(parts_widget)
        
        # Parts table
        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(7)
        self.parts_table.setHorizontalHeaderLabels([
            self._("Name"), self._("Part Number"), self._("Quantity"),
            self._("Min. Quantity"), self._("Location"), self._("Device Model"),
            self._("Actions")
        ])
        parts_layout.addWidget(self.parts_table)
        
        # Add new part button
        add_part_btn = QPushButton(self._("Add Spare Part"))
        add_part_btn.clicked.connect(self.show_part_dialog)
        parts_layout.addWidget(add_part_btn)
        
        self.tab_widget.addTab(parts_widget, self._("Spare Parts"))
        
        layout.addWidget(self.tab_widget)
        
        # Initial data load
        self.refresh_all()
        
    def setup_refresh_timer(self):
        """Setup automatic refresh timer"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all)
        self.refresh_timer.start(300000)  # Refresh every 5 minutes
        
    def refresh_all(self):
        """Refresh all data displays"""
        self.refresh_schedule()
        self.refresh_history()
        self.refresh_parts()
        
    def refresh_schedule(self):
        """Refresh maintenance schedule display"""
        self.schedule_table.setRowCount(0)
        devices = self.device_service.get_devices_due_maintenance()
        
        for row, device in enumerate(devices):
            self.schedule_table.insertRow(row)
            
            self.schedule_table.setItem(row, 0, QTableWidgetItem(device.name))
            self.schedule_table.setItem(row, 1, 
                                      QTableWidgetItem(device.next_maintenance_due.strftime("%Y-%m-%d")))
            self.schedule_table.setItem(row, 2, QTableWidgetItem("Scheduled Maintenance"))
            self.schedule_table.setItem(row, 3, QTableWidgetItem("Pending"))
            
            # Action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            complete_btn = QPushButton(self._("Complete"))
            complete_btn.clicked.connect(lambda checked, d=device: self.complete_maintenance(d))
            actions_layout.addWidget(complete_btn)
            
            reschedule_btn = QPushButton(self._("Reschedule"))
            reschedule_btn.clicked.connect(lambda checked, d=device: self.show_schedule_dialog(d))
            actions_layout.addWidget(reschedule_btn)
            
            self.schedule_table.setCellWidget(row, 4, actions_widget)
            
    def refresh_history(self):
        """Refresh maintenance history display"""
        self.history_table.setRowCount(0)
        
        # Get filter values
        device_filter = self.device_filter.currentText()
        date_range = self.date_range.currentText()
        
        # Calculate date range
        end_date = datetime.now()
        if date_range == self._("Last 30 days"):
            start_date = end_date - timedelta(days=30)
        elif date_range == self._("Last 90 days"):
            start_date = end_date - timedelta(days=90)
        elif date_range == self._("Last 12 months"):
            start_date = end_date - timedelta(days=365)
        else:
            start_date = None
            
        # Get maintenance records
        records = self.device_service.get_maintenance_history(
            device_id=None if device_filter == self._("All Devices") else device_filter,
            start_date=start_date,
            end_date=end_date
        )
        
        for row, record in enumerate(records):
            self.history_table.insertRow(row)
            
            device = self.device_service.get_device_by_id(record.device_id)
            self.history_table.setItem(row, 0, QTableWidgetItem(device.name if device else "Unknown"))
            self.history_table.setItem(row, 1, 
                                     QTableWidgetItem(record.date.strftime("%Y-%m-%d")))
            self.history_table.setItem(row, 2, QTableWidgetItem(record.description))
            self.history_table.setItem(row, 3, 
                                     QTableWidgetItem(f"${record.cost:.2f}" if record.cost else "N/A"))
            self.history_table.setItem(row, 4, QTableWidgetItem(str(record.performed_by)))
            self.history_table.setItem(row, 5, 
                                     QTableWidgetItem(record.next_maintenance.strftime("%Y-%m-%d")
                                                    if record.next_maintenance else "N/A"))
            
    def refresh_parts(self):
        """Refresh spare parts inventory display"""
        self.parts_table.setRowCount(0)
        parts = self.device_service.get_all_spare_parts()
        
        for row, part in enumerate(parts):
            self.parts_table.insertRow(row)
            
            self.parts_table.setItem(row, 0, QTableWidgetItem(part.name))
            self.parts_table.setItem(row, 1, QTableWidgetItem(part.part_number))
            self.parts_table.setItem(row, 2, QTableWidgetItem(str(part.quantity)))
            self.parts_table.setItem(row, 3, QTableWidgetItem(str(part.minimum_quantity)))
            self.parts_table.setItem(row, 4, QTableWidgetItem(part.location))
            self.parts_table.setItem(row, 5, QTableWidgetItem(part.device_model))
            
            # Action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            edit_btn = QPushButton(self._("Edit"))
            edit_btn.clicked.connect(lambda checked, p=part: self.show_part_dialog(p))
            actions_layout.addWidget(edit_btn)
            
            self.parts_table.setCellWidget(row, 6, actions_widget)
            
            # Highlight low stock
            if part.quantity <= part.minimum_quantity:
                for col in range(self.parts_table.columnCount()):
                    item = self.parts_table.item(row, col)
                    if item:
                        item.setBackground(Qt.GlobalColor.yellow)
                        
    def show_schedule_dialog(self, device=None):
        """Show dialog to schedule maintenance"""
        dialog = MaintenanceScheduleDialog(device.id if device else None, 
                                         self.device_service,
                                         self)
        if dialog.exec():
            self.refresh_schedule()
            
    def show_part_dialog(self, part=None):
        """Show dialog to add/edit spare part"""
        dialog = SparePartDialog(self.device_service,
                               part.id if part else None,
                               self)
        if dialog.exec():
            self.refresh_parts()
            
    def complete_maintenance(self, device):
        """Mark maintenance as completed"""
        # Get completion details from user
        # Implementation would go here
        
        # Update device status
        success = self.device_service.update_device(device.id, status="IDLE")
        if success:
            self.refresh_all()
            
    def showEvent(self, event):
        """Refresh data when widget becomes visible"""
        super().showEvent(event)
        self.refresh_all()
        
    def hideEvent(self, event):
        """Stop refresh timer when widget is hidden"""
        super().hideEvent(event)
        self.refresh_timer.stop()