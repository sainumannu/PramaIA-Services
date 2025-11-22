# Scheduler Event Source

Event Source PDK per lo scheduling automatico di workflow - supporta cron, intervalli e trigger temporali una tantum.

## Descrizione

Questo Event Source fornisce capacità di scheduling avanzate per automatizzare l'esecuzione di workflow PramaIA. Supporta:

- **Cron Scheduling**: Espressioni cron standard per scheduling complesso
- **Interval Scheduling**: Esecuzione ad intervalli regolari
- **One-Time Scheduling**: Esecuzione programmata per una data/ora specifica
- **Multiple schedules**: Gestione di più schedule simultaneamente
- **Timezone support**: Supporto completo per fusi orari
- **Error handling**: Gestione errori e retry automatici

## Tipi di Schedule Supportati

### 1. Cron Schedule
Utilizza espressioni cron standard per scheduling avanzato.

**Formato**: `minuto ora giorno_mese mese giorno_settimana`

**Esempi**:
- `0 9 * * *` - Ogni giorno alle 9:00 AM
- `0 9 * * MON` - Ogni lunedì alle 9:00 AM  
- `*/15 * * * *` - Ogni 15 minuti
- `0 0 1 * *` - Il primo giorno di ogni mese a mezzanotte
- `0 18 * * FRI` - Ogni venerdì alle 6:00 PM

### 2. Interval Schedule
Esecuzione ad intervalli regolari definiti in secondi.

**Esempi**:
- `3600` - Ogni ora (3600 secondi)
- `1800` - Ogni 30 minuti  
- `86400` - Ogni giorno (24 ore)

### 3. One-Time Schedule
Esecuzione programmata per una data/ora specifica (una sola volta).

**Formato**: ISO 8601 timestamp (`YYYY-MM-DDTHH:MM:SSZ`)

**Esempi**:
- `2025-08-04T10:00:00Z` - 4 agosto 2025 alle 10:00 UTC
- `2025-12-25T09:30:00Z` - 25 dicembre 2025 alle 9:30 UTC

## Configurazione

```json
{
  "schedules": [
    {
      "name": "daily_report",
      "type": "cron",
      "cron": "0 9 * * *",
      "enabled": true,
      "timezone": "Europe/Rome",
      "metadata": {
        "report_type": "daily",
        "recipients": ["admin@example.com"]
      }
    },
    {
      "name": "every_30_minutes",
      "type": "interval", 
      "interval_seconds": 1800,
      "enabled": true,
      "metadata": {
        "task": "health_check"
      }
    },
    {
      "name": "year_end_backup",
      "type": "one_time",
      "execute_at": "2025-12-31T23:00:00Z",
      "enabled": true,
      "metadata": {
        "backup_type": "full",
        "priority": "high"
      }
    }
  ],
  "max_concurrent_executions": 5,
  "execution_timeout": 300,
  "retry_failed_schedules": true,
  "max_retries": 3,
  "log_level": "INFO"
}
```

### Parametri di configurazione:

#### schedules (richiesto)
Array di configurazioni schedule. Ogni schedule deve avere:

- **name** (richiesto): Nome univoco per la schedule
- **type** (richiesto): Tipo di schedule (`cron`, `interval`, `one_time`)
- **enabled** (default: true): Se la schedule è attiva
- **timezone** (default: "UTC"): Fuso orario per cron schedules
- **metadata** (opzionale): Dati aggiuntivi da includere negli eventi

#### Parametri specifici per tipo:

**Per type="cron"**:
- **cron** (richiesto): Espressione cron

**Per type="interval"**:
- **interval_seconds** (richiesto): Intervallo in secondi

**Per type="one_time"**:
- **execute_at** (richiesto): Timestamp ISO 8601 di esecuzione

#### Parametri globali:
- **max_concurrent_executions** (default: 5): Max schedule simultanee
- **execution_timeout** (default: 300): Timeout esecuzione in secondi
- **retry_failed_schedules** (default: true): Se fare retry in caso di errore
- **max_retries** (default: 3): Numero massimo di retry
- **log_level** (default: "INFO"): Livello di logging (DEBUG, INFO, WARNING, ERROR)

## Eventi Emessi

### cron_trigger
Emesso quando una schedule cron viene eseguita.

