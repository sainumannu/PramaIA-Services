"""
Generic System Processor

Processore universale per operazioni di sistema: file management, cleanup, backup,
monitoring, logging, event management. Unifica tutte le operazioni di sistema
e manutenzione in un singolo nodo configurabile.
"""

import logging
import os
import shutil
import json
import time
import asyncio
import hashlib
import sqlite3
import schedule
from typing import Dict, Any, List, Optional, Union, Callable
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
import threading
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models for System Operations
# ============================================================================

@dataclass
class FileOperationResult:
    """Result of a file operation."""
    success: bool
    operation: str
    source_path: str
    destination_path: Optional[str] = None
    message: str = ""
    bytes_processed: int = 0
    files_processed: int = 0
    error_details: Optional[str] = None


@dataclass
class MonitoringEvent:
    """Event from file system monitoring."""
    event_type: str  # created, modified, deleted, moved
    file_path: str
    relative_path: str
    timestamp: datetime
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BackupOperation:
    """Backup operation configuration."""
    source_paths: List[str]
    destination_path: str
    backup_type: str  # full, incremental, differential
    compression: bool = False
    encryption: bool = False
    retention_days: int = 30
    exclude_patterns: List[str] = None


@dataclass
class CleanupOperation:
    """Cleanup operation configuration."""
    target_paths: List[str]
    cleanup_type: str  # files, logs, temp, cache, database
    age_threshold: int = 7  # days
    size_threshold: int = 0  # bytes
    pattern_filters: List[str] = None
    dry_run: bool = False


# ============================================================================
# Abstract Interfaces for System Operations
# ============================================================================

class FileManager(ABC):
    """Abstract base class for file management operations."""
    
    @abstractmethod
    async def copy_file(self, source: str, destination: str, **kwargs) -> FileOperationResult:
        """Copy a file from source to destination."""
        pass
    
    @abstractmethod
    async def move_file(self, source: str, destination: str, **kwargs) -> FileOperationResult:
        """Move a file from source to destination."""
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str, **kwargs) -> FileOperationResult:
        """Delete a file."""
        pass
    
    @abstractmethod
    async def archive_file(self, file_path: str, archive_dir: str, **kwargs) -> FileOperationResult:
        """Archive a file with timestamp."""
        pass


class SystemMonitor(ABC):
    """Abstract base class for system monitoring."""
    
    @abstractmethod
    async def start_monitoring(self, paths: List[str], **kwargs) -> bool:
        """Start monitoring file system paths."""
        pass
    
    @abstractmethod
    async def stop_monitoring(self) -> bool:
        """Stop monitoring."""
        pass
    
    @abstractmethod
    async def get_events(self, since: Optional[datetime] = None) -> List[MonitoringEvent]:
        """Get monitoring events."""
        pass


class BackupManager(ABC):
    """Abstract base class for backup operations."""
    
    @abstractmethod
    async def create_backup(self, backup_config: BackupOperation) -> FileOperationResult:
        """Create a backup according to configuration."""
        pass
    
    @abstractmethod
    async def restore_backup(self, backup_path: str, restore_path: str) -> FileOperationResult:
        """Restore from backup."""
        pass
    
    @abstractmethod
    async def list_backups(self, backup_dir: str) -> List[Dict[str, Any]]:
        """List available backups."""
        pass


class CleanupManager(ABC):
    """Abstract base class for cleanup operations."""
    
    @abstractmethod
    async def cleanup_files(self, cleanup_config: CleanupOperation) -> FileOperationResult:
        """Perform cleanup according to configuration."""
        pass
    
    @abstractmethod
    async def analyze_cleanup(self, cleanup_config: CleanupOperation) -> Dict[str, Any]:
        """Analyze what would be cleaned without actually doing it."""
        pass


