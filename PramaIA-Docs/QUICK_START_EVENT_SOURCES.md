````markdown
# Quick Start: Event Sources & Custom Event Implementation

**For Developers**: 10-minute primer on creating and using event sources

---

## 30-Second Overview

```
Event Source = Component that generates events
Event = Something happened (file_uploaded, user_login, timer_fired)
Trigger = "When X happens, run workflow Y"
Workflow = Pipeline of processing steps

You create an event source → System discovers it → 
Users create triggers → System runs workflows → Done!
```

---

## The 5-Minute Example: Timer Event Source

### Step 1: Create Plugin Manifest

**File**: `PramaIA-PDK/event-sources/my-timer/plugin.json`

```json
{
  "type": "event-source",
  "id": "my-timer",
  "name": "My Timer",
  "description": "Fires on schedule",
  "version": "1.0.0",
  "eventTypes": [
    {
      "type": "timer_fired",
      "label": "Timer Fired",
      "description": "Every minute, on the minute",
      "schema": {
        "properties": {
          "fired_at": {"type": "string", "format": "date-time"},
          "timer_id": {"type": "string"}
        }
      }
    }
  ]
}
```

### Step 2: Implement Event Emission

**File**: `PramaIA-PDK/event-sources/my-timer/timer.py`

```python
import asyncio
from datetime import datetime
from backend.services.event_emitter import emit_event

async def start_timer():
    while True:
        await asyncio.sleep(60)  # Every minute
        
        await emit_event(
            event_type="timer_fired",
            source="my-timer",
            data={
                "fired_at": datetime.utcnow().isoformat(),
                "timer_id": "default"
            }
        )
```

### Step 3: System Discovers It

On startup:
```
1. Backend starts
2. EventSourceRegistry scans PramaIA-PDK/event-sources/
3. Finds my-timer/plugin.json
4. Validates manifest
5. Registers as available event source
```

### Step 4: User Creates Trigger (UI)

1. Navigate to "Workflow Triggers"
2. Click "New Trigger"
3. Fill:
   - Name: "Daily Report"
   - Event Source: **"My Timer"** ← Auto-discovered!
   - Event Type: **"Timer Fired"** ← Shows automatically!
   - Workflow: "generate-report"
   - Conditions: (optional)
4. Save

### Step 5: Workflow Runs

Every minute:
```
Timer fires → emit_event(type=timer_fired, source=my-timer)
      ↓
Backend receives event
      ↓
TriggerService finds trigger matching (source=my-timer, type=timer_fired)
      ↓
Workflow "generate-report" executes
```

**Total effort: 15 minutes** 🎉

---

## Using emit_event() from Any Service

### Example 1: From Upload Router

```python
# In backend/routers/documents_router.py
from backend.services.event_emitter import emit_event

@router.post("/upload/")
async def upload_file(file, current_user):
    # ... save file ...
    
    await emit_event(
        event_type="file_upload",
        source="web-client-upload",
        data={
            "filename": file.filename,
            "file_size": len(content),
            "user_id": current_user.user_id
        },
        user_id=current_user.user_id
    )
```

### Example 2: From Background Task

```python
# In a scheduled task
from backend.services.event_emitter import emit_event

async def daily_task():
    result = do_work()
    
    await emit_event(
        event_type="daily_task_completed",
        source="background-scheduler",
        data={
            "task": "daily_sync",
            "status": "success",
            "duration_seconds": result.duration
        }
    )
```

### Example 3: From External Integration

```python
# In backend/routers/webhook.py
from backend.services.event_emitter import emit_event

@router.post("/webhooks/stripe")
async def stripe_webhook(payload):
    # Process webhook
    
    await emit_event(
        event_type="payment_received",
        source="stripe-webhook",
        data={
            "payment_id": payload["id"],
            "amount": payload["amount"],
            "customer": payload["customer_id"]
        }
    )
```

---

## Event Source Manifest (plugin.json) - Required Fields

```json
{
  "type": "event-source",              // Required: must be "event-source"
  "id": "kebab-case-id",               // Required: unique identifier
  "name": "Display Name",              // Required: shown in UI
  "description": "What it does",       // Required: brief explanation
  "version": "1.0.0",                  // Required: semantic versioning
  
  "eventTypes": [                      // Required: non-empty array
    {
      "type": "event_type_name",       // Required: identifier
      "label": "Event Label",          // Required: shown in UI
      "description": "...",            // Required: what this event means
      "schema": {                       // Optional but recommended
        "type": "object",
        "properties": {
          "field_name": {"type": "string"},
          "amount": {"type": "number"}
        }
      }
    }
  ],
  
  "configSchema": {},                  // Optional: for admin configuration
  "webhookEndpoint": "/api/my-source", // Optional: if has webhook
  "status": "active"                   // Optional: "active" or "inactive"
}
```

---

## Event Data Structure (What emit_event sends)

