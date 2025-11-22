"""
Modulo di logging standardizzato per plugin Python del PDK.
Fornisce un'interfaccia unificata per il logging, garantendo l'utilizzo del LogService.
"""

import os
import logging
import sys
import importlib.util
import uuid
from typing import Dict, Any, Optional, Union, cast

# Configura un logger fallback in caso di problemi
logging.basicConfig(level=logging.INFO)
_fallback_logger = logging.getLogger("pdk-plugin-fallback")
_handler = logging.StreamHandler(sys.stdout)
_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_handler.setFormatter(_formatter)
_fallback_logger.addHandler(_handler)
_fallback_logger.setLevel(logging.INFO)

# Definizioni statiche per evitare import problematici
class LogLevel:
    """Livelli di log supportati."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    LIFECYCLE = "lifecycle"

class LogProject:
    """Progetti PramaIA supportati."""
    SERVER = "PramaIAServer"
    PDK = "PramaIA-PDK"
    AGENTS = "PramaIA-Agents"
    PLUGINS = "PramaIA-Plugins"
    OTHER = "other"

# Cache delle configurazioni e stati
_default_plugin_name = "unknown_plugin"
_pramaialog_instance = None
_pramaialog_module = None
_plugin_name_cache = None
_module_name_cache = None

def _get_pramaialog_module():
    """
    Tenta di importare il modulo pramaialog con diversi approcci.
    
    Returns:
        Modulo pramaialog o None
    """
    global _pramaialog_module
    
    if _pramaialog_module:
        return _pramaialog_module
    
    # Metodo 1: Prova a caricare dalla stessa directory (common)
    try:
        module_path = os.path.join(os.path.dirname(__file__), "pramaialog.py")
        if os.path.exists(module_path):
            _fallback_logger.info(f"Caricamento pramaialog da: {module_path}")
            spec = importlib.util.spec_from_file_location("pramaialog", module_path)
            if spec and spec.loader:
                _pramaialog_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(_pramaialog_module)
                _fallback_logger.info("✅ Modulo pramaialog caricato dalla directory common")
                return _pramaialog_module
    except Exception as e:
        _fallback_logger.debug(f"Caricamento da common fallito: {str(e)}")
    
    try:
        # Metodo 2: Import diretto se installato
        import PramaIA_LogService.clients.pramaialog as _pramaialog_module
        _fallback_logger.info("Modulo pramaialog importato dal package PramaIA_LogService")
        return _pramaialog_module
    except ImportError:
        _fallback_logger.debug("Import da PramaIA_LogService fallito, provo percorsi alternativi")
        
    try:
        # Metodo 3: Import diretto del modulo
        import pramaialog as _pramaialog_module
        _fallback_logger.info("Modulo pramaialog importato direttamente")
        return _pramaialog_module
    except ImportError:
        _fallback_logger.debug("Import diretto fallito, provo percorsi relativi")
        
    # Metodo 3: Cerca nei percorsi relativi
    search_paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../PramaIA-LogService/clients/python")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../PramaIA-LogService/clients/python")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../clients/python")),
    ]
    
    for path in search_paths:
        module_path = os.path.join(path, "pramaialog.py")
        if os.path.exists(module_path):
            _fallback_logger.info(f"Modulo pramaialog trovato in: {module_path}")
            try:
                spec = importlib.util.spec_from_file_location("pramaialog", module_path)
                if spec and spec.loader:
                    _pramaialog_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(_pramaialog_module)
                    return _pramaialog_module
            except Exception as e:
                _fallback_logger.error(f"Errore durante il caricamento del modulo da {module_path}: {str(e)}")
    
    _fallback_logger.warning("Impossibile trovare o importare il modulo pramaialog")
    return None

def _create_dummy_logger(plugin_name: str, module_name: Optional[str] = None):
    """
    Crea un logger dummy per quando PramaIALogger non è disponibile.
    
    Args:
        plugin_name: Nome del plugin
        module_name: Nome del modulo specifico
        
    Returns:
        Un oggetto che emula PramaIALogger ma usa il logging standard
    """
    logger_name = f"pdk.plugin.{plugin_name}" + (f".{module_name}" if module_name else "")
    logger = logging.getLogger(logger_name)
    
    class DummyLogger:
        def debug(self, message, details=None, context=None):
            details_str = f" {details}" if details else ""
            logger.debug(f"{message}{details_str}")
        
        def info(self, message, details=None, context=None):
            details_str = f" {details}" if details else ""
            logger.info(f"{message}{details_str}")
        
        def warning(self, message, details=None, context=None):
            details_str = f" {details}" if details else ""
            logger.warning(f"{message}{details_str}")
        
        def error(self, message, details=None, context=None):
            details_str = f" {details}" if details else ""
            logger.error(f"{message}{details_str}")
        
        def critical(self, message, details=None, context=None):
            details_str = f" {details}" if details else ""
            logger.critical(f"{message}{details_str}")
        
        def lifecycle(self, message, details=None, context=None):
            details_str = f" {details}" if details else ""
            logger.info(f"[LIFECYCLE] {message}{details_str}")
        
        def flush(self):
            for handler in logger.handlers:
                handler.flush()
        
        def close(self):
            for handler in logger.handlers:
                handler.close()
    
    return DummyLogger()

def _get_logger(plugin_name: Optional[str] = None, module_name: Optional[str] = None) -> Any:
    """
    Ottiene un'istanza del logger PramaIA o un dummy logger.
    
    Args:
        plugin_name: Nome del plugin
        module_name: Nome del modulo specifico
        
    Returns:
        Istanza di PramaIALogger o DummyLogger
    """
    global _pramaialog_instance, _plugin_name_cache, _module_name_cache
    
    # Usa i valori memorizzati nella cache se non specificati
    plugin_name = plugin_name or _plugin_name_cache or _default_plugin_name
    if plugin_name:
        _plugin_name_cache = plugin_name
        
    if module_name:
        _module_name_cache = module_name
    
    # Se abbiamo già un'istanza, restituiscila
    if _pramaialog_instance:
        return _pramaialog_instance
    
    # Ottieni il modulo pramaialog
    pramaialog_mod = _get_pramaialog_module()
    
    if pramaialog_mod:
        try:
            # Risolvi host e porta dalle variabili d'ambiente
            host = os.getenv('PRAMAIALOG_HOST') or os.getenv('LOGSERVICE_URL') or 'http://localhost:8081'
            port_env = os.getenv('PRAMAIALOG_PORT')
            if port_env and ':' not in host.split('//')[-1]:
                host = f"{host.rstrip('/')}:{port_env}"
            
            # Utilizza l'API key dalle variabili d'ambiente o un default per il PDK
            api_key = os.getenv('PRAMAIALOG_API_KEY') or os.getenv('LOGSERVICE_API_KEY') or 'pramaialog_o6hlpft585hkykgb'
            
            # Ottieni riferimento alla classe PramaIALogger
            PramaIALogger = getattr(pramaialog_mod, 'PramaIALogger')
            
            # Ottieni riferimento alla classe LogProject o usa valore statico
            try:
                project_enum = getattr(pramaialog_mod, 'LogProject')
                project = project_enum.PDK
            except AttributeError:
                project = LogProject.PDK
            
            # Crea l'istanza del logger
            _pramaialog_instance = PramaIALogger(
                api_key=api_key,
                project=project,
                module=f"plugin.{plugin_name}" + (f".{module_name}" if module_name else ""),
                host=host
            )
            
            _fallback_logger.info(f"Logger PramaIA inizializzato con successo per {plugin_name}")
            return _pramaialog_instance
            
        except Exception as e:
            _fallback_logger.error(f"Errore durante l'inizializzazione di PramaIALogger: {str(e)}")
    
    # Fallback: crea un dummy logger
    _pramaialog_instance = _create_dummy_logger(plugin_name, module_name)
    return _pramaialog_instance

def debug(message: str, details: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None, plugin_name: Optional[str] = None, module_name: Optional[str] = None) -> None:
    """Log di livello DEBUG."""
    logger = _get_logger(plugin_name, module_name)
    try:
        logger.debug(message, details=details, context=context)
    except Exception as e:
        _fallback_logger.error(f"Errore durante il logging debug: {str(e)}")
        _fallback_logger.debug(f"{message} {details if details else ''}")

def info(message: str, details: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None, plugin_name: Optional[str] = None, module_name: Optional[str] = None) -> None:
    """Log di livello INFO."""
    logger = _get_logger(plugin_name, module_name)
    try:
        logger.info(message, details=details, context=context)
    except Exception as e:
        _fallback_logger.error(f"Errore durante il logging info: {str(e)}")
        _fallback_logger.info(f"{message} {details if details else ''}")

def warning(message: str, details: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None, plugin_name: Optional[str] = None, module_name: Optional[str] = None) -> None:
    """Log di livello WARNING."""
    logger = _get_logger(plugin_name, module_name)
    try:
        logger.warning(message, details=details, context=context)
    except Exception as e:
        _fallback_logger.error(f"Errore durante il logging warning: {str(e)}")
        _fallback_logger.warning(f"{message} {details if details else ''}")

def error(message: str, details: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None, plugin_name: Optional[str] = None, module_name: Optional[str] = None) -> None:
    """Log di livello ERROR."""
    logger = _get_logger(plugin_name, module_name)
    try:
        logger.error(message, details=details, context=context)
    except Exception as e:
        _fallback_logger.error(f"Errore durante il logging error: {str(e)}")
        _fallback_logger.error(f"{message} {details if details else ''}")

def critical(message: str, details: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None, plugin_name: Optional[str] = None, module_name: Optional[str] = None) -> None:
    """Log di livello CRITICAL."""
    logger = _get_logger(plugin_name, module_name)
    try:
        logger.critical(message, details=details, context=context)
    except Exception as e:
        _fallback_logger.error(f"Errore durante il logging critical: {str(e)}")
        _fallback_logger.critical(f"{message} {details if details else ''}")

def lifecycle(message: str, details: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None, plugin_name: Optional[str] = None, module_name: Optional[str] = None) -> None:
    """Log di livello LIFECYCLE (speciale per tracciare il ciclo di vita dei documenti)."""
    logger = _get_logger(plugin_name, module_name)
    try:
        logger.lifecycle(message, details=details, context=context)
    except Exception as e:
        _fallback_logger.error(f"Errore durante il lifecycle logging: {str(e)}")
        _fallback_logger.info(f"[LIFECYCLE] {message} {details if details else ''}")

def flush() -> None:
    """Forza l'invio di tutti i log in attesa."""
    logger = _get_logger()
    try:
        logger.flush()
    except Exception as e:
        _fallback_logger.error(f"Errore durante il flush dei log: {str(e)}")

def close() -> None:
    """Chiude il logger, flushando tutti i log in attesa."""
    logger = _get_logger()
    try:
        logger.flush()
        logger.close()
    except Exception as e:
        _fallback_logger.error(f"Errore durante la chiusura del logger: {str(e)}")

def init(plugin_name: str, module_name: Optional[str] = None) -> Any:
    """
    Inizializza esplicitamente il logger per un plugin specifico.
    
    Args:
        plugin_name: Nome del plugin
        module_name: Nome del modulo specifico all'interno del plugin (opzionale)
        
    Returns:
        L'istanza del logger
    """
    global _pramaialog_instance
    # Forza la reinizializzazione
    _pramaialog_instance = None
    return _get_logger(plugin_name, module_name)

# Alias per compatibilità con nomi diversi usati nei vecchi plugin
log_debug = debug
log_info = info
log_warning = warning
log_error = error
log_flush = flush
log_close = close