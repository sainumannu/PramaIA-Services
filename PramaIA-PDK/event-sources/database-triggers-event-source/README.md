# Database Triggers Event Source

Event source per monitoraggio database con change data capture (CDC) e trigger automatici.

## Caratteristiche

- **Multi-database**: PostgreSQL, MySQL, SQLite, SQL Server, Oracle
- **Metodi monitoraggio**: Polling, Database Triggers, Log-based CDC
- **Change Detection**: INSERT, UPDATE, DELETE con diff dettagliato
- **Schema Monitoring**: Rileva cambiamenti struttura database
- **Performance**: Connection pooling, batch processing, monitoring parallelo
- **Filtering**: Filtri avanzati su tabelle, colonne, utenti
- **Retry Logic**: Gestione errori robusta con backoff esponenziale

## Configurazione

### Connessione PostgreSQL
```json
{
  "connections": [
    {
      "name": "main_postgres",
      "type": "postgresql",
      "host": "localhost",
      "port": 5432,
      "database": "myapp",
      "username": "monitor_user",
      "password": "secure_password",
      "schema": "public",
      "ssl_mode": "prefer"
    }
  ]
}
```

### Connessione MySQL
```json
{
  "connections": [
    {
      "name": "main_mysql",
      "type": "mysql",
      "host": "localhost",
      "port": 3306,
      "database": "myapp",
      "username": "monitor_user",
      "password": "secure_password"
    }
  ]
}
```

### Connessione SQLite
```json
{
  "connections": [
    {
      "name": "local_sqlite",
      "type": "sqlite",
      "database": "./database.db",
      "username": "",
      "password": ""
    }
  ]
}
```

### Tabelle da Monitorare
```json
{
  "tables": [
    {
      "connection": "main_postgres",
      "schema": "public",
      "table": "users",
      "primary_key": "id",
      "timestamp_column": "updated_at",
      "events": ["INSERT", "UPDATE", "DELETE"],
      "filters": {
        "where_clause": "active = true",
        "exclude_columns": ["password_hash", "session_token"]
      },
      "tags": ["user_management", "critical"]
    },
    {
      "connection": "main_postgres",
      "table": "orders",
      "primary_key": "order_id",
      "timestamp_column": "modified_at",
      "events": ["INSERT", "UPDATE"],
      "tags": ["ecommerce", "orders"]
    }
  ]
}
```

### Configurazione Monitoraggio
```json
{
  "monitoring": {
    "method": "polling",
    "polling_interval": 30,
    "batch_size": 1000,
    "track_schema_changes": true
  },
  "change_detection": {
    "enable_checksums": false,
    "track_field_changes": true,
    "ignore_system_users": true,
    "system_users": ["postgres", "mysql", "sa", "system"]
  }
}
```

### Performance Tuning
```json
{
  "performance": {
    "connection_pool_size": 10,
    "query_timeout": 60,
    "max_concurrent_tables": 20
  },
  "retry": {
    "max_retries": 5,
    "retry_delay_seconds": 60,
    "exponential_backoff": true
  }
}
```

## Eventi Generati

### record_inserted
Generato quando un nuovo record viene inserito.

**Output**:
- `trigger_id`: ID univoco evento
- `database`: Nome database
- `schema`: Schema tabella
- `table`: Nome tabella
- `record_id`: Valore chiave primaria
- `new_values`: Dati del nuovo record
- `timestamp`: Timestamp inserimento
- `user`: Utente database (se disponibile)
- `metadata`: Metadati aggiuntivi

### record_updated
Generato quando un record esistente viene aggiornato.

**Output**:
- `trigger_id`: ID univoco evento
- `database`: Nome database
- `schema`: Schema tabella
- `table`: Nome tabella
- `record_id`: Valore chiave primaria
- `old_values`: Dati prima dell'aggiornamento
- `new_values`: Dati dopo l'aggiornamento
- `changed_fields`: Lista campi modificati
- `timestamp`: Timestamp aggiornamento
- `user`: Utente database
- `metadata`: Metadati aggiuntivi

### record_deleted
Generato quando un record viene eliminato.

**Output**:
- `trigger_id`: ID univoco evento
- `database`: Nome database
- `schema`: Schema tabella
- `table`: Nome tabella
- `record_id`: Valore chiave primaria
- `old_values`: Dati del record eliminato
- `timestamp`: Timestamp eliminazione
- `user`: Utente database
- `metadata`: Metadati aggiuntivi

### schema_changed
Generato quando viene rilevato un cambiamento schema.

**Output**:
- `trigger_id`: ID univoco evento
- `database`: Nome database
- `schema`: Schema modificato
- `change_type`: Tipo cambiamento (CREATE, ALTER, DROP)
- `object_type`: Tipo oggetto (TABLE, INDEX, COLUMN)
- `object_name`: Nome oggetto modificato
- `ddl_statement`: Statement DDL (se disponibile)
- `timestamp`: Timestamp cambiamento
- `user`: Utente che ha fatto il cambiamento

