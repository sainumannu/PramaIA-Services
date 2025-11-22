"""
Document Monitor Plugin - Main Entry Point
"""

import json
from typing import Dict, Any, Optional

# Importa il logger standardizzato
import sys
import os

try:
    # Prima tenta di importare il modulo locale
    from .logger import debug as log_debug, info as log_info, warning as log_warning, error as log_error
    from .logger import flush as log_flush, close as log_close
except ImportError:
    try:
        # Aggiungi la cartella common alla path
        plugin_common_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../common"))
        if os.path.exists(plugin_common_path):
            sys.path.append(plugin_common_path)
            
        # Importa il modulo logger.py
        import logger
        
        # Alias delle funzioni per mantenere la compatibilità
        log_debug = logger.debug
        log_info = logger.info
        log_warning = logger.warning
        log_error = logger.error
        log_flush = logger.flush
        log_close = logger.close
        
    except ImportError:
        # Fallback al logger standard
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        # Alias per mantenere la compatibilità anche nel fallback
        log_debug = logger.debug
        log_info = logger.info
        log_warning = logger.warning
        log_error = logger.error
        
        def log_flush():
            for handler in logger.handlers:
                handler.flush()
        
        def log_close():
            for handler in logger.handlers:
                handler.close()


class DocumentMonitorPlugin:
    """
    Plugin per il monitoraggio e la gestione di vari tipi di documenti.
    Fornisce nodi per operazioni di gestione metadati, logging eventi,
    parsing di file documento e operazioni su vectorstore.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        log_info("Plugin Document Monitor inizializzato")
    
    async def metadata_manager(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Processore per gestione metadati."""
        try:
            operation_type = inputs.get('operation_type', 'extract')
            document_id = inputs.get('document_id', '')
            metadata = inputs.get('metadata', {})
            
            log_info(f"Metadata Manager: operazione {operation_type} per documento {document_id}")
            
            # Implementazione semplificata
            return {
                "status": "success",
                "operation": operation_type,
                "document_id": document_id,
                "result": metadata
            }
        except Exception as e:
            log_error(f"Errore nel processore Metadata Manager: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def event_logger(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Processore per logging eventi."""
        try:
            event_type = inputs.get('event_type', 'info')
            event_source = inputs.get('event_source', 'document_monitor')
            event_data = inputs.get('event_data', {})
            
            log_info(f"Event Logger: evento {event_type} da {event_source}")
            
            # Implementazione semplificata
            return {
                "status": "success",
                "event_type": event_type,
                "event_id": "event_" + str(hash(str(event_data)))[:8],
                "timestamp": "2025-08-16T12:00:00Z"
            }
        except Exception as e:
            log_error(f"Errore nel processore Event Logger: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def file_parsing(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Processore per parsing di file documento."""
        try:
            # Estrai il file_path (potrebbe essere stringa o dict)
            file_path_input = inputs.get('file_path', '')
            
            # Se file_path è un dict (evento completo), estrai il path effettivo
            if isinstance(file_path_input, dict):
                file_path = file_path_input.get('data', {}).get('file_path', '')
            else:
                file_path = str(file_path_input)
            
            if not file_path:
                return {"status": "error", "error": "File path mancante"}
            
            log_info(f"File Parsing: elaborazione file {inputs}")
            
            # Delega al processore reale
            import file_parsing_processor
            result = await file_parsing_processor.process(inputs, {})
            
            return result
            
        except Exception as e:
            log_error(f"Errore nel processore File Parsing: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def document_processor(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Processore per elaborazione documenti."""
        try:
            document_content = inputs.get('document_content', '')
            processing_options = inputs.get('processing_options', {})
            
            log_info(f"Document Processor: elaborazione documento")
            
            # Implementazione semplificata
            return {
                "status": "success",
                "processed_content": document_content[:100] + "...",
                "processing_stats": {
                    "tokens": len(document_content.split()),
                    "characters": len(document_content)
                }
            }
        except Exception as e:
            log_error(f"Errore nel processore Document Processor: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def vector_store_operations(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Processore per operazioni su vectorstore."""
        try:
            operation_type = inputs.get('operation_type', 'query')
            collection_name = inputs.get('collection_name', 'default')
            
            log_info(f"Vector Store Operations: operazione {operation_type} su collezione {collection_name}")
            
            # Implementazione semplificata
            return {
                "status": "success",
                "operation": operation_type,
                "collection": collection_name,
                "result": {
                    "operation_successful": True,
                    "items_affected": 1
                }
            }
        except Exception as e:
            log_error(f"Errore nel processore Vector Store Operations: {str(e)}")
            return {"status": "error", "error": str(e)}


async def process_node(node_id: str, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Interfaccia principale per processare nodi del plugin"""
    plugin = DocumentMonitorPlugin(config)
    
    if node_id == "metadata_manager":
        return await plugin.metadata_manager(inputs)
    elif node_id == "event_logger":
        return await plugin.event_logger(inputs)
    elif node_id == "file_parsing":
        return await plugin.file_parsing(inputs)
    elif node_id == "document_processor":
        return await plugin.document_processor(inputs)
    elif node_id == "vector_store_operations":
        return await plugin.vector_store_operations(inputs)
    else:
        return {"status": "error", "error": f"Nodo non supportato: {node_id}"}
