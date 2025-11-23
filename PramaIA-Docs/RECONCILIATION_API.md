# ReconciliationService API Reference

Base URL: `http://localhost:8091`

## Health & Status

| Method | Endpoint | Response | Description |
|--------|----------|----------|-------------|
| GET | `/health` | `{"status": "ok", "service": "PramaIA-Reconciliation", "version": "1.0.0"}` | Service health check |
| GET | `/status` | Detailed service status | Service status with scheduler info |
| GET | `/reconciliation/status` | Same as `/status` | Alternative endpoint |

## Reconciliation

| Method | Endpoint | Body | Response | Description |
|--------|----------|------|----------|-------------|
| POST | `/start` | `{"delete_missing": false}` | `{"success": true, "job_id": "...", "message": "..."}` | Start reconciliation process |
| POST | `/reconciliation/start` | Same as above | Same as above | Alternative endpoint |

## Settings

| Method | Endpoint | Body | Response | Description |
|--------|----------|------|----------|-------------|
| GET | `/settings` | - | Current settings | Get reconciliation settings |
| POST | `/settings` | Settings object | Updated settings | Update reconciliation settings |

## Configuration (New)

| Method | Endpoint | Body | Response | Description |
|--------|----------|------|----------|-------------|
| GET | `/api/config/schedule` | - | `{"daily": {...}, "periodic": {...}}` | Get current scheduler configuration |
| POST | `/api/config/schedule` | Scheduler config object | `{"success": true, "message": "...", "config": {...}, "next_execution": "..."}` | Update scheduler configuration |
| GET | `/api/config/schedule/status` | - | Scheduler status info | Get scheduler status |
| POST | `/api/config/schedule/restart` | - | `{"success": true, "message": "...", "restart_required": true}` | Restart scheduler |

## Configuration Models

### Scheduler Configuration Object
```json
{
  "daily": {
    "enabled": true,
    "hour": 3,
    "minute": 30
  },
  "periodic": {
    "enabled": true,
    "interval_minutes": 45
  }
}
```

### VectorStore Configuration Object
```json
{
  "chroma_host": "localhost",
  "chroma_port": 8000,
  "batch_size": 100,
  "max_worker_threads": 4
}
```

## Response Formats

### Scheduler Status Response
```json
{
  "scheduler_running": true,
  "daily_scheduler": {
    "enabled": true,
    "next_run": "2025-11-24T03:30:00"
  },
  "periodic_scheduler": {
    "enabled": true,
    "interval_minutes": 45
  },
  "last_execution": null,
  "uptime": "N/A"
}
```

### Configuration Response
```json
{
  "success": true,
  "message": "Configurazione scheduler aggiornata con successo. Riavvio del servizio consigliato.",
  "config": {
    "daily": {
      "enabled": true,
      "hour": 3,
      "minute": 30
    },
    "periodic": {
      "enabled": true,
      "interval_minutes": 45
    }
  },
  "next_execution": "2025-11-24T03:30:00"
}
```

## Error Response
```json
{
  "detail": "Error message"
}
```

## Usage Examples

### Update VectorStore Configuration
```bash
# Get current configuration
curl -X GET "http://localhost:8090/api/configure"

# Update configuration
curl -X POST "http://localhost:8090/api/configure" \
  -H "Content-Type: application/json" \
  -d '{
    "chroma_host": "new-host",
    "chroma_port": 8001,
    "batch_size": 200,
    "max_worker_threads": 8
  }'
```

### Update Reconciliation Scheduler
```bash
# Get current scheduler configuration
curl -X GET "http://localhost:8091/api/config/schedule"

# Enable daily scheduler at 3:30 AM and periodic every 45 minutes
curl -X POST "http://localhost:8091/api/config/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "daily": {
      "enabled": true,
      "hour": 3,
      "minute": 30
    },
    "periodic": {
      "enabled": true,
      "interval_minutes": 45
    }
  }'

# Enable periodic scheduler every 30 minutes
curl -X POST "http://localhost:8091/api/config/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "daily": {
      "enabled": false,
      "hour": 2,
      "minute": 0
    },
    "periodic": {
      "enabled": true,
      "interval_minutes": 30
    }
  }'
```