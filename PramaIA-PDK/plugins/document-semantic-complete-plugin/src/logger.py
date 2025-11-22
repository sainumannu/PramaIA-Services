"""
Logger per Document Semantic Complete Plugin
Utilizza il modulo di logging standardizzato per i plugin PDK.
"""

import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Tenta di importare il modulo di logging standardizzato
try:
    # Aggiungi la cartella common alla path
    plugin_common_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../common"))
    if os.path.exists(plugin_common_path):
        sys.path.append(plugin_common_path)
        
    # Importa il modulo logger.py
    import logger as common_logger
    
    # Inizializza il logger con il nome del plugin
    common_logger.init("document-semantic-complete")
    
    # Funzioni esposte
    debug = lambda message, details=None, context=None: common_logger.debug(
        message, details=details, context=context, plugin_name="document-semantic-complete"
    )
    
    info = lambda message, details=None, context=None: common_logger.info(
        message, details=details, context=context, plugin_name="document-semantic-complete"
    )
    
    warning = lambda message, details=None, context=None: common_logger.warning(
        message, details=details, context=context, plugin_name="document-semantic-complete"
    )
    
    error = lambda message, details=None, context=None: common_logger.error(
        message, details=details, context=context, plugin_name="document-semantic-complete"
    )
    
    # Aggiungiamo anche il supporto per lifecycle e critical
    lifecycle = lambda message, details=None, context=None: common_logger.lifecycle(
        message, details=details, context=context, plugin_name="document-semantic-complete"
    )
    
    critical = lambda message, details=None, context=None: common_logger.critical(
        message, details=details, context=context, plugin_name="document-semantic-complete"
    )
    
    # Funzioni di utilità
    flush = common_logger.flush
    close = common_logger.close
    
    # Log di inizializzazione
    info("Logger standardizzato inizializzato per document-semantic-complete plugin")
    
except Exception as e:
    # Fallback al logger originale se non è possibile importare il modulo standardizzato
    import logging
    
    _logger = logging.getLogger("document-semantic-plugin")
    _handler = logging.StreamHandler(sys.stdout)
    _formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    _handler.setFormatter(_formatter)
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)
    
    # Registra l'errore di importazione
    _logger.error(f"Impossibile importare il modulo di logging standardizzato: {str(e)}")
    
    # Utility per formattare dettagli come JSON
    def _format_details(details: Optional[Dict[str, Any]] = None) -> str:
        if details:
            import json
            try:
                return json.dumps(details)
            except Exception:
                return str(details)
        return ""
    
    # Reimplementazione delle funzioni originali
    def debug(message: str, details: Optional[Dict[str, Any]] = None, context=None) -> None:
        """Log livello debug"""
        _logger.debug(f"{message} {_format_details(details)}")
    
    def info(message: str, details: Optional[Dict[str, Any]] = None, context=None) -> None:
        """Log livello info"""
        _logger.info(f"{message} {_format_details(details)}")
    
    def warning(message: str, details: Optional[Dict[str, Any]] = None, context=None) -> None:
        """Log livello warning"""
        _logger.warning(f"{message} {_format_details(details)}")
    
    def error(message: str, details: Optional[Dict[str, Any]] = None, context=None) -> None:
        """Log livello error"""
        _logger.error(f"{message} {_format_details(details)}")
    
    def critical(message: str, details: Optional[Dict[str, Any]] = None, context=None) -> None:
        """Log livello critical"""
        _logger.critical(f"{message} {_format_details(details)}")
    
    def lifecycle(message: str, details: Optional[Dict[str, Any]] = None, context=None) -> None:
        """Log livello lifecycle"""
        _logger.info(f"[LIFECYCLE] {message} {_format_details(details)}")
    
    def flush() -> None:
        """Esegue il flush dei log"""
        for handler in _logger.handlers:
            handler.flush()
    
    def close() -> None:
        """Chiude gli handler del logger"""
        for handler in _logger.handlers:
            handler.close()