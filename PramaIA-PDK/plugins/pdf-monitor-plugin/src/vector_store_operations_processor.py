"""
VectorStoreOperations Processor per PDK.
Fornisce un'interfaccia unificata per operazioni CRUD sul vectorstore.
"""

import uuid
import sys
import os
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

# Alias delle funzioni per mantenere la compatibilità
log_debug = logger.debug
log_info = logger.info
log_warning = logger.warning
log_error = logger.error
log_flush = logger.flush
log_close = logger.close

# Mock implementazioni per test
class Document:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}

class MockVectorStore:
    def similarity_search(self, *args, **kwargs):
        return [Document(page_content="Mock result", metadata={"source": "mock"})]
        
    def similarity_search_with_score(self, *args, **kwargs):
        return [(Document(page_content="Mock result", metadata={"source": "mock"}), 0.95)]
        
    def add_documents(self, *args, **kwargs):
        return True
        
    def delete(self, *args, **kwargs):
        return True

class MockEmbeddings:
    def embed_documents(self, texts):
        return [[0.1] * 10 for _ in texts]  # Mock embeddings
        
    def embed_query(self, text):
        return [0.1] * 10  # Mock query embedding

# Variabili globali per le implementazioni reali
get_vectorstore = None
add_documents_to_vectorstore = None
remove_documents_from_vectorstore = None
get_openai_embeddings = None

def _initialize_real_implementations():
    """Tenta di importare le implementazioni reali del vectorstore."""
    global get_vectorstore, add_documents_to_vectorstore, remove_documents_from_vectorstore, get_openai_embeddings
    
    try:
        # Importa le implementazioni reali
        from backend.core.rag_vectorstore import (
            get_vectorstore as real_get_vectorstore, 
            add_documents_to_vectorstore as real_add_documents_to_vectorstore,
            remove_documents_from_vectorstore as real_remove_documents_from_vectorstore
        )
        from backend.core.rag_chains_prompts import get_openai_embeddings as real_get_openai_embeddings
        from langchain.docstore.document import Document as LangchainDocument
        
        # Assegna alle variabili globali
        get_vectorstore = real_get_vectorstore
        add_documents_to_vectorstore = real_add_documents_to_vectorstore
        remove_documents_from_vectorstore = real_remove_documents_from_vectorstore
        get_openai_embeddings = real_get_openai_embeddings
        global Document
        Document = LangchainDocument
        
        log_info("Moduli backend disponibili, usando implementazioni reali")
        return True
    except ImportError:
        log_warning("Moduli backend non disponibili, usando implementazioni mock")
        
        # Usa le implementazioni mock
        get_vectorstore = lambda collection_name, namespace: MockVectorStore()
        add_documents_to_vectorstore = lambda docs, embeddings_service, filename: True
        remove_documents_from_vectorstore = lambda doc_id: True
        get_openai_embeddings = lambda: MockEmbeddings()
        
        return False

# Inizializza le implementazioni all'avvio
_initialize_real_implementations()

def _validate_inputs(operation_type: str, document_id: Optional[str], 
                   document_content: Optional[str], query_text: Optional[str]) -> None:
    """Valida gli input in base al tipo di operazione."""
    if operation_type == "add" and not document_content:
        raise ValueError("document_content è richiesto per l'operazione add")
    
    if operation_type in ["get", "update", "delete"] and not document_id:
        raise ValueError(f"document_id è richiesto per l'operazione {operation_type}")
        
    if operation_type == "update" and not document_content:
        raise ValueError("document_content è richiesto per l'operazione update")
        
    if operation_type == "query" and not query_text:
        raise ValueError("query_text è richiesto per l'operazione query")

def _get_vectorstore(collection_name: str, namespace: str) -> Any:
    """Ottieni riferimento al vectorstore."""
    try:
        return get_vectorstore(collection_name=collection_name, namespace=namespace)
    except Exception as e:
        log_error(f"Errore nell'ottenere il vectorstore: {str(e)}")
        return MockVectorStore()  # Fallback a mock

