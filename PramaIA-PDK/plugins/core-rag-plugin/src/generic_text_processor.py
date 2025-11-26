"""
Generic Text Processor

Processore universale per operazioni testuali: chunking, embedding, filtering, joining, transforming.
Supporta multiple strategie configurabili e provider diversi.
"""

import logging
import re
import hashlib
from typing import Dict, Any, List, Optional, Union, Callable
from abc import ABC, abstractmethod
import numpy as np

logger = logging.getLogger(__name__)


# ============================================================================
# Abstract Interfaces for Text Operations
# ============================================================================

class TextChunker(ABC):
    """Abstract base class for text chunking strategies."""
    
    @abstractmethod
    async def chunk(self, text: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk text into segments."""
        pass


class TextEmbedder(ABC):
    """Abstract base class for text embedding strategies."""
    
    @abstractmethod
    async def embed(self, texts: List[str], config: Dict[str, Any]) -> List[List[float]]:
        """Generate embeddings for texts."""
        pass


class TextFilter(ABC):
    """Abstract base class for text filtering strategies."""
    
    @abstractmethod
    async def filter(self, texts: List[str], config: Dict[str, Any]) -> List[str]:
        """Filter texts based on criteria."""
        pass


class TextJoiner(ABC):
    """Abstract base class for text joining strategies."""
    
    @abstractmethod
    async def join(self, texts: List[str], config: Dict[str, Any]) -> str:
        """Join texts using strategy."""
        pass


# ============================================================================
# Concrete Chunking Implementations
# ============================================================================

class TokenBasedChunker(TextChunker):
    """Chunk text based on token count with overlap."""
    
    async def chunk(self, text: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        chunk_size = config.get('chunk_size', 1000)
        chunk_overlap = config.get('chunk_overlap', 200)
        separator = config.get('separator', '\n\n')
        
        if not text:
            return []
        
        chunks = []
        if len(text) <= chunk_size:
            return [{"content": text, "start": 0, "end": len(text), "index": 0}]
        
        # Split by separator first
        sections = text.split(separator)
        current_chunk = ""
        start_pos = 0
        chunk_index = 0
        
        for section in sections:
            section_with_sep = section if not current_chunk else separator + section
            
            if len(current_chunk) + len(section_with_sep) > chunk_size:
                if current_chunk:
                    # Save current chunk
                    chunks.append({
                        "content": current_chunk.strip(),
                        "start": start_pos,
                        "end": start_pos + len(current_chunk),
                        "index": chunk_index
                    })
                    chunk_index += 1
                    
                    # Start new chunk with overlap
                    if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                        overlap_text = current_chunk[-chunk_overlap:]
                        start_pos = start_pos + len(current_chunk) - chunk_overlap
                        current_chunk = overlap_text + separator + section
                    else:
                        start_pos = start_pos + len(current_chunk)
                        current_chunk = section
                else:
                    # Section too large, force split
                    if len(section) > chunk_size:
                        sub_chunks = await self._split_large_section(
                            section, chunk_size, chunk_overlap, start_pos, chunk_index
                        )
                        chunks.extend(sub_chunks[:-1])
                        if sub_chunks:
                            last_chunk = sub_chunks[-1]
                            current_chunk = last_chunk["content"]
                            start_pos = last_chunk["start"]
                            chunk_index = last_chunk["index"] + 1
                    else:
                        current_chunk = section
            else:
                current_chunk = current_chunk + section_with_sep if current_chunk else section
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "start": start_pos,
                "end": start_pos + len(current_chunk),
                "index": chunk_index
            })
        
        return chunks
    
    async def _split_large_section(self, section: str, chunk_size: int, 
                                 chunk_overlap: int, start_pos: int, 
                                 start_index: int) -> List[Dict[str, Any]]:
        """Split a section that's too large into smaller chunks."""
        chunks = []
        pos = 0
        index = start_index
        
        while pos < len(section):
            end = pos + chunk_size
            
            # Find better split point
            if end < len(section):
                search_start = max(pos + chunk_size - 100, pos)
                for i in range(end, search_start, -1):
                    if section[i] in [' ', '.', '\n', '!', '?']:
                        end = i + 1
                        break
            
            chunk_content = section[pos:end].strip()
            if chunk_content:
                chunks.append({
                    "content": chunk_content,
                    "start": start_pos + pos,
                    "end": start_pos + end,
                    "index": index
                })
                index += 1
            
            pos = end - chunk_overlap if chunk_overlap > 0 and end < len(section) else end
        
        return chunks


class SentenceBasedChunker(TextChunker):
    """Chunk text by sentences with target size."""
    
    async def chunk(self, text: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        target_size = config.get('chunk_size', 1000)
        sentence_patterns = config.get('sentence_patterns', [r'\. ', r'\! ', r'\? ', r'\n\n'])
        
        # Split into sentences
        sentences = self._split_sentences(text, sentence_patterns)
        
        chunks = []
        current_chunk = ""
        start_pos = 0
        chunk_index = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > target_size and current_chunk:
                chunks.append({
                    "content": current_chunk.strip(),
                    "start": start_pos,
                    "end": start_pos + len(current_chunk),
                    "index": chunk_index
                })
                chunk_index += 1
                start_pos += len(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += sentence
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "start": start_pos,
                "end": start_pos + len(current_chunk),
                "index": chunk_index
            })
        
        return chunks
    
    def _split_sentences(self, text: str, patterns: List[str]) -> List[str]:
        """Split text into sentences using patterns."""
        sentences = [text]
        
        for pattern in patterns:
            new_sentences = []
            for sentence in sentences:
                parts = re.split(pattern, sentence)
                new_sentences.extend([part + pattern.replace('\\', '') for part in parts[:-1]])
                if parts[-1]:  # Add last part without separator
                    new_sentences.append(parts[-1])
            sentences = new_sentences
        
        return [s for s in sentences if s.strip()]


class SemanticChunker(TextChunker):
    """Chunk text by semantic similarity (requires embeddings)."""
    
    async def chunk(self, text: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        # For now, fallback to sentence-based chunking
        # TODO: Implement semantic similarity-based chunking
        sentence_chunker = SentenceBasedChunker()
        return await sentence_chunker.chunk(text, config)


# ============================================================================
# Concrete Embedding Implementations
# ============================================================================

class SentenceTransformersEmbedder(TextEmbedder):
    """Embedder using sentence-transformers library."""
    
    def __init__(self):
        self.model = None
        self.current_model_name = None
        self.is_available = self._check_availability()
    
    def _check_availability(self) -> bool:
        try:
            from sentence_transformers import SentenceTransformer
            return True
        except ImportError:
            logger.warning("⚠️ sentence-transformers not available")
            return False
    
    async def embed(self, texts: List[str], config: Dict[str, Any]) -> List[List[float]]:
        if not self.is_available:
            return await self._generate_mock_embeddings(texts, config)
        
        model_name = config.get('model', 'sentence-transformers/all-MiniLM-L6-v2')
        batch_size = config.get('batch_size', 32)
        normalize = config.get('normalize_embeddings', True)
        
        await self._load_model(model_name)
        
        try:
            from sentence_transformers import SentenceTransformer
            
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = self.model.encode(
                    batch_texts,
                    normalize_embeddings=normalize,
                    show_progress_bar=len(texts) > 100
                )
                all_embeddings.extend(batch_embeddings.tolist())
            
            return all_embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return await self._generate_mock_embeddings(texts, config)
    
    async def _load_model(self, model_name: str):
        if self.current_model_name == model_name and self.model is not None:
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name)
            self.current_model_name = model_name
            logger.info(f"Model loaded: {model_name}")
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            self.model = "mock"
            self.current_model_name = model_name
    
    async def _generate_mock_embeddings(self, texts: List[str], config: Dict[str, Any]) -> List[List[float]]:
        """Generate deterministic mock embeddings."""
        dimensions = config.get('embedding_dimensions', 384)
        embeddings = []
        
        for text in texts:
            # Generate deterministic embedding based on text hash
            hash_value = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
            np.random.seed(hash_value)
            embedding = np.random.normal(0, 1, dimensions)
            embedding = embedding / np.linalg.norm(embedding)  # Normalize
            embeddings.append(embedding.tolist())
        
        return embeddings


class OpenAIEmbedder(TextEmbedder):
    """Embedder using OpenAI API."""
    
    async def embed(self, texts: List[str], config: Dict[str, Any]) -> List[List[float]]:
        # TODO: Implement OpenAI embeddings
        # For now, fallback to mock
        mock_embedder = SentenceTransformersEmbedder()
        return await mock_embedder._generate_mock_embeddings(texts, config)


# ============================================================================
# Concrete Filter Implementations  
# ============================================================================

class LengthFilter(TextFilter):
    """Filter texts by length criteria."""
    
    async def filter(self, texts: List[str], config: Dict[str, Any]) -> List[str]:
        min_length = config.get('min_length', 0)
        max_length = config.get('max_length', float('inf'))
        
        return [text for text in texts 
                if min_length <= len(text) <= max_length]


class RegexFilter(TextFilter):
    """Filter texts using regex patterns."""
    
    async def filter(self, texts: List[str], config: Dict[str, Any]) -> List[str]:
        include_patterns = config.get('include_patterns', [])
        exclude_patterns = config.get('exclude_patterns', [])
        
        filtered_texts = texts
        
        # Apply include patterns
        if include_patterns:
            filtered_texts = []
            for text in texts:
                for pattern in include_patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        filtered_texts.append(text)
                        break
        
        # Apply exclude patterns
        if exclude_patterns:
            final_texts = []
            for text in filtered_texts:
                exclude = False
                for pattern in exclude_patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        exclude = True
                        break
                if not exclude:
                    final_texts.append(text)
            filtered_texts = final_texts
        
        return filtered_texts


class ContentFilter(TextFilter):
    """Filter texts by content criteria."""
    
    async def filter(self, texts: List[str], config: Dict[str, Any]) -> List[str]:
        keywords = config.get('keywords', [])
        language = config.get('language', None)
        quality_threshold = config.get('quality_threshold', 0.0)
        
        filtered_texts = []
        
        for text in texts:
            # Keyword filtering
            if keywords:
                has_keyword = any(keyword.lower() in text.lower() 
                                for keyword in keywords)
                if not has_keyword:
                    continue
            
            # Basic quality check
            quality_score = self._calculate_quality_score(text)
            if quality_score < quality_threshold:
                continue
            
            filtered_texts.append(text)
        
        return filtered_texts
    
    def _calculate_quality_score(self, text: str) -> float:
        """Calculate basic quality score for text."""
        if not text.strip():
            return 0.0
        
        # Basic heuristics
        word_count = len(text.split())
        if word_count < 3:
            return 0.3
        
        # Check for reasonable punctuation
        punct_ratio = sum(1 for c in text if c in '.,!?;:') / len(text)
        if punct_ratio > 0.1:  # Too much punctuation
            return 0.5
        
        # Check for reasonable capitalization
        cap_ratio = sum(1 for c in text if c.isupper()) / len(text)
        if cap_ratio > 0.8:  # ALL CAPS
            return 0.6
        
        return 1.0  # Default good quality


# ============================================================================
# Concrete Joiner Implementations
# ============================================================================

class SimpleJoiner(TextJoiner):
    """Join texts with simple separator."""
    
    async def join(self, texts: List[str], config: Dict[str, Any]) -> str:
        separator = config.get('separator', '\n\n')
        return separator.join(texts)


class TemplateJoiner(TextJoiner):
    """Join texts using a template."""
    
    async def join(self, texts: List[str], config: Dict[str, Any]) -> str:
        template = config.get('template', '{content}')
        separator = config.get('separator', '\n')
        
        formatted_texts = []
        for i, text in enumerate(texts):
            formatted = template.format(
                content=text,
                index=i,
                count=len(texts)
            )
            formatted_texts.append(formatted)
        
        return separator.join(formatted_texts)


class PriorityJoiner(TextJoiner):
    """Join texts with priority-based ordering."""
    
    async def join(self, texts: List[str], config: Dict[str, Any]) -> str:
        priority_keywords = config.get('priority_keywords', [])
        max_texts = config.get('max_texts', len(texts))
        separator = config.get('separator', '\n\n')
        
        # Score texts by priority
        scored_texts = []
        for text in texts:
            score = 0
            for keyword in priority_keywords:
                score += text.lower().count(keyword.lower())
            scored_texts.append((score, text))
        
        # Sort by score descending and take top N
        sorted_texts = sorted(scored_texts, key=lambda x: x[0], reverse=True)
        top_texts = [text for _, text in sorted_texts[:max_texts]]
        
        return separator.join(top_texts)


# ============================================================================
# Main Generic Text Processor
# ============================================================================

class GenericTextProcessor:
    """Universal text processor supporting multiple operations."""
    
    def __init__(self):
        # Registry of available implementations
        self.chunkers = {
            'token': TokenBasedChunker(),
            'sentence': SentenceBasedChunker(),
            'semantic': SemanticChunker()
        }
        
        self.embedders = {
            'sentence_transformers': SentenceTransformersEmbedder(),
            'openai': OpenAIEmbedder()
        }
        
        self.filters = {
            'length': LengthFilter(),
            'regex': RegexFilter(),
            'content': ContentFilter()
        }
        
        self.joiners = {
            'simple': SimpleJoiner(),
            'template': TemplateJoiner(),
            'priority': PriorityJoiner()
        }
    
    async def process(self, context) -> Dict[str, Any]:
        """Main processing method."""
        logger.info("[GenericTextProcessor] INGRESSO nodo: process")
        
        try:
            config = context.get('config', {})
            inputs = context.get('inputs', {})
            
            operation = config.get('operation', 'chunk')
            
            if operation == 'chunk':
                return await self._process_chunking(inputs, config)
            elif operation == 'embed':
                return await self._process_embedding(inputs, config)
            elif operation == 'filter':
                return await self._process_filtering(inputs, config)
            elif operation == 'join':
                return await self._process_joining(inputs, config)
            elif operation == 'pipeline':
                return await self._process_pipeline(inputs, config)
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            logger.error(f"[GenericTextProcessor] USCITA nodo (errore): {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "operation": config.get('operation', 'unknown'),
                "output": None
            }
    
    async def _process_chunking(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process text chunking."""
        text_input = inputs.get('text_input', inputs.get('text', ''))
        if not text_input:
            raise ValueError("No text provided for chunking")
        
        strategy = config.get('strategy', 'token')
        chunker = self.chunkers.get(strategy)
        if not chunker:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
        
        chunks = await chunker.chunk(text_input, config)
        
        logger.info(f"[GenericTextProcessor] USCITA chunking (successo): {len(chunks)} chunks created")
        return {
            "status": "success",
            "operation": "chunk",
            "output": {
                "chunks": chunks,
                "chunk_count": len(chunks),
                "strategy": strategy,
                "original_length": len(text_input)
            }
        }
    
    async def _process_embedding(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process text embedding."""
        texts = inputs.get('texts', inputs.get('text_chunks', []))
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            raise ValueError("No texts provided for embedding")
        
        provider = config.get('provider', 'sentence_transformers')
        embedder = self.embedders.get(provider)
        if not embedder:
            raise ValueError(f"Unknown embedding provider: {provider}")
        
        embeddings = await embedder.embed(texts, config)
        
        logger.info(f"[GenericTextProcessor] USCITA embedding (successo): {len(embeddings)} embeddings created")
        return {
            "status": "success", 
            "operation": "embed",
            "output": {
                "embeddings": embeddings,
                "texts": texts,
                "provider": provider,
                "dimensions": len(embeddings[0]) if embeddings else 0
            }
        }
    
    async def _process_filtering(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process text filtering."""
        texts = inputs.get('texts', inputs.get('text_list', []))
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            raise ValueError("No texts provided for filtering")
        
        filter_type = config.get('filter_type', 'length')
        filter_impl = self.filters.get(filter_type)
        if not filter_impl:
            raise ValueError(f"Unknown filter type: {filter_type}")
        
        filtered_texts = await filter_impl.filter(texts, config)
        
        logger.info(f"[GenericTextProcessor] USCITA filtering (successo): {len(filtered_texts)}/{len(texts)} texts passed filter")
        return {
            "status": "success",
            "operation": "filter", 
            "output": {
                "filtered_texts": filtered_texts,
                "original_count": len(texts),
                "filtered_count": len(filtered_texts),
                "filter_type": filter_type
            }
        }
    
    async def _process_joining(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process text joining."""
        texts = inputs.get('texts', inputs.get('text_list', []))
        if not texts:
            raise ValueError("No texts provided for joining")
        
        join_strategy = config.get('join_strategy', 'simple')
        joiner = self.joiners.get(join_strategy)
        if not joiner:
            raise ValueError(f"Unknown join strategy: {join_strategy}")
        
        joined_text = await joiner.join(texts, config)
        
        logger.info(f"[GenericTextProcessor] USCITA joining (successo): {len(texts)} texts joined")
        return {
            "status": "success",
            "operation": "join",
            "output": {
                "joined_text": joined_text,
                "original_count": len(texts),
                "join_strategy": join_strategy,
                "final_length": len(joined_text)
            }
        }
    
    async def _process_pipeline(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process multi-step text pipeline."""
        pipeline_steps = config.get('pipeline', [])
        if not pipeline_steps:
            raise ValueError("No pipeline steps defined")
        
        current_data = inputs
        step_results = []
        
        for i, step_config in enumerate(pipeline_steps):
            step_operation = step_config.get('operation')
            logger.info(f"[GenericTextProcessor] Executing pipeline step {i+1}: {step_operation}")
            
            # Create step context
            step_context = {
                'config': step_config,
                'inputs': current_data
            }
            
            # Execute step
            if step_operation == 'chunk':
                result = await self._process_chunking(current_data, step_config)
            elif step_operation == 'embed':
                result = await self._process_embedding(current_data, step_config)
            elif step_operation == 'filter':
                result = await self._process_filtering(current_data, step_config)
            elif step_operation == 'join':
                result = await self._process_joining(current_data, step_config)
            else:
                raise ValueError(f"Unknown pipeline operation: {step_operation}")
            
            if result['status'] != 'success':
                raise Exception(f"Pipeline step {i+1} failed: {result.get('error')}")
            
            step_results.append(result)
            
            # Prepare data for next step
            output_mapping = step_config.get('output_mapping', {})
            if output_mapping:
                current_data = {}
                for output_key, input_key in output_mapping.items():
                    if output_key in result['output']:
                        current_data[input_key] = result['output'][output_key]
            else:
                # Default mapping based on operation
                if step_operation == 'chunk':
                    current_data = {'texts': [chunk['content'] for chunk in result['output']['chunks']]}
                elif step_operation == 'embed':
                    current_data = {
                        'embeddings': result['output']['embeddings'],
                        'texts': result['output']['texts']
                    }
                elif step_operation == 'filter':
                    current_data = {'texts': result['output']['filtered_texts']}
                elif step_operation == 'join':
                    current_data = {'text': result['output']['joined_text']}
        
        logger.info(f"[GenericTextProcessor] USCITA pipeline (successo): {len(pipeline_steps)} steps completed")
        return {
            "status": "success",
            "operation": "pipeline",
            "output": {
                "final_result": current_data,
                "step_results": step_results,
                "steps_completed": len(pipeline_steps)
            }
        }


# Funzione entry point per il PDK
async def process_node(context):
    """Entry point per il Generic Text Processor."""
    processor = GenericTextProcessor()
    return await processor.process(context)