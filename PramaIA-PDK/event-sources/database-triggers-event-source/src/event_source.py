import asyncio
import logging
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
import sys
import os
from dataclasses import dataclass, asdict

# Database drivers
try:
    import asyncpg  # PostgreSQL
    import aiomysql  # MySQL  
    import aiosqlite  # SQLite
    import pyodbc  # SQL Server (sync fallback)
except ImportError as e:
    logging.getLogger(__name__).warning(f"[WARNING] Database driver non installato: {e}")

# Aggiungi il path del PDK per importare le utility
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

try:
    from core.event_source_base import BaseEventSourceProcessor
except ImportError:
    # Fallback per testing locale
    class BaseEventSourceProcessor:
        def __init__(self):
            self.logger = logging.getLogger(__name__)
        
        async def emit_event(self, event_type, data):
            logging.getLogger(__name__).info(f"[EVENT] {event_type}: {json.dumps(data, indent=2)}")
        
        def log_info(self, msg): logging.getLogger(__name__).info(msg)
        def log_warning(self, msg): logging.getLogger(__name__).warning(msg)
        def log_error(self, msg): logging.getLogger(__name__).error(msg)
        def log_debug(self, msg): logging.getLogger(__name__).debug(msg)

    # Adapter logger: prefer local wrapper 'logger', then pramaialog client, otherwise std logging
    try:
        from .logger import debug, info, warning, error, flush, close
    except Exception:
        try:
            from pramaialog import PramaIALogger

            _pramaialogger = PramaIALogger()

            def debug(msg, **kwargs):
                _pramaialogger.debug(msg, **kwargs)

            def info(msg, **kwargs):
                _pramaialogger.info(msg, **kwargs)

            def warning(msg, **kwargs):
                _pramaialogger.warning(msg, **kwargs)

            def error(msg, **kwargs):
                _pramaialogger.error(msg, **kwargs)

            def flush():
                try:
                    _pramaialogger.flush()
                except Exception:
                    pass

            def close():
                try:
                    _pramaialogger.close()
                except Exception:
                    pass

        except Exception:
            import logging as _std_logging

            def debug(msg, **kwargs):
                _std_logging.getLogger(__name__).debug(msg)

            def info(msg, **kwargs):
                _std_logging.getLogger(__name__).info(msg)

            def warning(msg, **kwargs):
                _std_logging.getLogger(__name__).warning(msg)

            def error(msg, **kwargs):
                _std_logging.getLogger(__name__).error(msg)

            def flush():
                return

            def close():
                return

@dataclass
class TableConfig:
    """Configurazione per una tabella monitorata"""
    connection: str
    schema: str
    table: str
    primary_key: str
    timestamp_column: Optional[str]
    events: List[str]
    filters: Dict[str, Any]
    tags: List[str]
    
    def get_full_name(self) -> str:
        """Ottiene il nome completo della tabella"""
        if self.schema:
            return f"{self.schema}.{self.table}"
        return self.table

@dataclass
class ChangeRecord:
    """Record di un cambiamento nel database"""
    trigger_id: str
    database: str
    schema: str
    table: str
    record_id: str
    operation: str
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    changed_fields: Optional[List[str]]
    timestamp: str
    user: str
    metadata: Dict[str, Any]

