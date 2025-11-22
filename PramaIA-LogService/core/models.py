"""
Modelli di dati per il servizio di logging.
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

class LogLevel(str, Enum):
    """Livelli di log supportati."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    LIFECYCLE = "lifecycle"  # Livello speciale per tracciare il ciclo di vita dei documenti

class LogProject(str, Enum):
    """Progetti PramaIA supportati."""
    SERVER = "PramaIAServer"
    PDK = "PramaIA-PDK"
    AGENTS = "PramaIA-Agents"
    PLUGINS = "PramaIA-Plugins"
    OTHER = "other"

class LogEntry(BaseModel):
    """
    Modello per una voce di log.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    project: LogProject
    level: LogLevel
    module: str
    message: str
    details: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "project": "PramaIAServer",
                "level": "error",
                "module": "workflow_triggers_router",
                "message": "Errore durante il caricamento dei trigger",
                "details": {
                    "workflow_id": "123456",
                    "error_type": "DatabaseError",
                    "exception": "Unable to connect to database"
                },
                "context": {
                    "user_id": "admin",
                    "request_id": "abcdef123456",
                    "ip_address": "192.168.1.100"
                }
            }
        }

class LogFilter(BaseModel):
    """
    Modello per filtrare i log.
    """
    project: Optional[LogProject] = None
    level: Optional[LogLevel] = None
    module: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    context_filter: Optional[Dict[str, Any]] = None
    
class LogStats(BaseModel):
    """
    Modello per le statistiche dei log.
    """
    total_logs: int
    logs_by_level: Dict[LogLevel, int]
    logs_by_project: Dict[LogProject, int]
    logs_by_module: Dict[str, int]
    time_period: Dict[str, datetime]
