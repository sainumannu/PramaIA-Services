# VectorStore Service Guide

**Centralized Vector Database Management Service**

PramaIA-VectorstoreService provides a comprehensive REST API for vector database operations, collection management, embedding generation, and file system reconciliation.

---

## 📖 **Service Overview**

The VectorStore Service is designed for:
1. **Centralized Vector Operations** - Unified interface for all vector database interactions
2. **Collection Management** - Complete CRUD operations for vector collections
3. **Document Processing** - Automated document ingestion and embedding generation
4. **Data Consistency** - Bidirectional synchronization between filesystem and vector store
5. **Scalable Operations** - Batch processing and background task support

### **Key Features**
- **Collection Management** - Create, read, update, delete vector collections
- **Document Operations** - Add, retrieve, search, delete documents in collections
- **Embedding Generation** - Automatic text embedding creation
- **Reconciliation Engine** - Bidirectional sync between filesystem and vector store
- **Scheduling Support** - Automated recurring tasks and maintenance
- **Health Monitoring** - Service status and dependency monitoring

---

## 🏗️ **Service Architecture**

The service is built on FastAPI with ChromaDB as the vector database backend:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   REST API      │    │   Core Logic    │    │   ChromaDB      │
│   (FastAPI)     │◄──►│   (Business)    │◄──►│   (Vectors)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Scheduler     │    │   Reconciler    │    │   File System   │
│   (Background)  │    │   (Sync Logic)  │    │   (Documents)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Module Organization**
- **API** - REST endpoints for service interaction
- **Core** - Business logic for vector operations and reconciliation
- **DB** - Database management for configurations and jobs
- **Scheduler** - Background task scheduling and execution
- **Utils** - Common utilities (configuration, logging, helpers)

---

## 🚀 **Installation & Setup**

### **Prerequisites**
- Python 3.10 or higher
- PramaIA-LogService running (for centralized logging)
- ChromaDB dependencies

### **Installation Steps**

#### **1. Clone and Setup**
```bash
# Clone repository
git clone https://github.com/your-org/PramaIA-VectorstoreService.git
cd PramaIA-VectorstoreService

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

#### **2. Install Dependencies**
```bash
# Install service dependencies
pip install -r requirements.txt

# Install PramaIA-LogService client
cd ../PramaIA-LogService/clients/python
pip install -e .
cd ../../../PramaIA-VectorstoreService
```

#### **3. Configuration**
```bash
# Copy environment configuration
cp .env.example .env

# Edit configuration as needed
nano .env
```

### **Environment Variables**
```env
# Service Configuration
HOST=0.0.0.0
PORT=8090
DEBUG=true

# ChromaDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_PERSIST_DIRECTORY=./chroma_db

# Embedding Model Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu

# Log Service Configuration
LOG_SERVICE_URL=http://localhost:8081
LOG_SERVICE_TIMEOUT=30

# Reconciliation Configuration
RECONCILIATION_INTERVAL=3600  # 1 hour
FILESYSTEM_WATCH_PATH=./documents
```

---

## 🎮 **Service Usage**

### **Starting the Service**
```bash
# Development mode
python main.py

# Production mode with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8090 --workers 4

# Background mode
nohup uvicorn main:app --host 0.0.0.0 --port 8090 &
```

### **Service Verification**
```bash
# Health check
curl http://localhost:8090/health

# API documentation
open http://localhost:8090/docs  # Interactive API docs
open http://localhost:8090/redoc # Alternative documentation
```

---

## 📡 **API Reference**

### **Collection Operations**

#### **Create Collection**
```bash
POST /collections
Content-Type: application/json

{
  "name": "my_collection",
  "metadata": {
    "description": "Sample document collection",
    "domain": "general"
  }
}
```

#### **List Collections**
```bash
GET /collections

# Response
[
  {
    "name": "my_collection",
    "count": 150,
    "metadata": {
      "description": "Sample document collection",
      "domain": "general"
    }
  }
]
```

#### **Get Collection Details**
```bash
GET /collections/{collection_name}

# Response
{
  "name": "my_collection",
  "count": 150,
  "metadata": {...},
  "sample_documents": [...],
  "embedding_stats": {
    "dimension": 384,
    "model": "sentence-transformers/all-MiniLM-L6-v2"
  }
}
```

### **Document Operations**

#### **Add Documents**
```bash
POST /documents/{collection_name}
Content-Type: application/json

{
  "documents": [
    "This is the first document content.",
    "This is the second document content."
  ],
  "metadatas": [
    {"source": "file1.txt", "category": "example"},
    {"source": "file2.txt", "category": "example"}
  ],
  "ids": ["doc1", "doc2"]  # Optional, auto-generated if omitted
}
```

#### **Search Documents**
```bash
POST /search/{collection_name}
Content-Type: application/json

{
  "query": "example content search query",
  "limit": 10,
  "metadata_filter": {
    "category": "example"
  }
}

# Response
{
  "results": [
    {
      "id": "doc1",
      "document": "This is the first document content.",
      "metadata": {"source": "file1.txt", "category": "example"},
      "distance": 0.123
    }
  ],
  "total_results": 1,
  "query_time_ms": 45
}
```

#### **Get Document**
```bash
GET /documents/{collection_name}/{document_id}

# Response
{
  "id": "doc1",
  "document": "This is the first document content.",
  "metadata": {"source": "file1.txt", "category": "example"},
  "embedding": [0.1, 0.2, ...],  # Optional
  "created_at": "2024-11-26T10:30:00Z"
}
```

### **Embedding Operations**

#### **Generate Embeddings**
```bash
POST /embeddings
Content-Type: application/json

{
  "texts": [
    "Generate embedding for this text",
    "And for this text too"
  ]
}

# Response
{
  "embeddings": [
    [0.1, 0.2, 0.3, ...],
    [0.4, 0.5, 0.6, ...]
  ],
  "model": "sentence-transformers/all-MiniLM-L6-v2",
  "dimension": 384
}
```

### **Reconciliation Operations**

#### **Trigger Manual Reconciliation**
```bash
POST /reconcile
Content-Type: application/json

{
  "filesystem_path": "./documents",
  "collection_name": "my_collection",
  "recursive": true,
  "dry_run": false
}

# Response
{
  "reconciliation_id": "recon_123",
  "status": "started",
  "estimated_duration": "5 minutes"
}
```

#### **Get Reconciliation Status**
```bash
GET /reconcile/{reconciliation_id}

# Response
{
  "id": "recon_123",
  "status": "completed",
  "started_at": "2024-11-26T10:30:00Z",
  "completed_at": "2024-11-26T10:35:00Z",
  "summary": {
    "files_processed": 250,
    "documents_added": 45,
    "documents_updated": 12,
    "documents_removed": 3,
    "errors": 0
  }
}
```

---

## 🔧 **Configuration Options**

### **Embedding Model Configuration**
```python
# Available embedding models
SUPPORTED_MODELS = [
    "sentence-transformers/all-MiniLM-L6-v2",       # Fast, good quality
    "sentence-transformers/all-mpnet-base-v2",      # Better quality, slower
    "sentence-transformers/distilbert-base-nli-mean-tokens",
    "text-embedding-ada-002"                        # OpenAI (requires API key)
]

# Model selection in .env
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
OPENAI_API_KEY=your_api_key_here  # If using OpenAI models
```

### **ChromaDB Configuration**
```env
# Persistent storage
CHROMA_PERSIST_DIRECTORY=./chroma_db

# In-memory database (development)
CHROMA_IN_MEMORY=true

# Remote ChromaDB instance
CHROMA_HOST=remote-chroma.example.com
CHROMA_PORT=8000
CHROMA_SSL=true
```

### **Performance Tuning**
```env
# Batch processing
BATCH_SIZE=100
MAX_CONCURRENT_EMBEDDINGS=5

# Memory management
MAX_MEMORY_USAGE_MB=4096
EMBEDDING_CACHE_SIZE=1000

# Timeouts
REQUEST_TIMEOUT=300
EMBEDDING_TIMEOUT=60
```

---

## 🔍 **Monitoring & Troubleshooting**

### **Health Checks**
```bash
# Service health
curl http://localhost:8090/health

# Dependency health
curl http://localhost:8090/health/detailed

# Response
{
  "status": "healthy",
  "version": "1.4.2",
  "uptime": "2 days, 14:30:15",
  "dependencies": {
    "chromadb": "healthy",
    "log_service": "healthy",
    "filesystem": "healthy"
  },
  "metrics": {
    "total_collections": 5,
    "total_documents": 1250,
    "embedding_cache_size": 150,
    "reconciliation_status": "idle"
  }
}
```

### **Performance Metrics**
```bash
# Service metrics
curl http://localhost:8090/metrics

# Response
{
  "requests": {
    "total": 15430,
    "success": 15285,
    "errors": 145,
    "average_response_time_ms": 85
  },
  "operations": {
    "documents_added": 1250,
    "searches_performed": 3200,
    "embeddings_generated": 1250
  },
  "resource_usage": {
    "memory_usage_mb": 512,
    "cpu_usage_percent": 15,
    "disk_usage_mb": 2048
  }
}
```

### **Troubleshooting Common Issues**

#### **Service Won't Start**
```bash
# Check Python version
python --version  # Should be 3.10+

# Check dependencies
pip list | grep -E "(fastapi|chromadb|sentence-transformers)"

# Check port availability
netstat -an | grep :8090

