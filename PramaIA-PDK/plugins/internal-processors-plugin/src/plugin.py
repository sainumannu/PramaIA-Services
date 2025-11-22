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
        try:
            texts = inputs.get('texts', [])
            separator = inputs.get('separator', '\n')
            
            if not texts:
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
            
            logger.info(f"Uniti {len(valid_texts)} testi con separatore")
            
            return {
                "result": result,
                "count": len(valid_texts)
            }
            
        except Exception as e:
            logger.error(f"Errore text joiner: {e}")
            return {
                "result": "",
                "count": 0
            }
    
    async def text_filter(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Filtra testi basandosi su criteri"""
        try:
            texts = inputs.get('texts', [])
            min_length = inputs.get('min_length', 10)
            filter_empty = inputs.get('filter_empty', True)
            
            if not texts:
                return {
                    "filtered_texts": [],
                    "filtered_count": 0
                }
            
            filtered_texts = []
            
            for text in texts:
                if not isinstance(text, str):
                    text = str(text) if text is not None else ""
                
                # Filtra testi vuoti se richiesto
                if filter_empty and not text.strip():
                    continue
                
                # Filtra per lunghezza minima
                if len(text.strip()) >= min_length:
                    filtered_texts.append(text)
            
            logger.info(f"Filtrati {len(filtered_texts)} testi da {len(texts)}")
            
            return {
                "filtered_texts": filtered_texts,
                "filtered_count": len(filtered_texts)
            }
            
        except Exception as e:
            logger.error(f"Errore text filter: {e}")
            return {
                "filtered_texts": [],
                "filtered_count": 0
            }
    
    async def user_context_provider(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Fornisce informazioni di contesto utente"""
        try:
            # Per ora genera un user_id mock - in futuro dovrebbe venire dal sistema di auth
            user_id = inputs.get('user_id', 'user_123')
            current_time = datetime.now().isoformat()
            
            return {
                "user_id": user_id,
                "timestamp": current_time
            }
            
        except Exception as e:
            logger.error(f"Errore user context provider: {e}")
            return {
                "user_id": "unknown",
                "timestamp": datetime.now().isoformat()
            }

# Funzioni di interfaccia per il PDK
async def process_node(node_id: str, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Interfaccia principale per processare nodi del plugin"""
    plugin = InternalProcessorsPlugin(config)
    
    if node_id == "text_joiner":
        return await plugin.text_joiner(inputs)
    elif node_id == "text_filter":
        return await plugin.text_filter(inputs)
    elif node_id == "user_context_provider":
        return await plugin.user_context_provider(inputs)
    else:
        raise ValueError(f"Nodo non supportato: {node_id}")

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
