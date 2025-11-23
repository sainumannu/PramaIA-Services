import json
import logging
import sys
import os
from typing import Dict, Any, List
import time
from datetime import datetime

# Prova a utilizzare il modulo di logging standardizzato
try:
    # Aggiungi la cartella common alla path
    plugin_common_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../common"))
    if os.path.exists(plugin_common_path):
        sys.path.append(plugin_common_path)
        
    # Importa il modulo logger
    import logger
    
    # Inizializza il logger
    logger = logger
    logger.init("internal-processors")
    
    # Log di inizializzazione
    logger.info("Logger standardizzato inizializzato per internal-processors plugin")
    
except Exception as e:
    # Fallback alla configurazione originale
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.error(f"Impossibile importare il modulo di logging standardizzato: {str(e)}")

class InternalProcessorsPlugin:
    """Plugin per processori interni e utilità"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info("Plugin Internal Processors inizializzato")
    
    async def text_joiner(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Unisce array di testi con un separatore"""
        entry_msg = f"[InternalProcessors] INGRESSO nodo: text_joiner"
        logger.info(entry_msg)
        try:
            texts = inputs.get('texts', [])
            separator = inputs.get('separator', '\n')
            if not texts:
                exit_msg = f"[InternalProcessors] USCITA nodo (successo): text_joiner, count=0"
                logger.info(exit_msg)
                return {
                    "result": "",
                    "count": 0
                }
            # Filtra elementi non validi
            valid_texts = []
            for text in texts:
                if isinstance(text, str) and text.strip():
                    valid_texts.append(text.strip())
                elif text is not None:
                    valid_texts.append(str(text))
            result = separator.join(valid_texts)
            exit_msg = f"[InternalProcessors] USCITA nodo (successo): text_joiner, count={len(valid_texts)}"
            logger.info(exit_msg)
            return {
                "result": result,
                "count": len(valid_texts)
            }
        except Exception as e:
            exit_msg = f"[InternalProcessors] USCITA nodo (errore): text_joiner, {e}"
            logger.error(exit_msg)
            return {
                "result": "",
                "count": 0
            }
    
    async def text_filter(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Filtra testi basandosi su criteri"""
        entry_msg = f"[InternalProcessors] INGRESSO nodo: text_filter"
        logger.info(entry_msg)
        try:
            texts = inputs.get('texts', [])
            min_length = inputs.get('min_length', 10)
            filter_empty = inputs.get('filter_empty', True)
            if not texts:
                exit_msg = f"[InternalProcessors] USCITA nodo (successo): text_filter, filtered_count=0"
                logger.info(exit_msg)
                return {
                    "filtered_texts": [],
                    "filtered_count": 0
                }
            filtered_texts = []
            for text in texts:
                if not isinstance(text, str):
                    text = str(text) if text is not None else ""
                if filter_empty and not text.strip():
                    continue
                if len(text.strip()) >= min_length:
                    filtered_texts.append(text)
            exit_msg = f"[InternalProcessors] USCITA nodo (successo): text_filter, filtered_count={len(filtered_texts)}"
            logger.info(exit_msg)
            return {
                "filtered_texts": filtered_texts,
                "filtered_count": len(filtered_texts)
            }
        except Exception as e:
            exit_msg = f"[InternalProcessors] USCITA nodo (errore): text_filter, {e}"
            logger.error(exit_msg)
            return {
                "filtered_texts": [],
                "filtered_count": 0
            }
    
    async def user_context_provider(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Fornisce informazioni di contesto utente"""
        entry_msg = f"[InternalProcessors] INGRESSO nodo: user_context_provider"
        logger.info(entry_msg)
        try:
            user_id = inputs.get('user_id', 'user_123')
            current_time = datetime.now().isoformat()
            exit_msg = f"[InternalProcessors] USCITA nodo (successo): user_context_provider, user_id={user_id}"
            logger.info(exit_msg)
            return {
                "user_id": user_id,
                "timestamp": current_time
            }
        except Exception as e:
            exit_msg = f"[InternalProcessors] USCITA nodo (errore): user_context_provider, {e}"
            logger.error(exit_msg)
            return {
                "user_id": "unknown",
                "timestamp": datetime.now().isoformat()
            }

# Funzioni di interfaccia per il PDK
async def process_node(node_id: str, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Interfaccia principale per processare nodi del plugin"""
    entry_msg = f"[InternalProcessors] INGRESSO process_node: node_id={node_id}"
    logger.info(entry_msg)
    plugin = InternalProcessorsPlugin(config)
    try:
        if node_id == "text_joiner":
            result = await plugin.text_joiner(inputs)
        elif node_id == "text_filter":
            result = await plugin.text_filter(inputs)
        elif node_id == "user_context_provider":
            result = await plugin.user_context_provider(inputs)
        else:
            raise ValueError(f"Nodo non supportato: {node_id}")
        exit_msg = f"[InternalProcessors] USCITA process_node (successo): node_id={node_id}"
        logger.info(exit_msg)
        return result
    except Exception as e:
        exit_msg = f"[InternalProcessors] USCITA process_node (errore): node_id={node_id}, {e}"
        logger.error(exit_msg)
        raise

def validate_config(config: Dict[str, Any]) -> bool:
    """Valida la configurazione del plugin"""
    return True  # Nessuna configurazione richiesta

def get_plugin_info() -> Dict[str, Any]:
    """Restituisce informazioni sul plugin"""
    return {
        "name": "internal-processors-plugin",
        "version": "1.0.0",
        "description": "Plugin interno per processori di testo e utilità generali",
        "nodes": [
            "text_joiner",
            "text_filter", 
            "user_context_provider"
        ]
    }