class EventLogger(ABC):
    """Abstract base class for event logging."""
    
    @abstractmethod
    async def log_event(self, event_type: str, details: Dict[str, Any]) -> bool:
        """Log a system event."""
        pass
    
    @abstractmethod
    async def get_events(self, event_type: Optional[str] = None, 
                        since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Retrieve logged events."""
        pass


# ============================================================================
# Concrete File Manager Implementation
# ============================================================================

class StandardFileManager(FileManager):
    """Standard file manager implementation."""
    
    async def copy_file(self, source: str, destination: str, **kwargs) -> FileOperationResult:
        """Copy a file with progress tracking."""
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                return FileOperationResult(
                    success=False,
                    operation="copy",
                    source_path=source,
                    message=f"Source file does not exist: {source}",
                    error_details="FILE_NOT_FOUND"
                )
            
            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy with metadata preservation
            preserve_metadata = kwargs.get('preserve_metadata', True)
            overwrite = kwargs.get('overwrite', False)
            
            if dest_path.exists() and not overwrite:
                return FileOperationResult(
                    success=False,
                    operation="copy",
                    source_path=source,
                    destination_path=destination,
                    message="Destination file exists and overwrite is disabled",
                    error_details="FILE_EXISTS"
                )
            
            if preserve_metadata:
                shutil.copy2(source, destination)
            else:
                shutil.copy(source, destination)
            
            file_size = source_path.stat().st_size
            
            return FileOperationResult(
                success=True,
                operation="copy",
                source_path=source,
                destination_path=destination,
                message=f"File copied successfully: {source} -> {destination}",
                bytes_processed=file_size,
                files_processed=1
            )
            
        except Exception as e:
            return FileOperationResult(
                success=False,
                operation="copy",
                source_path=source,
                destination_path=destination,
                message=f"Copy failed: {str(e)}",
                error_details=str(e)
            )
    
    async def move_file(self, source: str, destination: str, **kwargs) -> FileOperationResult:
        """Move a file."""
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                return FileOperationResult(
                    success=False,
                    operation="move",
                    source_path=source,
                    message=f"Source file does not exist: {source}",
                    error_details="FILE_NOT_FOUND"
                )
            
            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            overwrite = kwargs.get('overwrite', False)
            if dest_path.exists() and not overwrite:
                return FileOperationResult(
                    success=False,
                    operation="move",
                    source_path=source,
                    destination_path=destination,
                    message="Destination file exists and overwrite is disabled",
                    error_details="FILE_EXISTS"
                )
            
            file_size = source_path.stat().st_size
            shutil.move(source, destination)
            
            return FileOperationResult(
                success=True,
                operation="move",
                source_path=source,
                destination_path=destination,
                message=f"File moved successfully: {source} -> {destination}",
                bytes_processed=file_size,
                files_processed=1
            )
            
        except Exception as e:
            return FileOperationResult(
                success=False,
                operation="move",
                source_path=source,
                destination_path=destination,
                message=f"Move failed: {str(e)}",
                error_details=str(e)
            )
    
    async def delete_file(self, file_path: str, **kwargs) -> FileOperationResult:
        """Delete a file."""
        try:
            path = Path(file_path)
            
            if not path.exists():
                return FileOperationResult(
                    success=False,
                    operation="delete",
                    source_path=file_path,
                    message=f"File does not exist: {file_path}",
                    error_details="FILE_NOT_FOUND"
                )
            
            secure_delete = kwargs.get('secure_delete', False)
            file_size = path.stat().st_size
            
            if secure_delete:
                # Secure deletion by overwriting with random data
                with open(file_path, 'r+b') as f:
                    length = f.seek(0, 2)
                    f.seek(0)
                    for _ in range(3):  # 3 passes
                        f.write(os.urandom(length))
                        f.flush()
                        os.fsync(f.fileno())
                        f.seek(0)
            
            path.unlink()
            
            return FileOperationResult(
                success=True,
                operation="delete",
                source_path=file_path,
                message=f"File deleted successfully: {file_path}",
                bytes_processed=file_size,
                files_processed=1
            )
            
        except Exception as e:
            return FileOperationResult(
                success=False,
                operation="delete",
                source_path=file_path,
                message=f"Delete failed: {str(e)}",
                error_details=str(e)
            )
    
    async def archive_file(self, file_path: str, archive_dir: str, **kwargs) -> FileOperationResult:
        """Archive a file with timestamp."""
        try:
            source_path = Path(file_path)
            
            if not source_path.exists():
                return FileOperationResult(
                    success=False,
                    operation="archive",
                    source_path=file_path,
                    message=f"Source file does not exist: {file_path}",
                    error_details="FILE_NOT_FOUND"
                )
            
            archive_path = Path(archive_dir)
            archive_path.mkdir(parents=True, exist_ok=True)
            
            # Create archived filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archived_name = f"{source_path.stem}.{timestamp}.{source_path.suffix}.bak"
            destination = archive_path / archived_name
            
            # Move file to archive
            file_size = source_path.stat().st_size
            shutil.move(file_path, str(destination))
            
            return FileOperationResult(
                success=True,
                operation="archive",
                source_path=file_path,
                destination_path=str(destination),
                message=f"File archived successfully: {file_path} -> {destination}",
                bytes_processed=file_size,
                files_processed=1
            )
            
        except Exception as e:
            return FileOperationResult(
                success=False,
                operation="archive",
                source_path=file_path,
                destination_path=archive_dir,
                message=f"Archive failed: {str(e)}",
                error_details=str(e)
            )


# ============================================================================
# Concrete System Monitor Implementation
# ============================================================================

class FileSystemMonitor(SystemMonitor):
    """File system monitoring implementation."""
    
    def __init__(self):
        self.monitoring = False
        self.events = []
        self.watched_paths = []
        self.monitor_thread = None
        self.db_path = None
    
    async def start_monitoring(self, paths: List[str], **kwargs) -> bool:
        """Start monitoring file system paths."""
        try:
            if self.monitoring:
                await self.stop_monitoring()
            
            self.watched_paths = paths
            self.db_path = kwargs.get('db_path', './monitoring_events.db')
            self.max_events = kwargs.get('max_events', 10000)
            
            # Initialize event database
            self._init_event_db()
            
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            
            logger.info(f"Started monitoring {len(paths)} paths")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            return False
    
    async def stop_monitoring(self) -> bool:
        """Stop monitoring."""
        try:
            self.monitoring = False
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5.0)
            
            logger.info("Monitoring stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop monitoring: {e}")
            return False
    
    async def get_events(self, since: Optional[datetime] = None) -> List[MonitoringEvent]:
        """Get monitoring events."""
        try:
            if not self.db_path or not os.path.exists(self.db_path):
                return []
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if since:
                    cursor.execute(
                        "SELECT * FROM events WHERE timestamp > ? ORDER BY timestamp DESC LIMIT 1000",
                        (since.isoformat(),)
                    )
                else:
                    cursor.execute(
                        "SELECT * FROM events ORDER BY timestamp DESC LIMIT 1000"
                    )
                
                events = []
                for row in cursor.fetchall():
                    event = MonitoringEvent(
                        event_type=row[1],
                        file_path=row[2],
                        relative_path=row[3],
                        timestamp=datetime.fromisoformat(row[4]),
                        file_size=row[5],
                        file_hash=row[6],
                        metadata=json.loads(row[7]) if row[7] else None
                    )
                    events.append(event)
                
                return events
                
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            return []
    
    def _init_event_db(self):
        """Initialize events database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    file_size INTEGER,
                    file_hash TEXT,
                    metadata TEXT
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)
            """)
            conn.commit()
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        logger.info("Monitoring loop started")
        
        # Simple polling-based monitoring (could be enhanced with watchdog)
        file_states = {}
        
        while self.monitoring:
            try:
                for watch_path in self.watched_paths:
                    if not os.path.exists(watch_path):
                        continue
                    
                    self._scan_directory(watch_path, file_states)
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Wait before retrying
        
        logger.info("Monitoring loop stopped")
    
    def _scan_directory(self, directory: str, file_states: Dict[str, Dict]):
        """Scan directory for changes."""
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, directory)
                    
                    try:
                        stat = os.stat(file_path)
                        current_state = {
                            'size': stat.st_size,
                            'mtime': stat.st_mtime
                        }
                        
                        if file_path not in file_states:
                            # New file
                            self._record_event('created', file_path, relative_path, stat.st_size)
                            file_states[file_path] = current_state
                        else:
                            # Check for modifications
                            old_state = file_states[file_path]
                            if (current_state['size'] != old_state['size'] or 
                                current_state['mtime'] != old_state['mtime']):
                                self._record_event('modified', file_path, relative_path, stat.st_size)
                                file_states[file_path] = current_state
                        
                    except (OSError, IOError):
                        # File might have been deleted or is inaccessible
                        if file_path in file_states:
                            self._record_event('deleted', file_path, relative_path, 0)
                            del file_states[file_path]
            
            # Check for deleted files
            existing_files = set()
            for root, dirs, files in os.walk(directory):
                for file in files:
                    existing_files.add(os.path.join(root, file))
            
            for file_path in list(file_states.keys()):
                if file_path not in existing_files:
                    relative_path = os.path.relpath(file_path, directory)
                    self._record_event('deleted', file_path, relative_path, 0)
                    del file_states[file_path]
                    
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
    
    def _record_event(self, event_type: str, file_path: str, relative_path: str, file_size: int):
        """Record a monitoring event."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO events (event_type, file_path, relative_path, timestamp, file_size)
                    VALUES (?, ?, ?, ?, ?)
                """, (event_type, file_path, relative_path, datetime.now().isoformat(), file_size))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to record event: {e}")


# ============================================================================
# Concrete Backup Manager Implementation
# ============================================================================

class StandardBackupManager(BackupManager):
    """Standard backup manager implementation."""
    
    async def create_backup(self, backup_config: BackupOperation) -> FileOperationResult:
        """Create a backup according to configuration."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{timestamp}"
            
            if backup_config.backup_type == "full":
                backup_path = os.path.join(backup_config.destination_path, backup_name)
                os.makedirs(backup_path, exist_ok=True)
                
                total_bytes = 0
                total_files = 0
                
                for source_path in backup_config.source_paths:
                    if os.path.isfile(source_path):
                        dest_file = os.path.join(backup_path, os.path.basename(source_path))
                        shutil.copy2(source_path, dest_file)
                        total_bytes += os.path.getsize(source_path)
                        total_files += 1
                    elif os.path.isdir(source_path):
                        dest_dir = os.path.join(backup_path, os.path.basename(source_path))
                        shutil.copytree(source_path, dest_dir)
                        for root, dirs, files in os.walk(dest_dir):
                            for file in files:
                                total_bytes += os.path.getsize(os.path.join(root, file))
                                total_files += 1
                
                # Create backup metadata
                metadata = {
                    'backup_type': backup_config.backup_type,
                    'timestamp': timestamp,
                    'source_paths': backup_config.source_paths,
                    'total_bytes': total_bytes,
                    'total_files': total_files
                }
                
                metadata_path = os.path.join(backup_path, 'backup_metadata.json')
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                return FileOperationResult(
                    success=True,
                    operation="backup",
                    source_path=str(backup_config.source_paths),
                    destination_path=backup_path,
                    message=f"Full backup created successfully: {backup_path}",
                    bytes_processed=total_bytes,
                    files_processed=total_files
                )
            
            else:
                return FileOperationResult(
                    success=False,
                    operation="backup",
                    source_path=str(backup_config.source_paths),
                    message=f"Backup type '{backup_config.backup_type}' not implemented",
                    error_details="UNSUPPORTED_BACKUP_TYPE"
                )
                
        except Exception as e:
            return FileOperationResult(
                success=False,
                operation="backup",
                source_path=str(backup_config.source_paths),
                destination_path=backup_config.destination_path,
                message=f"Backup failed: {str(e)}",
                error_details=str(e)
            )
    
    async def restore_backup(self, backup_path: str, restore_path: str) -> FileOperationResult:
        """Restore from backup."""
        try:
            if not os.path.exists(backup_path):
                return FileOperationResult(
                    success=False,
                    operation="restore",
                    source_path=backup_path,
                    message=f"Backup path does not exist: {backup_path}",
                    error_details="BACKUP_NOT_FOUND"
                )
            
            # Read backup metadata
            metadata_path = os.path.join(backup_path, 'backup_metadata.json')
            metadata = {}
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            
            os.makedirs(restore_path, exist_ok=True)
            total_bytes = 0
            total_files = 0
            
            for item in os.listdir(backup_path):
                if item == 'backup_metadata.json':
                    continue
                
                source = os.path.join(backup_path, item)
                dest = os.path.join(restore_path, item)
                
                if os.path.isfile(source):
                    shutil.copy2(source, dest)
                    total_bytes += os.path.getsize(source)
                    total_files += 1
                elif os.path.isdir(source):
                    shutil.copytree(source, dest, dirs_exist_ok=True)
                    for root, dirs, files in os.walk(dest):
                        for file in files:
                            total_bytes += os.path.getsize(os.path.join(root, file))
                            total_files += 1
            
            return FileOperationResult(
                success=True,
                operation="restore",
                source_path=backup_path,
                destination_path=restore_path,
                message=f"Backup restored successfully to: {restore_path}",
                bytes_processed=total_bytes,
                files_processed=total_files
            )
            
        except Exception as e:
            return FileOperationResult(
                success=False,
                operation="restore",
                source_path=backup_path,
                destination_path=restore_path,
                message=f"Restore failed: {str(e)}",
                error_details=str(e)
            )
    
    async def list_backups(self, backup_dir: str) -> List[Dict[str, Any]]:
        """List available backups."""
        try:
            backups = []
            
            if not os.path.exists(backup_dir):
                return backups
            
            for item in os.listdir(backup_dir):
                item_path = os.path.join(backup_dir, item)
                if os.path.isdir(item_path) and item.startswith('backup_'):
                    metadata_path = os.path.join(item_path, 'backup_metadata.json')
                    
                    backup_info = {
                        'name': item,
                        'path': item_path,
                        'created': datetime.fromtimestamp(os.path.getctime(item_path)).isoformat(),
                        'size': self._get_directory_size(item_path)
                    }
                    
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                                backup_info.update(metadata)
                        except:
                            pass
                    
                    backups.append(backup_info)
            
            return sorted(backups, key=lambda x: x['created'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []
    
    def _get_directory_size(self, directory: str) -> int:
        """Calculate total size of directory."""
        total_size = 0
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
        except:
            pass
        return total_size


# ============================================================================
# Concrete Cleanup Manager Implementation
# ============================================================================

class StandardCleanupManager(CleanupManager):
    """Standard cleanup manager implementation."""
    
    async def cleanup_files(self, cleanup_config: CleanupOperation) -> FileOperationResult:
        """Perform cleanup according to configuration."""
        try:
            total_bytes = 0
            total_files = 0
            cleaned_files = []
            
            cutoff_date = datetime.now() - timedelta(days=cleanup_config.age_threshold)
            
            for target_path in cleanup_config.target_paths:
                if not os.path.exists(target_path):
                    continue
                
                files_to_clean = self._find_cleanup_candidates(
                    target_path, cleanup_config, cutoff_date
                )
                
                for file_path in files_to_clean:
                    try:
                        if cleanup_config.dry_run:
                            file_size = os.path.getsize(file_path)
                            cleaned_files.append(file_path)
                            total_bytes += file_size
                            total_files += 1
                        else:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            cleaned_files.append(file_path)
                            total_bytes += file_size
                            total_files += 1
                            
                    except Exception as e:
                        logger.warning(f"Failed to clean file {file_path}: {e}")
                        continue
            
            operation_type = "cleanup_dry_run" if cleanup_config.dry_run else "cleanup"
            
            return FileOperationResult(
                success=True,
                operation=operation_type,
                source_path=str(cleanup_config.target_paths),
                message=f"Cleanup completed: {total_files} files, {total_bytes} bytes",
                bytes_processed=total_bytes,
                files_processed=total_files
            )
            
        except Exception as e:
            return FileOperationResult(
                success=False,
                operation="cleanup",
                source_path=str(cleanup_config.target_paths),
                message=f"Cleanup failed: {str(e)}",
                error_details=str(e)
            )
    
    async def analyze_cleanup(self, cleanup_config: CleanupOperation) -> Dict[str, Any]:
        """Analyze what would be cleaned without actually doing it."""
        try:
            analysis = {
                'total_files': 0,
                'total_bytes': 0,
                'file_types': {},
                'directories': {},
                'age_distribution': {
                    '1_day': 0,
                    '1_week': 0,
                    '1_month': 0,
                    '1_year': 0,
                    'older': 0
                }
            }
            
            cutoff_date = datetime.now() - timedelta(days=cleanup_config.age_threshold)
            now = datetime.now()
            
            for target_path in cleanup_config.target_paths:
                if not os.path.exists(target_path):
                    continue
                
                files_to_clean = self._find_cleanup_candidates(
                    target_path, cleanup_config, cutoff_date
                )
                
                for file_path in files_to_clean:
                    try:
                        stat = os.stat(file_path)
                        file_size = stat.st_size
                        file_ext = os.path.splitext(file_path)[1].lower()
                        file_dir = os.path.dirname(file_path)
                        file_age = now - datetime.fromtimestamp(stat.st_mtime)
                        
                        analysis['total_files'] += 1
                        analysis['total_bytes'] += file_size
                        
                        # File type distribution
                        if file_ext in analysis['file_types']:
                            analysis['file_types'][file_ext]['count'] += 1
                            analysis['file_types'][file_ext]['size'] += file_size
                        else:
                            analysis['file_types'][file_ext] = {'count': 1, 'size': file_size}
                        
                        # Directory distribution
                        if file_dir in analysis['directories']:
                            analysis['directories'][file_dir]['count'] += 1
                            analysis['directories'][file_dir]['size'] += file_size
                        else:
                            analysis['directories'][file_dir] = {'count': 1, 'size': file_size}
                        
                        # Age distribution
                        if file_age.days <= 1:
                            analysis['age_distribution']['1_day'] += 1
                        elif file_age.days <= 7:
                            analysis['age_distribution']['1_week'] += 1
                        elif file_age.days <= 30:
                            analysis['age_distribution']['1_month'] += 1
                        elif file_age.days <= 365:
                            analysis['age_distribution']['1_year'] += 1
                        else:
                            analysis['age_distribution']['older'] += 1
                            
                    except Exception as e:
                        logger.warning(f"Failed to analyze file {file_path}: {e}")
                        continue
            
            return analysis
            
        except Exception as e:
            logger.error(f"Cleanup analysis failed: {e}")
            return {'error': str(e)}
    
    def _find_cleanup_candidates(self, target_path: str, cleanup_config: CleanupOperation, 
                                cutoff_date: datetime) -> List[str]:
        """Find files that match cleanup criteria."""
        candidates = []
        
        try:
            if os.path.isfile(target_path):
                if self._should_clean_file(target_path, cleanup_config, cutoff_date):
                    candidates.append(target_path)
            elif os.path.isdir(target_path):
                for root, dirs, files in os.walk(target_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if self._should_clean_file(file_path, cleanup_config, cutoff_date):
                            candidates.append(file_path)
        except Exception as e:
            logger.error(f"Error finding cleanup candidates in {target_path}: {e}")
        
        return candidates
    
    def _should_clean_file(self, file_path: str, cleanup_config: CleanupOperation, 
                          cutoff_date: datetime) -> bool:
        """Check if a file should be cleaned."""
        try:
            stat = os.stat(file_path)
            file_modified = datetime.fromtimestamp(stat.st_mtime)
            
            # Check age threshold
            if file_modified > cutoff_date:
                return False
            
            # Check size threshold
            if cleanup_config.size_threshold > 0 and stat.st_size < cleanup_config.size_threshold:
                return False
            
            # Check pattern filters
            if cleanup_config.pattern_filters:
                file_name = os.path.basename(file_path)
                match_patterns = False
                for pattern in cleanup_config.pattern_filters:
                    import fnmatch
                    if fnmatch.fnmatch(file_name, pattern):
                        match_patterns = True
                        break
                if not match_patterns:
                    return False
            
            return True
            
        except Exception:
            return False


# ============================================================================
# Concrete Event Logger Implementation
# ============================================================================

class SQLiteEventLogger(EventLogger):
    """SQLite-based event logger."""
    
    def __init__(self, db_path: str = "./system_events.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the events database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT NOT NULL,
                    source TEXT,
                    severity TEXT DEFAULT 'INFO'
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_timestamp ON system_events(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_type ON system_events(event_type)
            """)
            conn.commit()
    
    async def log_event(self, event_type: str, details: Dict[str, Any]) -> bool:
        """Log a system event."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO system_events (event_type, timestamp, details, source, severity)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    event_type,
                    datetime.now().isoformat(),
                    json.dumps(details),
                    details.get('source', 'system'),
                    details.get('severity', 'INFO')
                ))
                conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
            return False
    
    async def get_events(self, event_type: Optional[str] = None, 
                        since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Retrieve logged events."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM system_events WHERE 1=1"
                params = []
                
                if event_type:
                    query += " AND event_type = ?"
                    params.append(event_type)
                
                if since:
                    query += " AND timestamp > ?"
                    params.append(since.isoformat())
                
                query += " ORDER BY timestamp DESC LIMIT 1000"
                
                cursor.execute(query, params)
                
                events = []
                for row in cursor.fetchall():
                    event = {
                        'id': row[0],
                        'event_type': row[1],
                        'timestamp': row[2],
                        'details': json.loads(row[3]),
                        'source': row[4],
                        'severity': row[5]
                    }
                    events.append(event)
                
                return events
                
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            return []


# ============================================================================
# Main Generic System Processor
# ============================================================================

class GenericSystemProcessor:
    """Universal system processor supporting file operations, monitoring, backup, cleanup, and logging."""
    
    def __init__(self):
        # Registry of system managers
        self.file_manager = StandardFileManager()
        self.monitor = FileSystemMonitor()
        self.backup_manager = StandardBackupManager()
        self.cleanup_manager = StandardCleanupManager()
        self.event_logger = SQLiteEventLogger()
        
        # Background tasks
        self.background_tasks = []
        self.scheduler_thread = None
        self.scheduler_running = False
    
    async def process(self, context) -> Dict[str, Any]:
        """Main processing method."""
        logger.info("[GenericSystemProcessor] INGRESSO nodo: process")
        
        try:
            config = context.get('config', {})
            inputs = context.get('inputs', {})
            
            operation = config.get('operation', 'file_operation')
            
            if operation == 'file_operation':
                return await self._process_file_operation(inputs, config)
            elif operation == 'monitor':
                return await self._process_monitoring(inputs, config)
            elif operation == 'backup':
                return await self._process_backup(inputs, config)
            elif operation == 'cleanup':
                return await self._process_cleanup(inputs, config)
            elif operation == 'logging':
                return await self._process_logging(inputs, config)
            elif operation == 'schedule':
                return await self._process_scheduling(inputs, config)
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            logger.error(f"[GenericSystemProcessor] USCITA nodo (errore): {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "operation": config.get('operation', 'unknown'),
                "output": None
            }
    
    async def _process_file_operation(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process file operations."""
        file_operation = config.get('file_operation', 'copy')
        source_path = inputs.get('source_path', inputs.get('file_path'))
        destination_path = inputs.get('destination_path', inputs.get('archive_dir'))
        
        if not source_path:
            raise ValueError("No source path provided for file operation")
        
        operation_config = config.get('file_config', {})
        
        if file_operation == 'copy':
            if not destination_path:
                raise ValueError("No destination path provided for copy operation")
            result = await self.file_manager.copy_file(source_path, destination_path, **operation_config)
        
        elif file_operation == 'move':
            if not destination_path:
                raise ValueError("No destination path provided for move operation")
            result = await self.file_manager.move_file(source_path, destination_path, **operation_config)
        
        elif file_operation == 'delete':
            result = await self.file_manager.delete_file(source_path, **operation_config)
        
        elif file_operation == 'archive':
            if not destination_path:
                raise ValueError("No archive directory provided for archive operation")
            result = await self.file_manager.archive_file(source_path, destination_path, **operation_config)
        
        else:
            raise ValueError(f"Unsupported file operation: {file_operation}")
        
        # Log the operation
        await self.event_logger.log_event('file_operation', {
            'operation': file_operation,
            'source': source_path,
            'destination': destination_path,
            'success': result.success,
            'message': result.message
        })
        
        logger.info(f"[GenericSystemProcessor] USCITA file_operation (successo): {file_operation} completed")
        return {
            "status": "success",
            "operation": "file_operation",
            "output": {
                "result": asdict(result),
                "file_operation": file_operation,
                "source_path": source_path,
                "destination_path": destination_path
            }
        }
    
    async def _process_monitoring(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process monitoring operations."""
        monitor_operation = config.get('monitor_operation', 'start')
        
        if monitor_operation == 'start':
            paths = inputs.get('paths', inputs.get('watch_paths', []))
            if not paths:
                raise ValueError("No paths provided for monitoring")
            
            monitor_config = config.get('monitor_config', {})
            success = await self.monitor.start_monitoring(paths, **monitor_config)
            
            return {
                "status": "success",
                "operation": "monitor",
                "output": {
                    "monitor_operation": "start",
                    "success": success,
                    "watched_paths": paths,
                    "message": "Monitoring started successfully" if success else "Failed to start monitoring"
                }
            }
        
        elif monitor_operation == 'stop':
            success = await self.monitor.stop_monitoring()
            
            return {
                "status": "success", 
                "operation": "monitor",
                "output": {
                    "monitor_operation": "stop",
                    "success": success,
                    "message": "Monitoring stopped successfully" if success else "Failed to stop monitoring"
                }
            }
        
        elif monitor_operation == 'get_events':
            since_str = inputs.get('since')
            since = datetime.fromisoformat(since_str) if since_str else None
            events = await self.monitor.get_events(since)
            
            return {
                "status": "success",
                "operation": "monitor",
                "output": {
                    "monitor_operation": "get_events",
                    "events": [asdict(event) for event in events],
                    "event_count": len(events)
                }
            }
        
        else:
            raise ValueError(f"Unsupported monitor operation: {monitor_operation}")
    
    async def _process_backup(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process backup operations."""
        backup_operation = config.get('backup_operation', 'create')
        
        if backup_operation == 'create':
            backup_config_data = {
                'source_paths': inputs.get('source_paths', []),
                'destination_path': inputs.get('destination_path', ''),
                'backup_type': config.get('backup_type', 'full'),
                'compression': config.get('compression', False),
                'encryption': config.get('encryption', False),
                'retention_days': config.get('retention_days', 30),
                'exclude_patterns': config.get('exclude_patterns', [])
            }
            
            backup_config = BackupOperation(**backup_config_data)
            result = await self.backup_manager.create_backup(backup_config)
            
            return {
                "status": "success",
                "operation": "backup",
                "output": {
                    "backup_operation": "create",
                    "result": asdict(result),
                    "backup_config": asdict(backup_config)
                }
            }
        
        elif backup_operation == 'restore':
            backup_path = inputs.get('backup_path', '')
            restore_path = inputs.get('restore_path', '')
            
            if not backup_path or not restore_path:
                raise ValueError("Both backup_path and restore_path are required for restore operation")
            
            result = await self.backup_manager.restore_backup(backup_path, restore_path)
            
            return {
                "status": "success",
                "operation": "backup",
                "output": {
                    "backup_operation": "restore",
                    "result": asdict(result),
                    "backup_path": backup_path,
                    "restore_path": restore_path
                }
            }
        
        elif backup_operation == 'list':
            backup_dir = inputs.get('backup_dir', '')
            if not backup_dir:
                raise ValueError("backup_dir is required for list operation")
            
            backups = await self.backup_manager.list_backups(backup_dir)
            
            return {
                "status": "success",
                "operation": "backup",
                "output": {
                    "backup_operation": "list",
                    "backups": backups,
                    "backup_count": len(backups)
                }
            }
        
        else:
            raise ValueError(f"Unsupported backup operation: {backup_operation}")
    
    async def _process_cleanup(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process cleanup operations."""
        cleanup_operation = config.get('cleanup_operation', 'analyze')
        
        cleanup_config_data = {
            'target_paths': inputs.get('target_paths', []),
            'cleanup_type': config.get('cleanup_type', 'files'),
            'age_threshold': config.get('age_threshold', 7),
            'size_threshold': config.get('size_threshold', 0),
            'pattern_filters': config.get('pattern_filters', []),
            'dry_run': config.get('dry_run', True)
        }
        
        cleanup_config = CleanupOperation(**cleanup_config_data)
        
        if cleanup_operation == 'analyze':
            analysis = await self.cleanup_manager.analyze_cleanup(cleanup_config)
            
            return {
                "status": "success",
                "operation": "cleanup",
                "output": {
                    "cleanup_operation": "analyze",
                    "analysis": analysis,
                    "cleanup_config": asdict(cleanup_config)
                }
            }
        
        elif cleanup_operation == 'execute':
            result = await self.cleanup_manager.cleanup_files(cleanup_config)
            
            return {
                "status": "success",
                "operation": "cleanup",
                "output": {
                    "cleanup_operation": "execute",
                    "result": asdict(result),
                    "cleanup_config": asdict(cleanup_config)
                }
            }
        
        else:
            raise ValueError(f"Unsupported cleanup operation: {cleanup_operation}")
    
    async def _process_logging(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process logging operations."""
        logging_operation = config.get('logging_operation', 'log')
        
        if logging_operation == 'log':
            event_type = inputs.get('event_type', 'system_event')
            details = inputs.get('details', inputs.get('event_data', {}))
            
            success = await self.event_logger.log_event(event_type, details)
            
            return {
                "status": "success",
                "operation": "logging",
                "output": {
                    "logging_operation": "log",
                    "success": success,
                    "event_type": event_type,
                    "details": details
                }
            }
        
        elif logging_operation == 'get':
            event_type = inputs.get('event_type')
            since_str = inputs.get('since')
            since = datetime.fromisoformat(since_str) if since_str else None
            
            events = await self.event_logger.get_events(event_type, since)
            
            return {
                "status": "success",
                "operation": "logging",
                "output": {
                    "logging_operation": "get",
                    "events": events,
                    "event_count": len(events),
                    "event_type_filter": event_type
                }
            }
        
        else:
            raise ValueError(f"Unsupported logging operation: {logging_operation}")
    
    async def _process_scheduling(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process scheduling operations."""
        schedule_operation = config.get('schedule_operation', 'add')
        
        if schedule_operation == 'add':
            task_name = inputs.get('task_name', f"task_{int(time.time())}")
            schedule_config = inputs.get('schedule_config', {})
            task_config = inputs.get('task_config', {})
            
            # This would implement task scheduling
            # For now, return a placeholder
            return {
                "status": "success",
                "operation": "schedule",
                "output": {
                    "schedule_operation": "add",
                    "task_name": task_name,
                    "message": "Task scheduling not yet implemented",
                    "scheduled": False
                }
            }
        
        else:
            raise ValueError(f"Unsupported schedule operation: {schedule_operation}")


# Funzione entry point per il PDK
async def process_node(context):
    """Entry point per il Generic System Processor."""
    processor = GenericSystemProcessor()
    return await processor.process(context)