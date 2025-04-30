from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QLabel, QPushButton, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPalette
from ..business_logic.device_service import DeviceService
from ..device_communication.base_device import DeviceStatus
import asyncio

class DeviceStatusCard(QFrame):
    def __init__(self, device_data, parent=None):
        super().__init__(parent)
        self.device_data = device_data
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the device status card UI"""
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        
        layout = QVBoxLayout(self)
        
        # Device name and status
        header_layout = QHBoxLayout()
        name_label = QLabel(self.device_data.get('name', 'Unknown Device'))
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(name_label)
        
        status = self.device_data.get('status', 'disconnected')
        status_label = QLabel(status)
        status_label.setStyleSheet(self._get_status_style(status))
        header_layout.addWidget(status_label)
        layout.addLayout(header_layout)
        
        # Device details
        details_layout = QGridLayout()
        row = 0
        
        # Add model info
        details_layout.addWidget(QLabel("Model:"), row, 0)
        details_layout.addWidget(QLabel(self.device_data.get('model', 'N/A')), row, 1)
        row += 1
        
        # Add location info
        details_layout.addWidget(QLabel("Location:"), row, 0)
        details_layout.addWidget(QLabel(self.device_data.get('location', 'N/A')), row, 1)
        row += 1
        
        # Add last maintenance info
        details_layout.addWidget(QLabel("Last Maintenance:"), row, 0)
        last_maintenance = self.device_data.get('last_maintenance', 'Never')
        details_layout.addWidget(QLabel(str(last_maintenance)), row, 1)
        
        layout.addLayout(details_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        connect_btn = QPushButton("Connect" if status == "disconnected" else "Disconnect")
        connect_btn.clicked.connect(self.handle_connection)
        button_layout.addWidget(connect_btn)
        
        details_btn = QPushButton("Details")
        details_btn.clicked.connect(self.show_details)
        button_layout.addWidget(details_btn)
        
        layout.addLayout(button_layout)
        
    def _get_status_style(self, status):
        """Get CSS style based on device status"""
        colors = {
            'connected': 'green',
            'disconnected': 'gray',
            'error': 'red',
            'busy': 'orange',
            'maintenance': 'blue'
        }
        color = colors.get(status.lower(), 'black')
        return f"color: {color}; font-weight: bold;"
        
    def handle_connection(self):
        """Handle device connect/disconnect"""
        # This will be implemented to interact with DeviceService
        pass
        
    def show_details(self):
        """Show detailed device information and controls"""
        # This will be implemented to show device-specific UI
        pass

class DeviceDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.device_service = DeviceService()
        self.setup_ui()
        
        # Setup refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_devices)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
        
    def setup_ui(self):
        """Initialize the dashboard UI"""
        main_layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Device Dashboard")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_devices)
        header_layout.addWidget(refresh_btn)
        
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # Create scrollable device grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.device_grid = QWidget()
        self.grid_layout = QGridLayout(self.device_grid)
        scroll.setWidget(self.device_grid)
        
        main_layout.addWidget(scroll)
        
    async def _get_devices(self):
        """Get list of devices asynchronously"""
        return self.device_service.search_devices()
        
    def refresh_devices(self):
        """Update the device grid with current status"""
        # Clear existing grid
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
            
        # Get updated device list
        loop = asyncio.get_event_loop()
        devices = loop.run_until_complete(self._get_devices())
        
        # Add device cards to grid
        row = 0
        col = 0
        max_cols = 3  # Number of cards per row
        
        for device in devices:
            device_data = {
                'id': device.id,
                'name': device.name,
                'model': device.model,
                'status': device.status,
                'location': device.location,
                'last_maintenance': device.last_maintenance
            }
            
            card = DeviceStatusCard(device_data)
            self.grid_layout.addWidget(card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
        # Add stretch to fill empty space
        self.grid_layout.setRowStretch(row + 1, 1)
        
    def showEvent(self, event):
        """Override showEvent to refresh devices when dashboard becomes visible"""
        super().showEvent(event)
        self.refresh_devices()
        
    def hideEvent(self, event):
        """Override hideEvent to stop refresh timer when dashboard is hidden"""
        super().hideEvent(event)
        self.refresh_timer.stop()