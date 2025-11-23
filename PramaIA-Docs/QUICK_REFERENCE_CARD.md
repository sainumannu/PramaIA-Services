````markdown
# 🔍 Quick Reference Card - Event Sources System

**Laminated reference for developers**

---

## The Pipeline (One Diagram)

```
┌──────────────┐
│ Event Source │ (plugin.json + emit_event() calls)
└──────┬───────┘
       │ emit_event("event_type", "source", {...})
       ↓
┌──────────────────────┐
│ EventEmitter Service │ (validates + sends)
└──────┬───────────────┘
       │ POST /api/events/process
       ↓
┌─────────────────────────┐
│ TriggerService          │ (finds matches)
│ WHERE event_type = X    │
│ AND source = Y          │
└──────┬──────────────────┘
       │ if matched & conditions OK
       ↓
┌──────────────────────┐
│ WorkflowEngine       │ (executes)
└──────────────────────┘
```

---

## The 3-Minute Explanation

1. **Event Source** = Component that generates events
2. **Event** = Something happened (file_uploaded, timer_fired, etc.)
3. **Trigger** = Rule that says "when X happens, run workflow Y"
4. **Workflow** = Pipeline of processing steps

**Connection**: Event source calls `emit_event()` → backend matches trigger → workflow runs

---

## Creating an Event Source (Checklist)

```
☐ 1. Create directory: PramaIA-PDK/event-sources/my-source/
☐ 2. Create plugin.json with:
     {
       "type": "event-source",
       "id": "my-source",
       "name": "Display Name",
       "eventTypes": [...]
     }
☐ 3. In your service, call:
     await emit_event(
       event_type="...",
       source="my-source",
       data={...}
     )
☐ 4. Restart backend
☐ 5. Verify: curl http://127.0.0.1:8000/api/event-sources/
☐ 6. Create trigger in UI
☐ 7. Test workflow execution
```

---

## emit_event() - The Key Function

```python
from backend.services.event_emitter import emit_event

# Usage
await emit_event(
    event_type="my_event",      # Must be in plugin.json
    source="my-source",         # Must be registered
    data={                       # Must match schema
        "field1": "value1",
        "timestamp": datetime.utcnow().isoformat()
    },
    user_id=current_user.id     # Optional, for audit
)
```

---

## plugin.json - Minimal Valid Example

```json
{
  "type": "event-source",
  "id": "my-timer",
  "name": "My Timer",
  "description": "Fires every minute",
  "version": "1.0.0",
  "eventTypes": [
    {
      "type": "timer_fired",
      "label": "Timer Fired",
      "description": "When timer goes off",
      "schema": {
        "properties": {
          "timestamp": {"type": "string"}
        }
      }
    }
  ]
}
```

---

## Event Structure (What Gets Sent)

```python
{
    "event_type": "file_upload",
    "source": "web-client-upload",
    "data": {
        "filename": "doc.pdf",
        "file_size": 1024,
        "user_id": "user-123"
    },
    "metadata": {
        "source": "web-client-upload",
        "timestamp": "2025-11-19T10:30:00Z",
        "user_id": "user-123"
    }
}
```

---

## Trigger Matching Rules

```
TriggerService receives event and checks:

1. Is there a trigger where:
   event_type = event.event_type AND
   source = event.source

2. If yes, evaluate conditions (if any):
   - filename_pattern: regex match
   - min_size / max_size: file size check
   - metadata_contains: field matching

3. If all pass: Execute workflow
```

---

## Built-in Event Sources

| ID | Event Types | Notes |
|----|-------------|-------|
| system | user_login, workflow_completed | Built-in |
| api-webhook | webhook_received | External HTTP |
| web-client-upload | file_upload | UI uploads |
| pdf-monitor-event-source | pdf_file_added, pdf_file_modified, pdf_file_deleted | File system |

---

## Common Patterns

### Pattern: Emit on Action
```python
# After successful operation
await emit_event(
    event_type="document_processed",
    source="my-service",
    data={"doc_id": "123", "status": "success"}
)
```

