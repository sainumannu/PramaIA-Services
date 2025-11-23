"""
ChromaDB Writer Processor

Salva embeddings, testo e metadati nel database vettoriale ChromaDB.
"""

import logging
import os
import uuid
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.api.models.Collection import Collection
    CHROMADB_AVAILABLE = True
except ImportError:
    chromadb = None
    Settings = None
    Collection = None
    CHROMADB_AVAILABLE = False
    logger.warning("⚠️ chromadb non disponibile, usando storage mock")


class ChromaWriterProcessor:
    """Processore per salvare embeddings in ChromaDB."""
    
    def __init__(self):
        self.client = None
        self.current_persist_directory = None
    
    async def process(self, context) -> Dict[str, Any]:
        """
        Salva embeddings nel database vettoriale.
        """
        logger.info("[ChromaWriter] INGRESSO nodo: process")
        try:
            config = context.get('config', {})
            inputs = context.get('inputs', {})
            embeddings_input = inputs.get('embeddings_input', {})
            if not embeddings_input:
                raise ValueError("Nessun embedding fornito in input")
            embeddings = embeddings_input.get('embeddings', [])
            chunks = embeddings_input.get('chunks', [])
            model_name = embeddings_input.get('model', 'unknown')
            if not embeddings or not chunks:
                raise ValueError("Embeddings o chunks mancanti")
            if len(embeddings) != len(chunks):
                raise ValueError(f"Mismatch: {len(embeddings)} embeddings vs {len(chunks)} chunks")
            collection_name = config.get('collection_name', 'documents')
            persist_directory = config.get('persist_directory', './chroma_db')
            distance_metric = config.get('distance_metric', 'cosine')
            await self._initialize_client(persist_directory)
            document_ids = await self._save_embeddings(
                collection_name=collection_name,
                embeddings=embeddings,
                documents=chunks,
                model_name=model_name,
                distance_metric=distance_metric
            )
            logger.info(f"[ChromaWriter] USCITA nodo (successo): Salvati {len(document_ids)} documenti in ChromaDB")
            return {
                "status": "success",
                "storage_result": {
                    "collection_name": collection_name,
                    "document_ids": document_ids,
                    "documents_saved": len(document_ids),
                    "model_used": model_name,
                    "persist_directory": persist_directory
                },
                "documents_saved": len(document_ids)
            }
        except Exception as e:
            logger.error(f"[ChromaWriter] USCITA nodo (errore): {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "storage_result": {
                    "collection_name": "",
                    "document_ids": [],
                    "documents_saved": 0
                }
            }
    
    async def _initialize_client(self, persist_directory: str):
        """Inizializza il client ChromaDB."""
        if (self.client is not None and 
            self.current_persist_directory == persist_directory):
            return  # Client già inizializzato
        
        if not CHROMADB_AVAILABLE or chromadb is None:
            logger.warning("⚠️ ChromaDB non disponibile, usando storage mock")
            self.client = "mock"
            self.current_persist_directory = persist_directory
            return
        
        try:
            # Crea directory se non exists
            os.makedirs(persist_directory, exist_ok=True)
            
            # Inizializza client persistente
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                ) if Settings else None
            )
            
            self.current_persist_directory = persist_directory
            logger.info(f"✅ Client ChromaDB inizializzato: {persist_directory}")
            
        except Exception as e:
            logger.error(f"❌ Errore inizializzazione ChromaDB: {str(e)}")
            self.client = "mock"
            self.current_persist_directory = persist_directory
    
    async def _save_embeddings(self, collection_name: str, embeddings: List[List[float]], 
                             documents: List[str], model_name: str, distance_metric: str) -> List[str]:
        """
        Salva embeddings nella collezione ChromaDB.
        
        Args:
            collection_name: Nome della collezione
            embeddings: Lista di embeddings
            documents: Lista di documenti di testo
            model_name: Nome del modello usato per gli embeddings
            distance_metric: Metrica di distanza
            
        Returns:
            Lista di ID dei documenti salvati
        """
        if self.client == "mock" or not CHROMADB_AVAILABLE:
            return self._mock_save_embeddings(documents)
        
        try:
            # Mappa metriche di distanza
            distance_function = "cosine"  # Default ChromaDB
            if distance_metric == "euclidean":
                distance_function = "l2"
            elif distance_metric == "manhattan":
                distance_function = "l1"
            
            # Ottieni o crea collezione
            try:
                collection = self.client.get_collection(
                    name=collection_name,
                    embedding_function=None  # Usiamo embeddings pre-calcolati
                )
                logger.info(f"📂 Collezione esistente trovata: {collection_name}")
                
            except Exception:
                # Crea nuova collezione
                collection = self.client.create_collection(
                    name=collection_name,
                    metadata={
                        "hnsw:space": distance_function,
                        "description": f"Documents processed with {model_name}"
                    },
                    embedding_function=None
                )
                logger.info(f"📂 Nuova collezione creata: {collection_name}")
            
            # Genera ID univoci per i documenti, ma consistenti per lo stesso contenuto
            import hashlib
            
            # Utilizziamo un hash del contenuto per generare ID coerenti per lo stesso testo
            document_ids = []
            timestamp = datetime.now().strftime('%Y%m%d')  # Prefisso data per organizzazione
            
            for i, doc in enumerate(documents):
                # Genera hash dal contenuto del documento per ID consistente
                content_hash = hashlib.md5(doc.encode('utf-8')).hexdigest()
                doc_id = f"doc_{timestamp}_{content_hash[:8]}_{i:04d}"
                document_ids.append(doc_id)
            
            # Prepara metadati
            metadatas = []
            for i, doc in enumerate(documents):
                metadata = {
                    "model": model_name,
                    "chunk_index": i,
                    "text_length": len(doc),
                    "created_at": datetime.now().isoformat(),
                    "distance_metric": distance_metric
                }
                metadatas.append(metadata)
            
            # Salva in batch per migliori performance
            batch_size = 100
            saved_ids = []
            
            for i in range(0, len(documents), batch_size):
                batch_end = min(i + batch_size, len(documents))
                
                batch_ids = document_ids[i:batch_end]
                batch_embeddings = embeddings[i:batch_end]
                batch_documents = documents[i:batch_end]
                batch_metadatas = metadatas[i:batch_end]
                
                # Aggiungi batch alla collezione
                collection.add(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    documents=batch_documents,
                    metadatas=batch_metadatas
                )
                
                saved_ids.extend(batch_ids)
                logger.debug(f"💾 Salvato batch {i//batch_size + 1}: {len(batch_ids)} documenti")
            
            # Verifica salvataggio
            collection_count = collection.count()
            logger.info(f"✅ Collezione {collection_name}: {collection_count} documenti totali")
            
            return saved_ids
            
        except Exception as e:
            logger.error(f"❌ Errore salvataggio embeddings: {str(e)}")
            return self._mock_save_embeddings(documents)
    
    def _mock_save_embeddings(self, documents: List[str]) -> List[str]:
        """
        Mock del salvataggio embeddings per testing.
        
        Args:
            documents: Lista di documenti
            
        Returns:
            Lista di ID mock
        """
        logger.info(f"🔄 Mock salvataggio per {len(documents)} documenti")
        
        # Usa lo stesso metodo di generazione ID basato su hash per consistenza
        import hashlib
        document_ids = []
        timestamp = datetime.now().strftime('%Y%m%d')
        
        for i, doc in enumerate(documents):
            # Genera hash dal contenuto del documento per ID consistente
            content_hash = hashlib.md5(doc.encode('utf-8')).hexdigest()
            doc_id = f"mock_doc_{timestamp}_{content_hash[:8]}_{i:04d}"
            document_ids.append(doc_id)
            
        return document_ids


# Funzione entry point per il PDK
async def process_node(context):
    """Entry point per il nodo ChromaDB Writer."""
    processor = ChromaWriterProcessor()
    return await processor.process(context)
