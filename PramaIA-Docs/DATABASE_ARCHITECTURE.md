# Database Architecture - PramaIA System

**Last Updated**: 18 November 2025  
**Status**: Complete mapping of all databases in PramaIA ecosystem

---

## 📍 Database Locations & Functions

### 1. **PramaIAServer - Main Backend Database**

**Location**: `PramaIAServer/backend/db/database.db`  
**Type**: SQLite3  
**Purpose**: Central management of users, workflows, triggers, sessions, audit logs

#### Tables:
| Table | Purpose | Status |
|-------|---------|--------|
| `users` | User accounts, roles, authentication (with user_id UUID) | Core |
| `chat_sessions` | Chat/conversation state | Core |
| `messages` | Chat message history | Core |
| `workflows` | Workflow definitions (name, description, metadata) | Core |
| `workflow_nodes` | DAG nodes within workflows | Core |
| `workflow_connections` | Edges between nodes (connections) | Core |
| `workflow_executions` | Execution history & results | Core |
| `workflow_triggers` | Event → Workflow mappings | Core |
| `pdf_monitor_events` | File monitoring events (creation, deletion, modification) | Monitoring |
| `file_hashes` | Checksum tracking for deduplication | Auxiliary |
| `user_groups` | Group management & permissions | Auxiliary |
| `user_group_members` | Group membership | Auxiliary |
| `group_permissions` | Role-based access control | Auxiliary |

#### Key Relationships:
```
users ←─── chat_sessions
        ├─ workflow_executions
        └─ workflows

workflows ←─── workflow_nodes
           ├─ workflow_connections
           ├─ workflow_executions
           └─ workflow_triggers
```

#### Usage:
- Backend startup: Initializes SQLAlchemy ORM
- WorkflowEngine: Reads workflow definitions, creates execution records
- TriggerService: Queries triggers for event matching
- DocumentService: Logs PDF monitor events

---

### 2. **VectorstoreService - Document & Metadata Database**

**Location**: `PramaIA-VectorstoreService/data/documents.db`  
**Type**: SQLite3  
**Purpose**: **PRIMARY** storage for document metadata and content indexing

#### Tables:
| Table | Purpose | Rows |
|-------|---------|------|
| `documents` | Document records (filename, collection, content, timestamps) | Variable |
| `document_metadata` | Key-value metadata for documents (owner, tags, properties) | Variable |

#### Schema:

**documents table:**
```sql
CREATE TABLE documents (
  id TEXT PRIMARY KEY,
  filename TEXT NOT NULL,
  collection TEXT NOT NULL,
  content TEXT,
  created_at TEXT,
  last_updated TEXT
)
```

**document_metadata table:**
```sql
CREATE TABLE document_metadata (
  document_id TEXT NOT NULL,
  key TEXT NOT NULL,
  value TEXT,
  value_type TEXT NOT NULL,
  PRIMARY KEY (document_id, key),
  FOREIGN KEY (document_id) REFERENCES documents(id)
)
```

#### Usage:
- **Source of truth** for all document records
- Stores file metadata: filename, creation date, collection
- Stores custom metadata: key-value pairs (owner, tags, properties)
- Queried by DocumentService for CRUD operations
- Synced with VectorStore embeddings via Reconciliation service

#### Current Data:
- documents: Contains uploaded document records
- document_metadata: 17 entries of metadata key-value pairs

---

### 3. **VectorstoreService - ChromaDB Vector Database**

**Location**: `PramaIA-VectorstoreService/data/chroma_db/chroma.sqlite3`  
**Type**: ChromaDB (SQLite backend)  
**Purpose**: Vector embeddings for semantic search & RAG operations

#### Key Tables:
| Table | Purpose |
|-------|---------|
| `collections` | Vector collections (1 default) |
| `embeddings` | Vector embeddings with metadata |
| `embeddings_queue` | Async queue for embedding operations |
| `embedding_metadata` | Metadata about embeddings |

#### Usage:
- Semantic search on documents
- RAG (Retrieval-Augmented Generation) queries
- Vector storage for LLM context
- Async embedding pipeline

#### Current Data:
- embeddings: **0 entries** (embeddings not yet populated)
- collections: 1 default collection

---

### 4. **PramaIA-LogService - Centralized Logging**

**Location**: `PramaIA-LogService/logs/` (various log files)  
**Type**: File-based + SQLite (if configured)  
**Purpose**: Aggregated logging from all microservices

#### Usage:
- All services POST logs to LogService API (`http://127.0.0.1:8081/api/logs`)
- Centralized debugging and audit trail
- Per-service log levels (ERROR, INFO, DEBUG, TRACE)

#### Configuration:
- `PDK_LOG_LEVEL` environment variable controls verbosity
- Logs stored in service-specific folders

---

### 5. **PramaIA-PDK - Plugin System (No Direct DB)**

**Type**: Node.js server with database-backed plugin registry  
**Purpose**: Plugin definitions and node schemas

#### Data Storage:
- **plugins/*/nodes.json**: Node schema definitions (JSON files)
- **plugins/*/package.json**: Plugin metadata
- No database - purely file-based

