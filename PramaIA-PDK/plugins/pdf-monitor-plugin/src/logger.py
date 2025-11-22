"""
Logger per PDF Monitor Plugin
Utilizza il modulo di logging standardizzato per i plugin PDK.
"""

import sys
import os
from typing import Dict, Any, Optional

# Tenta di importare il modulo di logging standardizzato
try:
    # Aggiungi la cartella common alla path
    plugin_common_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../common"))
    if os.path.exists(plugin_common_path):
        sys.path.append(plugin_common_path)
        
    # Importa il modulo logger.py
    import logger as common_logger
    
    # Inizializza il logger con il nome del plugin
    common_logger.init("pdf-monitor")
    
    # Alias delle funzioni
    debug = lambda message, details=None, context=None: common_logger.debug(
        message, details=details, context=context
    )
    
    info = lambda message, details=None, context=None: common_logger.info(
        message, details=details, context=context
    )
    
    warning = lambda message, details=None, context=None: common_logger.warning(
        message, details=details, context=context
    )
    
    error = lambda message, details=None, context=None: common_logger.error(
        message, details=details, context=context
    )
    
    critical = lambda message, details=None, context=None: common_logger.critical(
        message, details=details, context=context
    )
    
    lifecycle = lambda message, details=None, context=None: common_logger.lifecycle(
        message, details=details, context=context
    )
    
    # Alias per compatibilità con codice esistente
    log_debug = debug
    log_info = info
    log_warning = warning
    log_error = error
    
    # Funzioni di utilità
    flush = common_logger.flush
    close = common_logger.close
    log_flush = flush
    log_close = close
    
    # Log di inizializzazione
    info("Logger standardizzato inizializzato per pdf-monitor plugin")
    
except Exception as e:
    # Fallback al logger standard
    import logging
    
    _logger = logging.getLogger("pdf-monitor-plugin")
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
    
    # Implementazione delle funzioni standard
    def debug(message: str, details: Optional[Dict[str, Any]] = None, context=None) -> None:
        _logger.debug(f"{message} {_format_details(details)}")
    
    def info(message: str, details: Optional[Dict[str, Any]] = None, context=None) -> None:
        _logger.info(f"{message} {_format_details(details)}")
    
    def warning(message: str, details: Optional[Dict[str, Any]] = None, context=None) -> None:
        _logger.warning(f"{message} {_format_details(details)}")
    
    def error(message: str, details: Optional[Dict[str, Any]] = None, context=None) -> None:
        _logger.error(f"{message} {_format_details(details)}")
    
    def critical(message: str, details: Optional[Dict[str, Any]] = None, context=None) -> None:
        _logger.critical(f"{message} {_format_details(details)}")
    
    def lifecycle(message: str, details: Optional[Dict[str, Any]] = None, context=None) -> None:
        _logger.info(f"[LIFECYCLE] {message} {_format_details(details)}")
    
    # Alias per compatibilità
    log_debug = debug
    log_info = info
    log_warning = warning
    log_error = error
    
    # Funzioni di utilità
    def flush() -> None:
        for handler in _logger.handlers:
            handler.flush()
    
    def close() -> None:
        for handler in _logger.handlers:
            handler.close()
            
    log_flush = flush
    log_close = close