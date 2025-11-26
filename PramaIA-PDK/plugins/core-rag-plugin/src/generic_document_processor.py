"""
Generic Document Processor

Processore universale per gestire documenti di diversi formati: PDF, DOCX, TXT, HTML, MD, ecc.
Supporta estrazione testo, metadati, immagini e conversioni multiple.
"""

import logging
import re
import mimetypes
from typing import Dict, Any, List, Optional, Union, BinaryIO
from abc import ABC, abstractmethod
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


# ============================================================================
# Abstract Interfaces for Document Operations
# ============================================================================

class DocumentExtractor(ABC):
    """Abstract base class for document extractors."""
    
    @abstractmethod
    async def extract(self, document: Union[bytes, str, BinaryIO], config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content from document."""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        pass


class MetadataExtractor(ABC):
    """Abstract base class for metadata extractors."""
    
    @abstractmethod 
    async def extract_metadata(self, document: Union[bytes, str, BinaryIO], config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from document."""
        pass


# ============================================================================
# Concrete Document Extractors
# ============================================================================

class PDFExtractor(DocumentExtractor):
    """Extract content from PDF documents."""
    
    def __init__(self):
        self.is_available = self._check_availability()
    
    def _check_availability(self) -> bool:
        try:
            import PyPDF2
            return True
        except ImportError:
            logger.warning("⚠️ PyPDF2 not available for PDF extraction")
            return False
    
    def get_supported_formats(self) -> List[str]:
        return ['pdf'] if self.is_available else []
    
    async def extract(self, document: Union[bytes, str, BinaryIO], config: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_available:
            return await self._mock_extraction(document, config)
        
        try:
            import PyPDF2
            import io
            
            preserve_layout = config.get('preserve_layout', True)
            extract_images = config.get('extract_images', False)
            page_range = config.get('page_range', None)  # [start, end] or None for all
            
            # Handle different input types
            if isinstance(document, str):
                # Assume it's a file path
                with open(document, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    return await self._extract_from_reader(pdf_reader, config)
            elif isinstance(document, bytes):
                # Binary data
                pdf_stream = io.BytesIO(document)
                pdf_reader = PyPDF2.PdfReader(pdf_stream)
                return await self._extract_from_reader(pdf_reader, config)
            else:
                # File-like object
                pdf_reader = PyPDF2.PdfReader(document)
                return await self._extract_from_reader(pdf_reader, config)
                
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            return await self._mock_extraction(document, config)
    
    async def _extract_from_reader(self, pdf_reader, config: Dict[str, Any]) -> Dict[str, Any]:
        page_range = config.get('page_range', None)
        preserve_layout = config.get('preserve_layout', True)
        
        text_parts = []
        page_texts = []
        total_pages = len(pdf_reader.pages)
        
        start_page = page_range[0] if page_range else 0
        end_page = min(page_range[1], total_pages) if page_range else total_pages
        
        for page_num in range(start_page, end_page):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            
            if preserve_layout:
                # Try to preserve some layout
                page_text = self._clean_extracted_text(page_text)
            
            page_texts.append({
                'page_number': page_num + 1,
                'text': page_text,
                'length': len(page_text)
            })
            text_parts.append(page_text)
        
        full_text = '\n\n'.join(text_parts)
        
        return {
            'text': full_text,
            'pages': page_texts,
            'total_pages': total_pages,
            'pages_processed': end_page - start_page,
            'format': 'pdf',
            'length': len(full_text)
        }
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and format extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Fix common OCR issues
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between camelCase
        
        return text.strip()
    
    async def _mock_extraction(self, document: Union[bytes, str, BinaryIO], config: Dict[str, Any]) -> Dict[str, Any]:
        """Mock extraction when PyPDF2 is not available."""
        return {
            'text': '[PDF content - PyPDF2 not available for extraction]',
            'pages': [{'page_number': 1, 'text': '[Mock PDF content]', 'length': 20}],
            'total_pages': 1,
            'pages_processed': 1,
            'format': 'pdf',
            'length': 20,
            'mock': True
        }


class DOCXExtractor(DocumentExtractor):
    """Extract content from DOCX documents."""
    
    def __init__(self):
        self.is_available = self._check_availability()
    
    def _check_availability(self) -> bool:
        try:
            import python_docx
            return True
        except ImportError:
            logger.warning("⚠️ python-docx not available for DOCX extraction")
            return False
    
    def get_supported_formats(self) -> List[str]:
        return ['docx', 'doc'] if self.is_available else []
    
    async def extract(self, document: Union[bytes, str, BinaryIO], config: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_available:
            return await self._mock_extraction(document, config)
        
        try:
            import python_docx
            
            # Handle different input types
            if isinstance(document, str):
                doc = python_docx.Document(document)
            else:
                doc = python_docx.Document(document)
            
            paragraphs = []
            full_text_parts = []
            
            for i, paragraph in enumerate(doc.paragraphs):
                para_text = paragraph.text.strip()
                if para_text:
                    paragraphs.append({
                        'index': i,
                        'text': para_text,
                        'length': len(para_text)
                    })
                    full_text_parts.append(para_text)
            
            full_text = '\n\n'.join(full_text_parts)
            
            return {
                'text': full_text,
                'paragraphs': paragraphs,
                'total_paragraphs': len(paragraphs),
                'format': 'docx',
                'length': len(full_text)
            }
            
        except Exception as e:
            logger.error(f"Error extracting DOCX: {e}")
            return await self._mock_extraction(document, config)
    
    async def _mock_extraction(self, document: Union[bytes, str, BinaryIO], config: Dict[str, Any]) -> Dict[str, Any]:
        """Mock extraction when python-docx is not available."""
        return {
            'text': '[DOCX content - python-docx not available for extraction]',
            'paragraphs': [{'index': 0, 'text': '[Mock DOCX content]', 'length': 20}],
            'total_paragraphs': 1,
            'format': 'docx',
            'length': 20,
            'mock': True
        }


class HTMLExtractor(DocumentExtractor):
    """Extract content from HTML documents."""
    
    def __init__(self):
        self.is_available = self._check_availability()
    
    def _check_availability(self) -> bool:
        try:
            from bs4 import BeautifulSoup
            return True
        except ImportError:
            logger.warning("⚠️ BeautifulSoup not available for HTML extraction")
            return False
    
    def get_supported_formats(self) -> List[str]:
        return ['html', 'htm'] if self.is_available else []
    
    async def extract(self, document: Union[bytes, str, BinaryIO], config: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_available:
            return await self._fallback_html_extraction(document, config)
        
        try:
            from bs4 import BeautifulSoup
            
            # Handle different input types
            if isinstance(document, bytes):
                html_content = document.decode('utf-8', errors='ignore')
            elif hasattr(document, 'read'):
                html_content = document.read()
                if isinstance(html_content, bytes):
                    html_content = html_content.decode('utf-8', errors='ignore')
            else:
                html_content = str(document)
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract title
            title = soup.title.string if soup.title else ""
            
            # Extract main text
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return {
                'text': text,
                'title': title,
                'format': 'html',
                'length': len(text)
            }
            
        except Exception as e:
            logger.error(f"Error extracting HTML: {e}")
            return await self._fallback_html_extraction(document, config)
    
    async def _fallback_html_extraction(self, document: Union[bytes, str, BinaryIO], config: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback HTML extraction using regex when BeautifulSoup is not available."""
        try:
            # Handle different input types
            if isinstance(document, bytes):
                html_content = document.decode('utf-8', errors='ignore')
            elif hasattr(document, 'read'):
                html_content = document.read()
                if isinstance(html_content, bytes):
                    html_content = html_content.decode('utf-8', errors='ignore')
            else:
                html_content = str(document)
            
            # Extract title
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1) if title_match else ""
            
            # Remove script and style tags
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', html_content)
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            return {
                'text': text,
                'title': title,
                'format': 'html',
                'length': len(text),
                'fallback': True
            }
            
        except Exception as e:
            logger.error(f"Error in fallback HTML extraction: {e}")
            return {
                'text': '[HTML extraction failed]',
                'title': '',
                'format': 'html',
                'length': 0,
                'error': str(e)
            }


class PlainTextExtractor(DocumentExtractor):
    """Extract content from plain text documents."""
    
    def get_supported_formats(self) -> List[str]:
        return ['txt', 'md', 'markdown', 'csv', 'json', 'xml', 'log']
    
    async def extract(self, document: Union[bytes, str, BinaryIO], config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            encoding = config.get('encoding', 'utf-8')
            
            # Handle different input types
            if isinstance(document, bytes):
                text_content = document.decode(encoding, errors='ignore')
            elif hasattr(document, 'read'):
                content = document.read()
                if isinstance(content, bytes):
                    text_content = content.decode(encoding, errors='ignore')
                else:
                    text_content = str(content)
            else:
                text_content = str(document)
            
            # Basic formatting for different text types
            file_type = config.get('file_type', 'txt').lower()
            
            if file_type in ['md', 'markdown']:
                text_content = self._clean_markdown(text_content)
            elif file_type == 'csv':
                text_content = self._format_csv(text_content)
            elif file_type in ['json', 'xml']:
                text_content = self._format_structured_text(text_content)
            
            return {
                'text': text_content,
                'format': file_type,
                'length': len(text_content),
                'lines': len(text_content.splitlines())
            }
            
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return {
                'text': '',
                'format': 'txt',
                'length': 0,
                'error': str(e)
            }
    
    def _clean_markdown(self, text: str) -> str:
        """Clean markdown formatting for better readability."""
        # Remove markdown headers but keep content
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # Convert markdown links [text](url) to just text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Remove markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Italic
        text = re.sub(r'`([^`]+)`', r'\1', text)        # Code
        
        return text
    
    def _format_csv(self, text: str) -> str:
        """Format CSV for better text extraction."""
        lines = text.splitlines()
        formatted_lines = []
        
        for line in lines:
            # Replace commas with tabs for better readability
            formatted_line = line.replace(',', '\t')
            formatted_lines.append(formatted_line)
        
        return '\n'.join(formatted_lines)
    
    def _format_structured_text(self, text: str) -> str:
        """Format structured text (JSON/XML) for better extraction."""
        # Add line breaks after major structural elements
        text = re.sub(r'([{}\[\]])', r'\1\n', text)
        text = re.sub(r'([,;])', r'\1\n', text)
        
        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text


# ============================================================================
# Concrete Metadata Extractors
# ============================================================================

class BasicMetadataExtractor(MetadataExtractor):
    """Extract basic metadata from documents."""
    
    async def extract_metadata(self, document: Union[bytes, str, BinaryIO], config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            metadata = {}
            
            # File size
            if isinstance(document, bytes):
                metadata['file_size'] = len(document)
            elif hasattr(document, 'seek') and hasattr(document, 'tell'):
                # Get file size for file objects
                current_pos = document.tell()
                document.seek(0, 2)  # Seek to end
                metadata['file_size'] = document.tell()
                document.seek(current_pos)  # Restore position
            elif isinstance(document, str) and Path(document).exists():
                # File path
                metadata['file_size'] = Path(document).stat().st_size
                metadata['file_name'] = Path(document).name
                metadata['file_extension'] = Path(document).suffix
            
            # Content hash
            if isinstance(document, (bytes, str)):
                content_bytes = document.encode() if isinstance(document, str) else document
                metadata['content_hash'] = hashlib.md5(content_bytes).hexdigest()
            
            # MIME type detection
            if isinstance(document, str) and Path(document).exists():
                mime_type, _ = mimetypes.guess_type(document)
                metadata['mime_type'] = mime_type
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {'error': str(e)}


# ============================================================================
# Main Generic Document Processor  
# ============================================================================

class GenericDocumentProcessor:
    """Universal document processor supporting multiple formats."""
    
    def __init__(self):
        # Registry of available extractors
        self.extractors = {
            'pdf': PDFExtractor(),
            'docx': DOCXExtractor(), 
            'html': HTMLExtractor(),
            'text': PlainTextExtractor()
        }
        
        self.metadata_extractor = BasicMetadataExtractor()
    
    async def process(self, context) -> Dict[str, Any]:
        """Main processing method."""
        logger.info("[GenericDocumentProcessor] INGRESSO nodo: process")
        
        try:
            config = context.get('config', {})
            inputs = context.get('inputs', {})
            
            operation = config.get('operation', 'extract')
            
            if operation == 'extract':
                return await self._process_extraction(inputs, config)
            elif operation == 'metadata':
                return await self._process_metadata(inputs, config)
            elif operation == 'convert':
                return await self._process_conversion(inputs, config)
            elif operation == 'analyze':
                return await self._process_analysis(inputs, config)
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            logger.error(f"[GenericDocumentProcessor] USCITA nodo (errore): {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "operation": config.get('operation', 'unknown'),
                "output": None
            }
    
    async def _process_extraction(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process document text extraction."""
        document = inputs.get('document', inputs.get('file', inputs.get('content')))
        if not document:
            raise ValueError("No document provided")
        
        # Auto-detect format if not specified
        format_type = config.get('format', 'auto')
        if format_type == 'auto':
            format_type = self._detect_format(document, config)
        
        # Select appropriate extractor
        extractor = self._get_extractor_for_format(format_type)
        if not extractor:
            raise ValueError(f"No extractor available for format: {format_type}")
        
        # Extract content
        extraction_result = await extractor.extract(document, config)
        
        logger.info(f"[GenericDocumentProcessor] USCITA extraction (successo): {format_type} document processed")
        return {
            "status": "success",
            "operation": "extract",
            "output": {
                **extraction_result,
                "detected_format": format_type,
                "extractor_used": extractor.__class__.__name__
            }
        }
    
    async def _process_metadata(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process metadata extraction."""
        document = inputs.get('document', inputs.get('file', inputs.get('content')))
        if not document:
            raise ValueError("No document provided")
        
        metadata = await self.metadata_extractor.extract_metadata(document, config)
        
        logger.info(f"[GenericDocumentProcessor] USCITA metadata (successo): metadata extracted")
        return {
            "status": "success",
            "operation": "metadata",
            "output": {
                "metadata": metadata
            }
        }
    
    async def _process_conversion(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process document conversion."""
        # First extract content
        extract_config = {**config, 'operation': 'extract'}
        extraction_result = await self._process_extraction(inputs, extract_config)
        
        if extraction_result['status'] != 'success':
            return extraction_result
        
        target_format = config.get('target_format', 'text')
        source_content = extraction_result['output']
        
        # Perform conversion
        converted_content = await self._convert_content(source_content, target_format, config)
        
        logger.info(f"[GenericDocumentProcessor] USCITA conversion (successo): converted to {target_format}")
        return {
            "status": "success",
            "operation": "convert",
            "output": {
                "converted_content": converted_content,
                "source_format": source_content.get('format'),
                "target_format": target_format
            }
        }
    
    async def _process_analysis(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process document analysis."""
        # Extract content and metadata
        extract_result = await self._process_extraction(inputs, config)
        metadata_result = await self._process_metadata(inputs, config)
        
        if extract_result['status'] != 'success':
            return extract_result
        
        content = extract_result['output']
        metadata = metadata_result['output']['metadata'] if metadata_result['status'] == 'success' else {}
        
        # Perform analysis
        analysis = await self._analyze_content(content, metadata, config)
        
        logger.info(f"[GenericDocumentProcessor] USCITA analysis (successo): document analyzed")
        return {
            "status": "success",
            "operation": "analyze",
            "output": {
                "content": content,
                "metadata": metadata,
                "analysis": analysis
            }
        }
    
    def _detect_format(self, document: Union[bytes, str, BinaryIO], config: Dict[str, Any]) -> str:
        """Auto-detect document format."""
        if isinstance(document, str):
            # Could be file path or content
            if Path(document).exists():
                # File path - use extension
                ext = Path(document).suffix.lower().lstrip('.')
                return ext if ext else 'text'
            else:
                # Text content
                return 'text'
        elif isinstance(document, bytes):
            # Check magic bytes for common formats
            if document.startswith(b'%PDF'):
                return 'pdf'
            elif document.startswith(b'PK'):  # ZIP-based formats (DOCX, etc.)
                return 'docx'
            elif document.startswith(b'<html') or document.startswith(b'<!DOCTYPE'):
                return 'html'
            else:
                return 'text'
        else:
            # File-like object - try to detect from content
            return 'text'
    
    def _get_extractor_for_format(self, format_type: str) -> Optional[DocumentExtractor]:
        """Get appropriate extractor for format."""
        format_mapping = {
            'pdf': 'pdf',
            'docx': 'docx',
            'doc': 'docx',
            'html': 'html',
            'htm': 'html',
            'txt': 'text',
            'md': 'text',
            'markdown': 'text',
            'csv': 'text',
            'json': 'text',
            'xml': 'text'
        }
        
        extractor_type = format_mapping.get(format_type.lower(), 'text')
        return self.extractors.get(extractor_type)
    
    async def _convert_content(self, content: Dict[str, Any], target_format: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert content to target format."""
        source_text = content.get('text', '')
        
        if target_format == 'text':
            return {'text': source_text}
        elif target_format == 'html':
            # Convert text to simple HTML
            html_text = f"<html><body><p>{source_text.replace(chr(10), '</p><p>')}</p></body></html>"
            return {'html': html_text}
        elif target_format == 'markdown':
            # Convert to markdown
            lines = source_text.splitlines()
            md_lines = ['# Document Content', ''] + lines
            return {'markdown': '\n'.join(md_lines)}
        else:
            return {'text': source_text}  # Fallback
    
    async def _analyze_content(self, content: Dict[str, Any], metadata: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze document content."""
        text = content.get('text', '')
        
        analysis = {
            'word_count': len(text.split()),
            'character_count': len(text),
            'line_count': len(text.splitlines()),
            'paragraph_count': len([p for p in text.split('\n\n') if p.strip()]),
        }
        
        # Language detection (simple heuristic)
        analysis['estimated_language'] = self._detect_language(text)
        
        # Content type analysis
        analysis['content_type'] = self._analyze_content_type(text)
        
        # Reading time estimate (average 200 words per minute)
        analysis['estimated_reading_time_minutes'] = max(1, analysis['word_count'] // 200)
        
        return analysis
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection based on common words."""
        text_lower = text.lower()
        
        # Simple heuristics for common languages
        if any(word in text_lower for word in ['the', 'and', 'of', 'to', 'a']):
            return 'english'
        elif any(word in text_lower for word in ['il', 'la', 'di', 'che', 'è']):
            return 'italian'
        elif any(word in text_lower for word in ['le', 'de', 'et', 'à', 'un']):
            return 'french'
        elif any(word in text_lower for word in ['el', 'la', 'de', 'que', 'y']):
            return 'spanish'
        else:
            return 'unknown'
    
    def _analyze_content_type(self, text: str) -> str:
        """Analyze the type of content."""
        text_lower = text.lower()
        
        # Check for common document types
        if any(word in text_lower for word in ['contract', 'agreement', 'contratto', 'accordo']):
            return 'contract'
        elif any(word in text_lower for word in ['invoice', 'fattura', 'bill', 'payment']):
            return 'invoice'
        elif any(word in text_lower for word in ['report', 'analysis', 'relazione', 'analisi']):
            return 'report'
        elif any(word in text_lower for word in ['manual', 'guide', 'manuale', 'guida']):
            return 'manual'
        elif any(word in text_lower for word in ['email', 'subject:', 'from:', 'to:']):
            return 'email'
        else:
            return 'document'


# Funzione entry point per il PDK
async def process_node(context):
    """Entry point per il Generic Document Processor."""
    processor = GenericDocumentProcessor()
    return await processor.process(context)