def _add_document(vectorstore: Any, document_content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Aggiunge un documento al vectorstore."""
    try:
        # Genera un ID se non fornito
        document_id = metadata.get("document_id", str(uuid.uuid4()))
        
        # Assicura che document_id sia nei metadati
        metadata["document_id"] = document_id
        
        # Aggiungi timestamp
        metadata["created_at"] = datetime.now().isoformat()
        
        # Crea oggetto documento
        doc = Document(
            page_content=document_content,
            metadata=metadata
        )
        
        # Ottieni servizio embeddings
        embeddings_service = get_openai_embeddings()
        
        # Aggiungi al vectorstore
        source_filename = metadata.get("source_filename", document_id)
        success = add_documents_to_vectorstore(
            docs=[doc],
            embeddings_service=embeddings_service,
            filename=source_filename
        )
        
        if not success:
            raise ValueError("Impossibile aggiungere documento al vectorstore")
        
        return {
            "status": "success",
            "document_id": document_id,
            "operation": "add"
        }
        
    except Exception as e:
        log_error(f"Errore nell'aggiunta del documento: {str(e)}")
        raise

def _get_document(vectorstore: Any, document_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Ottieni documento dal vectorstore."""
    try:
        # Usa document_id per interrogare il vectorstore
        results = vectorstore.similarity_search(
            query=f"id:{document_id}", 
            k=1,
            filter={"document_id": document_id}
        )
        
        if not results:
            return {
                "status": "not_found",
                "document_id": document_id,
                "operation": "get"
            }
        
        document = results[0]
        
        return {
            "status": "success",
            "document_id": document_id,
            "document_content": document.page_content,
            "document_metadata": document.metadata,
            "operation": "get"
        }
        
    except Exception as e:
        log_error(f"Errore nel recupero del documento: {str(e)}")
        raise

def _update_document(vectorstore: Any, document_id: str, 
                    content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Aggiorna documento nel vectorstore."""
    try:
        # Prima, rimuovi il documento esistente
        success = remove_documents_from_vectorstore(document_id)
        if not success:
            log_warning(f"Documento {document_id} non trovato per l'aggiornamento")
        
        # Assicura che document_id sia nei metadati
        metadata["document_id"] = document_id
        
        # Aggiungi timestamp
        metadata["updated_at"] = datetime.now().isoformat()
        
        # Crea oggetto documento
        doc = Document(
            page_content=content,
            metadata=metadata
        )
        
        # Ottieni servizio embeddings
        embeddings_service = get_openai_embeddings()
        
        # Aggiungi documento aggiornato
        source_filename = metadata.get("source_filename", document_id)
        success = add_documents_to_vectorstore(
            docs=[doc],
            embeddings_service=embeddings_service,
            filename=source_filename
        )
        
        if not success:
            raise ValueError("Impossibile aggiornare documento nel vectorstore")
        
        return {
            "status": "success",
            "document_id": document_id,
            "operation": "update"
        }
        
    except Exception as e:
        log_error(f"Errore nell'aggiornamento del documento: {str(e)}")
        raise

def _delete_document(vectorstore: Any, document_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Elimina documento dal vectorstore."""
    try:
        # Rimuovi documento
        success = remove_documents_from_vectorstore(document_id)
        
        if not success:
            return {
                "status": "not_found",
                "document_id": document_id,
                "operation": "delete"
            }
        
        return {
            "status": "success",
            "document_id": document_id,
            "operation": "delete"
        }
        
    except Exception as e:
        log_error(f"Errore nell'eliminazione del documento: {str(e)}")
        raise

def _query_documents(vectorstore: Any, query_text: str, top_k: int) -> Dict[str, Any]:
    """Interroga documenti dal vectorstore."""
    try:
        # Cerca con punteggi
        results = vectorstore.similarity_search_with_score(
            query=query_text,
            k=top_k
        )
        
        # Formatta risultati
        documents = []
        for doc, score in results:
            documents.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score)  # Converti in float per serializzazione JSON
            })
        
        return {
            "status": "success",
            "query": query_text,
            "documents": documents,
            "total_results": len(documents),
            "operation": "query"
        }
        
    except Exception as e:
        log_error(f"Errore nell'interrogazione dei documenti: {str(e)}")
        raise

async def process(inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Esegue operazioni sul vectorstore.
    """
    # Log ingresso nodo
    operation_type = inputs.get("operation_type", "").lower()
    collection_name = inputs.get("collection_name", "default")
    namespace = inputs.get("namespace", "default")
    document_id = inputs.get("document_id")
    document_content = inputs.get("document_content")
    document_metadata = inputs.get("document_metadata", {})
    query_text = inputs.get("query_text")
    entry_msg = f"[VectorStoreOperations] INGRESSO nodo: operation_type={operation_type}, collection={collection_name}, namespace={namespace}, document_id={document_id}"
    log_info(entry_msg)
    try:
        # Valida input
        _validate_inputs(operation_type, document_id, document_content, query_text)
        # Ottieni riferimento al vectorstore
        vectorstore = _get_vectorstore(collection_name, namespace)
        # Esegui l'operazione richiesta
        if operation_type == "add":
            result = _add_document(vectorstore, document_content, document_metadata)
        elif operation_type == "get":
            result = _get_document(vectorstore, document_id, document_metadata)
        elif operation_type == "update":
            result = _update_document(vectorstore, document_id, document_content, document_metadata)
        elif operation_type == "delete":
            result = _delete_document(vectorstore, document_id, document_metadata)
        elif operation_type == "query":
            result = _query_documents(vectorstore, query_text, inputs.get("top_k", 5))
        else:
            raise ValueError(f"Tipo di operazione non supportato: {operation_type}")
        # Log uscita nodo (successo)
        exit_msg = f"[VectorStoreOperations] USCITA nodo (successo): operation_type={operation_type}, result_status={result.get('status', 'ok')}"
        log_info(exit_msg)
        return result
    except Exception as e:
        # Log uscita nodo (errore)
        exit_msg = f"[VectorStoreOperations] USCITA nodo (errore): {str(e)}"
        log_error(exit_msg)
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }
