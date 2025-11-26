# Chat Query Trigger & Event Source Design

## Overview
This document specifies the new `chat_query` trigger type and event source that will enable PramaIA's chat system to use the unified trigger-based workflow architecture instead of direct RAG engine calls.

---

## 1. Trigger Definition

### Trigger Type: `chat_query`

**Description**: Fires when a user submits a question in the chat interface

**Event Source Type**: `chat`

**Payload Structure**:
```json
{
  "event_type": "chat_query",
  "timestamp": "2025-11-24T21:12:00.000Z",
  "user_id": 1,
  "username": "user@example.com",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "question": "Mi puoi dire quando sono stati creati i documenti?",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": 1,
    "message_id": "msg_12345",
    "mode": "rag",
    "model": "gpt-4o",
    "system_prompt": null,
    "provider": "openai"
  }
}
```

---

## 2. Trigger Conditions & Matching

### Default Trigger Configuration
```json
{
  "name": "Chat Query Analyzer Trigger",
  "event_type": "chat_query",
  "description": "Routes all chat queries to the Query Analyzer workflow",
  "is_active": true,
  "conditions": [],
  "linked_workflow_id": "workflow_chat_query_analyzer",
  "priority": 100,
  "execution_mode": "synchronous",
  "timeout_seconds": 30
}
```

### Condition Examples (Optional)
Users can create additional triggers with conditions like:

```json
{
  "conditions": [
    {
      "field": "data.mode",
      "operator": "equals",
      "value": "rag"
    }
  ]
}
```

Or:
```json
{
  "conditions": [
    {
      "field": "user_id",
      "operator": "in_group",
      "value": ["admin", "power_users"]
    }
  ]
}
```

---

## 3. Event Source Implementation

### EventSource Class: `ChatEventSource`

**Location**: `backend/services/event_sources/chat_event_source.py`

```python
class ChatEventSource(BaseEventSource):
    """
    Event source that detects and fires chat_query events
    when users submit questions in the chat interface
    """
    
    name = "chat"
    description = "Chat query events from user questions"
    event_types = ["chat_query"]
    
    async def emit_chat_query_event(self, 
        user_id: int,
        username: str,
        session_id: str,
        question: str,
        message_id: str,
        mode: str = "rag",
        model: str = "gpt-4o",
        system_prompt: Optional[str] = None,
        provider: str = "openai"
    ) -> Dict[str, Any]:
        """
        Emit a chat_query event and wait for workflow execution
        
        Returns:
            Workflow execution result or timeout error
        """
        
        event_payload = {
            "event_type": "chat_query",
            "user_id": user_id,
            "username": username,
            "session_id": session_id,
            "data": {
                "question": question,
                "session_id": session_id,
                "user_id": user_id,
                "message_id": message_id,
                "mode": mode,
                "model": model,
                "system_prompt": system_prompt,
                "provider": provider
            }
        }
        
        # Fire event and get workflow result
        result = await self.trigger_service.fire_and_wait(
            event_type="chat_query",
            payload=event_payload,
            timeout_seconds=30
        )
        
        return result
```

---

## 4. Integration with TriggerService

### Modified TriggerService Methods

```python
class TriggerService:
    
    async def fire_and_wait(self, 
        event_type: str,
        payload: Dict[str, Any],
        timeout_seconds: int = 30
    ) -> Dict[str, Any]:
        """
        Fire an event, execute matching triggers' workflows,
        and wait for the result (synchronous mode)
        
        Args:
            event_type: Type of event to fire
            payload: Event payload
            timeout_seconds: Max time to wait for workflow completion
            
        Returns:
            Workflow execution result
            
        Raises:
            TimeoutError: If workflow doesn't complete in time
            WorkflowExecutionError: If workflow fails
        """
        
        # Find all active triggers matching this event
        triggers = self.find_matching_triggers(event_type, payload)
        
        if not triggers:
            logger.warning(f"No triggers found for event_type: {event_type}")
            return {"status": "no_triggers", "data": None}
        
        # Execute linked workflow (for chat_query, should be only one)
        results = []
        for trigger in triggers:
            workflow_id = trigger.linked_workflow_id
            
            # Execute workflow with event payload as input
            result = await self.workflow_engine.execute(
                workflow_id=workflow_id,
                inputs=payload["data"],
                user_id=payload["user_id"],
                session_id=payload.get("session_id")
            )
            
            results.append(result)
        
        # Return first (main) result
        return results[0] if results else None
```

---

## 5. Backend Integration Points

### 5.1 Modified chat_router.ask_question()

**Current Flow**:
```python
@router.post("/ask/")
async def ask_question(request: ChatRequest, ...):
    rag_response = rag_engine.process_question(...)
    return response
```

**New Flow**:
```python
from backend.services.event_sources.chat_event_source import ChatEventSource

@router.post("/ask/")
async def ask_question(request: ChatRequest, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Processa una domanda dell'utente tramite il sistema di trigger e workflow
    """
    try:
        # Prepare event data
        event_source = ChatEventSource()
        
        # Fire chat_query event and wait for workflow result
        workflow_result = await event_source.emit_chat_query_event(
            user_id=current_user.user_id,
            username=current_user.username,
            session_id=request.session_id,
            question=request.question,
            message_id=str(uuid.uuid4()),
            mode=request.mode,
            model=request.model,
            system_prompt=request.first_prompt,
            provider=request.provider
        )
        
        # Extract response from workflow output node
        answer = workflow_result.get("response", "")
        sources = workflow_result.get("sources", [])
        session_id = workflow_result.get("session_id", request.session_id)
        
        # Save message to database
        db_user = chat_service.get_or_create_user(db, user_id=current_user.user_id)
        session = db.query(chat_service.models.ChatSession).filter_by(
            session_id=session_id
        ).first()
        
        if not session:
            session = chat_service.get_or_create_session(
                db, db_user, session_id=session_id
            )
        
        chat_service.save_message(
            db=db,
            session=session,
            prompt=request.question,
            answer=answer,
            tokens=workflow_result.get("tokens_used", 0)
        )
        
        return {
            "answer": answer,
            "source": "workflow",
            "session_id": session_id,
            "sources": sources
        }
        
    except TimeoutError:
        logger.error(f"Workflow timeout for user {current_user.user_id}")
        return HTTPException(status_code=504, detail="Workflow execution timeout")
    except Exception as e:
        logger.error(f"Error in chat processing: {e}", exc_info=True)
        return HTTPException(status_code=500, detail="Error processing chat query")
```

