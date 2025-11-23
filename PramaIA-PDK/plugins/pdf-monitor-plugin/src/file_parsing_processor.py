"""
File Parsing Processor per PDK.
Esegue il parsing di file PDF e ne estrae testo, metadati e altre informazioni.
"""

import os
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import tempfile
import json

# Importa il logger standardizzato
import sys

# DISABILITA LOGGING SU STDOUT PER EVITARE CORRUZIONE JSON
# Il PDK si aspetta SOLO JSON puro su stdout
class NoOpLogger:
    """Logger che non fa nulla per evitare corruzione output JSON"""
    def debug(self, *args, **kwargs): pass
    def info(self, *args, **kwargs): pass
    def warning(self, *args, **kwargs): pass
    def error(self, *args, **kwargs): pass
    def flush(self): pass
    def close(self): pass

logger = NoOpLogger()
log_debug = logger.debug
log_info = logger.info
log_warning = logger.warning
log_error = logger.error
log_flush = logger.flush
log_close = logger.close

# Inizializzazione PyMuPDF
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    log_warning("PyMuPDF non trovato. Alcune funzionalità saranno limitate.")
    HAS_PYMUPDF = False
    fitz = None

# Inizializzazione Pytesseract per OCR
try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    log_warning("Pytesseract non trovato. L'OCR non sarà disponibile.")
    HAS_OCR = False
    pytesseract = None

