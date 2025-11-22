# Workflow Scheduler - Documentazione

## Panoramica
Il nodo **Workflow Scheduler** permette di programmare l'esecuzione di workflow secondo vari criteri temporali. Può essere utilizzato per automatizzare processi ricorrenti, pianificare elaborazioni in orari specifici o rispondere a eventi del sistema.

## Identificativo
- **ID Plugin**: `workflow-scheduler-plugin`
- **ID Nodo**: `workflow_scheduler`
- **Tipo**: `control`
- **Categoria**: `Workflow Control`

## Ingressi
- **trigger** (opzionale): Segnale di trigger esterno per avviare lo scheduler

## Uscite
- **output**: Dati da passare al nodo successivo quando viene attivato lo scheduler
- **metadata**: Informazioni sulla schedulazione (stato, conteggio esecuzioni, timestamp, ecc.)

## Tipi di schedulazione supportati

### Intervallo
Esecuzione ripetuta a intervalli fissi.

```json
{
  "schedule_type": "interval",
  "interval": {
    "value": 10,
    "unit": "minutes"
  }
}
```

Unità supportate: seconds, minutes, hours, days

### Cron
Esecuzione in base a un'espressione cron.

```json
{
  "schedule_type": "cron",
  "cron_expression": "0 9 * * 1-5",
  "timezone": "Europe/Rome"
}
```

L'espressione cron segue il formato standard: minuto ora giorno-del-mese mese giorno-della-settimana

### Data specifica
Esecuzione singola a una data e ora precise.

```json
{
  "schedule_type": "date",
  "specific_date": "2025-12-31T23:59:59"
}
```

### Evento
Esecuzione in risposta a un evento specifico.

```json
{
  "schedule_type": "event",
  "event_name": "nuovo_documento"
}
```

## Opzioni avanzate

### Limitazione temporale
```json
{
  "start_date": "2025-01-01T00:00:00",
  "end_date": "2025-12-31T23:59:59"
}
```

### Limitazione esecuzioni
```json
{
  "max_executions": 10,
  "skip_immediate": true
}
```

### Monitoraggio
```json
{
  "execution_tracking": {
    "store_history": true,
    "max_history_items": 100,
    "notify_on_execution": false,
    "notify_on_error": true
  }
}
```

## Esempio completo
```json
{
  "id": "daily_report_scheduler",
  "type": "pdk_workflow-scheduler-plugin_workflow_scheduler",
  "config": {
    "schedule_type": "cron",
    "cron_expression": "0 8 * * 1-5",
    "timezone": "Europe/Rome",
    "max_executions": 0,
    "skip_immediate": true,
    "execution_tracking": {
      "store_history": true,
      "notify_on_error": true
    }
  }
}
```

## Note di utilizzo
- La precisione della schedulazione dipende dal carico del server
- Per espressioni cron complesse, verificare la sintassi con uno strumento apposito
- Gli scheduler con "max_executions" impostato a 0 continueranno indefinitamente
- Se il server viene riavviato, gli scheduler verranno ricreati all'avvio del workflow

## Compatibilità
- Versione PDK richiesta: 1.0.0 o superiore
- Compatibile con tutti i tipi di nodi di elaborazione e output