### 5.2 Database Schema Changes

Add to `backend/db/models.py`:

```python
class TriggerType(Base):
    __tablename__ = "trigger_types"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)  # "chat_query"
    description = Column(String(500))
    event_source_type = Column(String(100), nullable=False)  # "chat"
    payload_schema = Column(JSON, nullable=True)  # JSON schema for validation
    created_at = Column(DateTime, default=datetime.utcnow)
    
    triggers = relationship("Trigger", back_populates="trigger_type")
```

Update `Trigger` model to link to TriggerType:

```python
class Trigger(Base):
    # ... existing fields ...
    trigger_type_id = Column(Integer, ForeignKey('trigger_types.id'), nullable=False)
    trigger_type = relationship("TriggerType", back_populates="triggers")
```

### 5.3 TriggerService Registration

Add trigger type registration in `backend/services/trigger_service.py`:

```python
class TriggerService:
    
    def register_trigger_type(self, db: Session):
        """Register the chat_query trigger type in database"""
        
        chat_query_type = db.query(TriggerType).filter_by(name="chat_query").first()
        
        if not chat_query_type:
            chat_query_type = TriggerType(
                name="chat_query",
                description="Fires when a user submits a chat question",
                event_source_type="chat",
                payload_schema={
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "session_id": {"type": "string"},
                        "user_id": {"type": "integer"}
                    },
                    "required": ["question", "session_id", "user_id"]
                }
            )
            db.add(chat_query_type)
            db.commit()
            db.refresh(chat_query_type)
            
            logger.info("chat_query trigger type registered")
        
        return chat_query_type
```

---

## 6. Workflow Execution Flow

```
Chat Router
    ↓
emit_chat_query_event(...)
    ↓
TriggerService.fire_and_wait()
    ├─ Find matching triggers for "chat_query"
    ├─ Get linked workflow: "Chat Query Analyzer"
    ├─ Execute workflow with event payload
    │  ├─ [Query Analyzer Node] → analyze question
    │  ├─ [Parallel: Semantic + Metadata Search] → retrieve documents
    │  ├─ [Response Aggregator Node] → synthesize response
    │  └─ [Output Node] → return workflow result
    ├─ Wait for completion (max 30 seconds)
    └─ Return workflow result
    ↓
Save message to database
    ↓
Return response to frontend
```

---

## 7. Error Handling Strategy

| Scenario | Handling |
|----------|----------|
| No triggers found | Log warning, return empty result |
| Workflow timeout (>30s) | Return 504 Gateway Timeout |
| Workflow execution error | Return error details, log issue |
| Database save failure | Log error but return response anyway |
| Event payload invalid | Return 400 Bad Request |

---

## 8. Configuration Requirements

### Environment Variables (`.env`)
```env
# Trigger execution timeout (seconds)
TRIGGER_EXECUTION_TIMEOUT=30

# Whether chat queries use trigger system (gradual migration)
CHAT_USE_TRIGGER_SYSTEM=true

# Default chat query workflow ID
DEFAULT_CHAT_WORKFLOW_ID=workflow_chat_query_analyzer
```

---

## 9. Backward Compatibility

During migration, support both:

```python
# Option 1: Use trigger system (new)
if os.getenv("CHAT_USE_TRIGGER_SYSTEM") == "true":
    result = await event_source.emit_chat_query_event(...)
else:
    # Option 2: Use direct RAG engine (legacy)
    result = rag_engine.process_question(...)
```

---

## 10. Monitoring & Logging

All trigger firing and workflow execution should be logged:

```python
logger.info(
    "chat_query event fired",
    extra={
        "user_id": user_id,
        "session_id": session_id,
        "question_length": len(question),
        "triggers_matched": len(triggers),
        "workflow_id": workflow_id,
        "execution_time_ms": execution_time
    }
)
```

---

## Next Steps for Implementation

1. Create `ChatEventSource` class in `backend/services/event_sources/chat_event_source.py`
2. Modify `TriggerService` to implement `fire_and_wait()` method
3. Add `chat_query` trigger type to database schema
4. Register trigger type on backend startup
5. Update `chat_router.ask_question()` to use trigger system
6. Create default trigger linking `chat_query` to "Chat Query Analyzer" workflow
7. Add configuration environment variables
8. Test end-to-end with various query types
9. Implement fallback to RAG engine if workflow fails
10. Monitor performance and optimize timeout values

---

## Testing Checklist

- [ ] Trigger fires correctly when chat query received
- [ ] Workflow executes and returns result within timeout
- [ ] Metadata is properly included in response
- [ ] Timeout handling works (trigger times out after 30s)
- [ ] Error handling for missing workflow
- [ ] Database message saving works correctly
- [ ] Frontend receives complete response with sources
- [ ] Works with different query types (semantic, metadata, hybrid)
- [ ] Performance acceptable (<5s average response time)