async def process(inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Elabora un file PDF estraendo testo, metadati e altre informazioni.
    """
    # Log ingresso nodo
    file_path = str(inputs.get("file_path", ""))
    entry_msg = f"[FileParsing] INGRESSO nodo: file_path={file_path}"
    log_info(entry_msg)
    start_time = time.time()
    try:
        # Estrazione e validazione dei parametri
        extract_text = bool(inputs.get("extract_text", True))
        extract_metadata = bool(inputs.get("extract_metadata", True))
        extract_images = bool(inputs.get("extract_images", False))
        extract_tables = bool(inputs.get("extract_tables", False))
        page_range = str(inputs.get("page_range", "all"))
        output_format = str(inputs.get("output_format", "text"))
        include_page_numbers = bool(inputs.get("include_page_numbers", True))
        ocr_enabled = bool(inputs.get("ocr_enabled", False))
        ocr_language = str(inputs.get("ocr_language", "ita"))
        # Validazione parametri
        if not file_path:
            raise ValueError("Il percorso del file è obbligatorio")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File non trovato: {file_path}")
        if not HAS_PYMUPDF:
            raise ImportError("PyMuPDF è necessario per elaborare i file PDF")
        if ocr_enabled and not HAS_OCR:
            log_warning("OCR richiesto ma pytesseract non è disponibile")
            ocr_enabled = False
        # Estrazione del nome del file
        file_name = os.path.basename(file_path)
        # Apertura del documento PDF
        doc = fitz.open(file_path)
        page_count = len(doc)
        # Determinazione delle pagine da elaborare
        pages_to_process = _parse_page_range(page_range, page_count)
        # Inizializzazione dei risultati
        result = {
            "success": True,
            "file_name": file_name,
            "page_count": page_count,
            "processing_time": 0
        }
        # Estrazione dei metadati
        if extract_metadata:
            result["metadata"] = _extract_metadata(doc)
        # Estrazione del testo
        if extract_text:
            result["text_content"] = _extract_text(
                doc, pages_to_process, output_format, include_page_numbers
            )
        # Estrazione delle immagini
        if extract_images:
            result["images"] = _extract_images(
                doc, pages_to_process, ocr_enabled, ocr_language
            )
        # Estrazione delle tabelle
        if extract_tables:
            result["tables"] = _extract_tables(doc, pages_to_process)
        # Chiusura del documento
        doc.close()
        # Calcolo del tempo di elaborazione
        processing_time = time.time() - start_time
        result["processing_time"] = round(processing_time, 2)
        # Log uscita nodo (successo)
        exit_msg = f"[FileParsing] USCITA nodo (successo): file_name={file_name}, processing_time={processing_time:.2f}s"
        log_info(exit_msg)
        return result
    except Exception as e:
        # Log uscita nodo (errore)
        exit_msg = f"[FileParsing] USCITA nodo (errore): {str(e)}"
        log_error(exit_msg)
        return {
            "success": False,
            "error": str(e)
        }
            "file_name": os.path.basename(file_path) if file_path else "",
            "error": str(e),
            "processing_time": round(processing_time, 2)
        }

def _parse_page_range(page_range: str, total_pages: int) -> List[int]:
    """
    Converte una stringa di intervallo pagine in una lista di indici.
    
    Args:
        page_range: Stringa dell'intervallo (es. '1-5', 'all')
        total_pages: Numero totale di pagine
        
    Returns:
        Lista di indici di pagina (0-based)
    """
    if page_range.lower() == "all":
        return list(range(total_pages))
    
    pages = []
    
    # Gestione di intervalli multipli separati da virgola
    ranges = page_range.split(",")
    
    for r in ranges:
        r = r.strip()
        
        # Intervallo di pagine (es. "1-5")
        if "-" in r:
            start, end = r.split("-")
            try:
                start = int(start.strip())
                end = int(end.strip())
                
                # Conversione da 1-based a 0-based
                start = max(1, start) - 1
                end = min(total_pages, end) - 1
                
                pages.extend(range(start, end + 1))
            except ValueError:
                log_warning(f"Intervallo pagine non valido: {r}")
        
        # Pagina singola
        else:
            try:
                page = int(r)
                # Conversione da 1-based a 0-based
                page = max(1, min(total_pages, page)) - 1
                pages.append(page)
            except ValueError:
                log_warning(f"Numero pagina non valido: {r}")
    
    # Rimuove duplicati e ordina
    return sorted(list(set(pages)))

def _extract_metadata(doc) -> Dict[str, Any]:
    """
    Estrae i metadati dal documento PDF.
    
    Args:
        doc: Documento PDF PyMuPDF
        
    Returns:
        Dizionario con i metadati
    """
    # Metadati standard
    metadata = {
        "title": doc.metadata.get("title", ""),
        "author": doc.metadata.get("author", ""),
        "subject": doc.metadata.get("subject", ""),
        "keywords": doc.metadata.get("keywords", ""),
        "creator": doc.metadata.get("creator", ""),
        "producer": doc.metadata.get("producer", ""),
        "creationDate": doc.metadata.get("creationDate", ""),
        "modDate": doc.metadata.get("modDate", ""),
        "format": "PDF " + doc.metadata.get("format", ""),
        "pageCount": len(doc)
    }
    
    # Aggiungi fileSize se disponibile (PyMuPDF 1.18+)
    try:
        if hasattr(doc, 'filesize'):
            metadata["fileSize"] = doc.filesize
        elif doc.name and os.path.exists(doc.name):
            metadata["fileSize"] = os.path.getsize(doc.name)
    except Exception:
        pass
    
    # Informazioni aggiuntive
    try:
        # Dimensioni della prima pagina
        if len(doc) > 0:
            first_page = doc[0]
            rect = first_page.rect
            metadata["pageWidth"] = rect.width
            metadata["pageHeight"] = rect.height

        # Statistiche del documento
        stats = {"fonts": [], "images": 0, "forms": 0}

        # Conteggio immagini e fonts
        for page in doc:
            # Immagini
            img_list = page.get_images(full=True)
            stats["images"] += len(img_list)

            # Fonts
            for font in page.get_fonts():
                font_name = font[3]
                if font_name not in stats["fonts"]:
                    stats["fonts"].append(font_name)

            # Form fields
            if page.widgets:
                stats["forms"] += len(page.widgets)

        metadata["statistics"] = stats
        metadata["hasText"] = doc.has_text()
    except Exception as e:
        log_warning(f"Errore durante l'estrazione dei metadati avanzati: {str(e)}")
    
    return metadata

def _extract_text(doc, pages: List[int], output_format: str, 
                 include_page_numbers: bool) -> str:
    """
    Estrae il testo dalle pagine specificate.
    
    Args:
        doc: Documento PDF PyMuPDF
        pages: Lista di indici di pagina
        output_format: Formato di output (text, markdown, html, json)
        include_page_numbers: Indica se includere i numeri di pagina
        
    Returns:
        Testo estratto nel formato specificato
    """
    if output_format == "json":
        # Per il formato JSON, crea una struttura dati
        result = []
        for page_idx in pages:
            if page_idx < len(doc):
                page = doc[page_idx]
                text = page.get_text()
                result.append({
                    "page": page_idx + 1,
                    "content": text
                })
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    elif output_format == "html":
        # Formato HTML con stili di base
        html_parts = ["<!DOCTYPE html><html><head><style>",
                    "body { font-family: Arial, sans-serif; line-height: 1.6; }",
                    ".page { margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; }",
                    ".page-number { font-weight: bold; text-align: center; margin-bottom: 10px; }",
                    "</style></head><body>"]
        
        for page_idx in pages:
            if page_idx < len(doc):
                page = doc[page_idx]
                text = page.get_text().replace("\n", "<br>")
                
                html_parts.append(f'<div class="page">')
                if include_page_numbers:
                    html_parts.append(f'<div class="page-number">Pagina {page_idx + 1}</div>')
                html_parts.append(f'{text}</div>')
        
        html_parts.append("</body></html>")
        return "".join(html_parts)
        
    elif output_format == "markdown":
        # Formato Markdown
        md_parts = []
        
        for page_idx in pages:
            if page_idx < len(doc):
                page = doc[page_idx]
                text = page.get_text()
                
                if include_page_numbers:
                    md_parts.append(f"## Pagina {page_idx + 1}\n")
                
                md_parts.append(text)
                md_parts.append("\n---\n")
        
        return "".join(md_parts)
        
    else:  # Default: text
        # Formato testo semplice
        text_parts = []
        
        for page_idx in pages:
            if page_idx < len(doc):
                page = doc[page_idx]
                text = page.get_text()
                
                if include_page_numbers:
                    text_parts.append(f"--- Pagina {page_idx + 1} ---\n")
                
                text_parts.append(text)
                text_parts.append("\n\n")
        
        return "".join(text_parts)

def _extract_images(doc, pages: List[int], ocr_enabled: bool, 
                   ocr_language: str) -> List[Dict[str, Any]]:
    """
    Estrae le immagini dalle pagine specificate.
    
    Args:
        doc: Documento PDF PyMuPDF
        pages: Lista di indici di pagina
        ocr_enabled: Indica se applicare OCR alle immagini
        ocr_language: Lingua per l'OCR
        
    Returns:
        Lista di dizionari con informazioni sulle immagini
    """
    import io
    from PIL import Image
    
    images = []
    
    for page_idx in pages:
        if page_idx < len(doc):
            page = doc[page_idx]
            img_list = page.get_images(full=True)
            
            for img_idx, img_info in enumerate(img_list):
                xref = img_info[0]  # xref numero dell'immagine
                
                try:
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Informazioni sull'immagine
                    img_data = {
                        "page": page_idx + 1,
                        "index": img_idx,
                        "width": base_image.get("width", 0),
                        "height": base_image.get("height", 0),
                        "format": image_ext.upper(),
                        "size_bytes": len(image_bytes),
                        "xref": xref
                    }
                    
                    # OCR se richiesto
                    if ocr_enabled and HAS_OCR:
                        try:
                            pil_image = Image.open(io.BytesIO(image_bytes))
                            extracted_text = pytesseract.image_to_string(
                                pil_image, lang=ocr_language
                            )
                            img_data["ocr_text"] = extracted_text
                        except Exception as e:
                            log_warning(f"Errore OCR: {str(e)}")
                            img_data["ocr_error"] = str(e)
                    
                    images.append(img_data)
                except Exception as e:
                    log_warning(f"Errore nell'estrazione dell'immagine {xref}: {str(e)}")
    
    return images

def _extract_tables(doc, pages: List[int]) -> List[Dict[str, Any]]:
    """
    Estrae le tabelle dalle pagine specificate.
    
    Args:
        doc: Documento PDF PyMuPDF
        pages: Lista di indici di pagina
        
    Returns:
        Lista di dizionari con informazioni sulle tabelle
    """
    tables = []
    
    # Verificare se è disponibile l'estrazione di tabelle
    try:
        import tabula
        has_tabula = True
    except ImportError:
        log_warning("tabula-py non è installato. L'estrazione tabelle non è disponibile.")
        has_tabula = False
        
    if not has_tabula:
        return tables
        
    # Crea un file temporaneo se necessario
    temp_file = None
    if not doc.name:
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, "temp_doc.pdf")
        doc.save(temp_file)
        file_path = temp_file
    else:
        file_path = doc.name
        
    try:
        # Estrai le tabelle da ogni pagina
        for page_idx in pages:
            if page_idx < len(doc):
                page_num = page_idx + 1  # tabula usa 1-based
                
                # Estrai le tabelle
                page_tables = tabula.read_pdf(
                    file_path,
                    pages=page_num,
                    multiple_tables=True
                )
                
                for table_idx, df in enumerate(page_tables):
                    # Converti DataFrame in lista di liste
                    table_data = df.values.tolist()
                    headers = df.columns.tolist()
                    
                    table_info = {
                        "page": page_num,
                        "index": table_idx,
                        "headers": headers,
                        "data": table_data,
                        "rows": len(table_data),
                        "columns": len(headers)
                    }
                    
                    tables.append(table_info)
    except Exception as e:
        log_error(f"Errore nell'estrazione delle tabelle: {str(e)}")
    finally:
        # Rimuovi il file temporaneo se necessario
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
            os.rmdir(os.path.dirname(temp_file))
            
    return tables
