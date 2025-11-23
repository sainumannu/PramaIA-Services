"""
Text Embedder Processor

Genera embeddings vettoriali per i chunks di testo utilizzando sentence-transformers.
"""

from typing import Dict, Any, List
import numpy as np

# Logger adapter
try:
    from .logger import debug as log_debug, info as log_info, warning as log_warning, error as log_error
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

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    log_warning("⚠️ sentence-transformers non disponibile, usando embeddings mock")


class TextEmbedderProcessor:
    """Processore per generare embeddings vettoriali."""
    
    def __init__(self):
        self.model = None
        self.current_model_name = None
    
    async def process(self, context) -> Dict[str, Any]:
        """
        Genera embeddings per chunks di testo.
        """
        log_info("[TextEmbedder] INGRESSO nodo: process")
        try:
            config = context.get('config', {})
            inputs = context.get('inputs', {})
            text_chunks = inputs.get('text_chunks', [])
            if not text_chunks:
                raise ValueError("Nessun chunk di testo fornito in input")
            model_name = config.get('model', 'sentence-transformers/all-MiniLM-L6-v2')
            batch_size = config.get('batch_size', 32)
            normalize_embeddings = config.get('normalize_embeddings', True)
            await self._load_model(model_name)
            embeddings = await self._generate_embeddings(
                text_chunks,
                batch_size=batch_size,
                normalize=normalize_embeddings
            )
            log_info(f"[TextEmbedder] USCITA nodo (successo): Generati embeddings per {len(text_chunks)} chunks")
            return {
                "status": "success",
                "embeddings_output": {
                    "embeddings": embeddings,
                    "chunks": text_chunks,
                    "model": model_name,
                    "dimensions": len(embeddings[0]) if embeddings else 0
                },
                "chunk_count": len(text_chunks),
                "embedding_dimensions": len(embeddings[0]) if embeddings else 0
            }
        except Exception as e:
            log_error(f"[TextEmbedder] USCITA nodo (errore): {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "embeddings_output": {
                    "embeddings": [],
                    "chunks": [],
                    "model": "",
                    "dimensions": 0
                }
            }
    
    async def _load_model(self, model_name: str):
        """Carica il modello per gli embeddings."""
        if self.current_model_name == model_name and self.model is not None:
            return  # Modello già caricato
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            log_warning(f"⚠️ sentence-transformers non disponibile, usando embeddings mock per {model_name}")
            self.model = "mock"
            self.current_model_name = model_name
            return
        
        try:
            log_info(f"🔄 Caricamento modello: {model_name}")
            self.model = SentenceTransformer(model_name)
            self.current_model_name = model_name
            log_info(f"✅ Modello caricato: {model_name}")
            
        except Exception as e:
            log_error(f"❌ Errore caricamento modello {model_name}: {str(e)}")
            # Fallback a modello mock
            self.model = "mock"
            self.current_model_name = model_name
    
    async def _generate_embeddings(self, chunks: List[str], batch_size: int, normalize: bool) -> List[List[float]]:
        """
        Genera embeddings per i chunks di testo.
        
        Args:
            chunks: Lista di chunks di testo
            batch_size: Dimensione del batch per l'elaborazione
            normalize: Se normalizzare gli embeddings
            
        Returns:
            Lista di embeddings (liste di float)
        """
        if not chunks:
            return []
        
        if self.model == "mock" or not SENTENCE_TRANSFORMERS_AVAILABLE:
            return self._generate_mock_embeddings(chunks)
        
        try:
            # Genera embeddings in batch
            all_embeddings = []
            
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                
                # Genera embeddings per il batch
                batch_embeddings = self.model.encode(
                    batch_chunks,
                    normalize_embeddings=normalize,
                    show_progress_bar=len(chunks) > 100  # Progress bar solo per grandi dataset
                )
                
                # Converti in liste
                batch_embeddings_list = batch_embeddings.tolist()
                all_embeddings.extend(batch_embeddings_list)
                
                log_debug(f"🔄 Processati {min(i + batch_size, len(chunks))}/{len(chunks)} chunks")
            
            return all_embeddings
            
        except Exception as e:
            log_error(f"❌ Errore generazione embeddings: {str(e)}")
            return self._generate_mock_embeddings(chunks)
    
    def _generate_mock_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """
        Genera embeddings mock per testing (quando sentence-transformers non è disponibile).
        
        Args:
            chunks: Lista di chunks di testo
            
        Returns:
            Lista di embeddings mock (384 dimensioni)
        """
    log_info(f"🔄 Generazione embeddings mock per {len(chunks)} chunks")
        
        embeddings = []
        for chunk in chunks:
            # Genera embedding deterministico basato sul hash del testo
            hash_value = hash(chunk)
            np.random.seed(hash_value % (2**32))  # Seed deterministico
            
            # Genera vettore random di 384 dimensioni (come all-MiniLM-L6-v2)
            embedding = np.random.normal(0, 1, 384)
            
            # Normalizza il vettore
            embedding = embedding / np.linalg.norm(embedding)
            
            embeddings.append(embedding.tolist())
        
        return embeddings


# Funzione entry point per il PDK
async def process_node(context):
    """Entry point per il nodo Text Embedder."""
    processor = TextEmbedderProcessor()
    return await processor.process(context)
