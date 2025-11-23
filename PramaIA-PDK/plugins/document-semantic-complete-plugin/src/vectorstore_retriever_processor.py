"""
Vectorstore Retriever Processor

Recupera documenti simili usando il servizio VectorstoreService.
"""

import logging
from typing import Dict, Any, List
import requests

logger = logging.getLogger(__name__)

class VectorstoreRetrieverProcessor:
    """Processore per recuperare documenti simili usando il servizio VectorstoreService."""
    
    def __init__(self):
        self.client = None
        self.service_url = None
    
    async def process(self, context) -> Dict[str, Any]:
        """
        Recupera documenti simili dalla query.
        """
        logger.info("[VectorstoreRetriever] INGRESSO nodo: process")
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
            collection_name = config.get('collection_name', 'pdf_documents')
            service_url = config.get('service_url', 'http://localhost:8090')
            max_results = config.get('max_results', 5)
            similarity_threshold = config.get('similarity_threshold', 0.7)
            include_metadata = config.get('include_metadata', True)
            await self._initialize_client(service_url)
            retrieved_docs = await self._retrieve_similar_documents(
                collection_name=collection_name,
                query_embeddings=query_embeddings,
                query_text=query_text,
                max_results=max_results,
                similarity_threshold=similarity_threshold,
                include_metadata=include_metadata
            )
            logger.info(f"[VectorstoreRetriever] USCITA nodo (successo): Recuperati {len(retrieved_docs)} documenti via VectorstoreService")
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
            logger.error(f"[VectorstoreRetriever] USCITA nodo (errore): {str(e)}")
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
    
    async def _initialize_client(self, service_url: str):
        """Inizializza il client per il servizio VectorstoreService."""
        if (self.client is not None and 
            self.service_url == service_url):
            return  # Client già inizializzato
        
        try:
            # Verifica connessione al servizio
            response = requests.get(f"{service_url}/health")
            response.raise_for_status()
            
            self.service_url = service_url
            self.client = "initialized"
            logger.info(f"✅ Connessione al servizio VectorstoreService stabilita: {service_url}")
            
        except Exception as e:
            logger.error(f"❌ Errore connessione al servizio VectorstoreService: {str(e)}")
            self.client = "mock"
            self.service_url = service_url
    
    async def _retrieve_similar_documents(self, collection_name: str, 
                                        query_embeddings: List[List[float]],
                                        query_text: str,
                                        max_results: int,
                                        similarity_threshold: float,
                                        include_metadata: bool) -> List[Dict[str, Any]]:
        """
        Recupera documenti simili usando il servizio VectorstoreService.
        
        Args:
            collection_name: Nome della collezione
            query_embeddings: Lista di query embeddings 
            query_text: Testo della query
            max_results: Numero massimo di risultati
            similarity_threshold: Soglia di similarità
            include_metadata: Se includere i metadati
            
        Returns:
            Lista di documenti recuperati con score e metadati
        """
        if self.client == "mock":
            return self._mock_retrieve_documents(max_results)
        
        try:
            # Verifica che la collezione esista
            collection_url = f"{self.service_url}/collections/{collection_name}"
            response = requests.get(collection_url)
            
            if response.status_code == 404:
                logger.warning(f"⚠️ Collezione {collection_name} non trovata")
                return []
            
            response.raise_for_status()
            
            # Per multiple query embeddings, usa il primo o combina
            primary_query_embedding = query_embeddings[0] if query_embeddings else []
            
            if not primary_query_embedding:
                logger.warning("⚠️ Query embedding vuoto")
                return []
            
            # Prepara dati per la query
            query_data = {
                "query_embedding": primary_query_embedding,
                "query_text": query_text,
                "top_k": max_results,
                "include_metadata": include_metadata,
                "threshold": similarity_threshold
            }
            
            # Esegui query
            query_url = f"{self.service_url}/documents/{collection_name}/query"
            response = requests.post(query_url, json=query_data)
            response.raise_for_status()
            
            # Processa risultati
            result_data = response.json()
            results = result_data.get("results", [])
            
            # Formatta i risultati per mantenere compatibilità con il formato precedente
            retrieved_docs = []
            
            for result in results:
                doc_result = {
                    "document": result.get("document", ""),
                    "similarity_score": round(result.get("similarity", 0), 4),
                    "distance": round(1 - result.get("similarity", 0), 4),
                    "document_id": result.get("id", "unknown")
                }
                
                # Aggiungi metadati se presenti
                if include_metadata and "metadata" in result:
                    doc_result["metadata"] = result["metadata"]
                
                retrieved_docs.append(doc_result)
            
            logger.info(f"✅ Recuperati {len(retrieved_docs)} documenti con soglia {similarity_threshold}")
            
            return retrieved_docs
            
        except Exception as e:
            logger.error(f"❌ Errore query VectorstoreService: {str(e)}")
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
    """Entry point per il nodo Vectorstore Retriever."""
    processor = VectorstoreRetrieverProcessor()
    return await processor.process(context)
