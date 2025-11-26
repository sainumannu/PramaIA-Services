"""
Generic Vector Store Processor

Processore universale per operazioni vector database: write, read, search, manage.
Supporta Chroma, VectorStore Service, Pinecone, Weaviate, Elasticsearch e connettori custom.
"""

import logging
import json
import hashlib
import uuid
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


# ============================================================================
# Abstract Interfaces for Vector Store Operations
# ============================================================================

class VectorStoreConnector(ABC):
    """Abstract base class for vector store connectors."""
    
    @abstractmethod
    async def connect(self, config: Dict[str, Any]) -> bool:
        """Establish connection to vector store."""
        pass
    
    @abstractmethod
    async def create_collection(self, name: str, config: Dict[str, Any]) -> bool:
        """Create a new collection."""
        pass
    
    @abstractmethod
    async def write_vectors(self, collection: str, vectors: List[Dict[str, Any]], config: Dict[str, Any]) -> List[str]:
        """Write vectors to collection."""
        pass
    
    @abstractmethod
    async def read_vectors(self, collection: str, ids: List[str], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Read vectors by IDs."""
        pass
    
    @abstractmethod
    async def search_vectors(self, collection: str, query_vector: List[float], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search similar vectors."""
        pass
    
    @abstractmethod
    async def delete_vectors(self, collection: str, ids: List[str], config: Dict[str, Any]) -> bool:
        """Delete vectors by IDs."""
        pass
    
    @abstractmethod
    async def list_collections(self, config: Dict[str, Any]) -> List[str]:
        """List all collections."""
        pass
    
    @abstractmethod
    async def get_collection_info(self, collection: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get collection metadata."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Close connection."""
        pass


# ============================================================================
# Chroma Connector Implementation
# ============================================================================

class ChromaConnector(VectorStoreConnector):
    """Connector for ChromaDB."""
    
    def __init__(self):
        self.client = None
        self.current_persist_directory = None
        self.is_available = self._check_availability()
    
    def _check_availability(self) -> bool:
        try:
            import chromadb
            return True
        except ImportError:
            logger.warning("⚠️ chromadb not available")
            return False
    
    async def connect(self, config: Dict[str, Any]) -> bool:
        if not self.is_available:
            return False
        
        try:
            import chromadb
            from chromadb.config import Settings
            
            persist_directory = config.get('persist_directory', './chroma_db')
            
            if (self.client is not None and 
                self.current_persist_directory == persist_directory):
                return True
            
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            self.current_persist_directory = persist_directory
            
            logger.info(f"✅ Connected to ChromaDB at {persist_directory}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to ChromaDB: {e}")
            return False
    
    async def create_collection(self, name: str, config: Dict[str, Any]) -> bool:
        if not self.client:
            return False
        
        try:
            distance_metric = config.get('distance_metric', 'cosine')
            
            # Check if collection exists
            try:
                self.client.get_collection(name)
                logger.info(f"Collection '{name}' already exists")
                return True
            except Exception:
                # Collection doesn't exist, create it
                self.client.create_collection(
                    name=name,
                    metadata={
                        "hnsw:space": distance_metric,
                        "created_at": datetime.now().isoformat()
                    }
                )
                logger.info(f"✅ Created ChromaDB collection '{name}'")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to create collection '{name}': {e}")
            return False
    
    async def write_vectors(self, collection: str, vectors: List[Dict[str, Any]], config: Dict[str, Any]) -> List[str]:
        if not self.client:
            return []
        
        try:
            chroma_collection = self.client.get_collection(collection)
            
            ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            for vector_data in vectors:
                vector_id = vector_data.get('id', str(uuid.uuid4()))
                ids.append(vector_id)
                embeddings.append(vector_data['embedding'])
                documents.append(vector_data.get('document', ''))
                
                metadata = vector_data.get('metadata', {})
                metadata.update({
                    'timestamp': datetime.now().isoformat(),
                    'model': vector_data.get('model', 'unknown')
                })
                metadatas.append(metadata)
            
            # Write in batches
            batch_size = config.get('batch_size', 100)
            written_ids = []
            
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i:i + batch_size]
                batch_embeddings = embeddings[i:i + batch_size]
                batch_documents = documents[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]
                
                chroma_collection.add(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    documents=batch_documents,
                    metadatas=batch_metadatas
                )
                written_ids.extend(batch_ids)
            
            logger.info(f"✅ Written {len(written_ids)} vectors to ChromaDB collection '{collection}'")
            return written_ids
            
        except Exception as e:
            logger.error(f"❌ Failed to write vectors to ChromaDB: {e}")
            return []
    
    async def search_vectors(self, collection: str, query_vector: List[float], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        
        try:
            chroma_collection = self.client.get_collection(collection)
            
            n_results = config.get('n_results', 10)
            include = config.get('include', ['documents', 'metadatas', 'distances'])
            
            results = chroma_collection.query(
                query_embeddings=[query_vector],
                n_results=n_results,
                include=include
            )
            
            # Format results
            formatted_results = []
            if results['ids'] and len(results['ids']) > 0:
                for i, doc_id in enumerate(results['ids'][0]):
                    result = {
                        'id': doc_id,
                        'score': 1.0 - results['distances'][0][i] if 'distances' in results else 1.0,  # Convert distance to similarity
                        'distance': results['distances'][0][i] if 'distances' in results else 0.0
                    }
                    
                    if 'documents' in include and 'documents' in results:
                        result['document'] = results['documents'][0][i]
                    
                    if 'metadatas' in include and 'metadatas' in results:
                        result['metadata'] = results['metadatas'][0][i] or {}
                    
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Failed to search ChromaDB: {e}")
            return []
    
    async def read_vectors(self, collection: str, ids: List[str], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        
        try:
            chroma_collection = self.client.get_collection(collection)
            
            results = chroma_collection.get(
                ids=ids,
                include=['documents', 'metadatas', 'embeddings']
            )
            
            formatted_results = []
            if results['ids']:
                for i, doc_id in enumerate(results['ids']):
                    result = {
                        'id': doc_id,
                        'document': results['documents'][i] if 'documents' in results else '',
                        'metadata': results['metadatas'][i] if 'metadatas' in results else {},
                        'embedding': results['embeddings'][i] if 'embeddings' in results else []
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Failed to read vectors from ChromaDB: {e}")
            return []
    
    async def delete_vectors(self, collection: str, ids: List[str], config: Dict[str, Any]) -> bool:
        if not self.client:
            return False
        
        try:
            chroma_collection = self.client.get_collection(collection)
            chroma_collection.delete(ids=ids)
            logger.info(f"✅ Deleted {len(ids)} vectors from ChromaDB collection '{collection}'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete vectors from ChromaDB: {e}")
            return False
    
    async def list_collections(self, config: Dict[str, Any]) -> List[str]:
        if not self.client:
            return []
        
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"❌ Failed to list ChromaDB collections: {e}")
            return []
    
    async def get_collection_info(self, collection: str, config: Dict[str, Any]) -> Dict[str, Any]:
        if not self.client:
            return {}
        
        try:
            chroma_collection = self.client.get_collection(collection)
            count = chroma_collection.count()
            
            return {
                'name': collection,
                'count': count,
                'metadata': chroma_collection.metadata or {}
            }
        except Exception as e:
            logger.error(f"❌ Failed to get ChromaDB collection info: {e}")
            return {}
    
    async def disconnect(self) -> bool:
        self.client = None
        self.current_persist_directory = None
        return True


# ============================================================================
# VectorStore Service Connector Implementation
# ============================================================================

class VectorStoreServiceConnector(VectorStoreConnector):
    """Connector for PramaIA VectorStore Service."""
    
    def __init__(self):
        self.service_url = None
        self.timeout = 30
    
    async def connect(self, config: Dict[str, Any]) -> bool:
        try:
            self.service_url = config.get('service_url', 'http://localhost:8090')
            self.timeout = config.get('timeout', 30)
            
            # Test connection
            response = requests.get(f"{self.service_url}/health", timeout=self.timeout)
            if response.status_code == 200:
                logger.info(f"✅ Connected to VectorStore Service at {self.service_url}")
                return True
            else:
                logger.error(f"❌ VectorStore Service returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to VectorStore Service: {e}")
            return False
    
    async def create_collection(self, name: str, config: Dict[str, Any]) -> bool:
        try:
            # VectorStore Service typically auto-creates collections
            # This is a placeholder for explicit creation if supported
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create collection in VectorStore Service: {e}")
            return False
    
    async def write_vectors(self, collection: str, vectors: List[Dict[str, Any]], config: Dict[str, Any]) -> List[str]:
        try:
            # Prepare data for VectorStore Service format
            documents = []
            embeddings = []
            
            for vector_data in vectors:
                documents.append(vector_data.get('document', ''))
                embeddings.append(vector_data['embedding'])
            
            payload = {
                'documents': documents,
                'embeddings': embeddings,
                'collection': collection
            }
            
            response = requests.post(
                f"{self.service_url}/add_documents",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                document_ids = result.get('document_ids', [])
                logger.info(f"✅ Written {len(document_ids)} vectors to VectorStore Service collection '{collection}'")
                return document_ids
            else:
                logger.error(f"❌ VectorStore Service write failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Failed to write vectors to VectorStore Service: {e}")
            return []
    
    async def search_vectors(self, collection: str, query_vector: List[float], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            limit = config.get('n_results', 10)
            
            payload = {
                'query_embedding': query_vector,
                'collection': collection,
                'limit': limit
            }
            
            response = requests.post(
                f"{self.service_url}/search",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                results = response.json()
                
                formatted_results = []
                for result in results.get('results', []):
                    formatted_results.append({
                        'id': result.get('id', ''),
                        'document': result.get('content', ''),
                        'score': result.get('score', 0.0),
                        'metadata': result.get('metadata', {})
                    })
                
                return formatted_results
            else:
                logger.error(f"❌ VectorStore Service search failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Failed to search VectorStore Service: {e}")
            return []
    
    async def read_vectors(self, collection: str, ids: List[str], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        # VectorStore Service typically doesn't support direct ID lookup
        # This could be implemented if the service supports it
        logger.warning("VectorStore Service doesn't support direct vector read by ID")
        return []
    
    async def delete_vectors(self, collection: str, ids: List[str], config: Dict[str, Any]) -> bool:
        # VectorStore Service typically doesn't support deletion
        # This could be implemented if the service supports it
        logger.warning("VectorStore Service doesn't support vector deletion")
        return False
    
    async def list_collections(self, config: Dict[str, Any]) -> List[str]:
        try:
            response = requests.get(f"{self.service_url}/collections", timeout=self.timeout)
            if response.status_code == 200:
                return response.json().get('collections', [])
            return []
        except Exception as e:
            logger.error(f"❌ Failed to list collections: {e}")
            return []
    
    async def get_collection_info(self, collection: str, config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = requests.get(f"{self.service_url}/collections/{collection}", timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"❌ Failed to get collection info: {e}")
            return {}
    
    async def disconnect(self) -> bool:
        return True


# ============================================================================
# Elasticsearch Vector Connector Implementation  
# ============================================================================

class ElasticsearchVectorConnector(VectorStoreConnector):
    """Connector for Elasticsearch with vector search capabilities."""
    
    def __init__(self):
        self.client = None
        self.is_available = self._check_availability()
    
    def _check_availability(self) -> bool:
        try:
            from elasticsearch import Elasticsearch
            return True
        except ImportError:
            logger.warning("⚠️ elasticsearch not available")
            return False
    
    async def connect(self, config: Dict[str, Any]) -> bool:
        if not self.is_available:
            return False
        
        try:
            from elasticsearch import Elasticsearch
            
            host = config.get('host', 'localhost')
            port = config.get('port', 9200)
            username = config.get('username')
            password = config.get('password')
            
            es_config = {
                'hosts': [f"{host}:{port}"],
                'timeout': config.get('timeout', 30)
            }
            
            if username and password:
                es_config['basic_auth'] = (username, password)
            
            self.client = Elasticsearch(**es_config)
            
            # Test connection
            if self.client.ping():
                logger.info(f"✅ Connected to Elasticsearch at {host}:{port}")
                return True
            else:
                logger.error("❌ Failed to ping Elasticsearch")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to Elasticsearch: {e}")
            return False
    
    async def create_collection(self, name: str, config: Dict[str, Any]) -> bool:
        if not self.client:
            return False
        
        try:
            vector_dimensions = config.get('vector_dimensions', 384)
            
            mapping = {
                "mappings": {
                    "properties": {
                        "vector": {
                            "type": "dense_vector",
                            "dims": vector_dimensions
                        },
                        "document": {"type": "text"},
                        "metadata": {"type": "object"},
                        "timestamp": {"type": "date"}
                    }
                }
            }
            
            if not self.client.indices.exists(index=name):
                self.client.indices.create(index=name, body=mapping)
                logger.info(f"✅ Created Elasticsearch index '{name}'")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create Elasticsearch index: {e}")
            return False
    
    async def write_vectors(self, collection: str, vectors: List[Dict[str, Any]], config: Dict[str, Any]) -> List[str]:
        if not self.client:
            return []
        
        try:
            written_ids = []
            
            for vector_data in vectors:
                doc_id = vector_data.get('id', str(uuid.uuid4()))
                
                doc = {
                    'vector': vector_data['embedding'],
                    'document': vector_data.get('document', ''),
                    'metadata': vector_data.get('metadata', {}),
                    'timestamp': datetime.now().isoformat()
                }
                
                self.client.index(index=collection, id=doc_id, body=doc)
                written_ids.append(doc_id)
            
            # Refresh index
            self.client.indices.refresh(index=collection)
            
            logger.info(f"✅ Written {len(written_ids)} vectors to Elasticsearch index '{collection}'")
            return written_ids
            
        except Exception as e:
            logger.error(f"❌ Failed to write vectors to Elasticsearch: {e}")
            return []
    
    async def search_vectors(self, collection: str, query_vector: List[float], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        
        try:
            size = config.get('n_results', 10)
            
            query = {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                        "params": {"query_vector": query_vector}
                    }
                }
            }
            
            response = self.client.search(index=collection, body={"query": query, "size": size})
            
            formatted_results = []
            for hit in response['hits']['hits']:
                formatted_results.append({
                    'id': hit['_id'],
                    'score': hit['_score'] - 1.0,  # Subtract 1.0 to get back to cosine similarity
                    'document': hit['_source'].get('document', ''),
                    'metadata': hit['_source'].get('metadata', {})
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Failed to search Elasticsearch: {e}")
            return []
    
    async def read_vectors(self, collection: str, ids: List[str], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        
        try:
            response = self.client.mget(index=collection, body={"ids": ids})
            
            formatted_results = []
            for doc in response['docs']:
                if doc['found']:
                    formatted_results.append({
                        'id': doc['_id'],
                        'document': doc['_source'].get('document', ''),
                        'metadata': doc['_source'].get('metadata', {}),
                        'embedding': doc['_source'].get('vector', [])
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Failed to read vectors from Elasticsearch: {e}")
            return []
    
    async def delete_vectors(self, collection: str, ids: List[str], config: Dict[str, Any]) -> bool:
        if not self.client:
            return False
        
        try:
            for doc_id in ids:
                self.client.delete(index=collection, id=doc_id, ignore=[404])
            
            # Refresh index
            self.client.indices.refresh(index=collection)
            
            logger.info(f"✅ Deleted {len(ids)} vectors from Elasticsearch index '{collection}'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete vectors from Elasticsearch: {e}")
            return False
    
    async def list_collections(self, config: Dict[str, Any]) -> List[str]:
        if not self.client:
            return []
        
        try:
            indices = self.client.indices.get_alias(index="*")
            return list(indices.keys())
        except Exception as e:
            logger.error(f"❌ Failed to list Elasticsearch indices: {e}")
            return []
    
    async def get_collection_info(self, collection: str, config: Dict[str, Any]) -> Dict[str, Any]:
        if not self.client:
            return {}
        
        try:
            stats = self.client.indices.stats(index=collection)
            index_stats = stats['indices'].get(collection, {})
            
            return {
                'name': collection,
                'count': index_stats.get('total', {}).get('docs', {}).get('count', 0),
                'size': index_stats.get('total', {}).get('store', {}).get('size_in_bytes', 0)
            }
        except Exception as e:
            logger.error(f"❌ Failed to get Elasticsearch collection info: {e}")
            return {}
    
    async def disconnect(self) -> bool:
        if self.client:
            self.client.transport.close()
        return True


# ============================================================================
# Mock Connector for Testing
# ============================================================================

class MockVectorStoreConnector(VectorStoreConnector):
    """Mock connector for testing when no real vector store is available."""
    
    def __init__(self):
        self.collections = {}
        self.connected = False
    
    async def connect(self, config: Dict[str, Any]) -> bool:
        self.connected = True
        logger.info("✅ Connected to Mock Vector Store")
        return True
    
    async def create_collection(self, name: str, config: Dict[str, Any]) -> bool:
        if name not in self.collections:
            self.collections[name] = {}
        return True
    
    async def write_vectors(self, collection: str, vectors: List[Dict[str, Any]], config: Dict[str, Any]) -> List[str]:
        if collection not in self.collections:
            self.collections[collection] = {}
        
        ids = []
        for vector_data in vectors:
            vector_id = vector_data.get('id', str(uuid.uuid4()))
            self.collections[collection][vector_id] = vector_data
            ids.append(vector_id)
        
        logger.info(f"✅ Mock: Written {len(ids)} vectors to collection '{collection}'")
        return ids
    
    async def search_vectors(self, collection: str, query_vector: List[float], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        if collection not in self.collections:
            return []
        
        # Return first N results (mock)
        n_results = config.get('n_results', 10)
        results = []
        
        for i, (doc_id, vector_data) in enumerate(list(self.collections[collection].items())[:n_results]):
            results.append({
                'id': doc_id,
                'score': 0.9 - (i * 0.1),  # Mock decreasing scores
                'document': vector_data.get('document', ''),
                'metadata': vector_data.get('metadata', {})
            })
        
        return results
    
    async def read_vectors(self, collection: str, ids: List[str], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        if collection not in self.collections:
            return []
        
        results = []
        for doc_id in ids:
            if doc_id in self.collections[collection]:
                vector_data = self.collections[collection][doc_id]
                results.append({
                    'id': doc_id,
                    'document': vector_data.get('document', ''),
                    'metadata': vector_data.get('metadata', {}),
                    'embedding': vector_data.get('embedding', [])
                })
        
        return results
    
    async def delete_vectors(self, collection: str, ids: List[str], config: Dict[str, Any]) -> bool:
        if collection not in self.collections:
            return False
        
        for doc_id in ids:
            self.collections[collection].pop(doc_id, None)
        
        return True
    
    async def list_collections(self, config: Dict[str, Any]) -> List[str]:
        return list(self.collections.keys())
    
    async def get_collection_info(self, collection: str, config: Dict[str, Any]) -> Dict[str, Any]:
        if collection not in self.collections:
            return {}
        
        return {
            'name': collection,
            'count': len(self.collections[collection]),
            'metadata': {'type': 'mock'}
        }
    
    async def disconnect(self) -> bool:
        self.connected = False
        return True


# ============================================================================
# Main Generic Vector Store Processor
# ============================================================================

class GenericVectorStoreProcessor:
    """Universal vector store processor supporting multiple backends."""
    
    def __init__(self):
        # Registry of available connectors
        self.connectors = {
            'chroma': ChromaConnector(),
            'vectorstore_service': VectorStoreServiceConnector(),
            'elasticsearch': ElasticsearchVectorConnector(),
            'mock': MockVectorStoreConnector()
        }
        
        self.current_connector = None
        self.current_backend = None
    
    async def process(self, context) -> Dict[str, Any]:
        """Main processing method."""
        logger.info("[GenericVectorStoreProcessor] INGRESSO nodo: process")
        
        try:
            config = context.get('config', {})
            inputs = context.get('inputs', {})
            
            operation = config.get('operation', 'write')
            
            if operation == 'write':
                return await self._process_write(inputs, config)
            elif operation == 'read':
                return await self._process_read(inputs, config)
            elif operation == 'search':
                return await self._process_search(inputs, config)
            elif operation == 'delete':
                return await self._process_delete(inputs, config)
            elif operation == 'manage':
                return await self._process_manage(inputs, config)
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            logger.error(f"[GenericVectorStoreProcessor] USCITA nodo (errore): {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "operation": config.get('operation', 'unknown'),
                "output": None
            }
    
    async def _get_connector(self, backend_type: str) -> Optional[VectorStoreConnector]:
        """Get and initialize connector for backend type."""
        if self.current_backend == backend_type and self.current_connector:
            return self.current_connector
        
        if backend_type not in self.connectors:
            logger.error(f"Unknown backend type: {backend_type}")
            return None
        
        self.current_connector = self.connectors[backend_type]
        self.current_backend = backend_type
        
        return self.current_connector
    
    async def _process_write(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process vector writing operation."""
        backend_type = config.get('backend_type', 'chroma')
        collection = config.get('collection', 'default')
        
        # Get input data
        embeddings_input = inputs.get('embeddings_input', inputs.get('embeddings', {}))
        if isinstance(embeddings_input, dict) and 'embeddings' in embeddings_input:
            # Format: {embeddings: [...], chunks: [...], model: "..."}
            embeddings = embeddings_input['embeddings']
            documents = embeddings_input.get('chunks', embeddings_input.get('documents', []))
            model = embeddings_input.get('model', 'unknown')
        else:
            # Direct input format
            embeddings = inputs.get('embeddings', [])
            documents = inputs.get('documents', inputs.get('texts', []))
            model = inputs.get('model', 'unknown')
        
        if not embeddings:
            raise ValueError("No embeddings provided")
        
        if len(embeddings) != len(documents):
            raise ValueError(f"Mismatch: {len(embeddings)} embeddings vs {len(documents)} documents")
        
        # Get connector
        connector = await self._get_connector(backend_type)
        if not connector:
            raise ValueError(f"Failed to initialize {backend_type} connector")
        
        # Connect to backend
        backend_config = config.get('backend_config', {})
        if not await connector.connect(backend_config):
            raise ValueError(f"Failed to connect to {backend_type}")
        
        # Create collection if needed
        await connector.create_collection(collection, config)
        
        # Prepare vector data
        vector_data = []
        for i, (embedding, document) in enumerate(zip(embeddings, documents)):
            vector_item = {
                'id': inputs.get('ids', [str(uuid.uuid4()) for _ in range(len(embeddings))])[i],
                'embedding': embedding,
                'document': document,
                'metadata': {
                    'model': model,
                    'timestamp': datetime.now().isoformat(),
                    'index': i,
                    **inputs.get('metadata', {})
                }
            }
            vector_data.append(vector_item)
        
        # Write vectors
        written_ids = await connector.write_vectors(collection, vector_data, config)
        
        logger.info(f"[GenericVectorStoreProcessor] USCITA write (successo): {len(written_ids)} vectors written")
        return {
            "status": "success",
            "operation": "write",
            "output": {
                "collection": collection,
                "backend": backend_type,
                "written_ids": written_ids,
                "vectors_written": len(written_ids),
                "model_used": model
            }
        }
    
    async def _process_read(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process vector reading operation."""
        backend_type = config.get('backend_type', 'chroma')
        collection = config.get('collection', 'default')
        ids = inputs.get('ids', inputs.get('vector_ids', []))
        
        if not ids:
            raise ValueError("No vector IDs provided")
        
        # Get connector
        connector = await self._get_connector(backend_type)
        if not connector:
            raise ValueError(f"Failed to initialize {backend_type} connector")
        
        # Connect to backend
        backend_config = config.get('backend_config', {})
        if not await connector.connect(backend_config):
            raise ValueError(f"Failed to connect to {backend_type}")
        
        # Read vectors
        vectors = await connector.read_vectors(collection, ids, config)
        
        logger.info(f"[GenericVectorStoreProcessor] USCITA read (successo): {len(vectors)} vectors read")
        return {
            "status": "success",
            "operation": "read",
            "output": {
                "collection": collection,
                "backend": backend_type,
                "vectors": vectors,
                "vectors_found": len(vectors),
                "requested_ids": len(ids)
            }
        }
    
    async def _process_search(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process vector search operation."""
        backend_type = config.get('backend_type', 'chroma')
        collection = config.get('collection', 'default')
        
        query_vector = inputs.get('query_vector', inputs.get('query_embedding', []))
        if not query_vector:
            raise ValueError("No query vector provided")
        
        # Get connector
        connector = await self._get_connector(backend_type)
        if not connector:
            raise ValueError(f"Failed to initialize {backend_type} connector")
        
        # Connect to backend
        backend_config = config.get('backend_config', {})
        if not await connector.connect(backend_config):
            raise ValueError(f"Failed to connect to {backend_type}")
        
        # Search vectors
        results = await connector.search_vectors(collection, query_vector, config)
        
        logger.info(f"[GenericVectorStoreProcessor] USCITA search (successo): {len(results)} results found")
        return {
            "status": "success",
            "operation": "search",
            "output": {
                "collection": collection,
                "backend": backend_type,
                "results": results,
                "results_count": len(results),
                "query_config": {
                    "n_results": config.get('n_results', 10),
                    "min_score": config.get('min_score', 0.0)
                }
            }
        }
    
    async def _process_delete(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process vector deletion operation."""
        backend_type = config.get('backend_type', 'chroma')
        collection = config.get('collection', 'default')
        ids = inputs.get('ids', inputs.get('vector_ids', []))
        
        if not ids:
            raise ValueError("No vector IDs provided for deletion")
        
        # Get connector
        connector = await self._get_connector(backend_type)
        if not connector:
            raise ValueError(f"Failed to initialize {backend_type} connector")
        
        # Connect to backend
        backend_config = config.get('backend_config', {})
        if not await connector.connect(backend_config):
            raise ValueError(f"Failed to connect to {backend_type}")
        
        # Delete vectors
        success = await connector.delete_vectors(collection, ids, config)
        
        logger.info(f"[GenericVectorStoreProcessor] USCITA delete (successo): {len(ids) if success else 0} vectors deleted")
        return {
            "status": "success" if success else "error",
            "operation": "delete",
            "output": {
                "collection": collection,
                "backend": backend_type,
                "deleted_ids": ids if success else [],
                "vectors_deleted": len(ids) if success else 0,
                "success": success
            }
        }
    
    async def _process_manage(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process management operations (list collections, get info, etc.)."""
        backend_type = config.get('backend_type', 'chroma')
        management_action = config.get('management_action', 'list_collections')
        
        # Get connector
        connector = await self._get_connector(backend_type)
        if not connector:
            raise ValueError(f"Failed to initialize {backend_type} connector")
        
        # Connect to backend
        backend_config = config.get('backend_config', {})
        if not await connector.connect(backend_config):
            raise ValueError(f"Failed to connect to {backend_type}")
        
        result = {}
        
        if management_action == 'list_collections':
            collections = await connector.list_collections(config)
            result = {
                'collections': collections,
                'collection_count': len(collections)
            }
        elif management_action == 'get_collection_info':
            collection = config.get('collection', inputs.get('collection', 'default'))
            info = await connector.get_collection_info(collection, config)
            result = {
                'collection_info': info
            }
        elif management_action == 'create_collection':
            collection = config.get('collection', inputs.get('collection'))
            if not collection:
                raise ValueError("Collection name required for creation")
            success = await connector.create_collection(collection, config)
            result = {
                'collection_created': success,
                'collection_name': collection
            }
        else:
            raise ValueError(f"Unknown management action: {management_action}")
        
        logger.info(f"[GenericVectorStoreProcessor] USCITA manage (successo): {management_action}")
        return {
            "status": "success",
            "operation": "manage",
            "output": {
                "backend": backend_type,
                "management_action": management_action,
                **result
            }
        }


# Funzione entry point per il PDK
async def process_node(context):
    """Entry point per il Generic Vector Store Processor."""
    processor = GenericVectorStoreProcessor()
    return await processor.process(context)