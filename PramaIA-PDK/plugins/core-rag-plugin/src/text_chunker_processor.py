import re
import logging
from typing import Dict, Any, List, Optional, Union

# Logger adapter: prefer local .logger, fallback to PramaIA LogService client, else stdlib
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

class TextChunkerProcessor:
    """
    Processore per dividere un testo in chunk più piccoli.
    Supporta vari metodi di divisione come carattere, parola, frase, paragrafo e ricorsivo.
    """
    
    def __init__(self, node_id: str, config: Dict[str, Any]):
        """Inizializzazione del processore con configurazione."""
        self.node_id = node_id
        self.config = config
        
        # Estrai parametri di configurazione
        self.chunk_size = config.get("chunk_size", 1000)
        self.chunk_overlap = config.get("chunk_overlap", 200)
        self.split_method = config.get("split_method", "paragraph")
        self.include_metadata = config.get("include_metadata", True)
        self.add_chunk_metadata = config.get("add_chunk_metadata", True)
    
    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Elabora l'input e divide il testo in chunk.
        
        Args:
            inputs: Dizionario con il testo da dividere e metadati opzionali
            
        Returns:
            Dizionario con i chunk di testo
        """
        if "text" not in inputs:
            raise ValueError("Input 'text' richiesto ma non fornito")
        
        text = inputs["text"]
        metadata = inputs.get("metadata", {})
        
        # Verifica che il testo sia valido
        if not text or not isinstance(text, str):
            return {"chunks": []}
        
        # Dividi il testo in chunk in base al metodo selezionato
        if self.split_method == "character":
            chunks = self._split_by_character(text)
        elif self.split_method == "word":
            chunks = self._split_by_word(text)
        elif self.split_method == "sentence":
            chunks = self._split_by_sentence(text)
        elif self.split_method == "paragraph":
            chunks = self._split_by_paragraph(text)
        elif self.split_method == "recursive":
            chunks = self._split_recursive(text)
        else:
            # Default a paragrafo
            chunks = self._split_by_paragraph(text)
        
        # Aggiungi metadati ai chunk
        result_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_obj = {
                "text": chunk,
                "chunk_id": i
            }
            
            # Aggiungi metadati del chunk se richiesto
            if self.add_chunk_metadata:
                chunk_obj["chunk_metadata"] = {
                    "index": i,
                    "total_chunks": len(chunks),
                    "length": len(chunk)
                }
            
            # Aggiungi metadati originali se richiesto
            if self.include_metadata and metadata:
                chunk_obj["metadata"] = metadata
            
            result_chunks.append(chunk_obj)
        
        return {"chunks": result_chunks}
    
    def _split_by_character(self, text: str) -> List[str]:
        """
        Divide il testo in chunk di dimensione fissa in base ai caratteri.
        
        Args:
            text: Testo da dividere
            
        Returns:
            Lista di chunk
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Determina la fine del chunk
            end = min(start + self.chunk_size, text_length)
            
            # Aggiungi il chunk alla lista
            chunks.append(text[start:end])
            
            # Sposta l'inizio del prossimo chunk tenendo conto della sovrapposizione
            start += self.chunk_size - self.chunk_overlap
            
            # Assicurati che l'inizio sia sempre maggiore di 0
            start = max(start, 0)
            
            # Esci se abbiamo raggiunto la fine del testo
            if start >= text_length:
                break
        
        return chunks
    
    def _split_by_word(self, text: str) -> List[str]:
        """
        Divide il testo in chunk di dimensione approssimativa in base alle parole.
        
        Args:
            text: Testo da dividere
            
        Returns:
            Lista di chunk
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            # Aggiungi uno spazio per ogni parola tranne la prima
            word_size = len(word) + (1 if current_chunk else 0)
            
            # Se aggiungere questa parola supera la dimensione massima, inizia un nuovo chunk
            if current_size + word_size > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                
                # Determina quante parole includere nel nuovo chunk per la sovrapposizione
                overlap_words = []
                overlap_size = 0
                for w in reversed(current_chunk):
                    if overlap_size + len(w) + 1 <= self.chunk_overlap:
                        overlap_words.insert(0, w)
                        overlap_size += len(w) + 1
                    else:
                        break
                
                # Inizia un nuovo chunk con le parole di sovrapposizione
                current_chunk = overlap_words
                current_size = overlap_size
            
            # Aggiungi la parola al chunk corrente
            current_chunk.append(word)
            current_size += word_size
        
        # Aggiungi l'ultimo chunk se non è vuoto
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _split_by_sentence(self, text: str) -> List[str]:
        """
        Divide il testo in chunk basati su frasi complete.
        
        Args:
            text: Testo da dividere
            
        Returns:
            Lista di chunk
        """
        # Pattern per dividere in frasi (punti, punti esclamativi, punti interrogativi)
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)
        
        # Filtra le frasi vuote
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence) + (1 if current_chunk else 0)
            
            # Se aggiungere questa frase supera la dimensione massima, inizia un nuovo chunk
            if current_size + sentence_size > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_size = 0
            
            # Aggiungi la frase al chunk corrente
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Aggiungi l'ultimo chunk se non è vuoto
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _split_by_paragraph(self, text: str) -> List[str]:
        """
        Divide il testo in chunk basati su paragrafi.
        
        Args:
            text: Testo da dividere
            
        Returns:
            Lista di chunk
        """
        # Pattern per dividere in paragrafi (due o più newline consecutivi)
        paragraph_pattern = r'\n\s*\n'
        paragraphs = re.split(paragraph_pattern, text)
        
        # Filtra i paragrafi vuoti
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for paragraph in paragraphs:
            paragraph_size = len(paragraph) + (2 if current_chunk else 0)  # +2 per il doppio newline
            
            # Se aggiungere questo paragrafo supera la dimensione massima, inizia un nuovo chunk
            if current_size + paragraph_size > self.chunk_size and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                
                # Cerca paragrafi di sovrapposizione
                overlap_paragraphs = []
                overlap_size = 0
                for p in reversed(current_chunk):
                    if overlap_size + len(p) + 2 <= self.chunk_overlap:
                        overlap_paragraphs.insert(0, p)
                        overlap_size += len(p) + 2
                    else:
                        break
                
                # Inizia un nuovo chunk con i paragrafi di sovrapposizione
                current_chunk = overlap_paragraphs
                current_size = overlap_size
            
            # Aggiungi il paragrafo al chunk corrente
            current_chunk.append(paragraph)
            current_size += paragraph_size
        
        # Aggiungi l'ultimo chunk se non è vuoto
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        
        return chunks
    
    def _split_recursive(self, text: str) -> List[str]:
        """
        Divide il testo in modo ricorsivo, cercando di mantenere il contesto.
        
        Args:
            text: Testo da dividere
            
        Returns:
            Lista di chunk
        """
        # Inizia con la divisione per paragrafo
        chunks = self._split_by_paragraph(text)
        
        # Se qualche chunk è ancora troppo grande, dividilo ulteriormente per frase
        result_chunks = []
        for chunk in chunks:
            if len(chunk) <= self.chunk_size:
                result_chunks.append(chunk)
            else:
                # Dividi ulteriormente per frase
                sentence_chunks = self._split_by_sentence(chunk)
                
                # Se qualche chunk è ancora troppo grande, dividilo per parola
                for sentence_chunk in sentence_chunks:
                    if len(sentence_chunk) <= self.chunk_size:
                        result_chunks.append(sentence_chunk)
                    else:
                        # Dividi ulteriormente per parola
                        word_chunks = self._split_by_word(sentence_chunk)
                        result_chunks.extend(word_chunks)
        
        return result_chunks
    
    def _log_info(self, message: str) -> None:
        """
        Registra un messaggio informativo.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
        try:
            log_info(f"[TextChunkerProcessor] INFO: {message}")
        except Exception:
            pass

    def _log_warning(self, message: str) -> None:
        """
        Registra un messaggio di avviso.
        In una implementazione reale, questo userebbe un sistema di logging appropriato.
        """
        try:
            log_warning(f"[TextChunkerProcessor] ATTENZIONE: {message}")
        except Exception:
            pass
