from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QComboBox, QFrame, QProgressBar, QTextEdit,
                            QListWidget, QSpinBox)
from PyQt6.QtCore import QTimer
from .base_device_panel import BaseDeviceControlPanel
from ..business_logic.sterilizer_manager import SterilizerManager
import asyncio

class SterilizerPanel(BaseDeviceControlPanel):
    def __init__(self, device_id, device_service, parent=None):
        super().__init__(device_id, device_service, parent)
        self.sterilizer_manager = SterilizerManager()
        self.setup_specific_ui()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.periodic_update)
        self.update_timer.start(1000)  # Update every second

    def setup_specific_ui(self):
        """Setup sterilizer specific controls"""
        layout = QVBoxLayout()
        
        # Status panel
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        status_layout = QVBoxLayout(status_frame)
        
        # Temperature display
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Temperature:"))
        self.temp_display = QProgressBar()
        self.temp_display.setRange(20, 140)  # 20-140°C
        temp_layout.addWidget(self.temp_display)
        self.temp_label = QLabel("20°C")
        temp_layout.addWidget(self.temp_label)
        status_layout.addLayout(temp_layout)
        
        # Pressure display
        pressure_layout = QHBoxLayout()
        pressure_layout.addWidget(QLabel("Pressure:"))
        self.pressure_display = QProgressBar()
        self.pressure_display.setRange(100, 220)  # 1.0-2.2 bar
        pressure_layout.addWidget(self.pressure_display)
        self.pressure_label = QLabel("1.0 bar")
        pressure_layout.addWidget(self.pressure_label)
        status_layout.addLayout(pressure_layout)
        
        # Door status and control
        door_layout = QHBoxLayout()
        self.door_status = QLabel("Door: Unknown")
        door_layout.addWidget(self.door_status)
        self.door_button = QPushButton("Lock Door")
        self.door_button.clicked.connect(self.toggle_door)
        door_layout.addWidget(self.door_button)
        status_layout.addLayout(door_layout)
        
        layout.addWidget(status_frame)
        
        # Cycle control panel
        cycle_frame = QFrame()
        cycle_frame.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        cycle_layout = QVBoxLayout(cycle_frame)
        
        # Cycle type selection
        cycle_type_layout = QHBoxLayout()
        cycle_type_layout.addWidget(QLabel("Cycle Type:"))
        self.cycle_type = QComboBox()
        self.cycle_type.addItems(["Standard", "Quick", "Custom"])
        cycle_type_layout.addWidget(self.cycle_type)
        cycle_layout.addLayout(cycle_type_layout)
        
        # Items list
        cycle_layout.addWidget(QLabel("Items for sterilization:"))
        self.items_list = QListWidget()
        self.items_list.setMaximumHeight(100)
        cycle_layout.addWidget(self.items_list)
        
        # Items input
        self.item_input = QTextEdit()
        self.item_input.setMaximumHeight(50)
        self.item_input.setPlaceholderText("Enter items (one per line)")
        cycle_layout.addWidget(self.item_input)
        
        # Custom cycle parameters (shown only for custom cycle)
        self.custom_params = QFrame()
        custom_layout = QVBoxLayout(self.custom_params)
        
        temp_param = QHBoxLayout()
        temp_param.addWidget(QLabel("Target Temperature (°C):"))
        self.target_temp = QSpinBox()
        self.target_temp.setRange(105, 137)
        self.target_temp.setValue(121)
        temp_param.addWidget(self.target_temp)
        custom_layout.addLayout(temp_param)
        
        pressure_param = QHBoxLayout()
        pressure_param.addWidget(QLabel("Target Pressure (bar):"))
        self.target_pressure = QSpinBox()
        self.target_pressure.setRange(10, 22)  # 1.0-2.2 bar (x10 for integer spinbox)
        self.target_pressure.setValue(20)  # 2.0 bar
        pressure_param.addWidget(self.target_pressure)
        custom_layout.addLayout(pressure_param)
        
        cycle_layout.addWidget(self.custom_params)
        self.custom_params.hide()
        
        # Cycle controls
        controls_layout = QHBoxLayout()
        self.start_cycle = QPushButton("Start Cycle")
        self.start_cycle.clicked.connect(self.start_sterilization)
        self.end_cycle = QPushButton("End Cycle")
        self.end_cycle.clicked.connect(self.end_sterilization)
        self.end_cycle.setEnabled(False)
        
        controls_layout.addWidget(self.start_cycle)
        controls_layout.addWidget(self.end_cycle)
        cycle_layout.addLayout(controls_layout)
        
        # Cycle status
        self.cycle_status = QLabel("No active cycle")
        cycle_layout.addWidget(self.cycle_status)
        
        layout.addWidget(cycle_frame)
        
        # Connect cycle type change event
        self.cycle_type.currentTextChanged.connect(self.on_cycle_type_changed)
        
        self.setLayout(layout)

    def on_cycle_type_changed(self, cycle_type):
        """Handle cycle type selection change"""
        self.custom_params.setVisible(cycle_type == "Custom")

    async def toggle_door(self):
        """Toggle door lock state"""
        await self.sterilizer_manager.set_door_lock(
            self.device_id, 
            self.door_button.text() == "Lock Door"
        )

    async def start_sterilization(self):
        """Start sterilization cycle"""
        # Get items list
        items = [line for line in self.item_input.toPlainText().split('\n') if line.strip()]
        if not items:
            # Show error message
            return
            
        cycle_type = self.cycle_type.currentText()
        
        # For custom cycle, set parameters first
        if cycle_type == "Custom":
            await self.sterilizer_manager.set_cycle_parameters(
                self.device_id,
                self.target_temp.value(),
                self.target_pressure.value() / 10.0
            )
            
        success = await self.sterilizer_manager.start_cycle(
            self.device_id, items, cycle_type)
            
        if success:
            self.start_cycle.setEnabled(False)
            self.end_cycle.setEnabled(True)
            self.cycle_type.setEnabled(False)
            self.item_input.setEnabled(False)
            self.custom_params.setEnabled(False)

    async def end_sterilization(self):
        """End sterilization cycle"""
        success = await self.sterilizer_manager.end_cycle(self.device_id)
        if success:
            self.start_cycle.setEnabled(True)
            self.end_cycle.setEnabled(False)
            self.cycle_type.setEnabled(True)
            self.item_input.setEnabled(True)
            self.custom_params.setEnabled(True)
            self.cycle_status.setText("No active cycle")

    async def update_parameters(self, parameters):
        """Update parameter displays with latest values"""
        # Update temperature
        temp = parameters.get('current_temperature', 20)
        self.temp_display.setValue(int(temp))
        self.temp_label.setText(f"{temp:.1f}°C")
        
        # Update pressure
        pressure = parameters.get('current_pressure', 1.0)
        self.pressure_display.setValue(int(pressure * 100))
        self.pressure_label.setText(f"{pressure:.1f} bar")
        
        # Update door status
        door_locked = parameters.get('door_locked', False)
        self.door_status.setText(f"Door: {'Locked' if door_locked else 'Unlocked'}")
        self.door_button.setText("Unlock Door" if door_locked else "Lock Door")
        
        # Update water level
        water_level = parameters.get('water_level', 0)
        if water_level < 20:
            self.cycle_status.setText("Warning: Low water level")
            self.start_cycle.setEnabled(False)
        elif not parameters.get('cycle_active', False):
            self.start_cycle.setEnabled(True)
            
        # Update cycle status if active
        if parameters.get('cycle_active'):
            cycle_info = parameters.get('cycle_info', {})
            if cycle_info:
                self.cycle_status.setText(
                    f"Active cycle: {cycle_info.get('type', 'Unknown')}\n"
                    f"Status: {cycle_info.get('status', 'Unknown')}"
                )

    async def show_diagnostic_results(self, results):
        """Display diagnostic results"""
        status_text = "Diagnostic Results:\n"
        for key, value in results.items():
            status_text += f"{key}: {value}\n"
        self.cycle_status.setText(status_text)

    def periodic_update(self):
        """Periodic status update"""
        loop = asyncio.get_event_loop()
        loop.create_task(self.update_status())