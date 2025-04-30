from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QStackedWidget, QPushButton, QMessageBox,
                            QSystemTrayIcon, QMenu)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
import gettext
from .device_dashboard import DeviceDashboard
from .devices_management import DevicesManagementWidget
from .maintenance_management import MaintenanceManagementWidget
from .reports_management import ReportsManagementWidget
from .settings_management import SettingsWidget
from ..business_logic.user_service import UserService
from ..business_logic.performance_monitor import PerformanceMonitor
from ..business_logic.alert_service import AlertService
import asyncio
import logging

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_service = UserService()
        self.performance_monitor = PerformanceMonitor()
        self.alert_service = AlertService()
        self.setup_localization()
        self.setup_ui()
        self.setup_system_tray()
        self.setup_performance_monitoring()
        self.setup_status_updates()
        asyncio.create_task(self.start_monitoring())

    async def start_monitoring(self):
        """Start monitoring services"""
        await self.performance_monitor.monitor_system_performance()
        await self.alert_service.start_monitoring()

    def setup_system_tray(self):
        """Initialize system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('icons/app.png'))
        self.tray_icon.setToolTip('Medical Device Management System')

        # Create tray menu
        tray_menu = QMenu()
        show_action = tray_menu.addAction(self._("Show"))
        show_action.triggered.connect(self.showNormal)
        hide_action = tray_menu.addAction(self._("Minimize"))
        hide_action.triggered.connect(self.hide)
        quit_action = tray_menu.addAction(self._("Quit"))
        quit_action.triggered.connect(self.close)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # Setup alert checking timer
        self.alert_timer = QTimer(self)
        self.alert_timer.timeout.connect(self.check_alerts)
        self.alert_timer.start(10000)  # Check every 10 seconds

    def check_alerts(self):
        """Check for active alerts and update system tray"""
        active_alerts = self.alert_service.get_active_alerts()
        if active_alerts:
            self.tray_icon.setIcon(QIcon('icons/alert.png'))
            
            # Show balloon tip for new high severity alerts
            high_severity = [a for a in active_alerts if a['severity'] == 'high']
            if high_severity:
                alert = high_severity[0]  # Show most recent high severity alert
                self.tray_icon.showMessage(
                    self._("High Priority Alert"),
                    f"{alert['type'].title()}: {alert.get('details', '')}",
                    QSystemTrayIcon.MessageIcon.Warning,
                    5000  # Show for 5 seconds
                )
        else:
            self.tray_icon.setIcon(QIcon('icons/app.png'))

    def setup_performance_monitoring(self):
        """Setup performance monitoring"""
        # Start system performance monitoring
        self.performance_timer = QTimer(self)
        self.performance_timer.timeout.connect(self.update_performance_display)
        self.performance_timer.start(5000)  # Update every 5 seconds

    def update_performance_display(self):
        """Update performance metrics display"""
        metrics = self.performance_monitor.get_system_performance()
        if metrics['cpu_usage'] > 80 or metrics['memory_usage'] > 80 or metrics['disk_usage'] > 80:
            self.show_performance_warning(metrics)

        # Update status bar with current metrics
        self.statusBar().showMessage(
            f"CPU: {metrics['cpu_usage']}% | "
            f"Memory: {metrics['memory_usage']}% | "
            f"Disk: {metrics['disk_usage']}%"
        )

    def show_performance_warning(self, metrics: dict):
        """Show warning if system performance is degraded"""
        warnings = []
        if metrics['cpu_usage'] > 80:
            warnings.append(self._("High CPU usage"))
        if metrics['memory_usage'] > 80:
            warnings.append(self._("High memory usage"))
        if metrics['disk_usage'] > 80:
            warnings.append(self._("High disk usage"))

        if warnings:
            QMessageBox.warning(
                self,
                self._("Performance Warning"),
                "\n".join(warnings)
            )

    def closeEvent(self, event):
        """Handle application closure"""
        try:
            # Stop monitoring services
            asyncio.create_task(self.alert_service.stop_monitoring())
            
            # Export performance statistics
            self.performance_monitor.export_statistics('logs/performance_report.json')
            
            # Cleanup system tray
            self.tray_icon.hide()
            
            event.accept()
        except Exception as e:
            logging.error(f"Error during shutdown: {str(e)}")
            event.accept()