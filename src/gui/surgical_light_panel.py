from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QSlider, QFrame, QProgressBar, QCheckBox)
from PyQt6.QtCore import Qt, QTimer
from .base_device_panel import BaseDeviceControlPanel
from ..business_logic.surgical_light_manager import SurgicalLightManager
import asyncio

class SurgicalLightPanel(BaseDeviceControlPanel):
    def __init__(self, device_id, device_service, parent=None):
        super().__init__(device_id, device_service, parent)
        self.surgical_light_manager = SurgicalLightManager()
        self.setup_specific_ui()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.periodic_update)
        self.update_timer.start(1000)  # Update every second

    def setup_specific_ui(self):
        """Setup surgical light specific controls"""
        layout = QVBoxLayout()
        
        # Light control panel
        light_frame = QFrame()
        light_frame.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        light_layout = QVBoxLayout(light_frame)
        
        # Intensity control
        intensity_label = QLabel("Light Intensity")
        light_layout.addWidget(intensity_label)
        
        self.intensity_display = QProgressBar()
        self.intensity_display.setRange(0, 100)
        light_layout.addWidget(self.intensity_display)
        
        intensity_control = QHBoxLayout()
        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setRange(0, 100)
        self.intensity_slider.valueChanged.connect(self.on_intensity_changed)
        intensity_control.addWidget(self.intensity_slider)
        
        self.intensity_value = QLabel("0%")
        intensity_control.addWidget(self.intensity_value)
        light_layout.addLayout(intensity_control)
        
        layout.addWidget(light_frame)
        
        # Focus control panel
        focus_frame = QFrame()
        focus_frame.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        focus_layout = QVBoxLayout(focus_frame)
        
        focus_label = QLabel("Focus Position")
        focus_layout.addWidget(focus_label)
        
        self.focus_display = QProgressBar()
        self.focus_display.setRange(0, 100)
        focus_layout.addWidget(self.focus_display)
        
        focus_control = QHBoxLayout()
        self.focus_slider = QSlider(Qt.Orientation.Horizontal)
        self.focus_slider.setRange(0, 100)
        self.focus_slider.valueChanged.connect(self.on_focus_changed)
        focus_control.addWidget(self.focus_slider)
        
        self.focus_value = QLabel("0%")
        focus_control.addWidget(self.focus_value)
        focus_layout.addLayout(focus_control)
        
        layout.addWidget(focus_frame)
        
        # Camera control panel
        camera_frame = QFrame()
        camera_frame.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        camera_layout = QVBoxLayout(camera_frame)
        
        camera_header = QHBoxLayout()
        camera_header.addWidget(QLabel("Camera Control"))
        
        self.camera_status = QLabel("Camera: Off")
        camera_header.addWidget(self.camera_status)
        camera_layout.addLayout(camera_header)
        
        self.camera_toggle = QCheckBox("Enable Camera")
        self.camera_toggle.stateChanged.connect(self.on_camera_toggled)
        camera_layout.addWidget(self.camera_toggle)
        
        layout.addWidget(camera_frame)
        
        # Status panel
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        status_layout = QVBoxLayout(status_frame)
        
        self.status_label = QLabel("Status: Unknown")
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_frame)
        
        self.setLayout(layout)

    async def on_intensity_changed(self, value):
        """Handle intensity slider changes"""
        self.intensity_value.setText(f"{value}%")
        await self.surgical_light_manager.set_light_intensity(self.device_id, value)

    async def on_focus_changed(self, value):
        """Handle focus slider changes"""
        self.focus_value.setText(f"{value}%")
        await self.surgical_light_manager.set_focus_position(self.device_id, value)

    async def on_camera_toggled(self, state):
        """Handle camera toggle changes"""
        await self.surgical_light_manager.toggle_camera(self.device_id, state == Qt.CheckState.Checked.value)

    async def update_parameters(self, parameters):
        """Update parameter displays with latest values"""
        # Update intensity display
        intensity = parameters.get('light_intensity', 0)
        self.intensity_display.setValue(int(intensity))
        self.intensity_slider.setValue(int(intensity))
        self.intensity_value.setText(f"{int(intensity)}%")
        
        # Update focus display
        focus = parameters.get('focus_position', 0)
        self.focus_display.setValue(int(focus))
        self.focus_slider.setValue(int(focus))
        self.focus_value.setText(f"{int(focus)}%")
        
        # Update camera status
        camera_active = parameters.get('camera_active', False)
        self.camera_toggle.setChecked(camera_active)
        self.camera_status.setText(f"Camera: {'On' if camera_active else 'Off'}")
        
        # Update status if available
        if 'status' in parameters:
            self.status_label.setText(f"Status: {parameters['status']}")

    async def show_diagnostic_results(self, results):
        """Display diagnostic results"""
        status_text = "Diagnostic Results:\n"
        for key, value in results.items():
            status_text += f"{key}: {value}\n"
        self.status_label.setText(status_text)

    def periodic_update(self):
        """Periodic status update"""
        loop = asyncio.get_event_loop()
        loop.create_task(self.update_status())