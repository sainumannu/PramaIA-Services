"""
ChromaDB Retriever Processor

Recupera documenti simili dal database vettoriale ChromaDB usando una query di embeddings.
"""

import logging
from typing import Dict, Any, List, Tuple
import numpy as np

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
    logger.warning("⚠️ chromadb non disponibile, usando retrieval mock")


class ChromaRetrieverProcessor:
    """Processore per recuperare documenti simili da ChromaDB."""
    
    def __init__(self):
        self.client = None
        self.current_persist_directory = None
    
    async def process(self, context) -> Dict[str, Any]:
        """
        Recupera documenti simili dalla query.
        """
        logger.info("[ChromaRetriever] INGRESSO nodo: process")
        try:
            config = context.get('config', {})
            inputs = context.get('inputs', {})
            query_input = inputs.get('query_embeddings', {})
            if not query_input:
                raise ValueError("Nessun query embedding fornito in input")
            query_embeddings = query_input.get('embeddings', [])
            query_text = query_input.get('query', '')
            if not query_embeddings:
                raise ValueError("Query embeddings mancanti")
            collection_name = config.get('collection_name', 'documents')
            persist_directory = config.get('persist_directory', './chroma_db')
            max_results = config.get('max_results', 5)
            similarity_threshold = config.get('similarity_threshold', 0.7)
            include_metadata = config.get('include_metadata', True)
            await self._initialize_client(persist_directory)
            retrieved_docs = await self._retrieve_similar_documents(
                collection_name=collection_name,
                query_embeddings=query_embeddings,
                max_results=max_results,
                similarity_threshold=similarity_threshold,
                include_metadata=include_metadata
            )
            logger.info(f"[ChromaRetriever] USCITA nodo (successo): Recuperati {len(retrieved_docs)} documenti da ChromaDB")
            return {
                "status": "success",
                "retrieved_documents": retrieved_docs,
                "retrieval_metadata": {
                    "query_text": query_text,
                    "collection_name": collection_name,
                    "max_results": max_results,
                    "similarity_threshold": similarity_threshold,
                    "documents_found": len(retrieved_docs)
                }
            }
        except Exception as e:
            logger.error(f"[ChromaRetriever] USCITA nodo (errore): {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "retrieved_documents": [],
                "retrieval_metadata": {
                    "query_text": "",
                    "collection_name": "",
                    "documents_found": 0
                }
            }
    
    async def _initialize_client(self, persist_directory: str):
        """Inizializza il client ChromaDB."""
        if (self.client is not None and 
            self.current_persist_directory == persist_directory):
            return  # Client già inizializzato
        
        if not CHROMADB_AVAILABLE or chromadb is None:
            logger.warning("⚠️ ChromaDB non disponibile, usando retrieval mock")
            self.client = "mock"
            self.current_persist_directory = persist_directory
            return
        
        try:
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
    
    async def _retrieve_similar_documents(self, collection_name: str, 
                                        query_embeddings: List[List[float]], 
                                        max_results: int,
                                        similarity_threshold: float,
                                        include_metadata: bool) -> List[Dict[str, Any]]:
        """
        Recupera documenti simili dalla collezione ChromaDB.
        
        Args:
            collection_name: Nome della collezione
            query_embeddings: Lista di query embeddings 
            max_results: Numero massimo di risultati
            similarity_threshold: Soglia di similarità
            include_metadata: Se includere i metadati
            
        Returns:
            Lista di documenti recuperati con score e metadati
        """
        if self.client == "mock" or not CHROMADB_AVAILABLE:
            return self._mock_retrieve_documents(max_results)
        
        try:
            # Ottieni collezione
            collection = self.client.get_collection(name=collection_name)
            collection_count = collection.count()
            
            if collection_count == 0:
                logger.warning(f"⚠️ Collezione {collection_name} vuota")
                return []
            
            logger.info(f"🔍 Ricerca in collezione {collection_name}: {collection_count} documenti")
            
            # Per multiple query embeddings, usa il primo o combina
            primary_query_embedding = query_embeddings[0] if query_embeddings else []
            
            if not primary_query_embedding:
                logger.warning("⚠️ Query embedding vuoto")
                return []
            
            # Query ChromaDB
            results = collection.query(
                query_embeddings=[primary_query_embedding],
                n_results=min(max_results, collection_count),
                include=['documents', 'metadatas', 'distances'] if include_metadata else ['documents', 'distances']
            )
            
            # Processa risultati
            retrieved_docs = []
            
            if results['documents'] and len(results['documents']) > 0:
                documents = results['documents'][0]  # Prima query
                distances = results['distances'][0] if results.get('distances') else []
                metadatas = results['metadatas'][0] if results.get('metadatas') and include_metadata else []
                ids = results['ids'][0] if results.get('ids') else []
                
                for i, doc in enumerate(documents):
                    # Calcola similarity score (1 - distance per cosine)
                    distance = distances[i] if i < len(distances) else 1.0
                    similarity_score = max(0, 1 - distance)  # Convert distance to similarity
                    
                    # Filtra per soglia di similarità
                    if similarity_score < similarity_threshold:
                        continue
                    
                    doc_result = {
                        "document": doc,
                        "similarity_score": round(similarity_score, 4),
                        "distance": round(distance, 4),
                        "document_id": ids[i] if i < len(ids) else f"doc_{i}"
                    }
                    
                    # Aggiungi metadati se richiesti
                    if include_metadata and i < len(metadatas) and metadatas[i]:
                        doc_result["metadata"] = metadatas[i]
                    
                    retrieved_docs.append(doc_result)
                
                # Ordina per similarity score decrescente
                retrieved_docs.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            logger.info(f"✅ Recuperati {len(retrieved_docs)} documenti con soglia {similarity_threshold}")
            
            return retrieved_docs
            
        except Exception as e:
            logger.error(f"❌ Errore query ChromaDB: {str(e)}")
            return self._mock_retrieve_documents(max_results)
    
    def _mock_retrieve_documents(self, max_results: int) -> List[Dict[str, Any]]:
        """
        Mock del retrieval per testing.
        
        Args:
            max_results: Numero massimo di risultati
            
        Returns:
            Lista di documenti mock
        """
        logger.info(f"🔄 Mock retrieval per {max_results} documenti")
        
        mock_docs = [
            {
                "document": f"Questo è un documento di esempio numero {i+1}. Contiene informazioni rilevanti per la query di ricerca semantica. Il contenuto è generato per scopi di testing del sistema di retrieval.",
                "similarity_score": round(0.9 - (i * 0.1), 2),
                "distance": round(0.1 + (i * 0.1), 2),
                "document_id": f"mock_doc_{i+1}",
                "metadata": {
                    "model": "mock-embeddings",
                    "chunk_index": i,
                    "text_length": 150 + (i * 20),
                    "created_at": "2024-01-01T00:00:00",
                    "mock": True
                }
            }
            for i in range(min(max_results, 3))  # Max 3 mock docs
        ]
        
        return mock_docs


# Funzione entry point per il PDK
async def process_node(context):
    """Entry point per il nodo ChromaDB Retriever."""
    processor = ChromaRetrieverProcessor()
    return await processor.process(context)
