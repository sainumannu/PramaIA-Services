"""
Metadata Manager Processor per PDK.
Gestisce operazioni sui metadati dei documenti.
"""

import sys
import os
import json
import copy
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# Importa il logger standardizzato
try:
    # Prima tenta di importare il modulo locale
    from . import logger
except ImportError:
    try:
        # Aggiungi la cartella common alla path
        plugin_common_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../common"))
        if os.path.exists(plugin_common_path):
            sys.path.append(plugin_common_path)
            
        # Importa il modulo logger.py
        import logger
    except ImportError:
        # Fallback al logger standard
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.error("Impossibile importare il modulo di logging standardizzato")

try:
    import jsonschema
except ImportError:
    logger.warning("jsonschema not available. Validation functionality will be limited.")
    jsonschema = None

async def process(inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Elabora le operazioni sui metadati in base all'operazione specificata.
    
    Args:
        inputs: Dizionario contenente i parametri dell'operazione
        config: Configurazione del nodo
        
    Returns:
        Dizionario con i risultati dell'operazione
    """
    try:
        # Estrai parametri operazione
        operation = inputs.get("operation", "update")
        current_metadata = inputs.get("current_metadata", {})
        new_metadata = inputs.get("new_metadata", {})
        validation_schema = inputs.get("validation_schema")
        
        logger.info(f"Esecuzione operazione {operation} sui metadati")
        
        # Valida input
        if not isinstance(current_metadata, dict):
            raise ValueError("current_metadata deve essere un dizionario")
                
        if not isinstance(new_metadata, dict):
            raise ValueError("new_metadata deve essere un dizionario")
        
        # Esegui l'operazione richiesta
        if operation == "update":
            result_metadata = _update_metadata(current_metadata, new_metadata)
        elif operation == "merge":
            result_metadata = _merge_metadata(current_metadata, new_metadata)
        elif operation == "extract":
            result_metadata = _extract_metadata(current_metadata, new_metadata, inputs.get("content", ""))
        else:
            raise ValueError(f"Operazione non supportata: {operation}")
        
        # Aggiungi timestamp operazione
        result_metadata["metadata_updated_at"] = datetime.now().isoformat()
        
        # Valida i metadati risultanti se è fornito uno schema
        is_valid, validation_errors = _validate_metadata(result_metadata, validation_schema)
        
        return {
            "status": "success" if is_valid else "validation_error",
            "metadata": result_metadata,
            "is_valid": is_valid,
            "validation_errors": validation_errors,
            "operation": operation
        }
            
    except Exception as e:
        logger.error(f"Errore in MetadataManager: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }

def _update_metadata(current_metadata: Dict[str, Any], new_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sostituisce i metadati correnti con nuovi metadati.
    Preserva alcuni campi di sistema se esistono.
    """
    # Crea una copia profonda dei nuovi metadati
    result = copy.deepcopy(new_metadata)
    
    # Preserva campi di sistema dai metadati correnti se esistono
    system_fields = ["document_id", "created_at", "file_path", "source_id"]
    for field in system_fields:
        if field in current_metadata and field not in result:
            result[field] = current_metadata[field]
    
    return result

def _merge_metadata(current_metadata: Dict[str, Any], new_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unisce in modo intelligente i metadati correnti e nuovi.
    Gestisce dizionari annidati, liste e valori primitivi.
    """
    # Inizia con una copia profonda dei metadati correnti
    result = copy.deepcopy(current_metadata)
    
    # Funzione helper ricorsiva per unione profonda
    def deep_merge(target, source):
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Unisci ricorsivamente dizionari annidati
                deep_merge(target[key], value)
            elif key in target and isinstance(target[key], list) and isinstance(value, list):
                # Unisci liste senza duplicati per determinati campi
                if key in ["tags", "categories", "labels"]:
                    target[key] = list(set(target[key] + value))
                else:
                    # Per altre liste, aggiungi nuovi valori
                    target[key].extend(value)
            else:
                # Semplice sostituzione di valore
                target[key] = value
    
    # Esegui l'unione profonda
    deep_merge(result, new_metadata)
    
    return result

def _extract_metadata(current_metadata: Dict[str, Any], 
                    hints: Dict[str, Any], content: str) -> Dict[str, Any]:
    """
    Estrae metadati dal contenuto del documento in base a suggerimenti.
    Questa è un'implementazione semplificata - in un sistema reale potrebbe usare 
    modelli ML o tecniche di estrazione più sofisticate.
    """
    # Inizia con i metadati correnti
    result = copy.deepcopy(current_metadata)
    
    # Elabora statistiche di base sul contenuto
    if content:
        # Aggiungi statistiche di base sul documento se non già presenti
        if "stats" not in result:
            result["stats"] = {}
            
        result["stats"]["char_count"] = len(content)
        result["stats"]["word_count"] = len(content.split())
        result["stats"]["line_count"] = content.count('\n') + 1
        
        # Estrai potenziale titolo dalla prima riga
        lines = content.split('\n')
        if lines and lines[0].strip() and len(lines[0].strip()) < 100:
            result["extracted_title"] = lines[0].strip()
        
        # Semplice estrazione di parole chiave se i suggerimenti forniscono parole chiave da cercare
        if "keywords" in hints:
            found_keywords = []
            content_lower = content.lower()
            for keyword in hints.get("keywords", []):
                if keyword.lower() in content_lower:
                    found_keywords.append(keyword)
                    
            if found_keywords:
                result["keywords"] = list(set(result.get("keywords", []) + found_keywords))
    
    # Applica eventuali metadati espliciti dai suggerimenti
    if "metadata" in hints:
        result = _merge_metadata(result, hints["metadata"])
    
    return result

def _validate_metadata(metadata: Dict[str, Any], 
                    schema: Optional[Dict[str, Any]]) -> tuple[bool, Optional[List[str]]]:
    """
    Valida i metadati rispetto a uno schema JSON se fornito.
    Restituisce (is_valid, validation_errors)
    """
    # Se non c'è schema, considera valido
    if not schema:
        return True, None
        
    if not jsonschema:
        logger.warning("Libreria jsonschema non disponibile, validazione saltata")
        return True, ["Validazione saltata: libreria jsonschema non disponibile"]
    
    try:
        jsonschema.validate(instance=metadata, schema=schema)
        return True, None
    except Exception as e:
        logger.warning(f"Validazione metadati fallita: {e}")
        # Formatta errori di validazione in modo leggibile
        error_message = f"Errore di validazione: {str(e)}"
        return False, [error_message]
