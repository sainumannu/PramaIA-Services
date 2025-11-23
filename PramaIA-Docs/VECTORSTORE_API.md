# VectorstoreService API Reference

Base URL: `http://localhost:8090`

## Health & Status

| Method | Endpoint | Response | Description |
|--------|----------|----------|-------------|
| GET | `/health` | `{"status": "ok"}` | Service health check |
| GET | `/health/dependencies` | `{"chromadb": "ok", "sqlite": "ok"}` | Dependencies status |
| GET | `/status` | Service status | Service status |
| GET | `/service-status` | Service status | Service status |

## Documents

| Method | Endpoint | Params | Response | Description |
|--------|----------|--------|----------|-------------|
| GET | `/documents/` | `limit=50, offset=0` | `{"documents": [...], "total": N, "returned": N}` | List documents with pagination |
| GET | `/documents/list` | - | `{"documents": ["id1", "id2"], "total": N}` | List document IDs only |
| GET | `/documents/count/today` | - | `{"count": N, "date": "YYYY-MM-DD", "message": "..."}` | Count documents created today |
| GET | `/documents/{id}` | - | Document object | Get specific document |
| POST | `/documents/` | Document object | `{"id": "...", "message": "..."}` | Create document |
| DELETE | `/documents/{id}` | - | `{"message": "deleted"}` | Delete document |
| POST | `/documents/recalculate-stats` | - | Stats update | Recalculate document statistics |

## Collections

| Method | Endpoint | Params | Response | Description |
|--------|----------|--------|----------|-------------|
| GET | `/collections/` | - | `{"collections": [{"name": "...", "document_count": N}], "total": N}` | List collections with counts |
| GET | `/vectorstore/collections` | - | Same as above | Alternative endpoint |

## Vectorstore

| Method | Endpoint | Params | Response | Description |
|--------|----------|--------|----------|-------------|
| GET | `/vectorstore/` | - | `{"status": "ok", "documents_count": N, "collections_count": N}` | Vectorstore stats |
| GET | `/vectorstore/documents` | `collection=name` | `{"documents": [...], "total": N}` | List vectorstore documents, optional filter by collection |
| GET | `/vectorstore/document/{id}` | - | Document object | Get specific document from vectorstore |

## Query

| Method | Endpoint | Body | Response | Description |
|--------|----------|------|----------|-------------|
| POST | `/documents/{collection}/query` | `{"query_text": "...", "limit": 5}` | `{"matches": [...], "total": N}` | Semantic search in collection |
| POST | `/search` | Query object | Search results | Alternative search endpoint |

## Database Management

| Method | Endpoint | Response | Description |
|--------|----------|----------|-------------|
| GET | `/documents/status` | Document status | Documents management status |
| GET | `/documents/list` | Document list | Management document list |
| POST | `/documents/backup` | Backup result | Backup documents |
| POST | `/documents/reset` | Reset result | Reset documents |
| POST | `/reset` | Reset result | Reset all data |
| POST | `/reset/{type}` | Reset result | Reset specific type |
| GET | `/vectorstore/status` | Vectorstore status | Vectorstore management status |
| GET | `/vectorstore/documents` | Document list | Vectorstore documents for management |
| POST | `/vectorstore/backup` | Backup result | Backup vectorstore |
| POST | `/vectorstore/reset` | Reset result | Reset vectorstore |

## Statistics

| Method | Endpoint | Response | Description |
|--------|----------|----------|-------------|
| GET | `/stats/` | System stats | General statistics |
| GET | `/stats/processing` | Processing stats | Processing statistics |

## Settings

| Method | Endpoint | Body | Response | Description |
|--------|----------|------|----------|-------------|
| GET | `/settings/` | - | Current settings | Get settings |
| POST | `/settings/` | Settings object | Updated settings | Update settings |
| GET | `/settings/status` | - | Settings status | Settings status |

## File Hashes

| Method | Endpoint | Body | Response | Description |
|--------|----------|------|----------|-------------|
| POST | `/check-duplicate` | `{"file_hash": "...", "filename": "..."}` | `{"is_duplicate": boolean}` | Check if file is duplicate |
| POST | `/save` | Hash record | Save result | Save file hash record |
| GET | `/list` | - | `[{"file_hash": "...", "filename": "..."}]` | List hash records |
| DELETE | `/{file_hash}` | - | Delete result | Delete hash record |

## API Gateway (Legacy Compatibility)

| Method | Endpoint | Response | Description |
|--------|----------|----------|-------------|
| GET | `/api/database-management/vectorstore/documents` | Document list | Gateway for frontend |
| GET | `/api/database-management/documents/status` | Status | Gateway status |
| GET | `/api/database-management/vectorstore/status` | Status | Gateway vectorstore status |
| POST | `/api/database-management/vectorstore/documents` | Create result | Gateway create document |
| GET | `/api/database-management/vectorstore/statistics` | Stats | Gateway statistics |
| GET | `/api/database-management/vectorstore/health` | Health | Gateway health |
| GET | `/api/database-management/vectorstore/dependencies` | Dependencies | Gateway dependencies |
| GET | `/api/database-management/vectorstore/settings/status` | Settings | Gateway settings |

## Database Admin

| Method | Endpoint | Response | Description |
|--------|----------|----------|-------------|
| GET | `/api/v1/stats` | Database stats | Database statistics |
| POST | `/api/v1/backup` | Backup result | Create database backup |
| GET | `/api/v1/backup/latest` | Backup info | Latest backup info |
| POST | `/api/v1/optimize` | Optimize result | Optimize database |

## Common Response Formats

### Document Object
```json
{
  "id": "string",
  "content": "string", 
  "collection": "string",
  "metadata": {},
  "created_at": "timestamp"
}
```

### Query Response
```json
{
  "matches": [
    {
      "id": "string",
      "document": "string",
      "similarity_score": 0.85,
      "metadata": {}
    }
  ],
  "total": 3,
  "collection": "collection_name"
}
```

### Error Response
```json
{
  "detail": "Error message"
}
```