### database_error
Generato per errori durante il monitoraggio.

**Output**:
- `error_id`: ID univoco errore
- `database`: Database dove è avvenuto l'errore
- `error_type`: Tipo errore
- `error_message`: Messaggio dettagliato
- `error_at`: Timestamp errore
- `retry_count`: Numero tentativi retry
- `context`: Contesto aggiuntivo

## Metodi di Monitoraggio

### 1. Polling (Default)
Controlla periodicamente le tabelle per cambiamenti.

**Pro**:
- Funziona con tutti i database
- Non richiede permessi speciali
- Facile da configurare

**Contro**:
- Latenza basata sull'intervallo
- Carico aggiuntivo sul database
- Difficile rilevare DELETE

### 2. Database Triggers
Usa trigger database per notifiche real-time.

**Pro**:
- Notifiche immediate
- Cattura tutti i cambiamenti
- Basso overhead

**Contro**:
- Richiede permessi DBA
- Modifica schema database
- Complessità maggiore

### 3. Log-based CDC
Monitora transaction log del database.

**Pro**:
- Zero latenza
- Nessun overhead performance
- Non modifica schema

**Contro**:
- Supporto limitato per database
- Configurazione complessa
- Richiede accesso ai log

## Setup Database-Specifico

### PostgreSQL
```sql
-- Crea utente per monitoraggio
CREATE USER monitor_user WITH PASSWORD 'secure_password';

-- Permessi base
GRANT CONNECT ON DATABASE myapp TO monitor_user;
GRANT USAGE ON SCHEMA public TO monitor_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitor_user;

-- Per trigger-based monitoring
GRANT CREATE ON SCHEMA public TO monitor_user;
```

### MySQL
```sql
-- Crea utente per monitoraggio
CREATE USER 'monitor_user'@'%' IDENTIFIED BY 'secure_password';

-- Permessi base
GRANT SELECT ON myapp.* TO 'monitor_user'@'%';

-- Per trigger-based monitoring
GRANT CREATE, TRIGGER ON myapp.* TO 'monitor_user'@'%';
```

### SQLite
Non richiede setup speciale, basta accesso al file database.

## Use Cases

### 1. Audit Trail
```json
{
  "tables": [
    {
      "table": "financial_transactions",
      "events": ["INSERT", "UPDATE", "DELETE"],
      "tags": ["audit", "financial", "compliance"]
    }
  ]
}
```

### 2. Cache Invalidation
```json
{
  "tables": [
    {
      "table": "products",
      "events": ["UPDATE"],
      "filters": {
        "exclude_columns": ["last_viewed", "view_count"]
      },
      "tags": ["cache_invalidation"]
    }
  ]
}
```

### 3. Real-time Analytics
```json
{
  "tables": [
    {
      "table": "user_events",
      "events": ["INSERT"],
      "tags": ["analytics", "real_time"]
    }
  ]
}
```

### 4. Data Synchronization
```json
{
  "tables": [
    {
      "table": "customer_data",
      "events": ["INSERT", "UPDATE"],
      "tags": ["sync", "crm_integration"]
    }
  ]
}
```

## Testing

### Setup Test Database (PostgreSQL)
```sql
-- Crea database test
CREATE DATABASE test_monitoring;

-- Crea tabella test
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crea trigger per updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

### Test Script
```bash
cd database-triggers-event-source
pip install -r requirements.txt
# Configura connessione in event_source.py
python src/event_source.py
```

### Genera Test Data
```sql
-- INSERT test
INSERT INTO users (username, email) VALUES ('test1', 'test1@example.com');

-- UPDATE test  
UPDATE users SET email = 'newemail@example.com' WHERE username = 'test1';

-- DELETE test
DELETE FROM users WHERE username = 'test1';
```

## Troubleshooting

### Errori Comuni

#### Permessi Database
```
ERROR: permission denied for table users
```
**Soluzione**: Verifica permessi SELECT/CREATE per l'utente monitor.

#### Connection Pool Exhausted
```
ERROR: connection pool exhausted
```
**Soluzione**: Aumenta `connection_pool_size` o riduci `max_concurrent_tables`.

#### Timeout Query
```
ERROR: query timeout after 30 seconds
```
**Soluzione**: Aumenta `query_timeout` o ottimizza indici tabelle.

### Monitoring Performance

```json
{
  "logging": {
    "log_queries": true,
    "log_data_changes": false,
    "log_level": "DEBUG"
  }
}
```

**ATTENZIONE**: `log_data_changes: true` può esporre dati sensibili nei log.

## Sicurezza

### Best Practices
- Usa utenti database dedicati con permessi minimi
- Non loggare dati sensibili
- Crittografa credenziali database
- Monitora solo tabelle necessarie
- Implementa rate limiting per proteggere il database

### Gestione Credenziali
```json
{
  "connections": [
    {
      "username": "${DB_MONITOR_USER}",
      "password": "${DB_MONITOR_PASSWORD}"
    }
  ]
}
```

Usa sempre variabili d'ambiente per credenziali in produzione.