class DatabaseConnection:
    """Wrapper per connessioni database async"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config['name']
        self.db_type = config['type'].lower()
        self.connection = None
        self.pool = None
        
    async def connect(self):
        """Stabilisce connessione al database"""
        try:
            if self.db_type == 'postgresql':
                await self._connect_postgresql()
            elif self.db_type == 'mysql':
                await self._connect_mysql()
            elif self.db_type == 'sqlite':
                await self._connect_sqlite()
            elif self.db_type == 'sqlserver':
                await self._connect_sqlserver()
            else:
                raise ValueError(f"Database type non supportato: {self.db_type}")
                
        except Exception as e:
            raise ConnectionError(f"Errore connessione a {self.name}: {e}")
    
    async def _connect_postgresql(self):
        """Connessione PostgreSQL"""
        dsn = f"postgresql://{self.config['username']}:{self.config['password']}@{self.config['host']}:{self.config['port']}/{self.config['database']}"
        self.pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)
    
    async def _connect_mysql(self):
        """Connessione MySQL"""
        self.pool = await aiomysql.create_pool(
            host=self.config['host'],
            port=self.config['port'],
            user=self.config['username'],
            password=self.config['password'],
            db=self.config['database'],
            minsize=1,
            maxsize=5
        )
    
    async def _connect_sqlite(self):
        """Connessione SQLite"""
        self.connection = await aiosqlite.connect(self.config['database'])
    
    async def _connect_sqlserver(self):
        """Connessione SQL Server (fallback sync)"""
        # SQL Server async è complesso, implementazione base
        pass
    
    async def execute_query(self, query: str, *args) -> List[Dict]:
        """Esegue una query e restituisce risultati"""
        try:
            if self.db_type == 'postgresql':
                async with self.pool.acquire() as conn:
                    rows = await conn.fetch(query, *args)
                    return [dict(row) for row in rows]
            
            elif self.db_type == 'mysql':
                async with self.pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute(query, args)
                        rows = await cursor.fetchall()
                        columns = [desc[0] for desc in cursor.description]
                        return [dict(zip(columns, row)) for row in rows]
            
            elif self.db_type == 'sqlite':
                async with self.connection.execute(query, args) as cursor:
                    rows = await cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
            
            return []
            
        except Exception as e:
            raise RuntimeError(f"Errore esecuzione query su {self.name}: {e}")
    
    async def close(self):
        """Chiude connessione"""
        try:
            if self.pool:
                self.pool.close()
                await self.pool.wait_closed()
            if self.connection:
                await self.connection.close()
        except Exception as e:
            print(f"Errore chiusura connessione {self.name}: {e}")

class DatabaseTriggersEventSource(BaseEventSourceProcessor):
    def __init__(self):
        super().__init__()
        self.config = {}
        self.connections: Dict[str, DatabaseConnection] = {}
        self.table_configs: List[TableConfig] = []
        self.running = False
        self.monitoring_tasks = []
        self.last_checks: Dict[str, datetime] = {}
        self.processed_records: Set[str] = set()
        
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Inizializza l'event source con la configurazione"""
        try:
            self.config = config
            
            # Inizializza connessioni database
            connections_config = config.get('connections', [])
            if not connections_config:
                self.log_error("Nessuna connessione database configurata")
                return False
            
            for conn_config in connections_config:
                try:
                    db_conn = DatabaseConnection(conn_config)
                    await db_conn.connect()
                    self.connections[conn_config['name']] = db_conn
                    self.log_info(f"Connessione stabilita: {conn_config['name']} ({conn_config['type']})")
                except Exception as e:
                    self.log_error(f"Errore connessione {conn_config['name']}: {e}")
                    return False
            
            # Configura tabelle da monitorare
            tables_config = config.get('tables', [])
            for table_config in tables_config:
                try:
                    table_conf = TableConfig(
                        connection=table_config['connection'],
                        schema=table_config.get('schema', ''),
                        table=table_config['table'],
                        primary_key=table_config.get('primary_key', 'id'),
                        timestamp_column=table_config.get('timestamp_column'),
                        events=table_config.get('events', ['INSERT', 'UPDATE', 'DELETE']),
                        filters=table_config.get('filters', {}),
                        tags=table_config.get('tags', [])
                    )
                    self.table_configs.append(table_conf)
                    self.log_info(f"Configurata tabella: {table_conf.get_full_name()}")
                except Exception as e:
                    self.log_error(f"Errore configurazione tabella: {e}")
            
            if not self.table_configs:
                self.log_error("Nessuna tabella configurata per il monitoraggio")
                return False
            
            self.log_info("Database Triggers Event Source inizializzato correttamente")
            return True
            
        except Exception as e:
            self.log_error(f"Errore durante l'inizializzazione: {e}")
            return False
    
    async def start(self) -> bool:
        """Avvia il monitoraggio database"""
        try:
            if self.running:
                return True
            
            self.running = True
            
            # Avvia task di monitoraggio per ogni tabella
            monitoring_method = self.config.get('monitoring', {}).get('method', 'polling')
            
            if monitoring_method == 'polling':
                await self._start_polling_monitoring()
            elif monitoring_method == 'triggers':
                await self._start_trigger_monitoring()
            else:
                self.log_error(f"Metodo monitoraggio non supportato: {monitoring_method}")
                return False
            
            self.log_info(f"Database monitoring avviato con metodo: {monitoring_method}")
            return True
            
        except Exception as e:
            self.log_error(f"Errore durante l'avvio: {e}")
            return False
    
    async def stop(self) -> bool:
        """Ferma il monitoraggio database"""
        try:
            self.running = False
            
            # Ferma tutti i task di monitoraggio
            for task in self.monitoring_tasks:
                task.cancel()
            
            if self.monitoring_tasks:
                await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
            
            # Chiudi connessioni
            for conn in self.connections.values():
                await conn.close()
            
            self.log_info("Database monitoring fermato")
            return True
            
        except Exception as e:
            self.log_error(f"Errore durante lo stop: {e}")
            return False
    
    async def cleanup(self):
        """Pulizia risorse"""
        await self.stop()
    
    async def _start_polling_monitoring(self):
        """Avvia monitoraggio basato su polling"""
        polling_interval = self.config.get('monitoring', {}).get('polling_interval', 30)
        max_concurrent = self.config.get('performance', {}).get('max_concurrent_tables', 10)
        
        # Raggruppa tabelle per connessione
        tables_by_connection = {}
        for table_config in self.table_configs:
            if table_config.connection not in tables_by_connection:
                tables_by_connection[table_config.connection] = []
            tables_by_connection[table_config.connection].append(table_config)
        
        # Crea task per ogni connessione
        for conn_name, tables in tables_by_connection.items():
            task = asyncio.create_task(
                self._polling_loop(conn_name, tables, polling_interval)
            )
            self.monitoring_tasks.append(task)
    
    async def _polling_loop(self, connection_name: str, tables: List[TableConfig], interval: int):
        """Loop di polling per una connessione"""
        try:
            while self.running:
                try:
                    await self._check_tables_changes(connection_name, tables)
                except Exception as e:
                    self.log_error(f"Errore durante controllo {connection_name}: {e}")
                    await self._emit_database_error(connection_name, "polling_error", str(e))
                
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.log_error(f"Errore critico nel polling loop {connection_name}: {e}")
    
    async def _check_tables_changes(self, connection_name: str, tables: List[TableConfig]):
        """Controlla cambiamenti per un gruppo di tabelle"""
        db_conn = self.connections[connection_name]
        batch_size = self.config.get('monitoring', {}).get('batch_size', 1000)
        
        for table_config in tables:
            try:
                if 'INSERT' in table_config.events:
                    await self._check_inserts(db_conn, table_config, batch_size)
                
                if 'UPDATE' in table_config.events:
                    await self._check_updates(db_conn, table_config, batch_size)
                
                if 'DELETE' in table_config.events:
                    await self._check_deletes(db_conn, table_config, batch_size)
                    
            except Exception as e:
                self.log_error(f"Errore controllo tabella {table_config.get_full_name()}: {e}")
    
    async def _check_inserts(self, db_conn: DatabaseConnection, table_config: TableConfig, batch_size: int):
        """Controlla nuovi inserimenti"""
        table_name = table_config.get_full_name()
        last_check_key = f"{db_conn.name}:{table_name}:INSERT"
        
        # Query per trovare nuovi record
        if table_config.timestamp_column:
            # Usa timestamp column se disponibile
            last_check = self.last_checks.get(last_check_key, datetime.min)
            query = f"""
                SELECT * FROM {table_name} 
                WHERE {table_config.timestamp_column} > $1
                ORDER BY {table_config.timestamp_column} ASC
                LIMIT {batch_size}
            """
            rows = await db_conn.execute_query(query, last_check)
        else:
            # Fallback: usa primary key (meno affidabile)
            last_id = self.last_checks.get(last_check_key, 0)
            query = f"""
                SELECT * FROM {table_name} 
                WHERE {table_config.primary_key} > $1
                ORDER BY {table_config.primary_key} ASC
                LIMIT {batch_size}
            """
            rows = await db_conn.execute_query(query, last_id)
        
        # Processa nuovi record
        for row in rows:
            await self._emit_record_change(
                db_conn, table_config, 'INSERT', 
                record_id=str(row[table_config.primary_key]),
                new_values=row,
                old_values=None
            )
        
        # Aggiorna timestamp ultimo controllo
        if rows:
            if table_config.timestamp_column:
                last_timestamp = max(row[table_config.timestamp_column] for row in rows)
                self.last_checks[last_check_key] = last_timestamp
            else:
                last_id = max(row[table_config.primary_key] for row in rows)
                self.last_checks[last_check_key] = last_id
    
    async def _check_updates(self, db_conn: DatabaseConnection, table_config: TableConfig, batch_size: int):
        """Controlla aggiornamenti record (implementazione semplificata)"""
        # Per gli UPDATE è più complesso rilevare i cambiamenti senza trigger
        # Questa è una implementazione base che funziona solo con timestamp columns
        if not table_config.timestamp_column:
            return
        
        table_name = table_config.get_full_name()
        last_check_key = f"{db_conn.name}:{table_name}:UPDATE"
        last_check = self.last_checks.get(last_check_key, datetime.min)
        
        # Trova record modificati di recente
        query = f"""
            SELECT * FROM {table_name} 
            WHERE {table_config.timestamp_column} > $1
            ORDER BY {table_config.timestamp_column} ASC
            LIMIT {batch_size}
        """
        rows = await db_conn.execute_query(query, last_check)
        
        # Per una implementazione completa degli UPDATE servirebbe una tabella audit
        # o trigger che traccia le modifiche
        for row in rows:
            record_key = f"{db_conn.name}:{table_name}:{row[table_config.primary_key]}"
            if record_key not in self.processed_records:
                # Potrebbe essere un INSERT, non UPDATE
                self.processed_records.add(record_key)
                continue
            
            await self._emit_record_change(
                db_conn, table_config, 'UPDATE',
                record_id=str(row[table_config.primary_key]),
                new_values=row,
                old_values=None  # Non disponibile senza audit trail
            )
        
        if rows:
            last_timestamp = max(row[table_config.timestamp_column] for row in rows)
            self.last_checks[last_check_key] = last_timestamp
    
    async def _check_deletes(self, db_conn: DatabaseConnection, table_config: TableConfig, batch_size: int):
        """Controlla eliminazioni record"""
        # Per i DELETE è molto difficile rilevare senza trigger o soft delete
        # Questa implementazione funziona solo se c'è una colonna "deleted_at" o simile
        pass
    
    async def _emit_record_change(self, db_conn: DatabaseConnection, table_config: TableConfig, 
                                operation: str, record_id: str, new_values: Optional[Dict], 
                                old_values: Optional[Dict]):
        """Emetti evento per cambiamento record"""
        
        # Filtra valori se necessario
        if table_config.filters.get('exclude_columns'):
            exclude_cols = table_config.filters['exclude_columns']
            if new_values:
                new_values = {k: v for k, v in new_values.items() if k not in exclude_cols}
            if old_values:
                old_values = {k: v for k, v in old_values.items() if k not in exclude_cols}
        
        # Calcola campi modificati per UPDATE
        changed_fields = []
        if operation == 'UPDATE' and old_values and new_values:
            changed_fields = [k for k in new_values.keys() 
                            if k in old_values and new_values[k] != old_values[k]]
        
        # Dati evento
        event_data = {
            "trigger_id": str(uuid.uuid4()),
            "database": db_conn.config['database'],
            "schema": table_config.schema,
            "table": table_config.table,
            "record_id": record_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user": "unknown",  # Difficile da ottenere senza audit
            "metadata": {
                "connection": db_conn.name,
                "tags": table_config.tags,
                "operation": operation
            }
        }
        
        # Aggiungi dati specifici per tipo operazione
        if operation == 'INSERT':
            event_data["new_values"] = new_values
            await self.emit_event("record_inserted", event_data)
            
        elif operation == 'UPDATE':
            event_data["old_values"] = old_values
            event_data["new_values"] = new_values
            event_data["changed_fields"] = changed_fields
            await self.emit_event("record_updated", event_data)
            
        elif operation == 'DELETE':
            event_data["old_values"] = old_values
            await self.emit_event("record_deleted", event_data)
        
        self.log_debug(f"Evento {operation} emesso per {table_config.get_full_name()}:{record_id}")
    
    async def _start_trigger_monitoring(self):
        """Avvia monitoraggio basato su trigger database"""
        # Implementazione avanzata che crea trigger nel database
        # per notificare cambiamenti in tempo reale
        self.log_warning("Monitoraggio basado su trigger non ancora implementato")
        # TODO: Implementare trigger-based monitoring
    
    async def _emit_database_error(self, database: str, error_type: str, error_message: str, retry_count: int = 0):
        """Emetti evento per errore database"""
        error_data = {
            "error_id": str(uuid.uuid4()),
            "database": database,
            "error_type": error_type,
            "error_message": error_message,
            "error_at": datetime.utcnow().isoformat() + "Z",
            "retry_count": retry_count,
            "context": {
                "monitoring_method": self.config.get('monitoring', {}).get('method', 'polling')
            }
        }
        
        await self.emit_event("database_error", error_data)

