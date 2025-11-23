````markdown
# Event Sources System - Extensibility & Architecture

**Last Updated**: 19 November 2025  
**Status**: Complete architecture documentation for custom event source development

---

## 📚 Table of Contents

1. [Core Concepts](#core-concepts)
2. [Event Sources Management](#event-sources-management)
3. [Creating Custom Event Sources](#creating-custom-event-sources)
4. [Built-in Event Sources](#built-in-event-sources)
5. [Event Emission Pattern](#event-emission-pattern)
6. [Integration Examples](#integration-examples)
7. [Best Practices](#best-practices)

---

## 1. Core Concepts

### What is an Event Source?

An **Event Source** is a component that:
1. **Monitors** a condition or system state
2. **Detects changes** (events occur)
3. **Emits structured events** to the PramaIA event bus
4. **Triggers workflow automation** via the trigger system

### Event Source vs Trigger vs Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    EVENT SOURCE                              │
│  • Monitors file system, scheduler, API, database, etc.      │
│  • Generates events: "file_upload", "timer_tick", etc.       │
└────────────────────┬────────────────────────────────────────┘
                     │ POST /api/events/process
                     ↓
        ┌────────────────────────────┐
        │      TRIGGER SERVICE       │
        │  Matches event_type+source │
        │   to configured triggers   │
        └────────────┬───────────────┘
                     │ If matched & conditions pass
                     ↓
        ┌────────────────────────────┐
        │    WORKFLOW ENGINE         │
        │  Executes workflow nodes   │
        │  Produces results          │
        └────────────────────────────┘
```

### Event Lifecycle

```
Event Source generates event
          ↓
    {
      "event_type": "file_upload",
      "source": "web-client-upload",
      "data": { "filename": "doc.pdf", "user_id": 7, ... },
      "metadata": { "timestamp": "2025-11-19T10:30:00Z", ... }
    }
          ↓
POST /api/events/process (Backend)
          ↓
TriggerService searches for matching triggers:
  - WHERE event_type == "file_upload"
  - AND source == "web-client-upload"
  - AND conditions match (if any)
          ↓
If trigger found:
  - Executes associated workflow
  - Passes event data to target_node_id
  - Saves execution result
```

---

## 2. Event Sources Management

### PDK Server API Architecture

Event sources are now managed directly by the PDK server through API endpoints:

```python
# Event sources are discovered via PDK server APIs
# No central registry - direct API communication

class PDKEventSourceClient:
    """Client for PDK server event source APIs"""
    
    def __init__(self, pdk_url: str = "http://localhost:3001"):
        self.base_url = pdk_url
    
    async def get_available_sources(self) -> List[dict]:
        """Get all event sources from PDK server"""
        response = await self.client.get(f"{self.base_url}/api/event-sources")
        return response.json()
    
    async def get_event_types_for_source(self, source_id: str) -> List[dict]:
        """Get event types for specific source"""
        response = await self.client.get(f"{self.base_url}/api/event-sources/{source_id}/events")
        return response.json()

# Direct API client
pdk_client = PDKEventSourceClient()
```

### Discovery Mechanism

The PDK server automatically discovers event sources from:

1. **Built-in Sources**: Defined in PDK server configuration
   - System events (user_login, workflow_completed)
   - API webhooks
   - Web client uploads

2. **PDK Plugins**: Directory `PramaIA-PDK/event-sources/`
   - Custom event sources created by developers
   - Plugin format: `plugin.json` with `"type": "event-source"`

3. **Dynamic Discovery**: Real-time via API calls
   - No static configuration needed
   - Sources available immediately after plugin updates

### Registration Process

**Automatic (Plugin-based)**:
```python
# PDK server startup automatically discovers:
# 1. Scans PramaIA-PDK/event-sources/ for plugins
# 2. Loads plugin.json configurations
# 3. Makes sources available via API immediately
# → All sources ready via /api/event-sources
```

**API Access**:
```python
# Get all available event sources
GET http://127.0.0.1:3001/api/event-sources

# Get specific event source details
GET http://127.0.0.1:3001/api/event-sources/{source_id}

# No manual registration needed - plugin-based discovery
```

### PDK Server API Endpoints

```
GET /api/event-sources/
  → Returns all available event sources (from PDK server)

GET /api/event-sources/{source_id}
  → Returns specific event source details

GET /api/event-sources/{source_id}/events
  → Returns event types for specific source

POST /api/event-sources/{source_id}/start
  → Start an event source

POST /api/event-sources/{source_id}/stop
  → Stop an event source

# No registration endpoints - plugin-based discovery
```

---

## 3. Creating Custom Event Sources

### Structure of an Event Source

```
PramaIA-PDK/event-sources/my-event-source/
├── plugin.json              # Manifest file
├── README.md               # Documentation
└── implementation/         # Your code (Python, Node.js, etc.)
    └── ...
```

### Plugin Manifest Format (plugin.json)

```json
{
  "type": "event-source",
  "id": "my-event-source",
  "name": "My Event Source",
  "description": "Description of what this event source does",
  "version": "1.0.0",
  "author": "Your Name",
  "license": "MIT",
  
  "eventTypes": [
    {
      "type": "my_event_type",
      "label": "My Event Type",
      "description": "Fired when X happens",
      "schema": {
        "type": "object",
        "properties": {
          "key1": {"type": "string", "description": "..."},
          "key2": {"type": "number", "description": "..."},
          "timestamp": {"type": "string", "format": "date-time"}
        },
        "required": ["key1", "timestamp"]
      }
    },
    {
      "type": "another_event_type",
      "label": "Another Event",
      "description": "Fired when Y happens",
      "schema": { ... }
    }
  ],
  
  "configSchema": {
    "type": "object",
    "properties": {
      "apiKey": {
        "type": "string",
        "description": "API key for authentication",
        "secret": true
      },
      "pollInterval": {
        "type": "integer",
        "description": "Poll interval in seconds",
        "default": 60
      }
    }
  },
  
  "webhookEndpoint": "/api/events/my-source",
  "status": "active"
}
```

### Plugin Validation

PDK server validates plugin.json files automatically:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | Yes | Unique identifier (kebab-case) |
| `name` | string | Yes | Display name |
| `description` | string | Yes | What this source does |
| `version` | string | Yes | Semantic versioning |
| `eventTypes` | array | Yes | Non-empty list of event types |
| `eventTypes[].type` | string | Yes | Event type identifier |
| `eventTypes[].label` | string | Yes | Display label |
| `eventTypes[].description` | string | Yes | What this event means |
| `eventTypes[].schema` | object | No | JSON Schema for event data |
| `configSchema` | object | No | Configuration schema for admins |
| `webhookEndpoint` | string | No | Optional webhook endpoint |
| `status` | string | No | "active" or "inactive" |

### Example: Timer Event Source

```json
{
  "type": "event-source",
  "id": "scheduler-event-source",
  "name": "Scheduler",
  "description": "Triggers events based on time schedules",
  "version": "1.0.0",
  
  "eventTypes": [
    {
      "type": "timer_tick",
      "label": "Timer Tick",
      "description": "Fired when a scheduled timer fires",
      "schema": {
        "type": "object",
        "properties": {
          "schedule_id": {"type": "string"},
          "cron_expression": {"type": "string"},
          "fired_at": {"type": "string", "format": "date-time"}
        }
      }
    }
  ],
  
  "configSchema": {
    "type": "object",
    "properties": {
      "timezone": {
        "type": "string",
        "default": "UTC"
      },
      "max_concurrent": {
        "type": "integer",
        "default": 10
      }
    }
  },
  
  "webhookEndpoint": null,
  "status": "active"
}
```

### Example: External API Event Source

```json
{
  "type": "event-source",
  "id": "external-api-source",
  "name": "External API",
  "description": "Polls external API and generates events",
  "version": "1.0.0",
  
  "eventTypes": [
    {
      "type": "api_response_received",
      "label": "API Response",
      "description": "Fired when external API responds",
      "schema": {
        "type": "object",
        "properties": {
          "api_url": {"type": "string"},
          "status_code": {"type": "integer"},
          "response_body": {"type": "object"},
          "response_time_ms": {"type": "number"}
        }
      }
    },
    {
      "type": "api_error",
      "label": "API Error",
      "description": "Fired when API call fails",
      "schema": {
        "type": "object",
        "properties": {
          "api_url": {"type": "string"},
          "error_message": {"type": "string"},
          "retry_count": {"type": "integer"}
        }
      }
    }
  ],
  
  "configSchema": {
    "type": "object",
    "properties": {
      "api_base_url": {"type": "string"},
      "api_key": {"type": "string", "secret": true},
      "poll_interval_seconds": {"type": "integer", "default": 300}
    }
  },
  
  "webhookEndpoint": "/api/events/external-api",
  "status": "active"
}
```

---

## 4. Built-in Event Sources

### System Events

```json
{
  "id": "system",
  "name": "Sistema",
  "description": "Internal PramaIA system events",
  
  "eventTypes": [
    {
      "type": "user_login",
      "label": "User Login",
      "description": "When a user logs in",
      "schema": {
        "properties": {
          "userId": {"type": "string"},
          "timestamp": {"type": "string", "format": "date-time"},
          "ipAddress": {"type": "string"}
        }
      }
    },
    {
      "type": "workflow_completed",
      "label": "Workflow Completed",
      "description": "When workflow execution completes",
      "schema": {
        "properties": {
          "workflowId": {"type": "string"},
          "status": {"type": "string", "enum": ["success", "error"]},
          "duration": {"type": "number"},
          "timestamp": {"type": "string", "format": "date-time"}
        }
      }
    }
  ]
}
```

### API Webhook Events

```json
{
  "id": "api-webhook",
  "name": "API Webhook",
  "description": "External HTTP webhooks",
  
  "eventTypes": [
    {
      "type": "webhook_received",
      "label": "Webhook Received",
      "description": "When external webhook is called",
      "schema": {
        "properties": {
          "payload": {"type": "object"},
          "headers": {"type": "object"},
          "method": {"type": "string"},
          "timestamp": {"type": "string", "format": "date-time"}
        }
      }
    }
  ],
  
  "webhookEndpoint": "/api/events/webhook"
}
```

### Web Client Upload Events

```json
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
          "is_public": {"type": "boolean"},
          "timestamp": {"type": "string", "format": "date-time"}
        }
      }
    }
  ]
}
```

### PDF Monitor Events

```json
{
  "id": "pdf-monitor-event-source",
  "name": "PDF Monitor",
  "description": "File system monitoring for PDF files",
  
  "eventTypes": [
    {
      "type": "pdf_file_added",
      "label": "PDF Added",
      "description": "When PDF file is created",
      "schema": {
        "properties": {
          "filename": {"type": "string"},
          "file_path": {"type": "string"},
          "file_size": {"type": "integer"},
          "file_hash": {"type": "string"}
        }
      }
    },
    {
      "type": "pdf_file_modified",
      "label": "PDF Modified",
      "description": "When PDF file is modified"
    },
    {
      "type": "pdf_file_deleted",
      "label": "PDF Deleted",
      "description": "When PDF file is deleted"
    }
  ]
}
```

---

## 5. Event Emission Pattern

### How to Emit Events (From Any Service)

All services should use the **EventEmitter** pattern to emit events to the system:

```python
# Location: backend/services/event_emitter.py

from backend.services.event_emitter import emit_event

# Emit an event
emit_event(
    event_type="file_upload",
    source="web-client-upload",
    data={
        "filename": "document.pdf",
        "file_size": 102400,
        "user_id": current_user.user_id,
        "is_public": True
    },
    user_id=current_user.user_id  # Optional
)
```

### Event Emission Flow

```
Service generates event data
          ↓
Call emit_event(event_type, source, data)
          ↓
EventEmitter constructs EventPayload:
  {
    "event_type": "file_upload",
    "source": "web-client-upload",
    "data": { ... },
    "metadata": {
      "source": "web-client-upload",
      "timestamp": ISO8601,
      "user_id": "...",
      "additional_data": { ... }
    }
  }
          ↓
POST /api/events/process (internal call)
          ↓
TriggerService receives event
          ↓
Finds matching triggers
          ↓
Executes workflows
```

### EmitEvent API

```python
def emit_event(
    event_type: str,
    source: str,
    data: Dict[str, Any],
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Emit an event to the PramaIA event bus.
    
    Args:
        event_type: Type of event (must be registered in event source)
        source: Source ID that generates the event
        data: Event payload (must match schema)
        user_id: User who triggered the event (optional)
        metadata: Additional metadata (optional)
    
    Returns:
        True if event was processed, False if failed
    
    Raises:
        EventEmissionError: If event validation fails
        UnknownEventSourceError: If source not registered
    """
```

### Where to Use emit_event

**Document Upload**:
```python
# PramaIAServer/backend/routers/documents_router.py
async def upload_pdfs_with_visibility(...):
    # ... save file ...
    emit_event(
        event_type="file_upload",
        source="web-client-upload",
        data={
            "filename": file.filename,
            "file_size": len(content),
            "user_id": current_user.user_id,
            "is_public": is_public
        }
    )
```

**File Monitor**:
```python
# PramaIA-Agents/document-folder-monitor-agent/...
def on_file_created(path):
    emit_event(
        event_type="pdf_file_added",
        source="pdf-monitor-event-source",
        data={
            "filename": os.path.basename(path),
            "file_path": str(path),
            "file_size": os.path.getsize(path),
            "file_hash": compute_hash(path)
        }
    )
```

**Webhook**:
```python
# When webhook is received
emit_event(
    event_type="webhook_received",
    source="api-webhook",
    data={
        "payload": webhook_payload,
        "headers": headers,
        "method": "POST"
    }
)
```

---

## 6. Integration Examples

### Example 1: Create a Timer Event Source

**File**: `PramaIA-PDK/event-sources/scheduler-timer/plugin.json`

```json
{
  "type": "event-source",
  "id": "scheduler-timer",
  "name": "Scheduler Timer",
  "description": "Triggers events on schedule (cron-like)",
  "version": "1.0.0",
  
  "eventTypes": [
    {
      "type": "timer_fired",
      "label": "Timer Fired",
      "description": "Fired when scheduled time occurs",
      "schema": {
        "type": "object",
        "properties": {
          "schedule_name": {"type": "string"},
          "fired_at": {"type": "string", "format": "date-time"},
          "next_fire": {"type": "string", "format": "date-time"}
        }
      }
    }
  ],
  
  "configSchema": {
    "type": "object",
    "properties": {
      "cron_expressions": {
        "type": "array",
        "items": {"type": "string"},
        "description": "List of cron expressions"
      }
    }
  }
}
```

**Implementation** (Node.js, Python, etc.):
```python
# scheduler-timer/implementation/scheduler.py
import asyncio
from backend.services.event_emitter import emit_event

class SchedulerTimer:
    def __init__(self, config):
        self.config = config
        self.timers = []
    
    async def start(self):
        for cron_expr in self.config.get('cron_expressions', []):
            task = asyncio.create_task(self._cron_loop(cron_expr))
            self.timers.append(task)
    
    async def _cron_loop(self, cron_expr):
        while True:
            next_fire = calculate_next_fire(cron_expr)
            await asyncio.sleep(next_fire)
            
            emit_event(
                event_type="timer_fired",
                source="scheduler-timer",
                data={
                    "schedule_name": cron_expr,
                    "fired_at": datetime.utcnow().isoformat(),
                    "next_fire": calculate_next_fire(cron_expr)
                }
            )
```

### Example 2: Setup Trigger for Timer Events

**Via UI**:
1. Navigate to "Workflow Triggers"
2. Click "New Trigger"
3. Configure:
   - Name: "Daily Report Generation"
   - Event Source: "scheduler-timer"
   - Event Type: "timer_fired"
   - Workflow: "generate-daily-report"
   - Target Node: "report_generator"
   - Conditions: `{"schedule_name": "0 9 * * *"}` (daily at 9 AM)
4. Save trigger

**Result**: Every day at 9 AM, timer_fired event is emitted → trigger matches → workflow executes

### Example 3: Webhook Integration

**Configuration**:
```python
# In UI, create trigger:
# Event Source: "api-webhook"
# Event Type: "webhook_received"
# Workflow: "process-webhook-data"
```

**External system calls**:
```bash
curl -X POST http://127.0.0.1:8000/api/events/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "order_id": "12345",
      "status": "completed"
    }
  }'
```

**Flow**:
1. Webhook received at `/api/events/webhook`
2. `emit_event()` called with type="webhook_received"
3. TriggerService finds matching trigger
4. Workflow "process-webhook-data" executes
5. Order processing begins

---

## 7. Best Practices

### For Event Source Developers

#### 1. **Event Data Schema**
- Always include `timestamp` in ISO8601 format
- Use consistent field naming (snake_case)
- Document all fields in schema
- Make schema backward compatible

```json
{
  "eventTypes": [
    {
      "schema": {
        "properties": {
          "id": {"type": "string", "description": "Unique event ID"},
          "timestamp": {"type": "string", "format": "date-time"},
          "source_id": {"type": "string"},
          "payload": {"type": "object"}
        },
        "required": ["id", "timestamp"]
      }
    }
  ]
}
```

#### 2. **Event Type Naming**
- Use descriptive names: `file_uploaded`, `process_failed`
- Use past tense: something **happened**
- Use snake_case: `user_account_created`

#### 3. **Error Handling**
- Implement retry logic for transient failures
- Add exponential backoff
- Log all failures
- Buffer events locally if backend is down

```python
async def emit_with_retry(event, max_retries=3):
    for attempt in range(max_retries):
        try:
            emit_event(event_type=event['type'], ...)
            return True
        except ConnectionError:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            logger.error(f"Event emission failed: {e}")
            return False
```

#### 4. **Performance**
- Emit events asynchronously
- Batch multiple events if possible
- Don't block main application flow

#### 5. **Documentation**
- Document all event types in README
- Include example payloads
- Explain configuration options
- Provide sample trigger configuration

### For System Integrators

#### 1. **PDK API Inspection**
```bash
# Check available event sources
curl http://127.0.0.1:3001/api/event-sources/

# Check event types for specific source
curl http://127.0.0.1:3001/api/event-sources/pdf-monitor-event-source/events

# Get all event sources for UI dropdowns
curl http://127.0.0.1:3001/api/event-sources
```

#### 2. **Trigger Configuration**
- Map event_type + source to workflow
- Use conditions for fine-grained filtering
- Test triggers before activation
- Monitor execution results

#### 3. **Monitoring**
```python
# Query workflow executions for debugging
SELECT * FROM workflow_executions 
WHERE trigger_id = 'trigger-123'
ORDER BY created_at DESC
LIMIT 10;
```

---

## 🎯 Complete Workflow Example

### Scenario: Invoice Processing Automation

#### Step 1: Create Event Source

**File**: `PramaIA-PDK/event-sources/invoice-parser/plugin.json`
```json
{
  "type": "event-source",
  "id": "invoice-parser",
  "name": "Invoice Parser",
  "eventTypes": [
    {
      "type": "invoice_extracted",
      "label": "Invoice Extracted",
      "schema": {
        "properties": {
          "invoice_id": {"type": "string"},
          "amount": {"type": "number"},
          "vendor": {"type": "string"},
          "date": {"type": "string", "format": "date"}
        }
      }
    }
  ]
}
```

#### Step 2: Available via PDK API

On startup, PDK server discovers `invoice-parser` plugin and makes it available via API.

#### Step 3: Create Trigger (UI)

```
Name: "Process Large Invoices"
Event Source: "invoice-parser"
Event Type: "invoice_extracted"
Workflow: "validate-and-approve-invoice"
Target Node: "invoice_input"
Conditions: { "amount": ">1000" }
Active: true
```

#### Step 4: Implementation Emits Event

```python
# Some PDF parsing service
invoice_data = parse_pdf("invoice.pdf")

emit_event(
    event_type="invoice_extracted",
    source="invoice-parser",
    data={
        "invoice_id": "INV-2025-001",
        "amount": 2500,
        "vendor": "Acme Corp",
        "date": "2025-11-19"
    }
)
```

#### Step 5: Pipeline Executes

1. Event sent to backend
2. TriggerService finds trigger
3. Condition matched (2500 > 1000)
4. Workflow "validate-and-approve-invoice" executes
5. Data flows to invoice_input node
6. Workflow processes invoice (validation, approval, payment)
7. Result saved

---

## 📋 Checklist: Creating Custom Event Source

- [ ] Create `PramaIA-PDK/event-sources/my-source/` directory
- [ ] Create `plugin.json` manifest with valid schema
- [ ] Define all event types with descriptions
- [ ] Document event data schema
- [ ] Create README.md
- [ ] Implement event emission logic
- [ ] Test with `emit_event()`
- [ ] Verify PDK server discovers source
- [ ] Create sample trigger in UI
- [ ] Test end-to-end workflow execution
- [ ] Document for other developers

---

## 🔗 Related Documentation

- [EVENT_SOURCES_TRIGGERS_WORKFLOWS.md](./EVENT_SOURCES_TRIGGERS_WORKFLOWS.md) - Core concepts
- [ECOSYSTEM_OVERVIEW.md](./ECOSYSTEM_OVERVIEW.md) - System architecture
- [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) - Node & plugin development

---

**Questions?** Check the PDK Event Sources implementation in `PramaIA-PDK/server/event-source-routes.js` and `PramaIA-PDK/server/event-source-manager.js`.

````
