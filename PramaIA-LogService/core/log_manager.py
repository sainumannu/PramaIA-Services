"""
Sistema di gestione dei log.
"""

import os
import json
import sqlite3
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import uuid
import logging

from core.models import LogEntry, LogLevel, LogProject, LogStats

# Configura il logger interno
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LogManager")

class LogManager:
    """
    Gestisce la memorizzazione e il recupero dei log.
    """
    
    def __init__(self, db_path=None):
        """
        Inizializza il gestore dei log.
        
        Args:
            db_path: Percorso al database SQLite. Se None, usa il percorso predefinito.
        """
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            db_path = os.path.join(base_dir, "logs", "log_database.db")
            
            # Assicurati che la directory logs esista
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
        self.db_path = db_path
        self.start_time = datetime.now()
        self._initialize_database()
    
    def _get_connection(self):
        """
        Ottiene una connessione al database.
        
        Returns:
            Connessione a SQLite
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _initialize_database(self):
        """
        Inizializza il database creando le tabelle necessarie se non esistono.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Crea la tabella dei log
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            project TEXT NOT NULL,
            level TEXT NOT NULL,
            module TEXT NOT NULL,
            message TEXT NOT NULL,
            details TEXT,
            context TEXT
        )
        ''')
        
        # Crea indici per migliorare le performance delle query
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON logs (timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_project ON logs (project)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_level ON logs (level)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_module ON logs (module)')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Database inizializzato: {self.db_path}")
    
    def add_log(self, log_entry: LogEntry) -> str:
        """
        Aggiunge una voce di log al database.
        
        Args:
            log_entry: LogEntry da aggiungere
            
        Returns:
            ID del log aggiunto
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Converti le strutture dati in JSON con gestione degli errori
        try:
            details_json = json.dumps(log_entry.details) if log_entry.details else None
        except Exception as e:
            logger.error(f"Errore durante la serializzazione JSON dei dettagli per il log {log_entry.id}: {str(e)}")
            # Salva una versione semplificata che può essere serializzata
            details_json = json.dumps({"error": "Impossibile serializzare i dettagli originali", "message": str(e)})
            
        try:    
            context_json = json.dumps(log_entry.context) if log_entry.context else None
        except Exception as e:
            logger.error(f"Errore durante la serializzazione JSON del contesto per il log {log_entry.id}: {str(e)}")
            context_json = json.dumps({"error": "Impossibile serializzare il contesto originale", "message": str(e)})
        
        # Inserisci il log
        cursor.execute('''
        INSERT INTO logs (id, timestamp, project, level, module, message, details, context)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_entry.id,
            log_entry.timestamp.isoformat(),
            log_entry.project,
            log_entry.level,
            log_entry.module,
            log_entry.message,
            details_json,
            context_json
        ))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Log aggiunto: {log_entry.id} - {log_entry.message}")
        return log_entry.id
    
    def add_logs_batch(self, log_entries: List[LogEntry]) -> List[str]:
        """
        Aggiunge più voci di log al database in un'unica transazione.
        
        Args:
            log_entries: Lista di LogEntry da aggiungere
            
        Returns:
            Lista di ID dei log aggiunti
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        log_ids = []
        
        try:
            for log_entry in log_entries:
                # Converti le strutture dati in JSON con gestione degli errori
                try:
                    details_json = json.dumps(log_entry.details) if log_entry.details else None
                except Exception as e:
                    logger.error(f"Errore durante la serializzazione JSON dei dettagli per il log {log_entry.id}: {str(e)}")
                    # Salva una versione semplificata che può essere serializzata
                    details_json = json.dumps({"error": "Impossibile serializzare i dettagli originali", "message": str(e)})
                    
                try:    
                    context_json = json.dumps(log_entry.context) if log_entry.context else None
                except Exception as e:
                    logger.error(f"Errore durante la serializzazione JSON del contesto per il log {log_entry.id}: {str(e)}")
                    context_json = json.dumps({"error": "Impossibile serializzare il contesto originale", "message": str(e)})
                
                # Inserisci il log
                cursor.execute('''
                INSERT INTO logs (id, timestamp, project, level, module, message, details, context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    log_entry.id,
                    log_entry.timestamp.isoformat(),
                    log_entry.project,
                    log_entry.level,
                    log_entry.module,
                    log_entry.message,
                    details_json,
                    context_json
                ))
                
                log_ids.append(log_entry.id)
            
            conn.commit()
            logger.info(f"Batch di {len(log_ids)} log aggiunto con successo")
        except Exception as e:
            conn.rollback()
            logger.error(f"Errore durante l'aggiunta del batch di log: {str(e)}")
            raise
        finally:
            conn.close()
        
        return log_ids
    
    def get_logs(
        self,
        project: Optional[Union[LogProject, str]] = None,
        level: Optional[Union[LogLevel, str]] = None,
        module: Optional[str] = None,
        document_id: Optional[str] = None,
        file_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Recupera i log in base ai filtri specificati.
        
        Args:
            project: Filtra per progetto
            level: Filtra per livello di log
            module: Filtra per modulo
            document_id: Filtra per ID del documento
            file_name: Filtra per nome del file
            start_date: Data di inizio per il filtro temporale
            end_date: Data di fine per il filtro temporale
            sort_by: Campo per ordinare i risultati (timestamp, level, project, module)
            sort_order: Ordine di ordinamento (asc, desc)
            limit: Numero massimo di log da restituire
            offset: Offset per la paginazione
            
        Returns:
            Lista di log che soddisfano i criteri di filtro
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Costruisci la query
        query = "SELECT * FROM logs WHERE 1=1"
        params = []
        
        # Standardizza il valore di project a stringa
        project_str = project
        if isinstance(project, LogProject):
            project_str = project.value
            
        if project_str:
            query += " AND project = ?"
            params.append(project_str)
        
        # Standardizza il valore di level a stringa
        level_str = level
        if isinstance(level, LogLevel):
            level_str = level.value
            
        if level_str:
            # Filtra per il livello specifico richiesto - NESSUNA gestione speciale
            query += " AND level = ?"
            params.append(level_str)
        
        if module:
            query += " AND module = ?"
            params.append(module)
            
        # Filtri per documento e file - Migliorata per cercare in più campi
        if document_id:
            # Cerca nei dettagli o contesto JSON contenenti document_id
            query += " AND (details LIKE ? OR context LIKE ?)"
            doc_search = f"%{document_id}%"
            params.append(doc_search)
            params.append(doc_search)
            
        if file_name:
            # Cerca nei dettagli o contesto JSON contenenti file_name
            # Cerca sia nei campi file_name che file_path o semplicemente come parte di qualsiasi stringa
            query += " AND (details LIKE ? OR details LIKE ? OR details LIKE ? OR context LIKE ? OR context LIKE ? OR context LIKE ?)"
            
            # Ricerca per nome file in vari formati
            file_search1 = f"%\"file_name\":%{file_name}%"  # Nome file in campo file_name
            file_search2 = f"%\"file_path\":%{file_name}%"  # Nome file come parte del percorso
            file_search3 = f"%{file_name}%"                 # Nome file in qualsiasi punto
            
            params.append(file_search1)
            params.append(file_search2)
            params.append(file_search3)
            params.append(file_search1)
            params.append(file_search2)
            params.append(file_search3)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        # Validazione campi di ordinamento
        valid_sort_fields = ["timestamp", "level", "project", "module", "message"]
        valid_sort_orders = ["asc", "desc"]
        
        # Imposta i valori predefiniti se non validi
        if sort_by not in valid_sort_fields:
            sort_by = "timestamp"
        
        if sort_order.lower() not in valid_sort_orders:
            sort_order = "desc"
        
        # Applica l'ordinamento
        query += f" ORDER BY {sort_by} {sort_order.upper()}"
        
        # Limita i risultati
        query += " LIMIT ? OFFSET ?"
        params.append(limit)
        params.append(offset)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Converti i risultati in dizionari
        results = []
        
        # Variabili per post-filtraggio
        apply_document_filter = document_id is not None
        apply_file_filter = file_name is not None
        
        for row in rows:
            log_dict = dict(row)
            
            # Converti JSON in dizionari con gestione degli errori
            details_obj = None
            context_obj = None
            
            if log_dict["details"]:
                try:
                    details_obj = json.loads(log_dict["details"])
                    log_dict["details"] = details_obj
                except Exception as e:
                    logger.error(f"Errore durante il parsing JSON dei dettagli per il log {log_dict['id']}: {str(e)}")
                    # Invece di avere valori undefined, manteniamo almeno i dati originali
                    log_dict["details"] = {"error": "Formato JSON non valido", "raw_data": log_dict["details"]}
            
            if log_dict["context"]:
                try:
                    context_obj = json.loads(log_dict["context"])
                    log_dict["context"] = context_obj
                except Exception as e:
                    logger.error(f"Errore durante il parsing JSON del contesto per il log {log_dict['id']}: {str(e)}")
                    log_dict["context"] = {"error": "Formato JSON non valido", "raw_data": log_dict["context"]}
            
            # Aggiungi il log ai risultati senza alcun post-processing
            results.append(log_dict)
        
        conn.close()
        return results
    
    def get_stats(
        self,
        project: Optional[LogProject] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> LogStats:
        """
        Ottiene statistiche sui log.
        
        Args:
            project: Filtra per progetto
            start_date: Data di inizio per il filtro temporale
            end_date: Data di fine per il filtro temporale
            
        Returns:
            Statistiche sui log
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Query base per il conteggio totale
        query = "SELECT COUNT(*) as total FROM logs WHERE 1=1"
        params = []
        
        # Aggiungi filtri
        if project:
            query += " AND project = ?"
            params.append(project)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        # Esegui query per il conteggio totale
        cursor.execute(query, params)
        total_logs = cursor.fetchone()["total"]
        
        # Query per conteggio per livello
        level_query = query.replace("COUNT(*) as total", "level, COUNT(*) as count") + " GROUP BY level"
        cursor.execute(level_query, params)
        level_rows = cursor.fetchall()
        
        logs_by_level = {}
        for level in LogLevel:
            logs_by_level[level] = 0
            
        for row in level_rows:
            logs_by_level[row["level"]] = row["count"]
        
        # Query per conteggio per progetto
        project_query = query.replace("COUNT(*) as total", "project, COUNT(*) as count") + " GROUP BY project"
        cursor.execute(project_query, params)
        project_rows = cursor.fetchall()
        
        logs_by_project = {}
        for project_enum in LogProject:
            logs_by_project[project_enum] = 0
            
        for row in project_rows:
            logs_by_project[row["project"]] = row["count"]
        
        # Query per conteggio per modulo (top 10)
        module_query = query.replace("COUNT(*) as total", "module, COUNT(*) as count") + " GROUP BY module ORDER BY count DESC LIMIT 10"
        cursor.execute(module_query, params)
        module_rows = cursor.fetchall()
        
        logs_by_module = {}
        for row in module_rows:
            logs_by_module[row["module"]] = row["count"]
        
        # Determina il periodo di tempo
        time_period = {}
        
        if start_date:
            time_period["start"] = start_date
        if end_date:
            time_period["end"] = end_date
        
        if not start_date or not end_date:
            # Se non specificato, prendi il periodo effettivo dai dati
            min_max_query = "SELECT MIN(timestamp) as min_time, MAX(timestamp) as max_time FROM logs"
            cursor.execute(min_max_query)
            time_row = cursor.fetchone()
            
            if not start_date and time_row["min_time"]:
                try:
                    time_period["start"] = datetime.fromisoformat(time_row["min_time"])
                except ValueError:
                    # Fallback: utilizza la data corrente
                    time_period["start"] = datetime.now()
            
            if not end_date and time_row["max_time"]:
                try:
                    time_period["end"] = datetime.fromisoformat(time_row["max_time"])
                except ValueError:
                    # Fallback: utilizza la data corrente
                    time_period["end"] = datetime.now()
        
        conn.close()
        
        # Crea l'oggetto statistiche
        stats = LogStats(
            total_logs=total_logs,
            logs_by_level=logs_by_level,
            logs_by_project=logs_by_project,
            logs_by_module=logs_by_module,
            time_period=time_period
        )
        
        return stats
    
    def cleanup_logs(
        self,
        days_to_keep: int = 30,
        project: Optional[LogProject] = None,
        level: Optional[LogLevel] = None
    ) -> int:
        """
        Elimina i log più vecchi di un certo numero di giorni.
        
        Args:
            days_to_keep: Numero di giorni per cui mantenere i log
            project: Filtra per progetto
            level: Filtra per livello di log
            
        Returns:
            Numero di log eliminati
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Calcola la data limite
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        # Costruisci la query
        query = "DELETE FROM logs WHERE timestamp < ?"
        params = [cutoff_date]
        
        if project:
            query += " AND project = ?"
            params.append(project)
        
        if level:
            query += " AND level = ?"
            params.append(level)
        
        # Esegui la query
        cursor.execute(query, params)
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"Eliminati {deleted_count} log più vecchi di {days_to_keep} giorni")
        return deleted_count
    
    def reset_logs(
        self,
        cutoff_date: datetime,
        project: Optional[LogProject] = None
    ) -> int:
        """
        Elimina i log più recenti fino alla data di cutoff.
        
        Args:
            cutoff_date: Data di cutoff (elimina log più recenti)
            project: Filtra per progetto
            
        Returns:
            Numero di log eliminati
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Costruisci la query
        query = "DELETE FROM logs WHERE timestamp >= ?"
        params = [cutoff_date.isoformat()]
        
        if project:
            query += " AND project = ?"
            params.append(project)
        
        # Esegui la query
        cursor.execute(query, params)
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"Reset completato: eliminati {deleted_count} log più recenti della data {cutoff_date.isoformat()}")
        return deleted_count
    
    def get_logs_count(
        self,
        project: Optional[LogProject] = None,
        level: Optional[LogLevel] = None,
        module: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Conta i log in base ai filtri specificati.
        
        Args:
            project: Filtra per progetto
            level: Filtra per livello di log
            module: Filtra per modulo
            start_date: Data di inizio per il filtro temporale
            end_date: Data di fine per il filtro temporale
            
        Returns:
            Numero di log che soddisfano i criteri di filtro
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Costruisci la query
        query = "SELECT COUNT(*) as count FROM logs WHERE 1=1"
        params = []
        
        if project:
            query += " AND project = ?"
            params.append(project)
        
        if level:
            query += " AND level = ?"
            params.append(level)
        
        if module:
            query += " AND module = ?"
            params.append(module)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        
        conn.close()
        return row["count"]
    
    def get_db_size(self) -> str:
        """
        Ottiene la dimensione del file del database.
        
        Returns:
            Dimensione del database in formato leggibile (es. "1.5 MB")
        """
        try:
            # Ottieni la dimensione del file in bytes
            size_bytes = os.path.getsize(self.db_path)
            
            # Converti in formato leggibile
            units = ["B", "KB", "MB", "GB"]
            unit_index = 0
            size = float(size_bytes)
            
            while size >= 1024 and unit_index < len(units) - 1:
                size /= 1024
                unit_index += 1
            
            return f"{size:.1f} {units[unit_index]}"
        except Exception as e:
            logger.error(f"Errore durante il calcolo della dimensione del database: {str(e)}")
            return "N/A"

    def compress_old_logs(self, days_threshold: int = 1) -> int:
        """
        Comprime i log più vecchi di una certa soglia di giorni.
        
        Args:
            days_threshold: Soglia in giorni
            
        Returns:
            Numero di log compressi
        """
        import zipfile
        import json
        import tempfile
        from datetime import datetime, timedelta
        
        conn = None
        try:
            # Calcola la data soglia
            threshold_date = (datetime.now() - timedelta(days=days_threshold)).isoformat()
            
            # Ottieni i log da comprimere
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Crea la tabella per i log compressi se non esiste
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS compressed_logs (
                log_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                archive_path TEXT NOT NULL,
                compressed_at TEXT NOT NULL
            )
            ''')
            conn.commit()

            query = "SELECT * FROM logs WHERE timestamp < ? AND NOT EXISTS (SELECT 1 FROM compressed_logs WHERE compressed_logs.log_id = logs.id)"
            cursor.execute(query, (threshold_date,))
            logs_to_compress = cursor.fetchall()
            
            if not logs_to_compress:
                conn.close()
                return 0
                
            # Crea directory archives se non esiste
            base_dir = os.path.dirname(os.path.dirname(__file__))
            archives_dir = os.path.join(base_dir, "logs", "archives")
            os.makedirs(archives_dir, exist_ok=True)
            
            # Nome archivio basato sulla data
            today = datetime.now().strftime("%Y-%m-%d")
            archive_path = os.path.join(archives_dir, f"logs_before_{today}.zip")
        
            
            # Crea un file temporaneo per memorizzare i log in formato JSON
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_file:
                logs_json = []
                for log in logs_to_compress:
                    log_dict = dict(log)
                    # Converti JSON in dizionari per i campi details e context
                    if log_dict["details"]:
                        log_dict["details"] = json.loads(log_dict["details"])
                    if log_dict["context"]:
                        log_dict["context"] = json.loads(log_dict["context"])
                    logs_json.append(log_dict)
                
                # Scrivi i log nel file temporaneo
                json.dump(logs_json, temp_file, indent=2)
                temp_file_path = temp_file.name
            
            # Comprimi il file in un archivio ZIP
            with zipfile.ZipFile(archive_path, 'a', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.write(temp_file_path, f"logs_{len(logs_to_compress)}_{today}.json")
            
            # Elimina il file temporaneo
            os.unlink(temp_file_path)
            
            # Registra i log come compressi
            compressed_at = datetime.now().isoformat()
            for log in logs_to_compress:
                try:
                    cursor.execute(
                        "INSERT INTO compressed_logs (log_id, timestamp, archive_path, compressed_at) VALUES (?, ?, ?, ?)",
                        (log["id"], log["timestamp"], archive_path, compressed_at)
                    )
                except sqlite3.IntegrityError:
                    # Ignora se il log è già stato compresso
                    pass

            # Elimina i log originali dalla tabella `logs` dopo che sono stati registrati in `compressed_logs`.
            try:
                log_ids = [log["id"] for log in logs_to_compress]
                # Usa una query parametrizzata con il numero corretto di placeholder
                placeholders = ",".join(["?" for _ in log_ids])
                delete_query = f"DELETE FROM logs WHERE id IN ({placeholders})"
                cursor.execute(delete_query, tuple(log_ids))
            except Exception as e:
                # Se la cancellazione fallisce, rollback e logga
                conn.rollback()
                logger.error(f"Errore durante l'eliminazione dei log originali dopo compressione: {str(e)}")
                try:
                    conn.close()
                except:
                    pass
                return 0

            conn.commit()
            conn.close()

            logger.info(f"Compressi {len(logs_to_compress)} log nell'archivio {archive_path} e rimossi dalla tabella logs")
            return len(logs_to_compress)
            
        except Exception as e:
            logger.error(f"Errore durante la compressione dei log: {str(e)}")
            # Assicurati che la connessione venga chiusa in caso di errore
            if conn:
                try:
                    conn.close()
                except:
                    pass  # Ignora errori durante la chiusura della connessione
            return 0
            
    def cleanup_compressed_logs(self, days_to_keep: int = 365) -> int:
        """
        Elimina gli archivi di log compressi più vecchi di un certo numero di giorni.
        
        Args:
            days_to_keep: Numero di giorni per cui mantenere gli archivi
            
        Returns:
            Numero di archivi eliminati
        """
        conn = None
        try:
            from datetime import datetime, timedelta
            
            # Calcola la data limite
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
            
            # Ottieni gli archivi da eliminare
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Verifica se la tabella esiste
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='compressed_logs'")
            if not cursor.fetchone():
                conn.close()
                return 0
                
            # Ottieni gli archivi da eliminare
            query = "SELECT DISTINCT archive_path FROM compressed_logs WHERE compressed_at < ?"
            cursor.execute(query, (cutoff_date,))
            archives_to_delete = [row["archive_path"] for row in cursor.fetchall()]
            
            if not archives_to_delete:
                conn.close()
                return 0
            
            # Elimina gli archivi
            deleted_count = 0
            for archive_path in archives_to_delete:
                try:
                    if os.path.exists(archive_path):
                        os.remove(archive_path)
                        deleted_count += 1
                    
                    # Elimina i riferimenti agli archivi dalla tabella
                    cursor.execute(
                        "DELETE FROM compressed_logs WHERE archive_path = ?",
                        (archive_path,)
                    )
                except Exception as e:
                    logger.error(f"Errore durante l'eliminazione dell'archivio {archive_path}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"Eliminati {deleted_count} archivi di log compressi")
            return deleted_count
        except Exception as e:
            logger.error(f"Errore durante la pulizia dei log compressi: {str(e)}")
            if conn:
                try:
                    if conn.in_transaction:
                        conn.rollback()
                    conn.close()
                except:
                    pass  # Ignora errori durante la chiusura della connessione
            return 0

    def run_maintenance(self):
        """
        Esegue operazioni di manutenzione sui log.
        
        - Comprime i log più vecchi di X giorni
        - Elimina i log più vecchi di Y giorni
        - Elimina gli archivi di log compressi più vecchi di Z giorni
        """
        from core.config import get_settings
        import traceback
        
        settings = get_settings()
        logger = logging.getLogger("LogManager")
        
        try:
            # Elimina i log vecchi (questa operazione è più sicura)
            logger.info("Avvio pulizia log vecchi...")
            deleted_logs = self.cleanup_logs(days_to_keep=settings.retention_days)
            logger.info(f"Completata pulizia dei log: {deleted_logs} log eliminati")
            
            # Operazioni che richiedono la tabella compressed_logs (più problematiche)
            if settings.enable_log_compression:
                logger.info("Verifica tabella compressed_logs...")
                # Verifica se la tabella compressed_logs esiste
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Verifica se la tabella esiste
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='compressed_logs'")
                if not cursor.fetchone():
                    logger.info("Tabella compressed_logs non trovata, creazione in corso...")
                    # Crea la tabella se non esiste
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS compressed_logs (
                        log_id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        archive_path TEXT NOT NULL,
                        compressed_at TEXT NOT NULL
                    )
                    ''')
                    conn.commit()
                    conn.close()
                    
                    # Log informativo sulla creazione della tabella
                    logger.info("Creata tabella compressed_logs con successo")
                else:
                    logger.info("Tabella compressed_logs trovata, proseguo con le operazioni")
                    conn.close()
                
                # Ora che la tabella esiste, possiamo procedere con le operazioni
                logger.info("Avvio compressione log vecchi...")
                compressed = self.compress_old_logs(days_threshold=settings.compress_logs_older_than_days)
                logger.info(f"Compressi {compressed} log vecchi")
                
                logger.info("Avvio pulizia archivi compressi vecchi...")
                deleted_archives = self.cleanup_compressed_logs(days_to_keep=settings.compressed_logs_retention_days)
                logger.info(f"Eliminati {deleted_archives} archivi compressi")
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"Errore durante la manutenzione dei log: {str(e)}")
            logger.debug(f"Dettaglio errore: {error_details}")
            # Prova a registrare l'errore nel database dei log
            try:
                from core.models import LogEntry, LogLevel, LogProject
                
                log_entry = LogEntry(
                    project=LogProject.OTHER,  # O un altro progetto appropriato
                    level=LogLevel.ERROR,
                    module="LogManager",
                    message=f"Errore durante la manutenzione dei log: {str(e)}",
                    details={"traceback": error_details}
                )
                self.add_log(log_entry)
            except Exception as log_error:
                # Se fallisce, logga l'errore ma continua
                logger.error(f"Impossibile salvare il log dell'errore: {str(log_error)}")