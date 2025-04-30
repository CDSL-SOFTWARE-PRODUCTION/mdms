from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                            QTableWidgetItem, QPushButton, QStackedWidget,
                            QLabel, QComboBox, QLineEdit)
from PyQt6.QtCore import Qt
from .heating_bed_panel import HeatingBedPanel
from .phototherapy_panel import PhototherapyPanel
from .sterilizer_panel import SterilizerPanel
from .surgical_light_panel import SurgicalLightPanel
from .base_device_panel import BaseDeviceControlPanel
from ..business_logic.device_service import DeviceService
import asyncio
import gettext

class DevicesManagementWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.device_service = DeviceService()
        self.setup_localization()
        self.setup_ui()
        self.refresh_devices()  # Initial load
        
    def setup_localization(self):
        """Initialize localization support"""
        try:
            self.trans = gettext.translation('mdms', 'locale', languages=['vi'])
            self.trans.install()
            self._ = self.trans.gettext
        except FileNotFoundError:
            self._ = lambda x: x
            
    def setup_ui(self):
        """Initialize the UI components"""
        layout = QHBoxLayout(self)
        
        # Left side - Device list and filters
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Search and filter controls
        filter_layout = QHBoxLayout()
        
        # Category filter
        self.category_combo = QComboBox()
        self.category_combo.addItems([self._("All Categories"), self._("Heating Beds"),
                                    self._("Phototherapy"), self._("Sterilizers")])
        self.category_combo.currentTextChanged.connect(self.refresh_devices)
        filter_layout.addWidget(self.category_combo)
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self._("Search devices..."))
        self.search_input.textChanged.connect(self.refresh_devices)
        filter_layout.addWidget(self.search_input)
        
        left_layout.addLayout(filter_layout)
        
        # Devices table
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(4)
        self.devices_table.setHorizontalHeaderLabels([
            self._("Name"), self._("Model"), self._("Status"), self._("Actions")
        ])
        self.devices_table.horizontalHeader().setStretchLastSection(True)
        self.devices_table.verticalHeader().setVisible(False)
        left_layout.addWidget(self.devices_table)
        
        # Refresh button
        refresh_btn = QPushButton(self._("Refresh"))
        refresh_btn.clicked.connect(self.refresh_devices)
        left_layout.addWidget(refresh_btn)
        
        layout.addWidget(left_panel)
        
        # Right side - Device control panel
        self.control_stack = QStackedWidget()
        
        # Default/welcome panel
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.addWidget(QLabel(self._("Select a device to view controls")))
        welcome_layout.addStretch()
        
        self.control_stack.addWidget(welcome_widget)
        layout.addWidget(self.control_stack)
        
        # Set layout proportions
        layout.setStretch(0, 2)  # Left panel
        layout.setStretch(1, 3)  # Right panel
        
    def refresh_devices(self):
        """Update the devices table"""
        # Get filter values
        category = self.category_combo.currentText()
        search_text = self.search_input.text().lower()
        
        # Clear existing rows
        self.devices_table.setRowCount(0)
        
        # Get devices asynchronously
        loop = asyncio.get_event_loop()
        devices = loop.run_until_complete(self._get_devices())
        
        row = 0
        for device in devices:
            # Apply filters
            if category != self._("All Categories"):
                if not any(cat.name == category for cat in device.categories):
                    continue
                    
            if search_text:
                if search_text not in device.name.lower() and \
                   search_text not in device.model.lower():
                    continue
                    
            # Add device to table
            self.devices_table.insertRow(row)
            
            # Add device info
            self.devices_table.setItem(row, 0, QTableWidgetItem(device.name))
            self.devices_table.setItem(row, 1, QTableWidgetItem(device.model))
            self.devices_table.setItem(row, 2, QTableWidgetItem(device.status))
            
            # Add action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            view_btn = QPushButton(self._("View"))
            view_btn.clicked.connect(lambda checked, d=device: self.show_device_panel(d))
            actions_layout.addWidget(view_btn)
            
            self.devices_table.setCellWidget(row, 3, actions_widget)
            row += 1
            
    async def _get_devices(self):
        """Get list of devices asynchronously"""
        return self.device_service.search_devices()
        
    def show_device_panel(self, device):
        """Show the control panel for the selected device"""
        # Remove any existing panel for this device
        for i in reversed(range(1, self.control_stack.count())):
            widget = self.control_stack.widget(i)
            if isinstance(widget, BaseDeviceControlPanel) and \
               widget.device_id == device.id:
                self.control_stack.removeWidget(widget)
                widget.deleteLater()
                
        # Create appropriate panel based on device type
        panel = None
        if device.model == "HeatingBed":
            panel = HeatingBedPanel(device.id, self.device_service)
        elif device.model == "PhototherapyLight":
            panel = PhototherapyPanel(device.id, self.device_service)
        elif device.model == "Sterilizer":
            panel = SterilizerPanel(device.id, self.device_service)
        elif device.model == "SurgicalLight":
            panel = SurgicalLightPanel(device.id, self.device_service)
        
        if panel:
            self.control_stack.addWidget(panel)
            self.control_stack.setCurrentWidget(panel)
        else:
            self.control_stack.setCurrentIndex(0)  # Show welcome panel