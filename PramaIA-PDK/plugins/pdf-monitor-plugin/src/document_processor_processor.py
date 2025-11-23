"""
Document Processor per PDK.
Estrae e processa testo da documenti PDF.
"""

import os
import tempfile
from typing import Dict, Any, List, Optional
from datetime import datetime

# Importa il logger standardizzato
import sys

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

# Importazioni per l'elaborazione PDF
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    logger.warning("PyMuPDF non disponibile. Alcune funzionalità saranno limitate.")
    HAS_PYMUPDF = False
    fitz = None

# Implementazione base di un text splitter per ambienti senza langchain
class SimpleTextSplitter:
    def __init__(self, chunk_size=1000, chunk_overlap=200, separators=None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
        
    def split_text(self, text):
        # Implementazione semplificata di text chunking
        chunks = []
        current_chunk = ""
        
        # Uso il primo separatore per una divisione iniziale
        first_sep = self.separators[0] if self.separators else "\n\n"
        paragraphs = text.split(first_sep)
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # Se il paragrafo da solo è troppo grande, divide ulteriormente
            if len(para) > self.chunk_size:
                sub_chunks = self._split_large_paragraph(para)
                for sub in sub_chunks:
                    if len(current_chunk) + len(sub) + 2 <= self.chunk_size:
                        if current_chunk:
                            current_chunk += "\n\n" + sub
                        else:
                            current_chunk = sub
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sub
            else:
                # Aggiungi il paragrafo al chunk corrente o crea un nuovo chunk
                if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                    if current_chunk:
                        current_chunk += "\n\n" + para
                    else:
                        current_chunk = para
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = para
        
        # Aggiungi l'ultimo chunk se esiste
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks
        
    def _split_large_paragraph(self, paragraph):
        # Divide un paragrafo troppo grande usando i separatori
        result = []
        remaining = paragraph
        
        while len(remaining) > self.chunk_size:
            # Cerca il miglior punto di divisione
            split_point = self.chunk_size
            
            # Cerca i separatori in ordine
            for sep in self.separators[1:]:  # Salta il primo separatore che è già usato
                last_sep_pos = remaining[:self.chunk_size].rfind(sep)
                if last_sep_pos > 0:
                    split_point = last_sep_pos + len(sep)
                    break
            
            # Aggiungi la parte corrente e continua con il resto
            result.append(remaining[:split_point].strip())
            remaining = remaining[split_point - self.chunk_overlap:].strip()
        
        # Aggiungi l'ultima parte
        if remaining:
            result.append(remaining)
            
        return result

# Cerca di importare RecursiveCharacterTextSplitter da langchain, altrimenti usa la nostra implementazione
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    log_info("Usando RecursiveCharacterTextSplitter da langchain")
except ImportError:
    log_warning("langchain non disponibile, usando text splitter semplificato")
    RecursiveCharacterTextSplitter = SimpleTextSplitter

async def process(inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa il documento PDF ed estrae il testo.
    """
    # Log ingresso nodo
    chunking_strategy = inputs.get("chunking_strategy", "paragraph")
    entry_msg = f"[DocumentProcessor] INGRESSO nodo: chunking_strategy={chunking_strategy}"
    log_info(entry_msg)
    try:
        # Estrazione parametri
        file_path = inputs.get("file_path")
        file_content = inputs.get("file_content")
        chunk_size = inputs.get("chunk_size", 1000)
        chunk_overlap = inputs.get("chunk_overlap", 200)
        metadata = inputs.get("metadata", {})
        # Valida che ci sia o file_path o file_content
        if not file_path and not file_content:
            raise ValueError("È necessario fornire file_path o file_content")
        # Estrazione del testo dal documento
        document_text = _extract_text(file_path, file_content)
        # Divisione del testo in chunks
        chunks = _chunk_text(document_text, chunking_strategy, chunk_size, chunk_overlap)
        # Arricchimento dei metadati con informazioni sul documento
        enriched_metadata = _enrich_metadata(metadata, document_text)
        # Log uscita nodo (successo)
        exit_msg = f"[DocumentProcessor] USCITA nodo (successo): total_chunks={len(chunks)}"
        log_info(exit_msg)
        return {
            "status": "success",
            "document_text": document_text,
            "chunks": chunks,
            "total_chunks": len(chunks),
            "metadata": enriched_metadata
        }
    except Exception as e:
        # Log uscita nodo (errore)
        exit_msg = f"[DocumentProcessor] USCITA nodo (errore): {str(e)}"
        log_error(exit_msg)
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }

def _extract_text(file_path: Optional[str], file_content: Optional[bytes]) -> str:
    """Estrae il testo da un documento PDF."""
    if not HAS_PYMUPDF:
        raise ImportError("PyMuPDF (fitz) è necessario per l'elaborazione PDF")
        
    try:
        temp_file = None
        
        # Se abbiamo file_content ma non file_path, salva il contenuto in un file temporaneo
        if file_content and not file_path:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_file.write(file_content)
            temp_file.close()
            file_path = temp_file.name
        
        # Apertura del PDF
        document = fitz.open(file_path)
        
        # Estrazione del testo da ogni pagina
        text = ""
        for page_num in range(len(document)):
            page = document.load_page(page_num)
            text += page.get_text()
            # Aggiunta separatore di pagina
            if page_num < len(document) - 1:
                text += "\n\n--- Page Break ---\n\n"
        
        # Pulizia del file temporaneo se creato
        if temp_file:
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                        log_warning(f"Impossibile eliminare il file temporaneo: {str(e)}")
        
        return text
        
    except Exception as e:
    log_error(f"Errore nell'estrazione del testo: {str(e)}")
        # Pulizia del file temporaneo se creato e si è verificato un errore
        if temp_file:
            try:
                os.unlink(temp_file.name)
            except:
                pass
        raise

def _chunk_text(text: str, strategy: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Divide il testo in chunks in base alla strategia specificata."""
    try:
        if strategy == "paragraph":
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
        elif strategy == "sentence":
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ".", "!", "?", ". ", " ", ""]
            )
        elif strategy == "fixed_size":
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=[" ", ""]
            )
        else:
            raise ValueError(f"Strategia di chunking sconosciuta: {strategy}")
            
        return splitter.split_text(text)
        
    except Exception as e:
    log_error(f"Errore nel chunking del testo: {str(e)}")
        raise

def _enrich_metadata(metadata: Dict[str, Any], document_text: str) -> Dict[str, Any]:
    """Arricchisce i metadati con informazioni sul documento."""
    try:
        enriched = metadata.copy()
        
        # Aggiunge statistiche di base sul documento
        enriched["char_count"] = len(document_text)
        enriched["word_count"] = len(document_text.split())
        enriched["processed_at"] = datetime.now().isoformat()
        
        # Estrae il potenziale titolo
        lines = document_text.split("\n")
        if lines and lines[0].strip():
            potential_title = lines[0].strip()
            # Usa come titolo solo se ragionevolmente breve
            if len(potential_title) < 100:
                enriched["extracted_title"] = potential_title
        
        # Conta le pagine (in base ai nostri marcatori di interruzione pagina)
        page_count = document_text.count("--- Page Break ---") + 1
        enriched["estimated_page_count"] = page_count
        
        return enriched
        
    except Exception as e:
    log_error(f"Errore nell'arricchimento dei metadati: {str(e)}")
        # Restituisce i metadati originali se l'arricchimento fallisce
        return metadata