```python
# What emit_event(event_type, source, data) creates:
{
    "event_type": "file_upload",
    "source": "web-client-upload",
    "data": {
        "filename": "document.pdf",
        "file_size": 102400,
        "user_id": "user-123"
    },
    "metadata": {
        "source": "web-client-upload",
        "timestamp": "2025-11-19T10:30:00Z",
        "user_id": "user-123",
        "additional_data": {}
    }
}
```

This gets sent to `/api/events/process` which:
1. Finds matching triggers
2. Evaluates conditions
3. Executes workflows

---

## Built-in Event Sources

### 1. System Events
```
"system" event source:
  - user_login
  - workflow_completed
```

### 2. API Webhooks
```
"api-webhook" event source:
  - webhook_received
```

### 3. Web Uploads
```
"web-client-upload" event source:
  - file_upload
```

### 4. File Monitor
```
"pdf-monitor-event-source" event source:
  - pdf_file_added
  - pdf_file_modified
  - pdf_file_deleted
```

---

## Common Patterns

### Pattern 1: Emit on Success

```python
try:
    result = process_document(file)
    
    await emit_event(
        event_type="document_processed",
        source="document-processor",
        data={"document_id": result.id, "status": "success"}
    )
except Exception as e:
    await emit_event(
        event_type="document_failed",
        source="document-processor",
        data={"error": str(e)}
    )
```

### Pattern 2: Emit with User Context

```python
await emit_event(
    event_type="action_performed",
    source="my-system",
    data={"action": "delete", "entity_id": "123"},
    user_id=current_user.user_id  # Audit trail
)
```

### Pattern 3: Batch Events

```python
events = []
for item in items:
    events.append({
        "event_type": "item_processed",
        "source": "batch-processor",
        "data": {"item_id": item.id}
    })

# Emit all
for event in events:
    await emit_event(**event)
```

---

## Debugging

### Check Event Source is Registered

```bash
curl http://127.0.0.1:8000/api/event-sources/my-timer
```

Expected response:
```json
{
  "id": "my-timer",
  "name": "My Timer",
  "eventTypes": [...]
}
```

### Check Event Types Available

```bash
curl http://127.0.0.1:8000/api/event-sources/my-timer/events
```

### Check Trigger Matches

```bash
sqlite3 backend/db/database.db << EOF
SELECT * FROM workflow_triggers 
WHERE event_type='timer_fired' 
AND source='my-timer';
EOF
```

### Check Workflow Executed

```bash
sqlite3 backend/db/database.db << EOF
SELECT id, workflow_id, status, created_at 
FROM workflow_executions 
WHERE trigger_id='trigger-id' 
ORDER BY created_at DESC;
EOF
```

---

## Quick Checklist: New Event Source

- [ ] Created `PramaIA-PDK/event-sources/my-source/`
- [ ] Created `plugin.json` with valid schema
- [ ] Tested `emit_event()` calls
- [ ] Verified via `GET /api/event-sources/`
- [ ] Created trigger via UI
- [ ] Verified workflow executed
- [ ] Documented in README

---

## Common Gotchas

### ❌ Wrong: Hardcoded event type

```python
# BAD - the type must match schema!
await emit_event(
    event_type="random_event",  # ❌ Not registered!
    source="my-timer",
    data={}
)
```

### ✅ Right: Use registered event type

```python
# GOOD - matches plugin.json
await emit_event(
    event_type="timer_fired",  # ✅ Defined in plugin.json
    source="my-timer",
    data={...}
)
```

---

### ❌ Wrong: Wrong source ID

```python
# BAD - mismatch between emit and trigger
await emit_event(
    event_type="timer_fired",
    source="my-Timer",  # ❌ Case mismatch!
    data={}
)
# But trigger uses source="my-timer" → never matches!
```

### ✅ Right: Exact match

```python
# GOOD - must match exactly
await emit_event(
    event_type="timer_fired",
    source="my-timer",  # ✅ Matches trigger
    data={}
)
```

---

### ❌ Wrong: Missing required schema fields

```python
# plugin.json says:
{
  "schema": {
    "properties": {
      "fired_at": {"type": "string", "format": "date-time"},
      "timer_id": {"type": "string"}
    },
    "required": ["fired_at"]  # ← This is required!
  }
}

# But you emit without it:
await emit_event(..., data={"timer_id": "123"})  # ❌ Missing fired_at!
```

### ✅ Right: Include all required fields

```python
await emit_event(
    ...,
    data={
        "fired_at": datetime.utcnow().isoformat(),  # ✅ Included!
        "timer_id": "123"
    }
)
```

---

## See Also

- **Full Architecture**: `EVENT_SOURCES_EXTENSIBILITY.md`
- **Implementation Guide**: `UPLOAD_EVENT_PIPELINE.md`
- **Concepts**: `EVENT_SOURCES_TRIGGERS_WORKFLOWS.md`
- **System Overview**: `ECOSYSTEM_OVERVIEW.md`

---

**TL;DR**: Create plugin.json → System discovers it → emit_event() → Workflow runs 🚀

````
