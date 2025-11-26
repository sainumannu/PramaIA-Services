"""
Advanced Text Analyzer Plugin

Plugin esempio che implementa TextProcessorPlugin per analisi testuale avanzata
con sentiment analysis, keyword extraction e topic modeling.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re

# Import plugin framework interfaces
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.plugin_architecture_framework import TextProcessorPlugin, PluginMetadata

logger = logging.getLogger(__name__)


class AdvancedTextAnalyzer(TextProcessorPlugin):
    """Advanced text analyzer implementing TextProcessorPlugin interface."""
    
    def __init__(self):
        self.provider_name = "advanced_analyzer"
        self.sentiment_pipeline = None
        self.topic_model = None
        self.initialized = False
        self.config = {}
    
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            id="advanced_text_analyzer",
            name="Advanced Text Analyzer",
            version="1.0.0",
            description="Plugin avanzato per analisi testuale con sentiment analysis, keyword extraction e topic modeling",
            author="PramaIA Team", 
            category="text",
            plugin_type="strategy",
            interface_type="TextProcessorPlugin"
        )
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration."""
        try:
            self.config = config
            
            # Initialize sentiment analysis model
            if await self._init_sentiment_model():
                logger.info("Sentiment model initialized successfully")
            else:
                logger.warning("Failed to initialize sentiment model, using fallback")
            
            # Initialize topic modeling if enabled
            if config.get('enable_topic_modeling', False):
                if await self._init_topic_model():
                    logger.info("Topic model initialized successfully")
                else:
                    logger.warning("Failed to initialize topic model")
            
            self.initialized = True
            logger.info("Advanced Text Analyzer plugin initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Advanced Text Analyzer: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup plugin resources."""
        try:
            self.sentiment_pipeline = None
            self.topic_model = None
            self.initialized = False
            logger.info("Advanced Text Analyzer cleanup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup Advanced Text Analyzer: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check and return status."""
        health = {
            'status': 'healthy' if self.initialized else 'unhealthy',
            'initialized': self.initialized,
            'sentiment_model_loaded': self.sentiment_pipeline is not None,
            'topic_model_loaded': self.topic_model is not None,
            'provider_name': self.provider_name,
            'timestamp': datetime.now().isoformat()
        }
        
        if not self.initialized:
            health['issues'] = ['Plugin not initialized']
        
        return health
    
    async def process_text(self, text: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process text according to plugin functionality."""
        try:
            if not self.initialized:
                return {
                    'success': False,
                    'error': 'Plugin not initialized',
                    'analysis': {}
                }
            
            if not text or not isinstance(text, str):
                return {
                    'success': False,
                    'error': 'Invalid text input',
                    'analysis': {}
                }
            
            analysis = {}
            
            # Basic text statistics
            analysis['statistics'] = await self._calculate_text_stats(text)
            
            # Sentiment analysis
            analysis['sentiment'] = await self._analyze_sentiment(text)
            
            # Keyword extraction
            analysis['keywords'] = await self._extract_keywords(text)
            
            # Language detection
            analysis['language'] = await self._detect_language(text)
            
            # Topic modeling (if enabled and model loaded)
            if self.config.get('enable_topic_modeling', False) and self.topic_model:
                analysis['topics'] = await self._analyze_topics(text)
            
            # Text quality assessment
            analysis['quality'] = await self._assess_text_quality(text)
            
            return {
                'success': True,
                'analysis': analysis,
                'processed_at': datetime.now().isoformat(),
                'provider': self.provider_name
            }
            
        except Exception as e:
            logger.error(f"Text processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'analysis': {}
            }
    
    async def _init_sentiment_model(self) -> bool:
        """Initialize sentiment analysis model."""
        try:
            # Try to use transformers pipeline
            try:
                from transformers import pipeline
                model_name = self.config.get('sentiment_model', 'cardiffnlp/twitter-roberta-base-sentiment-latest')
                self.sentiment_pipeline = pipeline("sentiment-analysis", model=model_name)
                return True
            except ImportError:
                logger.warning("Transformers not available, using TextBlob fallback")
                # Fallback to TextBlob
                try:
                    import textblob
                    self.sentiment_pipeline = "textblob"
                    return True
                except ImportError:
                    logger.warning("TextBlob not available either")
                    return False
            
        except Exception as e:
            logger.error(f"Failed to initialize sentiment model: {e}")
            return False
    
    async def _init_topic_model(self) -> bool:
        """Initialize topic modeling."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.decomposition import LatentDirichletAllocation
            
            self.topic_model = {
                'vectorizer': TfidfVectorizer(max_features=100, stop_words='english'),
                'lda': LatentDirichletAllocation(
                    n_components=self.config.get('num_topics', 5),
                    random_state=42
                )
            }
            return True
            
        except ImportError:
            logger.warning("Scikit-learn not available for topic modeling")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize topic model: {e}")
            return False
    
    async def _calculate_text_stats(self, text: str) -> Dict[str, Any]:
        """Calculate basic text statistics."""
        words = text.split()
        sentences = text.split('.')
        
        return {
            'character_count': len(text),
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'average_word_length': sum(len(word) for word in words) / len(words) if words else 0,
            'average_sentence_length': len(words) / len(sentences) if sentences else 0
        }
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze text sentiment."""
        try:
            if self.sentiment_pipeline == "textblob":
                # Use TextBlob fallback
                import textblob
                blob = textblob.TextBlob(text)
                polarity = blob.sentiment.polarity
                
                if polarity > 0.1:
                    label = "POSITIVE"
                elif polarity < -0.1:
                    label = "NEGATIVE"
                else:
                    label = "NEUTRAL"
                
                return {
                    'label': label,
                    'confidence': abs(polarity),
                    'polarity': polarity,
                    'method': 'textblob'
                }
            
            elif self.sentiment_pipeline:
                # Use transformers pipeline
                result = self.sentiment_pipeline(text)[0]
                return {
                    'label': result['label'],
                    'confidence': result['score'],
                    'method': 'transformers'
                }
            
            else:
                # Mock sentiment if no model available
                return {
                    'label': 'NEUTRAL',
                    'confidence': 0.5,
                    'method': 'mock'
                }
                
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return {
                'label': 'UNKNOWN',
                'confidence': 0.0,
                'error': str(e),
                'method': 'error'
            }
    
    async def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        try:
            # Simple keyword extraction using frequency
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            
            # Filter common words (simple stopwords)
            stopwords = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 
                        'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were', 'be', 'been', 
                        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
            
            words = [word for word in words if word not in stopwords]
            
            # Count frequency and return top keywords
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Sort by frequency and return top 10
            keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            return [keyword[0] for keyword in keywords]
            
        except Exception as e:
            logger.warning(f"Keyword extraction failed: {e}")
            return []
    
    async def _detect_language(self, text: str) -> str:
        """Detect text language."""
        try:
            # Simple language detection based on common words
            english_indicators = ['the', 'and', 'or', 'but', 'this', 'that', 'with']
            italian_indicators = ['il', 'la', 'di', 'che', 'con', 'per', 'una', 'dello']
            
            text_lower = text.lower()
            
            english_count = sum(1 for word in english_indicators if word in text_lower)
            italian_count = sum(1 for word in italian_indicators if word in text_lower)
            
            if english_count > italian_count:
                return 'en'
            elif italian_count > 0:
                return 'it'
            else:
                return self.config.get('language', 'en')  # Default from config
                
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return 'unknown'
    
    async def _analyze_topics(self, text: str) -> List[Dict[str, Any]]:
        """Analyze topics in text."""
        try:
            if not self.topic_model:
                return []
            
            # Split text into sentences for topic modeling
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            
            if len(sentences) < 3:
                return []  # Need more content for topic modeling
            
            # Vectorize text
            tfidf_matrix = self.topic_model['vectorizer'].fit_transform(sentences)
            
            # Fit LDA model
            self.topic_model['lda'].fit(tfidf_matrix)
            
            # Get topics
            feature_names = self.topic_model['vectorizer'].get_feature_names_out()
            topics = []
            
            for topic_idx, topic in enumerate(self.topic_model['lda'].components_):
                top_words_idx = topic.argsort()[-10:][::-1]
                top_words = [feature_names[i] for i in top_words_idx]
                
                topics.append({
                    'topic_id': topic_idx,
                    'keywords': top_words[:5],  # Top 5 keywords
                    'weight': float(topic.max())
                })
            
            return topics
            
        except Exception as e:
            logger.warning(f"Topic analysis failed: {e}")
            return []
    
    async def _assess_text_quality(self, text: str) -> Dict[str, Any]:
        """Assess text quality."""
        try:
            stats = await self._calculate_text_stats(text)
            
            # Simple quality metrics
            quality_score = 0
            issues = []
            
            # Check word count
            if stats['word_count'] < 10:
                issues.append("Text too short")
            else:
                quality_score += 20
            
            # Check average word length
            if stats['average_word_length'] < 3:
                issues.append("Words too short on average")
            elif stats['average_word_length'] > 10:
                issues.append("Words too long on average")
            else:
                quality_score += 20
            
            # Check sentence structure
            if stats['average_sentence_length'] < 5:
                issues.append("Sentences too short")
            elif stats['average_sentence_length'] > 30:
                issues.append("Sentences too long")
            else:
                quality_score += 20
            
            # Check for basic punctuation
            if '.' in text or '?' in text or '!' in text:
                quality_score += 20
            else:
                issues.append("Missing punctuation")
            
            # Check for variety in vocabulary
            unique_words = len(set(text.lower().split()))
            vocabulary_ratio = unique_words / stats['word_count'] if stats['word_count'] > 0 else 0
            
            if vocabulary_ratio > 0.7:
                quality_score += 20
            elif vocabulary_ratio < 0.3:
                issues.append("Limited vocabulary variety")
            else:
                quality_score += 10
            
            # Determine quality level
            if quality_score >= 80:
                quality_level = "High"
            elif quality_score >= 60:
                quality_level = "Medium"
            elif quality_score >= 40:
                quality_level = "Low"
            else:
                quality_level = "Very Low"
            
            return {
                'score': quality_score,
                'level': quality_level,
                'vocabulary_ratio': vocabulary_ratio,
                'issues': issues
            }
            
        except Exception as e:
            logger.warning(f"Text quality assessment failed: {e}")
            return {
                'score': 0,
                'level': 'Unknown',
                'error': str(e)
            }


# Plugin metadata for automatic discovery
__plugin__ = {
    'id': 'advanced_text_analyzer',
    'name': 'Advanced Text Analyzer',
    'version': '1.0.0',
    'description': 'Plugin avanzato per analisi testuale con sentiment analysis, keyword extraction e topic modeling',
    'author': 'PramaIA Team',
    'category': 'text', 
    'plugin_type': 'strategy',
    'interface_type': 'TextProcessorPlugin',
    'dependencies': ['transformers', 'torch', 'scikit-learn', 'textblob'],
    'config_schema': {
        'type': 'object',
        'properties': {
            'sentiment_model': {
                'type': 'string',
                'default': 'cardiffnlp/twitter-roberta-base-sentiment-latest'
            },
            'enable_topic_modeling': {
                'type': 'boolean',
                'default': False
            },
            'num_topics': {
                'type': 'integer', 
                'default': 5
            },
            'language': {
                'type': 'string',
                'default': 'en'
            }
        }
    },
    'enabled': True,
    'priority': 50
}