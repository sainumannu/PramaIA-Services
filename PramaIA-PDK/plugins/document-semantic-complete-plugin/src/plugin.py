"""
Document Semantic Complete Plugin - Main Entry Point
"""

import json
import random
from typing import Dict, Any

# Logger adapter: prefer local .logger, fallback to pramaialog client, else stdlib
try:
    from .logger import debug as log_debug, info as log_info, warning as log_warning, error as log_error
    from .logger import flush as log_flush, close as log_close
except Exception:
    try:
        from pramaialog import PramaIALogger

        _pl = PramaIALogger()

        def log_debug(*a, **k):
            try:
                _pl.debug(*a, **k)
            except Exception:
                pass

        def log_info(*a, **k):
            try:
                _pl.info(*a, **k)
            except Exception:
                pass

        def log_warning(*a, **k):
            try:
                _pl.warning(*a, **k)
            except Exception:
                pass

        def log_error(*a, **k):
            try:
                _pl.error(*a, **k)
            except Exception:
                pass

        def log_flush():
            try:
                _pl.flush()
            except Exception:
                pass

        def log_close():
            try:
                _pl.close()
            except Exception:
                pass
    except Exception:
        import logging as _std_logging

        _logger = _std_logging.getLogger(__name__)

        def log_debug(*a, **k):
            _logger.debug(*a, **k)

        def log_info(*a, **k):
            _logger.info(*a, **k)

        def log_warning(*a, **k):
            _logger.warning(*a, **k)

        def log_error(*a, **k):
            _logger.error(*a, **k)

        def log_flush():
            for h in _logger.handlers:
                try:
                    h.flush()
                except Exception:
                    pass

        def log_close():
            for h in _logger.handlers:
                try:
                    h.close()
                except Exception:
                    pass


class DocumentSemanticPlugin:
    """
    Plugin per il completamento semantico di documenti.
    Fornisce nodi per estrazione semantica e operazioni avanzate sui documenti.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        log_info("Plugin Document Semantic inizializzato")
    
    async def document_input_node(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Processore per Document Input."""
        try:
            file_path = inputs.get('file_path', '') or self.config.get('file_path', '')
            if not file_path:
                return {"status": "error", "error": "file_path mancante"}
            
            # Usa os.path per gestire correttamente i percorsi
            import os
            import hashlib
            from datetime import datetime
            
            file_name = os.path.basename(file_path)
            folder_path = os.path.dirname(file_path)
            
            # Normalizza il percorso per evitare problemi con gli escape
            normalized_path = os.path.normpath(file_path)
            
            # Genera un ID deterministico basato sul nome del file e sul percorso
            # Questo garantisce che lo stesso file riceva sempre lo stesso ID
            file_info = f"{file_name}_{normalized_path}"
            document_hash = hashlib.md5(file_info.encode('utf-8')).hexdigest()
            document_id = f"doc_{document_hash[:16]}"
            
            log_info(f"Document Input: generato document_id deterministico: {document_id} per {file_name}")
            
            return {
                "status": "success",
                "id": document_id,  # Aggiungi l'ID deterministico qui
                "document_id": document_id,  # Aggiungi in entrambi i campi per compatibilità
                "document_file": {
                    "file_path": normalized_path,
                    "folder_path": folder_path,
                    "file_name": file_name,
                    "ready_for_processing": True,
                    "document_id": document_id,  # Includi anche nel campo document_file
                    "metadata": {
                        "document_id": document_id,  # Includi anche nei metadati
                        "original_path": file_path,
                        "folder_name": os.path.basename(folder_path),
                        "parent_folder": os.path.basename(os.path.dirname(folder_path)) if os.path.dirname(folder_path) else "",
                        "full_path_segments": normalized_path.split(os.sep)
                    }
                }
            }
        except Exception as e:
            log_error(f"Errore nel processore PDF Input: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def pdf_text_extractor(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """PDF Text Extractor per estrazione da file PDF."""
        try:
            pdf_file = inputs.get('pdf_file', {})
            file_path = pdf_file.get('file_path', '')
            document_id = pdf_file.get('document_id', '') or inputs.get('document_id', '')
            
            if not file_path:
                return {"status": "error", "error": "PDF file mancante"}
            
            # Mock extraction
            mock_text = f"Testo estratto dal file {file_path}. Contenuto esempio. " * 10
            
            result = {
                "status": "success",
                "extracted_text": {
                    "text": mock_text,
                    "pages": 1,
                    "characters": len(mock_text),
                    "source_file": file_path
                }
            }
            
            # Mantieni l'ID del documento nella catena di elaborazione
            if document_id:
                result["document_id"] = document_id
                result["id"] = document_id
            
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}


async def process_node(node_id: str, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Interfaccia principale per processare nodi del plugin"""
    plugin = DocumentSemanticPlugin(config)
    
    if node_id == "document_input_node":
        return await plugin.document_input_node(inputs)
    elif node_id == "pdf_text_extractor":
        return await plugin.pdf_text_extractor(inputs)
    else:
        return {"status": "error", "error": f"Nodo non supportato: {node_id}"}
