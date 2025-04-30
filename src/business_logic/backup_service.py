from typing import Optional, List
import os
import shutil
import json
import sqlite3
import psycopg2
from datetime import datetime, timedelta
from pathlib import Path
from .config_manager import ConfigManager
import logging
import asyncio

class BackupService:
    def __init__(self):
        self.config = ConfigManager()
        self.backup_dir = Path(self.config.get_setting('backup.backup_location'))
        self.backup_dir.mkdir(exist_ok=True)
        self.setup_logging()
        self._scheduler_task = None

    def setup_logging(self):
        """Setup logging for backup operations"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        logging.basicConfig(
            filename=log_dir / 'backup.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def create_backup(self) -> Optional[str]:
        """Create a new backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / f'backup_{timestamp}'
            backup_path.mkdir(exist_ok=True)

            # Backup database
            db_type = 'postgresql' if self.config.get_setting('database.port') == 5432 else 'sqlite'
            if db_type == 'postgresql':
                self._backup_postgresql(backup_path)
            else:
                self._backup_sqlite(backup_path)

            # Backup configuration
            self._backup_config(backup_path)

            # Create backup info
            backup_info = {
                'timestamp': timestamp,
                'db_type': db_type,
                'version': '1.0',
                'configs_included': True
            }
            with open(backup_path / 'backup_info.json', 'w') as f:
                json.dump(backup_info, f)

            # Create archive
            archive_name = f'backup_{timestamp}.bak'
            shutil.make_archive(
                str(self.backup_dir / f'backup_{timestamp}'),
                'zip',
                str(backup_path)
            )
            os.rename(
                str(self.backup_dir / f'backup_{timestamp}.zip'),
                str(self.backup_dir / archive_name)
            )

            # Cleanup temporary directory
            shutil.rmtree(backup_path)

            # Cleanup old backups
            self._cleanup_old_backups()

            logging.info(f'Backup created successfully: {archive_name}')
            return str(self.backup_dir / archive_name)

        except Exception as e:
            logging.error(f'Backup failed: {str(e)}')
            return None

    def restore_backup(self, backup_file: str) -> bool:
        """Restore system from backup"""
        try:
            # Extract backup
            backup_path = Path('temp_restore')
            backup_path.mkdir(exist_ok=True)
            shutil.unpack_archive(backup_file, str(backup_path))

            # Verify backup info
            with open(backup_path / 'backup_info.json', 'r') as f:
                backup_info = json.load(f)

            # Restore database
            if backup_info['db_type'] == 'postgresql':
                success = self._restore_postgresql(backup_path)
            else:
                success = self._restore_sqlite(backup_path)

            if not success:
                raise Exception("Database restore failed")

            # Restore configuration
            self._restore_config(backup_path)

            # Cleanup
            shutil.rmtree(backup_path)
            logging.info(f'Restore completed successfully from {backup_file}')
            return True

        except Exception as e:
            logging.error(f'Restore failed: {str(e)}')
            if backup_path.exists():
                shutil.rmtree(backup_path)
            return False

    def _backup_postgresql(self, backup_path: Path):
        """Backup PostgreSQL database"""
        db_settings = self.config.get_setting('database')
        os.environ['PGPASSWORD'] = db_settings['password']
        
        dump_file = backup_path / 'database.sql'
        os.system(
            f"pg_dump -h {db_settings['host']} -p {db_settings['port']} "
            f"-U {db_settings['user']} -F c -b -v -f {dump_file} {db_settings['name']}"
        )

    def _backup_sqlite(self, backup_path: Path):
        """Backup SQLite database"""
        db_path = Path('data.db')  # Adjust path as needed
        if db_path.exists():
            shutil.copy2(db_path, backup_path / 'database.db')

    def _backup_config(self, backup_path: Path):
        """Backup configuration files"""
        config_dir = Path('config')
        if config_dir.exists():
            shutil.copytree(config_dir, backup_path / 'config')

    def _restore_postgresql(self, backup_path: Path) -> bool:
        """Restore PostgreSQL database"""
        try:
            db_settings = self.config.get_setting('database')
            os.environ['PGPASSWORD'] = db_settings['password']
            
            # Drop existing database connections
            with psycopg2.connect(
                dbname='postgres',
                user=db_settings['user'],
                password=db_settings['password'],
                host=db_settings['host'],
                port=db_settings['port']
            ) as conn:
                conn.set_isolation_level(0)
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                        f"WHERE datname = '{db_settings['name']}'"
                    )
                    cur.execute(f"DROP DATABASE IF EXISTS {db_settings['name']}")
                    cur.execute(f"CREATE DATABASE {db_settings['name']}")

            # Restore from backup
            os.system(
                f"pg_restore -h {db_settings['host']} -p {db_settings['port']} "
                f"-U {db_settings['user']} -d {db_settings['name']} -v {backup_path / 'database.sql'}"
            )
            return True
        except Exception as e:
            logging.error(f'PostgreSQL restore failed: {str(e)}')
            return False

    def _restore_sqlite(self, backup_path: Path) -> bool:
        """Restore SQLite database"""
        try:
            db_path = Path('data.db')  # Adjust path as needed
            if (backup_path / 'database.db').exists():
                if db_path.exists():
                    db_path.unlink()
                shutil.copy2(backup_path / 'database.db', db_path)
            return True
        except Exception as e:
            logging.error(f'SQLite restore failed: {str(e)}')
            return False

    def _restore_config(self, backup_path: Path):
        """Restore configuration files"""
        config_backup = backup_path / 'config'
        if config_backup.exists():
            config_dir = Path('config')
            if config_dir.exists():
                shutil.rmtree(config_dir)
            shutil.copytree(config_backup, config_dir)

    def _cleanup_old_backups(self):
        """Remove backups older than retention period"""
        retention_days = self.config.get_setting('backup.retention_days', 30)
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        for backup_file in self.backup_dir.glob('*.bak'):
            try:
                # Parse timestamp from filename (backup_YYYYMMDD_HHMMSS.bak)
                timestamp_str = backup_file.stem.split('_')[1:3]  # ['YYYYMMDD', 'HHMMSS']
                timestamp = datetime.strptime('_'.join(timestamp_str), '%Y%m%d_%H%M%S')
                
                if timestamp < cutoff_date:
                    backup_file.unlink()
                    logging.info(f'Removed old backup: {backup_file.name}')
            except (IndexError, ValueError):
                continue

    def get_available_backups(self) -> List[dict]:
        """Get list of available backups"""
        backups = []
        for backup_file in sorted(self.backup_dir.glob('*.bak'), reverse=True):
            try:
                # Extract backup info
                with open(backup_file, 'rb') as f:
                    # Read only the backup info without extracting everything
                    backup_info = json.loads(shutil.unpack_archive(f, None, 'zip'))
                
                backups.append({
                    'file': str(backup_file),
                    'timestamp': backup_info['timestamp'],
                    'db_type': backup_info['db_type'],
                    'version': backup_info.get('version', '1.0')
                })
            except Exception:
                continue
        return backups

    async def start_backup_scheduler(self):
        """Start automated backup scheduler"""
        if self._scheduler_task is None:
            self._scheduler_task = asyncio.create_task(self._backup_scheduler())
            logging.info("Automated backup scheduler started")

    async def stop_backup_scheduler(self):
        """Stop automated backup scheduler"""
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
            self._scheduler_task = None
            logging.info("Automated backup scheduler stopped")

    async def _backup_scheduler(self):
        """Background task for automated backups"""
        while True:
            try:
                interval_hours = self.config.get_setting('backup.interval_hours', 24)
                backup_file = self.create_backup()
                if backup_file:
                    logging.info(f"Scheduled backup created: {backup_file}")
                else:
                    logging.error("Scheduled backup failed")
                
                # Wait for next backup interval
                await asyncio.sleep(interval_hours * 3600)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logging.error(f"Error in backup scheduler: {str(e)}")
                await asyncio.sleep(3600)  # Wait an hour on error