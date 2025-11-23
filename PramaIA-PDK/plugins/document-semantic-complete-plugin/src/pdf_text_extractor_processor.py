"""
PDF Text Extractor Processor

Estrae testo da file PDF utilizzando PyPDF2 e altre librerie.
"""

import PyPDF2
import io
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PDFTextExtractorProcessor:
    """Processore per estrazione testo da PDF."""
    
    async def process(self, context) -> Dict[str, Any]:
        """
        Estrae testo da un file PDF.
        """
        logger.info("[PDFTextExtractor] INGRESSO nodo: process")
        try:
            config = context.get('config', {})
            inputs = context.get('inputs', {})
            pdf_file = inputs.get('pdf_file')
            if not pdf_file:
                raise ValueError("Nessun file PDF fornito in input")
            preserve_layout = config.get('preserve_layout', True)
            extract_images = config.get('extract_images', False)
            extracted_text = self._extract_text_from_pdf(
                pdf_file, 
                preserve_layout=preserve_layout,
                extract_images=extract_images
            )
            logger.info(f"[PDFTextExtractor] USCITA nodo (successo): Estratto testo da PDF: {len(extracted_text)} caratteri")
            return {
                "status": "success",
                "text_output": extracted_text,
                "length": len(extracted_text),
                "pages_processed": self._get_page_count(pdf_file)
            }
        except Exception as e:
            logger.error(f"[PDFTextExtractor] USCITA nodo (errore): {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "text_output": ""
            }
    
    def _extract_text_from_pdf(self, pdf_file, preserve_layout=True, extract_images=False) -> str:
        """Estrae testo da file PDF."""
        text_content = []
        
        # Se il file è bytes, convertilo in BytesIO
        if isinstance(pdf_file, bytes):
            pdf_file = io.BytesIO(pdf_file)
        elif isinstance(pdf_file, str):
            # Se è un path, aprilo
            pdf_file = open(pdf_file, 'rb')
        
        try:
            # Usa PyPDF2 per estrarre il testo
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    
                    if preserve_layout:
                        # Mantieni la struttura originale
                        text_content.append(f"--- Pagina {page_num + 1} ---\n{page_text}\n")
                    else:
                        # Pulisci il testo
                        cleaned_text = self._clean_text(page_text)
                        text_content.append(cleaned_text)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Errore estrazione pagina {page_num + 1}: {str(e)}")
                    continue
            
            return "\n".join(text_content)
            
        finally:
            if hasattr(pdf_file, 'close'):
                pdf_file.close()
    
    def _clean_text(self, text: str) -> str:
        """Pulisce il testo estratto da caratteri indesiderati."""
        if not text:
            return ""
        
        # Rimuovi caratteri di controllo
        cleaned = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        # Normalizza spazi multipli
        cleaned = ' '.join(cleaned.split())
        
        return cleaned
    
    def _get_page_count(self, pdf_file) -> int:
        """Ottiene il numero di pagine del PDF."""
        try:
            if isinstance(pdf_file, bytes):
                pdf_file = io.BytesIO(pdf_file)
            elif isinstance(pdf_file, str):
                pdf_file = open(pdf_file, 'rb')
                
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            return len(pdf_reader.pages)
            
        except Exception as e:
            logger.warning(f"⚠️ Errore conteggio pagine: {str(e)}")
            return 0
        finally:
            if hasattr(pdf_file, 'close'):
                pdf_file.close()


# Funzione entry point per il PDK
async def process_node(context):
    """Entry point per il nodo PDF Text Extractor."""
    processor = PDFTextExtractorProcessor()
    return await processor.process(context)
