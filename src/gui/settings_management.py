from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QPushButton, QLabel, QComboBox, QLineEdit,
                            QFormLayout, QSpinBox, QCheckBox, QFileDialog,
                            QMessageBox, QFrame)
from PyQt6.QtCore import Qt, QTimer
import gettext
from ..business_logic.config_manager import ConfigManager
from ..business_logic.backup_service import BackupService
import logging
import asyncio

class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.backup_service = BackupService()
        self.config = ConfigManager()
        self.setup_localization()
        self.setup_ui()
        self.load_settings()

    def showEvent(self, event):
        """Initialize services when widget becomes visible"""
        super().showEvent(event)
        asyncio.create_task(self.init_services())

    def hideEvent(self, event):
        """Cleanup services when widget is hidden"""
        super().hideEvent(event)
        asyncio.create_task(self.cleanup_services())

    async def init_services(self):
        """Initialize background services"""
        if self.auto_backup_enabled.isChecked():
            await self.backup_service.start_backup_scheduler()

    async def cleanup_services(self):
        """Cleanup background services"""
        await self.backup_service.stop_backup_scheduler()

    def toggle_auto_backup(self, enabled: bool):
        """Toggle automated backup scheduler"""
        if enabled:
            interval = self.backup_interval.value() * 3600000  # Convert hours to milliseconds
            self.config.set_setting('backup.interval_hours', self.backup_interval.value())
            self.config.set_setting('backup.enabled', True)
            asyncio.create_task(self.backup_service.start_backup_scheduler())
        else:
            self.config.set_setting('backup.enabled', False)
            asyncio.create_task(self.backup_service.stop_backup_scheduler())

    def setup_localization(self):
        """Initialize localization support"""
        try:
            self.trans = gettext.translation('mdms', 'locale', languages=['vi'])
            self.trans.install()
            self._ = self.trans.gettext
        except FileNotFoundError:
            self._ = lambda x: x

    def load_settings(self):
        """Load current settings from config manager"""
        self.settings = self.config.settings

    def setup_ui(self):
        """Initialize the settings widget UI"""
        layout = QVBoxLayout(self)

        # Create tab widget
        tabs = QTabWidget()
        tabs.addTab(self._create_general_tab(), self._("General"))
        tabs.addTab(self._create_database_tab(), self._("Database"))
        tabs.addTab(self._create_interface_tab(), self._("Interface"))
        tabs.addTab(self._create_notifications_tab(), self._("Notifications"))
        tabs.addTab(self._create_backup_tab(), self._("Backup & Restore"))

        layout.addWidget(tabs)

        # Add save button at bottom
        save_btn = QPushButton(self._("Save Settings"))
        save_btn.clicked.connect(self.save_all_settings)
        layout.addWidget(save_btn)

    def _create_general_tab(self) -> QWidget:
        """Create general settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Language selection
        self.language_combo = QComboBox()
        self.language_combo.addItems(['Vietnamese', 'English'])
        self.language_combo.setCurrentText('Vietnamese' if self.settings['language'] == 'vi' else 'English')
        layout.addRow(self._("Language:"), self.language_combo)

        return widget

    def _create_database_tab(self) -> QWidget:
        """Create database settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Database settings
        self.db_host = QLineEdit(self.settings['database']['host'])
        layout.addRow(self._("Host:"), self.db_host)

        self.db_port = QSpinBox()
        self.db_port.setRange(1, 65535)
        self.db_port.setValue(self.settings['database']['port'])
        layout.addRow(self._("Port:"), self.db_port)

        self.db_name = QLineEdit(self.settings['database']['name'])
        layout.addRow(self._("Database Name:"), self.db_name)

        self.db_user = QLineEdit(self.settings['database']['user'])
        layout.addRow(self._("Username:"), self.db_user)

        self.db_password = QLineEdit()
        self.db_password.setEchoMode(QLineEdit.EchoMode.Password)
        if self.settings['database'].get('password'):
            self.db_password.setText(self.settings['database']['password'])
        layout.addRow(self._("Password:"), self.db_password)

        # Test connection button
        test_btn = QPushButton(self._("Test Connection"))
        test_btn.clicked.connect(self.test_database_connection)
        layout.addRow("", test_btn)

        return widget

    def _create_interface_tab(self) -> QWidget:
        """Create interface settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([self._("Light"), self._("Dark")])
        self.theme_combo.setCurrentText(
            self._("Light") if self.settings['ui']['theme'] == 'light' else self._("Dark")
        )
        layout.addRow(self._("Theme:"), self.theme_combo)

        # Font size
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setValue(self.settings['ui']['font_size'])
        layout.addRow(self._("Font Size:"), self.font_size)

        return widget

    def _create_notifications_tab(self) -> QWidget:
        """Create notifications settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Notification checkboxes
        self.maintenance_alerts = QCheckBox()
        self.maintenance_alerts.setChecked(self.settings['notifications']['maintenance_alerts'])
        layout.addRow(self._("Maintenance Alerts:"), self.maintenance_alerts)

        self.error_alerts = QCheckBox()
        self.error_alerts.setChecked(self.settings['notifications']['error_alerts'])
        layout.addRow(self._("Error Alerts:"), self.error_alerts)

        self.inventory_alerts = QCheckBox()
        self.inventory_alerts.setChecked(self.settings['notifications']['inventory_alerts'])
        layout.addRow(self._("Inventory Alerts:"), self.inventory_alerts)

        self.device_alerts = QCheckBox()
        self.device_alerts.setChecked(self.settings['notifications']['device_alerts'])
        layout.addRow(self._("Device Status Alerts:"), self.device_alerts)

        return widget

    def _create_backup_tab(self) -> QWidget:
        """Create backup settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Auto backup settings
        backup_frame = QFrame()
        backup_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        backup_layout = QFormLayout(backup_frame)

        self.auto_backup_enabled = QCheckBox()
        self.auto_backup_enabled.setChecked(self.settings['backup']['enabled'])
        self.auto_backup_enabled.toggled.connect(self.toggle_auto_backup)
        backup_layout.addRow(self._("Enable Auto Backup:"), self.auto_backup_enabled)

        self.backup_interval = QSpinBox()
        self.backup_interval.setRange(1, 168)  # 1 hour to 1 week
        self.backup_interval.setValue(self.settings['backup']['interval_hours'])
        backup_layout.addRow(self._("Backup Interval (hours):"), self.backup_interval)

        self.retention_days = QSpinBox()
        self.retention_days.setRange(1, 365)  # 1 day to 1 year
        self.retention_days.setValue(self.settings['backup']['retention_days'])
        backup_layout.addRow(self._("Retention Period (days):"), self.retention_days)

        self.backup_location = QLineEdit(self.settings['backup']['backup_location'])
        browse_btn = QPushButton(self._("Browse"))
        browse_btn.clicked.connect(self.browse_backup_location)

        location_layout = QHBoxLayout()
        location_layout.addWidget(self.backup_location)
        location_layout.addWidget(browse_btn)
        backup_layout.addRow(self._("Backup Location:"), location_layout)

        layout.addWidget(backup_frame)

        # Manual backup/restore buttons
        buttons_frame = QFrame()
        buttons_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        buttons_layout = QVBoxLayout(buttons_frame)

        backup_btn = QPushButton(self._("Create Backup Now"))
        backup_btn.clicked.connect(self.create_backup)
        buttons_layout.addWidget(backup_btn)

        restore_btn = QPushButton(self._("Restore from Backup"))
        restore_btn.clicked.connect(self.restore_from_backup)
        buttons_layout.addWidget(restore_btn)

        layout.addWidget(buttons_frame)
        layout.addStretch()

        return widget

    def browse_backup_location(self):
        """Open directory browser for backup location"""
        directory = QFileDialog.getExistingDirectory(
            self,
            self._("Select Backup Directory"),
            self.backup_location.text()
        )
        if directory:
            self.backup_location.setText(directory)

    def create_backup(self):
        """Create a manual backup"""
        backup_file = self.backup_service.create_backup()
        if backup_file:
            QMessageBox.information(
                self,
                self._("Backup"),
                self._("Backup created successfully") + f"\n{backup_file}"
            )
        else:
            QMessageBox.warning(
                self,
                self._("Error"),
                self._("Failed to create backup")
            )

    def restore_from_backup(self):
        """Restore system from a backup file"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            self._("Select Backup File"),
            self.backup_location.text(),
            self._("Backup files (*.bak)")
        )
        if file_name:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setText(self._("Are you sure you want to restore from backup?"))
            msg_box.setInformativeText(self._("This will overwrite current data"))
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)

            if msg_box.exec() == QMessageBox.StandardButton.Yes:
                if self.backup_service.restore_backup(file_name):
                    QMessageBox.information(
                        self,
                        self._("Restore"),
                        self._("System restored successfully")
                    )
                    # Reload settings
                    self.load_settings()
                else:
                    QMessageBox.warning(
                        self,
                        self._("Error"),
                        self._("Failed to restore from backup")
                    )

    def test_database_connection(self):
        """Test database connection with current settings"""
        import psycopg2

        try:
            conn = psycopg2.connect(
                dbname=self.db_name.text(),
                user=self.db_user.text(),
                password=self.db_password.text(),
                host=self.db_host.text(),
                port=self.db_port.value()
            )
            conn.close()
            QMessageBox.information(
                self,
                self._("Database Connection"),
                self._("Connection successful")
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                self._("Error"),
                str(e)
            )

    def save_all_settings(self):
        """Save all settings"""
        # Update settings dictionary
        self.settings['language'] = 'vi' if self.language_combo.currentText() == 'Vietnamese' else 'en'

        self.settings['database'].update({
            'host': self.db_host.text(),
            'port': self.db_port.value(),
            'name': self.db_name.text(),
            'user': self.db_user.text()
        })
        if self.db_password.text():
            self.settings['database']['password'] = self.db_password.text()

        self.settings['ui'].update({
            'theme': 'light' if self.theme_combo.currentText() == self._("Light") else 'dark',
            'font_size': self.font_size.value()
        })

        self.settings['notifications'].update({
            'maintenance_alerts': self.maintenance_alerts.isChecked(),
            'error_alerts': self.error_alerts.isChecked(),
            'inventory_alerts': self.inventory_alerts.isChecked(),
            'device_alerts': self.device_alerts.isChecked()
        })

        self.settings['backup'].update({
            'auto_backup': self.auto_backup.isChecked(),
            'backup_interval': self.backup_interval.value(),
            'retention_days': self.retention_days.value(),
            'backup_location': self.backup_location.text()
        })

        # Save settings using config manager
        if self.config.save_settings(self.settings):
            QMessageBox.information(
                self,
                self._("Success"),
                self._("Settings saved successfully")
            )

            # Apply settings
            self.apply_settings()
        else:
            QMessageBox.critical(
                self,
                self._("Error"),
                self._("Failed to save settings")
            )

    def apply_settings(self):
        """Apply current settings"""
        # Update backup timer if needed
        if self.settings['backup']['auto_backup']:
            interval = self.settings['backup']['backup_interval'] * 3600000
            self.backup_timer.setInterval(interval)
            if not self.backup_timer.isActive():
                self.backup_timer.start()
        else:
            self.backup_timer.stop()