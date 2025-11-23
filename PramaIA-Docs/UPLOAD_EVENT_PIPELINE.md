````markdown
# Upload → Event → Trigger → Workflow Pipeline

**Implementation Guide**: Connecting Web File Upload to Event-Driven Automation

**Last Updated**: 19 November 2025

---

## 📚 Quick Navigation

| Section | Purpose |
|---------|---------|
| [Overview](#overview) | Visual flow of the pipeline |
| [Architecture](#architecture) | System components and connections |
| [Current State](#current-state) | What exists vs what's missing |
| [Implementation Plan](#implementation-plan) | Step-by-step to complete the pipeline |
| [Code Changes](#code-changes) | Specific code modifications needed |
| [Testing](#testing) | How to verify the pipeline works |

---

## Overview

### The Pipeline Status

```
User uploads file via web UI
        ↓
File saved to backend
        ↓ ✅ IMPLEMENTED
        ↓
Event generated and sent to trigger system
        ↓ ✅ IMPLEMENTED & WORKING
        ↓
Trigger matches event type + source
        ↓ ⚠️ PARTIALLY WORKING (needs debugging)
        ↓
Workflow executes
        ↓ ⏳ PENDING (blocked by trigger matching)
        ↓
Results saved and returned
```

### Complete Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  Web Browser (React UI)                      │
│         POST /documents/upload-with-visibility/              │
│         (multipart/form-data)                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│            PramaIAServer Backend (FastAPI)                   │
│                                                              │
│   documents_router.py::upload_pdfs_with_visibility()         │
│        ↓                                                     │
│   document_service.process_uploaded_file()                   │
│        ├─ Save file to disk                                 │
│        ├─ Save metadata                                     │
│        └─ emit_event()  ← ⚠️ THIS IS NEW                   │
│        ↓                                                     │
│   EventEmitter (new service)                                │
│        ├─ Validate event structure                          │
│        ├─ POST /api/events/process (internal)               │
│        └─ Handle errors + retries                           │
│        ↓                                                     │
│   TriggerService::process_event()                           │
│        ├─ Find matching triggers                            │
│        │  (WHERE event_type=X AND source=Y)                 │
│        ├─ Evaluate conditions                               │
│        └─ Execute workflows                                 │
│        ↓                                                     │
│   WorkflowEngine::execute()                                 │
│        ├─ DAG validation                                    │
│        ├─ Topological sort of nodes                         │
│        ├─ Execute each node via PDK                         │
│        └─ Save execution results                            │
│        ↓                                                     │
│   Response to frontend                                      │
│        {                                                    │
│          "message": "File uploaded & processed",            │
│          "workflows_triggered": 1,                          │
│          "execution_id": "exec-123"                         │
│        }                                                    │
└─────────────────────────────────────────────────────────────┘
                       ↓
         ┌─────────────────────────────┐
         │   PDK Server (port 3001)    │
         │  Executes workflow nodes    │
         └─────────────────────────────┘
```

---

## Architecture

### Components Involved

#### 1. **Event Source: "web-client-upload"**

**Definition** (via PDK API):
```python
{
    "id": "web-client-upload",
    "name": "Web Client Upload",
    "description": "File uploads from web interface",
    "eventTypes": [
        {
            "type": "file_upload",
            "label": "File Uploaded",
            "description": "When user uploads file via web UI",
            "schema": {
                "properties": {
                    "filename": {"type": "string"},
                    "file_size": {"type": "integer"},
                    "content_type": {"type": "string"},
                    "user_id": {"type": "string"},
                    "is_public": {"type": "boolean"}
                }
            }
        }
    ]
}
```

#### 2. **Event Emitter Service**

**Purpose**: Centralized service to emit events from any part of the system

```python
# backend/services/event_emitter.py

def emit_event(
    event_type: str,
    source: str,
    data: Dict[str, Any],
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """Emit event to PramaIA event bus"""
```

#### 3. **Document Router Update**

**File**: `backend/routers/documents_router.py::upload_pdfs_with_visibility()`

Currently:
```python
async def upload_pdfs_with_visibility(...):
    for file in files:
        await document_service.process_uploaded_file(...)
    # ❌ NO EVENT EMISSION
```

Should become:
```python
async def upload_pdfs_with_visibility(...):
    for file in files:
        await document_service.process_uploaded_file(...)
        # ✅ EMIT EVENT
        emit_event(
            event_type="file_upload",
            source="web-client-upload",
            data={...}
        )
```

#### 4. **Trigger Configuration (UI)**

Users can now create triggers:
```
Event Source: "web-client-upload"
Event Type: "file_upload"
Workflow: "process-uploaded-pdf"
Conditions: { "filename_pattern": "*.pdf", "max_size": 10485760 }
```

#### 5. **Trigger Matching & Execution**

TriggerService automatically:
1. Receives event from /api/events/process
2. Finds trigger where (event_type="file_upload" AND source="web-client-upload")
3. Evaluates conditions (filename matches, size OK)
4. Executes workflow "process-uploaded-pdf"

---

## Current State

### What Already Exists ✅

| Component | Status | Location |
|-----------|--------|----------|
| Event Sources | ✅ Implemented | `PramaIA-PDK/server/event-source-*.js` |
| Event Trigger System | ✅ Implemented | `backend/routers/event_trigger_system.py` |
| TriggerService | ✅ Implemented | `backend/services/trigger_service.py` |
| WorkflowEngine | ✅ Implemented | `backend/engine/workflow_engine.py` |
| Document Upload Router | ✅ Implemented | `backend/routers/documents_router.py` |
| UI Trigger Creator | ✅ Implemented | `frontend/components/workflow/TriggerFormModal.jsx` |
| /api/event-sources/* API | ✅ Implemented | `backend/routers/event_sources_router.py` |
| /api/events/process endpoint | ✅ Implemented | `backend/routers/event_trigger_system.py` |

### What's Implemented ✅

| Component | Status | Implementation | Notes |
|-----------|--------|----------------|-------|
| EventEmitter service | ✅ Implemented | `backend/services/event_emitter.py` | Working, events logged to database |
| Web-upload event source registration | ✅ Working | Built-in source registered | Available in UI trigger creation |
| Upload → emit_event() call | ✅ Implemented | Both upload endpoints | Events emitted and logged |

### What's Partially Working ⚠️

| Component | Status | Issue | Next Steps |
|-----------|--------|-------|------------|
| Trigger matching | ⚠️ Events emitted but triggers not matching | Need to debug trigger conditions/database | Check trigger configuration and logs |
| Workflow execution | ⏳ Blocked | Waiting for trigger matching fix | Will work once triggers match |

### The Gap

```
File Upload:
  Step 1: ✅ POST /documents/upload-with-visibility/
  Step 2: ✅ Save file + metadata
  Step 3: ❌ MISSING: emit_event("file_upload", "web-client-upload", {...})
  Step 4: ❌ BLOCKED: Never reaches TriggerService
  Step 5: ❌ BLOCKED: Workflow never executes
```

---

## Debugging Guide

### Current Status Verification

**Check EventEmitter is working**:
```bash
# Verify events are being logged
python -c "
import sqlite3
conn = sqlite3.connect('PramaIAServer/backend/db/database.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM event_logs')
print(f'Event logs: {cursor.fetchone()[0]}')
conn.close()
"
```

**Expected output**: Should show increasing number of events after uploads

**Check recent events**:
```python
# Recent file upload events
import sqlite3
conn = sqlite3.connect('PramaIAServer/backend/db/database.db')
cursor = conn.cursor()
cursor.execute("""
    SELECT event_type, source, triggers_matched, workflows_executed 
    FROM event_logs 
    WHERE event_type='file_upload' 
    ORDER BY id DESC LIMIT 5
""")
for row in cursor.fetchall():
    print(f"Event: {row[0]} from {row[1]}, triggers: {row[2]}, workflows: {row[3]}")
conn.close()
```

### Troubleshooting Trigger Matching

**If triggers_matched = 0**:

1. **Check trigger configuration**:
```sql
SELECT id, name, event_type, source, active, conditions 
FROM workflow_triggers 
WHERE active=1;
```

2. **Verify event data matches trigger conditions**:
```python
# Check last emitted event structure
import sqlite3, json
conn = sqlite3.connect('PramaIAServer/backend/db/database.db')
cursor = conn.cursor()
cursor.execute("""SELECT event_data FROM event_logs 
                  WHERE event_type='file_upload' 
                  ORDER BY id DESC LIMIT 1""")
result = cursor.fetchone()
if result:
    print(json.dumps(json.loads(result[0]), indent=2))
conn.close()
```

3. **Test trigger manually**:
```bash
curl -X POST http://127.0.0.1:8000/api/events/process \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "file_upload",
    "data": {"filename": "test.pdf", "file_size": 1024},
    "metadata": {
      "source": "web-client-upload",
      "timestamp": "2025-11-20T10:00:00",
      "user_id": "1"
    }
  }'
```

### Phase 2: Register Web-Client-Upload Event Source

**Location**: `PramaIA-PDK/server/event-source-upload.js` (PDK-based event source)

Verify it's in `_load_built_in_sources()`:
```python
{
    "id": "web-client-upload",
    "name": "Web Client Upload",
    "description": "File uploads from web interface",
    "version": "1.0.0",
    "type": "built-in",
    "eventTypes": [
        {
            "type": "file_upload",
            "label": "File Uploaded",
            "description": "When user uploads file via web UI",
            "schema": {
                "properties": {
                    "filename": {"type": "string"},
                    "file_size": {"type": "integer"},
                    "content_type": {"type": "string"},
                    "user_id": {"type": "string"},
                    "is_public": {"type": "boolean"}
                }
            }
        }
    ],
    "webhookEndpoint": None,
    "status": "active"
}
```

**Verification**:
```bash
# After restart, check PDK API
curl http://127.0.0.1:8000/api/event-sources/ | grep -A 5 '"id":"web-client-upload"'
```

### Phase 3: Update Document Upload Router

**File**: `backend/routers/documents_router.py`

Add at the top:
```python
from backend.services.event_emitter import emit_event
```

In `upload_pdfs_with_visibility()`, after `document_service.process_uploaded_file()`:
```python
# Emit event for workflow triggering
emit_event(
    event_type="file_upload",
    source="web-client-upload",
    data={
        "filename": file.filename,
        "file_size": len(content),
        "content_type": file.content_type,
        "user_id": user_id,
        "is_public": is_public
    },
    user_id=user_id
)
```

### Phase 4: Test the Pipeline

**Create a Test Trigger via API or UI**:
```bash
POST /api/workflows/triggers/create
{
    "name": "Test Upload Trigger",
    "event_type": "file_upload",
    "source": "web-client-upload",
    "workflow_id": "simple-test-workflow",
    "target_node_id": "input_node",
    "conditions": { "filename_pattern": ".*" },
    "active": true
}
```

**Upload a File**:
```bash
curl -X POST http://127.0.0.1:8000/api/documents/upload-with-visibility/ \
  -F "files=@test.pdf" \
  -F "is_public=false" \
  -H "Authorization: Bearer TOKEN"
```

**Verify Workflow Executed**:
```bash
# Check workflow_executions table
sqlite3 PramaIAServer/backend/db/database.db \
  "SELECT * FROM workflow_executions WHERE trigger_id='trigger-id' ORDER BY created_at DESC LIMIT 1;"
```

---

## Code Changes

### Summary of Files to Modify/Create

```
CREATE:
  └─ PramaIAServer/backend/services/event_emitter.py (new)

MODIFY:
  ├─ PramaIAServer/backend/routers/documents_router.py
  │   └─ Add emit_event() call in upload_pdfs_with_visibility()
  │
  ├─ PramaIAServer/backend/routers/documents_router.py (verify)
  │   └─ Ensure web-client-upload in built-in sources
  │
  └─ PramaIAServer/backend/main.py (verify)
      └─ Ensure event_trigger_router is included
```

### File 1: Create event_emitter.py

**Path**: `PramaIAServer/backend/services/event_emitter.py`

[See above Phase 1 section]

### File 2: Modify documents_router.py

**Location**: `backend/routers/documents_router.py`

**Add import**:
```python
from backend.services.event_emitter import emit_event
```

**Modify function**:
```python
@router.post("/upload-with-visibility/")
async def upload_pdfs_with_visibility(
    files: List[UploadFile] = File(...),
    is_public: bool = Form(False),
    current_user: UserInToken = Depends(get_current_user)
):
    # ... existing code ...
    user_id = current_user.user_id
    
    for file in files:
        content = await file.read()
        await document_service.process_uploaded_file(
            content, 
            file.filename, 
            user_id, 
            is_public
        )
        
        # ✅ EMIT EVENT
        success = await emit_event(
            event_type="file_upload",
            source="web-client-upload",
            data={
                "filename": file.filename,
                "file_size": len(content),
                "content_type": file.content_type,
                "user_id": user_id,
                "is_public": is_public
            },
            user_id=user_id
        )
        
        if not success:
            logger.warning(
                f"Failed to emit event for {file.filename}, "
                f"but file was uploaded successfully"
            )
    
    return {"message": f"{len(files)} file(s) uploaded successfully", ...}
```

---

## Testing

### Unit Test: EventEmitter

**File**: `tests/test_event_emitter.py`

```python
import pytest
from backend.services.event_emitter import emit_event

@pytest.mark.asyncio
async def test_emit_event_success():
    """Test emitting a valid event"""
    result = await emit_event(
        event_type="file_upload",
        source="web-client-upload",
        data={"filename": "test.pdf", "file_size": 1024},
        user_id="test-user"
    )
    assert result is True

@pytest.mark.asyncio
async def test_emit_event_missing_source():
    """Test emitting event with missing source"""
    result = await emit_event(
        event_type="file_upload",
        source="",
        data={}
    )
    assert result is False

@pytest.mark.asyncio
async def test_emit_event_unknown_source():
    """Test emitting event from unknown source"""
    result = await emit_event(
        event_type="file_upload",
        source="unknown-source",
        data={}
    )
    assert result is False
```

### Integration Test: Upload → Event → Trigger → Workflow

**File**: `tests/test_upload_pipeline.py`

```python
import pytest
from httpx import AsyncClient
from pathlib import Path

@pytest.mark.asyncio
async def test_upload_triggers_workflow():
    """Test that file upload emits event and triggers workflow"""
    
    # Setup: Create a simple test workflow
    workflow = {
        "name": "test-upload-pipeline",
        "nodes": [{
            "node_id": "input",
            "node_type": "input",
            "outputs": [{"port_name": "data", "type": "file"}]
        }],
        "connections": []
    }
    # ... create workflow ...
    
    # Setup: Create trigger for file_upload
    trigger = {
        "name": "test-trigger",
        "event_type": "file_upload",
        "source": "web-client-upload",
        "workflow_id": workflow["id"],
        "target_node_id": "input",
        "conditions": {"filename_pattern": ".*"},
        "active": True
    }
    # ... create trigger ...
    
    # Test: Upload file
    client = AsyncClient(app=app)
    
    with open("test.pdf", "rb") as f:
        response = await client.post(
            "/api/documents/upload-with-visibility/",
            files={"files": ("test.pdf", f)},
            data={"is_public": False},
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 200
    
    # Verify: Check workflow was executed
    db_session = SessionLocal()
    execution = db_session.query(WorkflowExecution).filter(
        WorkflowExecution.trigger_id == trigger["id"]
    ).first()
    
    assert execution is not None
    assert execution.status == "completed"
```

### E2E Test: Manual Verification

```bash
# 1. Start backend
cd PramaIAServer
python -m uvicorn backend.main:app --reload --port 8000

# 2. Check web-client-upload event source is registered
curl http://127.0.0.1:8000/api/event-sources/web-client-upload

# 3. Create a trigger via UI or API
# (See UI: Workflow Triggers → New Trigger)

# 4. Upload a file
curl -X POST http://127.0.0.1:8000/api/documents/upload-with-visibility/ \
  -F "files=@test.pdf" \
  -F "is_public=false" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 5. Check workflow_executions
sqlite3 PramaIAServer/backend/db/database.db << EOF
SELECT id, workflow_id, status, created_at 
FROM workflow_executions 
ORDER BY created_at DESC 
LIMIT 1;
EOF

# 6. Verify result
# Should see 1 execution for your workflow
```

---

## Troubleshooting

### Event Not Emitted

**Symptoms**: File uploads but no workflow executes

**Debug Steps**:
```python
# 1. Check import works
python -c "from backend.services.event_emitter import emit_event; print('OK')"

# 2. Check event source registered
curl http://127.0.0.1:8000/api/event-sources/web-client-upload

# 3. Check logs
# Look for: "Event emitted: file_upload from web-client-upload"
```

### Trigger Not Matching

**Symptoms**: Event emitted but workflow doesn't execute

**Debug Steps**:
```bash
# 1. Check trigger is active
sqlite3 PramaIAServer/backend/db/database.db \
  "SELECT * FROM workflow_triggers WHERE active=1;"

# 2. Verify event_type and source match
# Event: event_type="file_upload", source="web-client-upload"
# Trigger: event_type="file_upload", source="web-client-upload"

# 3. Check conditions
sqlite3 PramaIAServer/backend/db/database.db \
  "SELECT conditions FROM workflow_triggers WHERE id='trigger-id';"

# 4. Check TriggerService logs
```

### Workflow Not Executing

**Symptoms**: Trigger matches but workflow doesn't run

**Debug Steps**:
```bash
# 1. Check workflow exists
sqlite3 PramaIAServer/backend/db/database.db \
  "SELECT * FROM workflows WHERE id='workflow-id';"

# 2. Check WorkflowEngine logs
# Look for: "Executing workflow..."

# 3. Check PDK is running
curl http://127.0.0.1:3001/health

# 4. Check workflow nodes are valid
curl http://127.0.0.1:3001/api/nodes
```

---

## Summary

### Before Implementation
```
Upload file → Saved to disk → Done ❌ (Pipeline incomplete)
```

### After Implementation
```
Upload file 
  → Saved to disk 
  → emit_event() ✅ 
  → TriggerService matches 
  → Workflow executes 
  → Results saved ✅ (Pipeline complete!)
```

---

## Next Steps

1. ✅ Understand the architecture
2. 🚀 Implement EventEmitter service
3. 🚀 Update documents_router.py
4. 🚀 Test end-to-end
5. 📚 Document for team

---

**Questions?** See `EVENT_SOURCES_EXTENSIBILITY.md` for deeper dive into event source architecture.

````
