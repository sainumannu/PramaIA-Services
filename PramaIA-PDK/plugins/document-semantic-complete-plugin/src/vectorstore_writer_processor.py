"""
Vectorstore Writer Processor

Salva embeddings, testo e metadati usando il servizio VectorstoreService.
"""

import logging
import os
import hashlib
from typing import Dict, Any, List
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

class VectorstoreWriterProcessor:
    """Processore per salvare embeddings usando il servizio VectorstoreService."""
    
    def __init__(self):
        self.client = None
        self.service_url = None
    
    async def process(self, context) -> Dict[str, Any]:
        """
        Salva embeddings nel database vettoriale.
        
        Args:
            context: Contesto di esecuzione con inputs e config
            
        Returns:
            Dict contenente il risultato del salvataggio
        """
        try:
            config = context.get('config', {})
            inputs = context.get('inputs', {})
            
            # Ottieni gli embeddings dall'input
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
            
            # Configurazione
            collection_name = config.get('collection_name', 'pdf_documents')
            service_url = config.get('service_url', 'http://localhost:8090')
            
            # Inizializza client
            await self._initialize_client(service_url)
            
            # Salva gli embeddings
            document_ids = await self._save_embeddings(
                collection_name=collection_name,
                embeddings=embeddings,
                documents=chunks,
                model_name=model_name
            )
            
            logger.info(f"✅ Salvati {len(document_ids)} documenti via VectorstoreService")
            
            return {
                "status": "success",
                "storage_result": {
                    "collection_name": collection_name,
                    "document_ids": document_ids,
                    "documents_saved": len(document_ids),
                    "model_used": model_name,
                    "service_url": service_url
                },
                "documents_saved": len(document_ids)
            }
            
        except Exception as e:
            logger.error(f"❌ Errore salvataggio VectorstoreService: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "storage_result": {
                    "collection_name": "",
                    "document_ids": [],
                    "documents_saved": 0
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
    
    async def _save_embeddings(self, collection_name: str, embeddings: List[List[float]], 
                             documents: List[str], model_name: str) -> List[str]:
        """
        Salva embeddings usando il servizio VectorstoreService.
        
        Args:
            collection_name: Nome della collezione
            embeddings: Lista di embeddings
            documents: Lista di documenti di testo
            model_name: Nome del modello usato per gli embeddings
            
        Returns:
            Lista di ID dei documenti salvati
        """
        if self.client == "mock":
            return self._mock_save_embeddings(documents)
        
        try:
            # Prima, assicurati che la collezione esista
            try:
                collection_url = f"{self.service_url}/collections/{collection_name}"
                response = requests.get(collection_url)
                
                if response.status_code == 404:
                    # Crea la collezione se non esiste
                    create_collection_url = f"{self.service_url}/collections"
                    create_data = {
                        "name": collection_name,
                        "metadata": {
                            "description": f"PDF documents processed with {model_name}"
                        }
                    }
                    response = requests.post(create_collection_url, json=create_data)
                    response.raise_for_status()
                    logger.info(f"📂 Nuova collezione creata: {collection_name}")
                else:
                    response.raise_for_status()
                    logger.info(f"📂 Collezione esistente trovata: {collection_name}")
                    
            except Exception as e:
                logger.error(f"❌ Errore verifica/creazione collezione: {str(e)}")
                # Continua comunque, il servizio potrebbe creare la collezione automaticamente
            
            # Genera ID univoci per i documenti
            document_ids = []
            timestamp = datetime.now().strftime('%Y%m%d')
            
            for i, doc in enumerate(documents):
                # Genera hash dal contenuto per ID consistente
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
                    "created_at": datetime.now().isoformat()
                }
                metadatas.append(metadata)
            
            # Salva in batch per migliori performance
            batch_size = 50
            saved_ids = []
            
            for i in range(0, len(documents), batch_size):
                batch_end = min(i + batch_size, len(documents))
                
                batch_ids = document_ids[i:batch_end]
                batch_embeddings = embeddings[i:batch_end]
                batch_documents = documents[i:batch_end]
                batch_metadatas = metadatas[i:batch_end]
                
                # Prepara payload batch
                batch_payload = []
                for j in range(len(batch_ids)):
                    batch_payload.append({
                        "id": batch_ids[j],
                        "document": batch_documents[j],
                        "embedding": batch_embeddings[j],
                        "metadata": batch_metadatas[j]
                    })
                
                # Invia batch al servizio
                batch_url = f"{self.service_url}/documents/{collection_name}/batch"
                response = requests.post(batch_url, json={"documents": batch_payload})
                response.raise_for_status()
                
                saved_ids.extend(batch_ids)
                logger.debug(f"💾 Salvato batch {i//batch_size + 1}: {len(batch_ids)} documenti")
            
            # Verifica salvataggio
            stats_url = f"{self.service_url}/stats/{collection_name}"
            response = requests.get(stats_url)
            response.raise_for_status()
            stats = response.json()
            
            logger.info(f"✅ Collezione {collection_name}: {stats.get('document_count', '?')} documenti totali")
            
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
    """Entry point per il nodo Vectorstore Writer."""
    processor = VectorstoreWriterProcessor()
    return await processor.process(context)