# Entry point per testing
if __name__ == "__main__":
    async def main():
        # Configurazione di test per SQLite
        config = {
            "connections": [
                {
                    "name": "test_sqlite",
                    "type": "sqlite",
                    "database": "./test.db",
                    "username": "",
                    "password": ""
                }
            ],
            "monitoring": {
                "method": "polling",
                "polling_interval": 10,
                "batch_size": 100
            },
            "tables": [
                {
                    "connection": "test_sqlite",
                    "table": "users",
                    "primary_key": "id",
                    "timestamp_column": "updated_at",
                    "events": ["INSERT", "UPDATE"],
                    "tags": ["user_management"]
                }
            ],
            "performance": {
                "connection_pool_size": 2,
                "query_timeout": 30
            },
            "logging": {
                "log_queries": True,
                "log_level": "DEBUG"
            }
        }
        
        db_monitor = DatabaseTriggersEventSource()
        
        try:
            logging.getLogger(__name__).warning("ATTENZIONE: Configura connessioni database reali prima del test!")
            logging.getLogger(__name__).info("Questo è solo un esempio di configurazione.")
    
            # await db_monitor.initialize(config)
            # await db_monitor.start()
    
            logging.getLogger(__name__).info("Database monitor configurato (non avviato per sicurezza)")
            logging.getLogger(__name__).info("Modifica le connessioni nel codice per testare")
    
        except KeyboardInterrupt:
            logging.getLogger(__name__).info("\nFermando monitor...")
        finally:
            await db_monitor.cleanup()
    
    asyncio.run(main())