**Outputs**:
- `trigger_time`: Timestamp ISO di esecuzione
- `cron_expression`: Espressione cron che ha scatenato l'evento
- `schedule_name`: Nome della schedule
- `next_execution`: Timestamp ISO della prossima esecuzione
- `[metadata]`: Eventuali metadati configurati

### interval_trigger  
Emesso quando una schedule ad intervalli viene eseguita.

**Outputs**:
- `trigger_time`: Timestamp ISO di esecuzione
- `interval_seconds`: Intervallo in secondi
- `schedule_name`: Nome della schedule
- `execution_count`: Numero di esecuzioni totali
- `[metadata]`: Eventuali metadati configurati

### one_time_trigger
Emesso quando una schedule one-time viene eseguita.

**Outputs**:
- `trigger_time`: Timestamp ISO di esecuzione effettiva
- `scheduled_time`: Timestamp ISO di esecuzione programmata
- `schedule_name`: Nome della schedule
- `delay_seconds`: Ritardo effettivo (positivo se in ritardo)
- `[metadata]`: Eventuali metadati configurati

### schedule_error
Emesso quando si verifica un errore nell'esecuzione di una schedule.

**Outputs**:
- `error_time`: Timestamp ISO dell'errore
- `schedule_name`: Nome della schedule fallita
- `error_message`: Descrizione dell'errore
- `schedule_type`: Tipo di schedule (cron, interval, one_time)

## Utilizzo

### Tramite PDK Server API

```bash
# Avvia lo scheduler event source
curl -X POST http://localhost:3001/api/event-sources/scheduler-event-source/start \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "schedules": [
        {
          "name": "hourly_task",
          "type": "cron", 
          "cron": "0 * * * *",
          "enabled": true,
          "timezone": "Europe/Rome"
        }
      ]
    }
  }'

# Ottieni lo status dettagliato
curl http://localhost:3001/api/event-sources/scheduler-event-source/status

# Ferma lo scheduler
curl -X POST http://localhost:3001/api/event-sources/scheduler-event-source/stop
```

### Esempi di Espressioni Cron

| Espressione | Descrizione |
|-------------|-------------|
| `0 9 * * *` | Ogni giorno alle 9:00 AM |
| `0 9 * * MON` | Ogni lunedì alle 9:00 AM |
| `*/15 * * * *` | Ogni 15 minuti |
| `30 2 * * *` | Ogni giorno alle 2:30 AM |
| `0 0 1 * *` | Il primo di ogni mese a mezzanotte |
| `0 0 * * SUN` | Ogni domenica a mezzanotte |
| `0 */2 * * *` | Ogni 2 ore |
| `0 9-17 * * MON-FRI` | Dalle 9 alle 17, dal lunedì al venerdì |

### Fusi Orari Supportati

Il sistema supporta tutti i fusi orari standard IANA:
- `UTC` - Tempo coordinato universale
- `Europe/Rome` - Ora italiana
- `America/New_York` - Ora orientale USA
- `Asia/Tokyo` - Ora giapponese
- `Australia/Sydney` - Ora australiana

## Integrazione con Workflow

Gli eventi emessi da questo Event Source possono essere utilizzati come trigger per workflow PramaIA:

1. **Report Automatici**: Schedule giornaliere/settimanali per generazione report
2. **Backup Programmati**: Backup periodici di dati e configurazioni  
3. **Manutenzione Sistema**: Task di pulizia e ottimizzazione programmati
4. **Notifiche Ricorrenti**: Reminder e notifiche su base temporale
5. **Data Processing**: Elaborazione batch di dati ad orari prestabiliti

## Dipendenze

- Python 3.7+
- croniter>=1.3.0 (per parsing espressioni cron)
- pytz>=2023.3 (per gestione fusi orari)
- asyncio (built-in)
- datetime (built-in)

## Monitoraggio e Debugging

Lo scheduler fornisce logging dettagliato configurabile:

- **DEBUG**: Log dettagliati di ogni operazione
- **INFO**: Informazioni su avvio/stop e esecuzioni schedule
- **WARNING**: Avvisi per situazioni anomale
- **ERROR**: Solo errori critici

Il comando status restituisce informazioni dettagliate su ogni schedule attiva:
- Stato corrente (running/stopped)  
- Numero di esecuzioni
- Ultima esecuzione
- Prossima esecuzione programmata
- Configurazione completa