#### Available Plugins:
- `core-input-plugin`: Input nodes
- `core-output-plugin`: Output nodes
- `core-data-plugin`: Data transformation
- `core-llm-plugin`: LLM integration
- `core-rag-plugin`: RAG operations
- `pdf-monitor-plugin`: PDF file monitoring
- `document-semantic-complete-plugin`: Semantic search
- `workflow-scheduler-plugin`: Scheduled workflows

---

### 6. **PramaIA-Reconciliation - State Sync Service**

**Location**: Syncs across all databases  
**Type**: Microservice (no local DB)  
**Purpose**: Data consistency across VectorStore, PramaIAServer, and PDK

#### Responsibilities:
- Verify document consistency between databases.db and documents.db
- Sync VectorStore embeddings with document metadata
- Reconcile workflow execution states
- Audit trail maintenance

#### Health Check Endpoints:
- `GET /health`: Service status
- `POST /api/reconcile`: Trigger manual reconciliation
- `GET /api/sync-status`: View sync state

---

### 7. **PramaIA-Agents - Monitoring Agent (Optional)**

**Location**: `PramaIA-Agents/document-folder-monitor-agent/`  
**Type**: Autonomous agent service  
**Purpose**: File system monitoring and trigger execution

#### Integration:
- Monitors folders specified in configuration
- Generates `file_upload`, `file_delete`, `file_modify` events
- Events trigger workflows via TriggerService
- Logs events to `pdf_monitor_events` table in PramaIAServer

---

## 🔄 Data Flow Between Databases

### Document Upload Flow:
```
1. User uploads file
   ↓
2. PramaIAServer.DocumentService saves file
   ↓
3. Insert into documents.db (VectorstoreService)
   ├─ documents table: filename, collection
   └─ document_metadata table: custom metadata
   ↓
4. Generate embedding
   ↓
5. Insert into chroma.sqlite3
   ├─ embeddings table: vector + metadata
   └─ embeddings_queue: async operations
   ↓
6. Log event to pdf_monitor_events (if file monitoring enabled)
   ↓
7. Reconciliation service verifies consistency
```

### Query Flow:
```
1. User searches documents
   ↓
2. VectorstoreService.search_endpoint()
   ├─ Query chroma.sqlite3 for embeddings (semantic)
   └─ Query documents.db for metadata
   ↓
3. Return ranked results with metadata
```

---

## ⚠️ Critical Notes

### Database Independence
- **PramaIAServer** (`database.db`) and **VectorstoreService** (`documents.db`) are **SEPARATE**
- NO foreign key relationships between them
- Reconciliation service maintains eventual consistency

### VectorStore Embeddings Status
- **chroma.sqlite3** has 0 embeddings currently
- Embeddings must be generated when documents are uploaded
- Reconciliation service can rebuild embeddings from documents.db

### Document Metadata Storage
- **Single source of truth**: `documents.db` (VectorstoreService)
- NOT stored in PramaIAServer database.db
- NOT stored in JSON files (architecture mistake)
- Can be queried via VectorstoreService REST API

### Scalability for Folder Monitoring
With proper indexing on documents.db:
- Can handle **100,000+ documents** per user
- Metadata queries indexed on (document_id, key)
- Collection-based partitioning supported
- VectorStore embeddings scaled via ChromaDB vector indexing

---

## 🔧 Database Maintenance Commands

### Check documents.db:
```bash
sqlite3 PramaIA-VectorstoreService/data/documents.db
> SELECT COUNT(*) FROM documents;
> SELECT document_id, key, value FROM document_metadata LIMIT 10;
```

### Check database.db:
```bash
sqlite3 PramaIAServer/backend/db/database.db
> SELECT COUNT(*) FROM workflows;
> SELECT COUNT(*) FROM pdf_monitor_events;
```

### Check ChromaDB:
```bash
sqlite3 PramaIA-VectorstoreService/data/chroma_db/chroma.sqlite3
> SELECT COUNT(*) FROM embeddings;
> SELECT name FROM collections;
```

### Run Reconciliation:
```bash
POST http://127.0.0.1:8091/api/reconcile
```

---

## 📋 Summary Table

| Service | Database | Location | Purpose | Status |
|---------|----------|----------|---------|--------|
| **PramaIAServer** | database.db | `backend/db/` | Workflows, users, triggers, executions | ✅ Active |
| **VectorstoreService** | documents.db | `data/` | Document metadata (PRIMARY) | ✅ Active |
| **VectorstoreService** | chroma.sqlite3 | `data/chroma_db/` | Vector embeddings | ✅ Active |
| **LogService** | Files | `logs/` | Centralized logging | ✅ Active |
| **PDK** | JSON files | `plugins/*/` | Node schemas | ✅ Active |
| **Reconciliation** | N/A (microservice) | N/A | Cross-DB sync | ✅ Active |

---

## 🚀 Next Steps for Development

1. **Verify Embedding Pipeline**: Ensure documents.db → chroma.sqlite3 sync works
2. **Test Reconciliation**: Run manual sync and verify consistency
3. **Document API Endpoints**: Map REST endpoints to database operations
4. **Performance Testing**: Load test with 10K+ documents
5. **Backup Strategy**: Define backup procedures for all databases
