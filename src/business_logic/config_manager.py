from typing import Any, Dict, Optional
import os
import json
from cryptography.fernet import Fernet
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config_dir = Path('config')
        self.config_file = self.config_dir / 'settings.json'
        self.key_file = self.config_dir / '.key'
        self._init_encryption()
        self.settings = self.load_settings()

    def _init_encryption(self):
        """Initialize encryption key"""
        self.config_dir.mkdir(exist_ok=True)
        if not self.key_file.exists():
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
        else:
            with open(self.key_file, 'rb') as f:
                key = f.read()
        self.fernet = Fernet(key)

    def load_settings(self) -> Dict[str, Any]:
        """Load settings from encrypted config file"""
        if not self.config_file.exists():
            return self._create_default_settings()

        try:
            with open(self.config_file, 'rb') as f:
                encrypted_data = f.read()
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data)
        except Exception:
            return self._create_default_settings()

    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings with encryption"""
        try:
            encrypted_data = self.fernet.encrypt(json.dumps(settings).encode())
            with open(self.config_file, 'wb') as f:
                f.write(encrypted_data)
            return True
        except Exception:
            return False

    def _create_default_settings(self) -> Dict[str, Any]:
        """Create default settings"""
        settings = {
            'language': 'vi',
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'mdms',
                'user': 'mdms_user',
                'password': ''
            },
            'security': {
                'jwt_secret': os.urandom(32).hex(),
                'encryption_key': os.urandom(32).hex(),
                'session_timeout': 24  # hours
            },
            'ui': {
                'theme': 'light',
                'font_size': 12
            },
            'notifications': {
                'maintenance_alerts': True,
                'error_alerts': True,
                'inventory_alerts': True,
                'device_alerts': True
            },
            'backup': {
                'auto_backup': True,
                'backup_interval': 24,
                'backup_location': 'backups/',
                'retention_days': 30
            }
        }
        self.save_settings(settings)
        return settings

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key"""
        keys = key.split('.')
        value = self.settings
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set_setting(self, key: str, value: Any) -> bool:
        """Set a setting value by key"""
        keys = key.split('.')
        target = self.settings
        for k in keys[:-1]:
            target = target.setdefault(k, {})
        target[keys[-1]] = value
        return self.save_settings(self.settings)