# Check logs
tail -f logs/vectorstore.log
```

#### **ChromaDB Connection Issues**
```bash
# Test ChromaDB connection
curl http://localhost:8000/api/v1/heartbeat

# Check ChromaDB logs
docker logs chromadb-container  # If using Docker

# Verify persistence directory
ls -la ./chroma_db/
```

#### **Embedding Generation Errors**
```bash
# Test embedding model
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print(model.encode(['test']).shape)
"

# Check memory usage
htop  # or top on some systems

# Reduce batch size
export BATCH_SIZE=10
```

#### **Performance Issues**
```bash
# Monitor resource usage
curl http://localhost:8090/metrics | jq '.resource_usage'

# Check slow queries
curl http://localhost:8090/admin/slow-queries

# Optimize ChromaDB
curl -X POST http://localhost:8090/admin/optimize
```

---

## 🔗 **Integration Examples**

### **Python Client Example**
```python
import requests
import json

class VectorStoreClient:
    def __init__(self, base_url="http://localhost:8090"):
        self.base_url = base_url
    
    def create_collection(self, name, metadata=None):
        response = requests.post(
            f"{self.base_url}/collections",
            json={"name": name, "metadata": metadata or {}}
        )
        return response.json()
    
    def add_documents(self, collection_name, documents, metadatas=None):
        response = requests.post(
            f"{self.base_url}/documents/{collection_name}",
            json={
                "documents": documents,
                "metadatas": metadatas or [{}] * len(documents)
            }
        )
        return response.json()
    
    def search(self, collection_name, query, limit=10):
        response = requests.post(
            f"{self.base_url}/search/{collection_name}",
            json={"query": query, "limit": limit}
        )
        return response.json()

# Usage example
client = VectorStoreClient()

# Create collection
client.create_collection("docs", {"type": "documentation"})

# Add documents
client.add_documents(
    "docs",
    ["Python is a programming language", "FastAPI is a web framework"],
    [{"source": "python.txt"}, {"source": "fastapi.txt"}]
)

# Search
results = client.search("docs", "web framework programming")
print(f"Found {len(results['results'])} results")
```

### **Node.js Client Example**
```javascript
const axios = require('axios');

class VectorStoreClient {
    constructor(baseURL = 'http://localhost:8090') {
        this.client = axios.create({ baseURL });
    }
    
    async createCollection(name, metadata = {}) {
        const response = await this.client.post('/collections', {
            name, metadata
        });
        return response.data;
    }
    
    async addDocuments(collectionName, documents, metadatas = []) {
        const response = await this.client.post(`/documents/${collectionName}`, {
            documents,
            metadatas: metadatas.length ? metadatas : documents.map(() => ({}))
        });
        return response.data;
    }
    
    async search(collectionName, query, limit = 10) {
        const response = await this.client.post(`/search/${collectionName}`, {
            query, limit
        });
        return response.data;
    }
}

// Usage
const client = new VectorStoreClient();

async function example() {
    // Create collection
    await client.createCollection('docs', { type: 'documentation' });
    
    // Add documents
    await client.addDocuments(
        'docs',
        ['JavaScript is a programming language', 'Express is a web framework'],
        [{ source: 'js.txt' }, { source: 'express.txt' }]
    );
    
    // Search
    const results = await client.search('docs', 'web framework programming');
    console.log(`Found ${results.results.length} results`);
}
```

---

## 📚 **Related Documentation**

- [VectorStore Architecture](VECTORSTORE_ARCHITECTURE.md) - Detailed architecture documentation
- [VectorStore Integration](VECTORSTORE_INTEGRATION.md) - Integration patterns and examples
- [VectorStore Migration](VECTORSTORE_MIGRATION.md) - Migration and upgrade procedures
- [API Documentation](../PDK/API_DOCUMENTATION.md) - Complete API reference

---

## 🆘 **Support & Maintenance**

### **Backup Procedures**
```bash
# Backup ChromaDB data
tar -czf vectorstore_backup_$(date +%Y%m%d).tar.gz ./chroma_db/

# Backup configuration
cp .env config_backup_$(date +%Y%m%d).env
```

### **Updates & Upgrades**
```bash
# Update service
git pull
pip install -r requirements.txt --upgrade

# Database migrations (if needed)
python scripts/migrate.py

# Restart service
systemctl restart vectorstore-service
```

### **Log Analysis**
```bash
# View recent logs
tail -f logs/vectorstore.log

# Filter error logs
grep ERROR logs/vectorstore.log | tail -20

# Performance analysis
grep "response_time" logs/vectorstore.log | awk '{print $5}' | sort -n
```

**Service Status:** ✅ Active  
**Default Port:** 8090  
**Health Endpoint:** `http://localhost:8090/health`