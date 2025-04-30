from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QSpinBox, QLineEdit, QFrame, QProgressBar)
from PyQt6.QtCore import QTimer
from datetime import datetime, timedelta
import asyncio
from .base_device_panel import BaseDeviceControlPanel
from ..business_logic.phototherapy_manager import PhototherapyManager

class PhototherapyPanel(BaseDeviceControlPanel):
    def __init__(self, device_id, device_service, parent=None):
        super().__init__(device_id, device_service, parent)
        self.phototherapy_manager = PhototherapyManager()
        self.setup_specific_ui()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.periodic_update)
        self.update_timer.start(1000)  # Update every second

    def setup_specific_ui(self):
        """Setup phototherapy specific controls"""
        layout = QVBoxLayout()
        
        # Session controls
        session_frame = QFrame()
        session_frame.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        session_layout = QVBoxLayout(session_frame)
        
        # Patient ID input
        patient_layout = QHBoxLayout()
        patient_layout.addWidget(QLabel("Patient ID:"))
        self.patient_id_input = QLineEdit()
        patient_layout.addWidget(self.patient_id_input)
        session_layout.addLayout(patient_layout)
        
        # Duration input
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration (minutes):"))
        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 480)  # 1 minute to 8 hours
        self.duration_input.setValue(60)  # Default 1 hour
        duration_layout.addWidget(self.duration_input)
        session_layout.addLayout(duration_layout)
        
        # Session controls
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Session")
        self.start_button.clicked.connect(self.start_session)
        self.end_button = QPushButton("End Session")
        self.end_button.clicked.connect(self.end_session)
        self.end_button.setEnabled(False)
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.end_button)
        session_layout.addLayout(control_layout)
        
        # Session status
        self.session_status = QLabel("No active session")
        session_layout.addWidget(self.session_status)
        
        # Remaining time
        self.remaining_time = QLabel("Remaining time: --:--")
        session_layout.addWidget(self.remaining_time)
        
        layout.addWidget(session_frame)
        
        # Light intensity controls
        intensity_frame = QFrame()
        intensity_frame.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        intensity_layout = QVBoxLayout(intensity_frame)
        
        intensity_label = QLabel("Light Intensity")
        intensity_layout.addWidget(intensity_label)
        
        self.intensity_bar = QProgressBar()
        self.intensity_bar.setRange(0, 100)
        intensity_layout.addWidget(self.intensity_bar)
        
        intensity_control = QHBoxLayout()
        self.intensity_input = QSpinBox()
        self.intensity_input.setRange(0, 100)
        self.intensity_input.setValue(100)
        intensity_control.addWidget(self.intensity_input)
        
        set_intensity = QPushButton("Set Intensity")
        set_intensity.clicked.connect(self.set_intensity)
        intensity_control.addWidget(set_intensity)
        intensity_layout.addLayout(intensity_control)
        
        layout.addWidget(intensity_frame)
        
        # Lamp status
        lamp_frame = QFrame()
        lamp_frame.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        lamp_layout = QVBoxLayout(lamp_frame)
        
        self.lamp_status = QLabel("Lamp Status: Unknown")
        self.lamp_hours = QLabel("Lamp Hours: 0")
        self.lamp_life = QProgressBar()
        self.lamp_life.setRange(0, 100)
        
        lamp_layout.addWidget(self.lamp_status)
        lamp_layout.addWidget(self.lamp_hours)
        lamp_layout.addWidget(self.lamp_life)
        
        layout.addWidget(lamp_frame)
        
        self.setLayout(layout)

    async def start_session(self):
        """Start a new therapy session"""
        patient_id = self.patient_id_input.text()
        if not patient_id:
            # Show error message
            return
            
        duration = self.duration_input.value()
        success = await self.phototherapy_manager.start_therapy_session(
            self.device_id, patient_id, duration)
            
        if success:
            self.start_button.setEnabled(False)
            self.end_button.setEnabled(True)
            self.patient_id_input.setEnabled(False)
            self.duration_input.setEnabled(False)

    async def end_session(self):
        """End the current therapy session"""
        success = await self.phototherapy_manager.end_therapy_session(self.device_id)
        if success:
            self.start_button.setEnabled(True)
            self.end_button.setEnabled(False)
            self.patient_id_input.setEnabled(True)
            self.duration_input.setEnabled(True)
            self.session_status.setText("No active session")
            self.remaining_time.setText("Remaining time: --:--")

    async def set_intensity(self):
        """Set light intensity"""
        intensity = self.intensity_input.value()
        await self.phototherapy_manager.set_light_intensity(self.device_id, intensity)

    async def update_parameters(self, parameters):
        """Update parameter displays with latest values"""
        # Update intensity display
        current_intensity = parameters.get('current_intensity', 0)
        self.intensity_bar.setValue(int(current_intensity))
        
        # Update session info if active
        session_info = parameters.get('session_info')
        if session_info:
            self.session_status.setText(f"Active session for patient: {session_info['patient_id']}")
            
            # Calculate and display remaining time
            start_time = datetime.fromisoformat(session_info['start_time'])
            duration = timedelta(minutes=session_info['planned_duration_minutes'])
            elapsed = datetime.utcnow() - start_time
            remaining = duration - elapsed
            
            if remaining.total_seconds() > 0:
                hours, remainder = divmod(remaining.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                self.remaining_time.setText(f"Remaining time: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
            else:
                self.remaining_time.setText("Session complete")
        
        # Update lamp status
        lamp_hours = parameters.get('lamp_hours', 0)
        lamp_life = parameters.get('lamp_life_remaining', 100)
        
        self.lamp_hours.setText(f"Lamp Hours: {lamp_hours:.1f}")
        self.lamp_life.setValue(int(lamp_life))
        
        if lamp_life <= 10:
            self.lamp_status.setText("Lamp Status: Replace Required")
        elif lamp_life <= 20:
            self.lamp_status.setText("Lamp Status: Replace Soon")
        else:
            self.lamp_status.setText("Lamp Status: OK")

    async def show_diagnostic_results(self, results):
        """Display diagnostic results"""
        lamp_health = results.get('lamp_health', 'Unknown')
        self.lamp_status.setText(f"Lamp Status: {lamp_health}")

    def periodic_update(self):
        """Periodic status update"""
        loop = asyncio.get_event_loop()
        loop.create_task(self.update_status())