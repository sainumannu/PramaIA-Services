"""
Text Chunker Processor

Divide il testo in chunks per una migliore elaborazione e indicizzazione.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class TextChunkerProcessor:
    """Processore per dividere testo in chunks."""
    
    async def process(self, context) -> Dict[str, Any]:
        """
        Divide il testo in chunks gestibili.
        """
        logger.info("[TextChunker] INGRESSO nodo: process")
        try:
            config = context.get('config', {})
            inputs = context.get('inputs', {})
            text_input = inputs.get('text_input', '')
            if not text_input:
                raise ValueError("Nessun testo fornito in input")
            chunk_size = config.get('chunk_size', 1000)
            chunk_overlap = config.get('chunk_overlap', 200)
            separator = config.get('separator', '\n\n')
            chunks = self._create_chunks(
                text_input,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separator=separator
            )
            logger.info(f"[TextChunker] USCITA nodo (successo): Testo diviso in {len(chunks)} chunks")
            return {
                "status": "success",
                "chunks_output": chunks,
                "chunk_count": len(chunks),
                "original_length": len(text_input),
                "average_chunk_size": sum(len(chunk) for chunk in chunks) // len(chunks) if chunks else 0
            }
        except Exception as e:
            logger.error(f"[TextChunker] USCITA nodo (errore): {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "chunks_output": []
            }
    
    def _create_chunks(self, text: str, chunk_size: int, chunk_overlap: int, separator: str) -> List[str]:
        """
        Crea chunks di testo con sovrapposizione.
        
        Args:
            text: Testo da dividere
            chunk_size: Dimensione massima del chunk
            chunk_overlap: Sovrapposizione tra chunks
            separator: Separatore per divisione intelligente
            
        Returns:
            Lista di chunks di testo
        """
        if not text:
            return []
        
        # Se il testo è più piccolo del chunk_size, restituiscilo intero
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        
        # Prima divisione usando il separatore
        sections = text.split(separator)
        
        current_chunk = ""
        
        for section in sections:
            # Se la sezione corrente più quella nuova eccede chunk_size
            if len(current_chunk) + len(section) + len(separator) > chunk_size:
                if current_chunk:
                    # Salva il chunk corrente
                    chunks.append(current_chunk.strip())
                    
                    # Inizia nuovo chunk con sovrapposizione
                    if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                        overlap_text = current_chunk[-chunk_overlap:]
                        current_chunk = overlap_text + separator + section
                    else:
                        current_chunk = section
                else:
                    # La sezione da sola è troppo grande, dividila forzatamente
                    if len(section) > chunk_size:
                        sub_chunks = self._split_large_section(section, chunk_size, chunk_overlap)
                        chunks.extend(sub_chunks[:-1])  # Aggiungi tutti tranne l'ultimo
                        current_chunk = sub_chunks[-1] if sub_chunks else ""
                    else:
                        current_chunk = section
            else:
                # Aggiungi sezione al chunk corrente
                if current_chunk:
                    current_chunk += separator + section
                else:
                    current_chunk = section
        
        # Aggiungi l'ultimo chunk se non vuoto
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_large_section(self, section: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """
        Divide una sezione troppo grande in chunks più piccoli.
        
        Args:
            section: Sezione da dividere
            chunk_size: Dimensione massima del chunk
            chunk_overlap: Sovrapposizione tra chunks
            
        Returns:
            Lista di chunks della sezione
        """
        chunks = []
        start = 0
        
        while start < len(section):
            end = start + chunk_size
            
            # Se non è l'ultimo chunk, cerca un punto di divisione migliore
            if end < len(section):
                # Cerca spazio, punto o newline vicino alla fine
                search_start = max(start + chunk_size - 100, start)
                for i in range(end, search_start, -1):
                    if section[i] in [' ', '.', '\n', '!', '?']:
                        end = i + 1
                        break
            
            chunk = section[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Calcola nuovo inizio con sovrapposizione
            if chunk_overlap > 0 and end < len(section):
                start = end - chunk_overlap
            else:
                start = end
        
        return chunks


# Funzione entry point per il PDK
async def process_node(context):
    """Entry point per il nodo Text Chunker."""
    processor = TextChunkerProcessor()
    return await processor.process(context)
