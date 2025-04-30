from PyQt6.QtWidgets import (QLabel, QPushButton, QSpinBox, QDoubleSpinBox,
                            QGridLayout, QFrame, QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from .base_device_panel import BaseDeviceControlPanel
from ..business_logic.heating_bed_manager import HeatingBedManager
import asyncio

class HeatingBedPanel(BaseDeviceControlPanel):
    def __init__(self, device_id, device_service, parent=None):
        super().__init__(device_id, device_service, parent)
        self.heating_bed_manager = HeatingBedManager()
        self.setup_specific_ui()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.periodic_update)
        self.update_timer.start(1000)  # Update every second
        
    def setup_specific_ui(self):
        """Setup heating bed specific controls"""
        # Temperature controls
        temp_frame = QFrame()
        temp_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        temp_layout = QGridLayout(temp_frame)
        
        # Current temperature display
        temp_layout.addWidget(QLabel("Current Temperature:"), 0, 0)
        self.current_temp_label = QLabel("--.-°C")
        temp_layout.addWidget(self.current_temp_label, 0, 1)
        
        # Target temperature control
        temp_layout.addWidget(QLabel("Target Temperature:"), 1, 0)
        self.target_temp_spin = QDoubleSpinBox()
        self.target_temp_spin.setRange(35.0, 38.0)
        self.target_temp_spin.setSingleStep(0.1)
        self.target_temp_spin.setValue(37.0)
        self.target_temp_spin.valueChanged.connect(self.set_target_temperature)
        temp_layout.addWidget(self.target_temp_spin, 1, 1)
        
        # Add temperature frame to parameters section
        self.parameters_layout.addWidget(temp_frame)
        
        # Heating power indicator
        power_layout = QGridLayout()
        power_layout.addWidget(QLabel("Heating Power:"), 0, 0)
        self.power_bar = QProgressBar()
        self.power_bar.setRange(0, 100)
        power_layout.addWidget(self.power_bar, 0, 1)
        self.parameters_layout.addLayout(power_layout)
        
        # Safety status
        safety_frame = QFrame()
        safety_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        safety_layout = QGridLayout(safety_frame)
        
        # Alarm status
        safety_layout.addWidget(QLabel("Alarm Status:"), 0, 0)
        self.alarm_label = QLabel("Normal")
        self.alarm_label.setStyleSheet("color: green;")
        safety_layout.addWidget(self.alarm_label, 0, 1)
        
        # Mattress sensor status
        safety_layout.addWidget(QLabel("Mattress Sensor:"), 1, 0)
        self.mattress_label = QLabel("OK")
        self.mattress_label.setStyleSheet("color: green;")
        safety_layout.addWidget(self.mattress_label, 1, 1)
        
        # Add safety frame to parameters section
        self.parameters_layout.addWidget(safety_frame)
        
        # Control buttons
        control_layout = QGridLayout()
        
        # Reset alarm button
        self.reset_alarm_btn = QPushButton("Reset Alarm")
        self.reset_alarm_btn.clicked.connect(self.reset_alarm)
        self.reset_alarm_btn.setEnabled(False)
        control_layout.addWidget(self.reset_alarm_btn, 0, 0)
        
        # Safety check button
        safety_check_btn = QPushButton("Safety Check")
        safety_check_btn.clicked.connect(self.check_safety)
        control_layout.addWidget(safety_check_btn, 0, 1)
        
        self.controls_layout.addLayout(control_layout)
        
    async def update_parameters(self, parameters):
        """Update parameter displays with latest values"""
        # Update temperature displays
        current_temp = parameters.get('current_temperature')
        if current_temp is not None:
            self.current_temp_label.setText(f"{current_temp:.1f}°C")
            
        # Update heating power
        power = parameters.get('heating_power', 0)
        self.power_bar.setValue(int(power))
        
        # Update alarm status
        alarm_active = parameters.get('alarm_active', False)
        self.alarm_label.setText("ALARM" if alarm_active else "Normal")
        self.alarm_label.setStyleSheet("color: red; font-weight: bold;" if alarm_active else "color: green;")
        self.reset_alarm_btn.setEnabled(alarm_active)
        
        # Update mattress sensor status
        mattress_ok = parameters.get('mattress_sensor_ok', True)
        self.mattress_label.setText("OK" if mattress_ok else "Fault")
        self.mattress_label.setStyleSheet("color: green;" if mattress_ok else "color: red; font-weight: bold;")
        
    async def show_diagnostic_results(self, results):
        """Display diagnostic results"""
        message = "Diagnostic Results:\n\n"
        for key, value in results.items():
            message += f"{key}: {value}\n"
            
        QMessageBox.information(self, "Diagnostic Results", message)
        
    async def set_target_temperature(self):
        """Set new target temperature"""
        temperature = self.target_temp_spin.value()
        success = await self.heating_bed_manager.set_target_temperature(self.device_id, temperature)
        if not success:
            QMessageBox.warning(self, "Error", "Failed to set target temperature")
        
    async def reset_alarm(self):
        """Reset alarm condition"""
        success = await self.heating_bed_manager.reset_alarm(self.device_id)
        if success:
            await self.update_status()
        else:
            QMessageBox.warning(self, "Error", "Failed to reset alarm")
        
    async def check_safety(self):
        """Perform safety status check"""
        status = await self.heating_bed_manager.check_safety_status(self.device_id)
        if status:
            message = "Safety Status:\n\n"
            message += f"Temperature in range: {'Yes' if status['temperature_in_range'] else 'No'}\n"
            message += f"Current temperature: {status['current_temperature']:.1f}°C\n"
            message += f"Safety cutoff: {status['safety_cutoff_temp']:.1f}°C\n"
            message += f"Mattress sensor: {'OK' if status['mattress_sensor_ok'] else 'Fault'}\n"
            message += f"System status: {status['system_status']}"
            
            QMessageBox.information(self, "Safety Check Results", message)
        else:
            QMessageBox.warning(self, "Error", "Failed to retrieve safety status")
        
    def periodic_update(self):
        """Periodic status update"""
        if self.isVisible():
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.update_status())