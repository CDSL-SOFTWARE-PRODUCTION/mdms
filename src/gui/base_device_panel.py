from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from ..device_communication.base_device import DeviceStatus

class BaseDeviceControlPanel(QWidget):
    statusChanged = pyqtSignal(str)  # Signal emitted when device status changes
    
    def __init__(self, device_id, device_service, parent=None):
        super().__init__(parent)
        self.device_id = device_id
        self.device_service = device_service
        self.setup_base_ui()
        
    def setup_base_ui(self):
        """Initialize base UI components common to all device control panels"""
        self.main_layout = QVBoxLayout(self)
        
        # Header with status
        header = QHBoxLayout()
        self.status_label = QLabel("Status: Disconnected")
        header.addWidget(self.status_label)
        
        # Connection controls
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)
        header.addWidget(self.connect_button)
        
        # Diagnostic button
        self.diagnostic_button = QPushButton("Run Diagnostic")
        self.diagnostic_button.clicked.connect(self.run_diagnostic)
        self.diagnostic_button.setEnabled(False)
        header.addWidget(self.diagnostic_button)
        
        header.addStretch()
        self.main_layout.addLayout(header)
        
        # Parameters section
        self.parameters_layout = QVBoxLayout()
        self.main_layout.addLayout(self.parameters_layout)
        
        # Controls section
        self.controls_layout = QVBoxLayout()
        self.main_layout.addLayout(self.controls_layout)
        
        self.main_layout.addStretch()
        
    async def update_status(self):
        """Update device status display"""
        status = await self.device_service.get_device_status(self.device_id)
        if status:
            self.status_label.setText(f"Status: {status['status']}")
            self.statusChanged.emit(status['status'])
            
            # Enable/disable controls based on connection state
            is_connected = status['status'] == DeviceStatus.CONNECTED.value
            self.diagnostic_button.setEnabled(is_connected)
            self.connect_button.setText("Disconnect" if is_connected else "Connect")
            
            # Update parameters display if connected
            if is_connected and 'parameters' in status:
                await self.update_parameters(status['parameters'])
                
    async def toggle_connection(self):
        """Toggle device connection state"""
        if self.connect_button.text() == "Connect":
            success = await self.device_service.connect_device(self.device_id)
        else:
            success = await self.device_service.disconnect_device(self.device_id)
            
        if success:
            await self.update_status()
            
    async def run_diagnostic(self):
        """Run device diagnostic"""
        results = await self.device_service.run_device_diagnostic(self.device_id)
        if results:
            await self.show_diagnostic_results(results)
            
    async def update_parameters(self, parameters):
        """Update parameter displays - to be implemented by subclasses"""
        pass
        
    async def show_diagnostic_results(self, results):
        """Display diagnostic results - to be implemented by subclasses"""
        pass