### Pattern: Emit on Error
```python
# When something fails
await emit_event(
    event_type="process_failed",
    source="my-service",
    data={"error": str(e), "entity": "123"}
)
```

### Pattern: Batch Emit
```python
# Process multiple items
for item in items:
    await emit_event(
        event_type="item_processed",
        source="batch-processor",
        data={"item_id": item.id}
    )
```

---

## Debugging Checklist

### Event Not Emitted
- [ ] Service imports emit_event
- [ ] emit_event() is called
- [ ] event_type available via PDK API
- [ ] source available via PDK API

### Event Received But No Workflow
- [ ] Trigger exists in DB
- [ ] Trigger is active (active=true)
- [ ] event_type in trigger matches event
- [ ] source in trigger matches event
- [ ] Conditions evaluate to true

### Workflow Didn't Execute
- [ ] Workflow exists (check DB)
- [ ] Workflow is active
- [ ] Target node exists in workflow
- [ ] PDK is running (check port 3001)

### Debug Commands

```bash
# Check if event source registered
curl http://127.0.0.1:8000/api/event-sources/my-source

# Get all event types
curl http://127.0.0.1:8000/api/event-sources/events/all

# Check database for trigger
sqlite3 database.db "SELECT * FROM workflow_triggers WHERE active=1;"

# Check if workflow executed
sqlite3 database.db "SELECT * FROM workflow_executions ORDER BY created_at DESC LIMIT 1;"
```

---

## File Locations

| What | Where |
|------|-------|
| Event sources | `PramaIA-PDK/event-sources/*/plugin.json` |
| Event Sources | `PramaIA-PDK/server/event-source-*.js` |
| Router | `backend/routers/event_sources_router.py` |
| Event endpoint | `backend/routers/event_trigger_system.py` |
| Trigger service | `backend/services/trigger_service.py` |
| Workflow engine | `backend/engine/workflow_engine.py` |
| Upload router | `backend/routers/documents_router.py` |

---

## Required Reading

| Role | Read First | Then Read |
|------|-----------|-----------|
| Developer | QUICK_START | EVENT_SOURCES_EXTENSIBILITY |
| QA | UPLOAD_EVENT_PIPELINE | QUICK_START (debugging) |
| Tech Lead | SESSION_SUMMARY | DOCUMENTATION_ROADMAP |
| Architect | ECOSYSTEM_OVERVIEW | EVENT_SOURCES_EXTENSIBILITY |

---

## Key Insights

1. **Discovery is automatic** - PDK API handles plugin detection
2. **System is extensible** - Just add plugin.json
3. **Pattern is consistent** - All services use emit_event()
4. **UI is dynamic** - Shows available sources automatically
5. **Matching is simple** - (event_type, source) tuple

---

## The Missing Piece (What We're Fixing)

```
BEFORE (broken):
  User uploads file → Saved → Done ❌

AFTER (fixed):
  User uploads file → emit_event() → Trigger matches → Workflow runs ✅
```

**Code change needed**: 
```python
# In documents_router.py
await emit_event(
    event_type="file_upload",
    source="web-client-upload",
    data={...}
)
```

**Effort**: 30 minutes

---

## Success Looks Like

```
1. File uploaded via web UI
2. Backend logs: "Event emitted: file_upload from web-client-upload"
3. Workflow starts executing
4. Check: sqlite3 database.db "SELECT * FROM workflow_executions ORDER BY created_at DESC LIMIT 1;"
5. Result: Execution record found with status="success" or "error"
```

---

## See More

- **Quick Start**: QUICK_START_EVENT_SOURCES.md
- **Full Details**: EVENT_SOURCES_EXTENSIBILITY.md
- **Implementation**: UPLOAD_EVENT_PIPELINE.md
- **Analysis**: SESSION_SUMMARY_EVENT_SOURCES.md

---

**Keep this card nearby while implementing!**

*Last Updated: 19 November 2025*

````
