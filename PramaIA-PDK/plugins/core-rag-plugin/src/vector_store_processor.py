import numpy as np
import json
import os
import time
import logging
from typing import Dict, Any, List, Optional, Union

# Logger adapter: prefer local .logger, fallback to pramaialog client, else stdlib
try:
    from .logger import debug as log_debug, info as log_info, warning as log_warning, error as log_error
    from .logger import flush as log_flush, close as log_close
except Exception:
    try:
        from PramaIA_LogService.clients.pramaialog import PramaIALogger

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

class VectorStoreProcessor:
    """
    Processore per salvare e recuperare embedding vettoriali da un database vettoriale.
    Supporta operazioni di archiviazione, ricerca ed eliminazione.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        
        # Estrai parametri di configurazione
        self.db_type = config.get("db_type", "chroma")
        self.collection_name = config.get("collection_name", "documents")
        self.persist_directory = config.get("persist_directory", "./vector_db")
        self.default_operation = config.get("default_operation", "search")
        self.embedding_dimension = config.get("embedding_dimension", 1536)
        self.similarity_metric = config.get("similarity_metric", "cosine")
        self.top_k = config.get("top_k", 5)
        self.connection_string = config.get("connection_string", "")
        self.api_key = config.get("api_key", "")
        
        # Inizializza il database vettoriale
        self._initialize_vector_db()
    
    def _initialize_vector_db(self):
        """
        Inizializza il database vettoriale in base alla configurazione.
        """
        self._log_info(f"Inizializzazione database vettoriale {self.db_type}")
        
        # Nella realtà, qui ci sarebbe l'inizializzazione del database vettoriale specifico
        # In questa simulazione, creiamo una directory per la persistenza se necessario
        if self.db_type in ["chroma", "faiss"] and self.persist_directory:
            os.makedirs(self.persist_directory, exist_ok=True)
            self._log_info(f"Directory di persistenza creata: {self.persist_directory}")
        
        # Simula l'inizializzazione del database
        self._db = self._create_simulated_db()
    
    def _create_simulated_db(self):
        """
        Crea un database vettoriale simulato.
        
        Returns:
            Dizionario che simula un database vettoriale
        """
        # Simula un database vettoriale con un dizionario
        db_file = os.path.join(self.persist_directory, f"{self.collection_name}.json")
        
        if os.path.exists(db_file):
            try:
                with open(db_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self._log_error(f"Errore nella lettura del database: {e}")
        
        # Crea un nuovo database vuoto
        return {
            "type": self.db_type,
            "collection": self.collection_name,
            "documents": {},  # id -> documento
            "metadata": {},   # id -> metadata
            "embeddings": {}, # id -> embedding
            "timestamp": time.time()
        }
    
    def _save_simulated_db(self):
        """
        Salva il database vettoriale simulato su disco.
        """
        db_file = os.path.join(self.persist_directory, f"{self.collection_name}.json")
        
        try:
            with open(db_file, 'w') as f:
                json.dump(self._db, f, indent=2)
            self._log_info(f"Database salvato in {db_file}")
        except Exception as e:
            self._log_error(f"Errore nel salvataggio del database: {e}")
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Elabora l'input ed esegue operazioni sul database vettoriale.
        
        Args:
            inputs: Dizionario con l'operazione da eseguire e i dati relativi
            
        Returns:
            Dizionario con i risultati dell'operazione e lo stato
        """
        # Determina l'operazione da eseguire
        operation = inputs.get("operation", self.default_operation)
        
        result = {}
        status = {"success": True, "timestamp": time.time()}
        
        try:
            if operation == "store":
                # Archivia documenti nel database
                result = await self._store_documents(inputs)
                status["operation"] = "store"
                
            elif operation == "search":
                # Cerca documenti nel database
                result = await self._search_documents(inputs)
                status["operation"] = "search"
                
            elif operation == "delete":
                # Elimina documenti dal database
                result = await self._delete_documents(inputs)
                status["operation"] = "delete"
                
            else:
                # Operazione non supportata
                raise ValueError(f"Operazione non supportata: {operation}")
            
        except Exception as e:
            self._log_error(f"Errore nell'operazione {operation}: {e}")
            status["success"] = False
            status["error"] = str(e)
        
        return {
            "results": result,
            "status": status
        }
    
    async def _store_documents(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Archivia documenti nel database vettoriale.
        
        Args:
            inputs: Dizionario con i documenti da archiviare
            
        Returns:
            Dizionario con i risultati dell'operazione
        """
        if "documents" not in inputs:
            raise ValueError("Input 'documents' richiesto ma non fornito")
        
        documents = inputs["documents"]
        
        if not isinstance(documents, list):
            raise ValueError("L'input 'documents' deve essere una lista")
        
        # Verifica che i documenti siano validi
        for doc in documents:
            if not isinstance(doc, dict):
                raise ValueError("Ogni documento deve essere un dizionario")
            
            if "text" not in doc:
                raise ValueError("Ogni documento deve avere un campo 'text'")
            
            if "embedding" not in doc:
                raise ValueError("Ogni documento deve avere un campo 'embedding'")
        
        # Aggiungi i documenti al database
        for doc in documents:
            # Genera un ID se non presente
            doc_id = doc.get("id", f"doc_{int(time.time())}_{len(self._db['documents'])}")
            
            # Estrai testo, embedding e metadati
            text = doc["text"]
            embedding = doc["embedding"]
            metadata = doc.get("metadata", {})
            
            # Archivia nel database simulato
            self._db["documents"][doc_id] = text
            self._db["embeddings"][doc_id] = embedding
            self._db["metadata"][doc_id] = metadata
        
        # Salva il database
        self._save_simulated_db()
        
        return {
            "stored_count": len(documents),
            "stored_ids": [doc.get("id", f"doc_{i}") for i, doc in enumerate(documents)]
        }
    
    async def _search_documents(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cerca documenti nel database vettoriale.
        
        Args:
            inputs: Dizionario con la query di ricerca
            
        Returns:
            Dizionario con i risultati della ricerca
        """
        # Verifica che ci sia una query testuale o un embedding
        if "query" not in inputs and "query_embedding" not in inputs:
            raise ValueError("È richiesto 'query' o 'query_embedding'")
        
        # Usa l'embedding fornito o converte la query testuale
        if "query_embedding" in inputs:
            query_embedding = inputs["query_embedding"]
        else:
            # Nella realtà, qui convertiremmo la query in un embedding
            # In questa simulazione, generiamo un embedding casuale ma deterministico
            query = inputs["query"]
            seed = sum(ord(c) for c in query)
            np.random.seed(seed)
            query_embedding = np.random.rand(self.embedding_dimension).tolist()
        
        # Verifica che l'embedding sia valido
        if not isinstance(query_embedding, list):
            raise ValueError("L'embedding della query deve essere una lista")
        
        # Converti l'embedding in numpy array
        query_embedding_np = np.array(query_embedding)
        
        # Cerca i documenti più simili
        results = []
        
        for doc_id, embedding in self._db["embeddings"].items():
            # Converti l'embedding in numpy array
            doc_embedding_np = np.array(embedding)
            
            # Calcola la similarità
            similarity = self._calculate_similarity(query_embedding_np, doc_embedding_np)
            
            # Aggiungi alla lista dei risultati
            results.append({
                "id": doc_id,
                "text": self._db["documents"][doc_id],
                "metadata": self._db["metadata"].get(doc_id, {}),
                "similarity": float(similarity)
            })
        
        # Ordina i risultati per similarità (decrescente)
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Limita ai top_k risultati
        results = results[:self.top_k]
        
        return {
            "matches": results,
            "count": len(results)
        }
    
    def _calculate_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calcola la similarità tra due vettori.
        
        Args:
            vec1: Primo vettore
            vec2: Secondo vettore
            
        Returns:
            Valore di similarità
        """
        if self.similarity_metric == "cosine":
            # Similarità del coseno
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return float(np.dot(vec1, vec2) / (norm1 * norm2))
            
        elif self.similarity_metric == "euclidean":
            # Distanza euclidea (trasformata in similarità)
            distance = np.linalg.norm(vec1 - vec2)
            return float(1.0 / (1.0 + distance))
            
        elif self.similarity_metric == "dot_product":
            # Prodotto scalare
            return float(np.dot(vec1, vec2))
            
        else:
            # Default: similarità del coseno
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    async def _delete_documents(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Elimina documenti dal database vettoriale.
        
        Args:
            inputs: Dizionario con gli ID dei documenti da eliminare
            
        Returns:
            Dizionario con i risultati dell'operazione
        """
        if "ids" not in inputs:
            raise ValueError("Input 'ids' richiesto ma non fornito")
        
        ids = inputs["ids"]
        
        if not isinstance(ids, list):
            raise ValueError("L'input 'ids' deve essere una lista")
        
        # Elimina i documenti dal database
        deleted_ids = []
        
        for doc_id in ids:
            if doc_id in self._db["documents"]:
                # Elimina il documento, l'embedding e i metadati
                self._db["documents"].pop(doc_id, None)
                self._db["embeddings"].pop(doc_id, None)
                self._db["metadata"].pop(doc_id, None)
                deleted_ids.append(doc_id)
        
        # Salva il database
        self._save_simulated_db()
        
        return {
            "deleted_count": len(deleted_ids),
            "deleted_ids": deleted_ids
        }
    
    def _log_info(self, message: str) -> None:
        """
        Registra un messaggio informativo.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
        # Simulazione: nella realtà, questa funzione interagirebbe con il sistema di logging
        try:
            log_info(f"[VectorStoreProcessor] INFO: {message}")
        except Exception:
            pass
    
    def _log_warning(self, message: str) -> None:
        """
        Registra un messaggio di avviso.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
        # Simulazione: nella realtà, questa funzione interagirebbe con il sistema di logging
        try:
            log_warning(f"[VectorStoreProcessor] ATTENZIONE: {message}")
        except Exception:
            pass
    
    def _log_error(self, message: str) -> None:
        """
        Registra un messaggio di errore.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
        # Simulazione: nella realtà, questa funzione interagirebbe con il sistema di logging
        try:
            log_error(f"[VectorStoreProcessor] ERRORE: {message}")
        except Exception:
            pass
