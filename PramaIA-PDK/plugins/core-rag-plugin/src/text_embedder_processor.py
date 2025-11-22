import numpy as np
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

class TextEmbedderProcessor:
    """
    Processore per convertire testo in embedding vettoriali.
    Supporta vari modelli di embedding come OpenAI, Sentence Transformers e Hugging Face.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        
        # Estrai parametri di configurazione
        self.model = config.get("model", "openai")
        self.model_name = config.get("model_name", "text-embedding-ada-002")
        self.openai_api_key = config.get("openai_api_key", "")
        self.dimensions = config.get("dimensions", 1536)
        self.batch_size = config.get("batch_size", 32)
        self.normalize = config.get("normalize", True)
        
        # Inizializza il modello di embedding
        self._initialize_model()
    
    def _initialize_model(self):
        """
        Inizializza il modello di embedding in base alla configurazione.
        """
        self.embedding_function = None
        
        if self.model == "openai":
            try:
                # Simulazione: nella realtà, qui ci sarebbe l'inizializzazione del client OpenAI
                self._log_info(f"Inizializzazione modello OpenAI {self.model_name}")
                # Qui ci sarebbe l'inizializzazione vera del client, ad esempio:
                # import openai
                # openai.api_key = self.openai_api_key
                # self.embedding_function = lambda texts: [...]
                
                # Nella simulazione, usa un generatore di embedding casuale
                self.embedding_function = self._simulate_openai_embeddings
            except Exception as e:
                self._log_error(f"Errore nell'inizializzazione del modello OpenAI: {e}")
        
        elif self.model == "sentence-transformers":
            try:
                # Simulazione: nella realtà, qui ci sarebbe l'inizializzazione di sentence-transformers
                self._log_info(f"Inizializzazione modello Sentence Transformers {self.model_name}")
                # Qui ci sarebbe l'inizializzazione vera, ad esempio:
                # from sentence_transformers import SentenceTransformer
                # model = SentenceTransformer(self.model_name)
                # self.embedding_function = lambda texts: [...]
                
                # Nella simulazione, usa un generatore di embedding casuale
                self.embedding_function = self._simulate_sentence_transformer_embeddings
            except Exception as e:
                self._log_error(f"Errore nell'inizializzazione del modello Sentence Transformers: {e}")
        
        elif self.model == "huggingface":
            try:
                # Simulazione: nella realtà, qui ci sarebbe l'inizializzazione di un modello Hugging Face
                self._log_info(f"Inizializzazione modello Hugging Face {self.model_name}")
                # Qui ci sarebbe l'inizializzazione vera, ad esempio:
                # from transformers import AutoModel, AutoTokenizer
                # tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                # model = AutoModel.from_pretrained(self.model_name)
                # self.embedding_function = lambda texts: [...]
                
                # Nella simulazione, usa un generatore di embedding casuale
                self.embedding_function = self._simulate_huggingface_embeddings
            except Exception as e:
                self._log_error(f"Errore nell'inizializzazione del modello Hugging Face: {e}")
        
        elif self.model == "custom":
            # Qui potrebbe esserci l'implementazione di un modello custom
            self._log_info("Inizializzazione modello custom")
            self.embedding_function = self._simulate_custom_embeddings
        
        else:
            self._log_warning(f"Modello {self.model} non supportato, utilizzo simulazione")
            # Usa comunque un generatore di embedding casuale
            self.embedding_function = self._simulate_openai_embeddings
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Elabora l'input e genera gli embedding vettoriali.
        
        Args:
            inputs: Dizionario con il testo o array di testi da convertire in embedding
            
        Returns:
            Dizionario con gli embedding vettoriali e i documenti
        """
        # Ottieni i testi da convertire
        if "texts" in inputs and isinstance(inputs["texts"], list):
            texts = inputs["texts"]
        elif "text" in inputs:
            texts = [inputs["text"]]
        else:
            raise ValueError("Input 'text' o 'texts' richiesto ma non fornito")
        
        # Ottieni i metadati (opzionali)
        metadata = inputs.get("metadata", None)
        
        # Verifica che ci siano testi validi
        if not texts or not all(isinstance(t, str) for t in texts):
            raise ValueError("I testi devono essere stringhe valide")
        
        # Genera gli embedding
        embeddings = await self._generate_embeddings(texts)
        
        # Prepara i documenti con testo ed embedding
        documents = []
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            doc = {
                "text": text,
                "embedding": embedding.tolist(),  # Converti in lista per la serializzazione JSON
                "id": f"doc_{i}"
            }
            
            # Aggiungi metadati se presenti
            if metadata is not None:
                if isinstance(metadata, list) and len(metadata) > i:
                    # Se è una lista di metadati, prendi quello corrispondente
                    doc["metadata"] = metadata[i]
                elif isinstance(metadata, dict):
                    # Se è un singolo dizionario, usalo per tutti
                    doc["metadata"] = metadata
            
            documents.append(doc)
        
        return {
            "embeddings": [e.tolist() for e in embeddings],  # Converti in liste per la serializzazione JSON
            "documents": documents
        }
    
    async def _generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Genera gli embedding per i testi.
        
        Args:
            texts: Lista di testi
            
        Returns:
            Lista di array numpy con gli embedding
        """
        if self.embedding_function is None:
            raise ValueError("Modello di embedding non inizializzato")
        
        # Elabora i testi in batch
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i+self.batch_size]
            try:
                # Genera gli embedding per il batch
                batch_embeddings = self.embedding_function(batch)
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                self._log_error(f"Errore nella generazione degli embedding: {e}")
                # Genera embedding casuali come fallback
                for _ in batch:
                    random_embedding = np.random.rand(self.dimensions)
                    if self.normalize:
                        random_embedding = random_embedding / np.linalg.norm(random_embedding)
                    all_embeddings.append(random_embedding)
        
        return all_embeddings
    
    def _simulate_openai_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Simula la generazione di embedding con OpenAI.
        
        Args:
            texts: Lista di testi
            
        Returns:
            Lista di array numpy con gli embedding
        """
        embeddings = []
        for text in texts:
            # Genera un embedding casuale ma deterministico (basato sul testo)
            seed = sum(ord(c) for c in text)
            np.random.seed(seed)
            embedding = np.random.rand(self.dimensions)
            
            # Normalizza se richiesto
            if self.normalize:
                embedding = embedding / np.linalg.norm(embedding)
            
            embeddings.append(embedding)
        
        return embeddings
    
    def _simulate_sentence_transformer_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Simula la generazione di embedding con Sentence Transformers.
        
        Args:
            texts: Lista di testi
            
        Returns:
            Lista di array numpy con gli embedding
        """
        # Per la simulazione, usa lo stesso metodo di OpenAI
        return self._simulate_openai_embeddings(texts)
    
    def _simulate_huggingface_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Simula la generazione di embedding con Hugging Face.
        
        Args:
            texts: Lista di testi
            
        Returns:
            Lista di array numpy con gli embedding
        """
        # Per la simulazione, usa lo stesso metodo di OpenAI
        return self._simulate_openai_embeddings(texts)
    
    def _simulate_custom_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Simula la generazione di embedding con un modello custom.
        
        Args:
            texts: Lista di testi
            
        Returns:
            Lista di array numpy con gli embedding
        """
        # Per la simulazione, usa lo stesso metodo di OpenAI
        return self._simulate_openai_embeddings(texts)
    
    def _log_info(self, message: str) -> None:
        """
        Registra un messaggio informativo.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
        try:
            log_info(f"[TextEmbedderProcessor] INFO: {message}")
        except Exception:
            pass

    def _log_warning(self, message: str) -> None:
        """
        Registra un messaggio di avviso.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
        try:
            log_warning(f"[TextEmbedderProcessor] ATTENZIONE: {message}")
        except Exception:
            pass

    def _log_error(self, message: str) -> None:
        """
        Registra un messaggio di errore.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
        try:
            log_error(f"[TextEmbedderProcessor] ERRORE: {message}")
        except Exception:
            pass
