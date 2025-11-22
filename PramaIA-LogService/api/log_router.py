"""
Router per le API di logging.
Definisce gli endpoint per l'invio e la gestione dei log.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import json

from core.models import LogEntry, LogLevel, LogProject
from core.log_manager import LogManager
from core.auth import get_api_key

router = APIRouter()
log_manager = LogManager()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_log(
    log_entry: LogEntry = Body(...),
    api_key: str = Depends(get_api_key)
):
    """
    Crea una nuova voce di log.
    
    Richiede un API key valido per l'autenticazione.
    """
    log_id = log_manager.add_log(log_entry)
    return {"id": log_id, "message": "Log registrato con successo"}

@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def create_logs_batch(
    log_entries: List[LogEntry] = Body(...),
    api_key: str = Depends(get_api_key)
):
    """
    Crea multiple voci di log in un'unica richiesta.
    
    Utile per l'invio di log in batch in caso di connessione intermittente.
    Richiede un API key valido per l'autenticazione.
    """
    log_ids = log_manager.add_logs_batch(log_entries)
    return {"ids": log_ids, "count": len(log_ids), "message": "Logs registrati con successo"}

@router.get("/", response_model=List[Dict[str, Any]])
async def get_logs(
    project: Optional[LogProject] = None,
    level: Optional[LogLevel] = None,
    module: Optional[str] = None,
    document_id: Optional[str] = None,
    file_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    limit: int = 100,
    offset: int = 0,
    api_key: str = Depends(get_api_key)
):
    """
    Recupera le voci di log in base ai filtri specificati.
    
    Richiede un API key valido per l'autenticazione.
    
    Parametri:
    - project: Filtra per progetto
    - level: Filtra per livello di log
    - module: Filtra per modulo
    - document_id: Filtra per ID del documento
    - file_name: Filtra per nome del file
    - start_date: Data di inizio per il filtro temporale
    - end_date: Data di fine per il filtro temporale
    - sort_by: Campo per ordinare i risultati (timestamp, level, project, module, message)
    - sort_order: Ordine di ordinamento (asc, desc)
    - limit: Numero massimo di log da restituire
    - offset: Offset per la paginazione
    """
    logs = log_manager.get_logs(
        project=project,
        level=level,
        module=module,
        document_id=document_id,
        file_name=file_name,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )
    return logs

@router.get("/{log_id}", response_model=Dict[str, Any])
async def get_log_by_id(
    log_id: str,
    api_key: str = Depends(get_api_key)
):
    """
    Recupera una voce di log specifica in base all'ID.
    
    Richiede un API key valido per l'autenticazione.
    """
    # Aggiungiamo il metodo get_log_by_id al LogManager
    conn = log_manager._get_connection()
    cursor = conn.cursor()
    
    # Esegui la query per trovare il log con l'ID specificato
    cursor.execute("SELECT * FROM logs WHERE id = ?", (log_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log con ID {log_id} non trovato"
        )
    
    # Converti in dizionario
    log_dict = dict(row)
    
    # Converti JSON in dizionari con gestione degli errori
    if log_dict["details"]:
        try:
            log_dict["details"] = json.loads(log_dict["details"])
        except Exception as e:
            import logging
            logging.error(f"Errore durante il parsing JSON dei dettagli per il log {log_id}: {str(e)}")
            # Invece di avere valori undefined, manteniamo almeno i dati originali
            log_dict["details"] = {"error": "Formato JSON non valido", "raw_data": log_dict["details"]}
    
    if log_dict["context"]:
        try:
            log_dict["context"] = json.loads(log_dict["context"])
        except Exception as e:
            import logging
            logging.error(f"Errore durante il parsing JSON del contesto per il log {log_id}: {str(e)}")
            log_dict["context"] = {"error": "Formato JSON non valido", "raw_data": log_dict["context"]}
    
    conn.close()
    return log_dict

@router.get("/stats")
async def get_log_stats(
    project: Optional[LogProject] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    api_key: str = Depends(get_api_key)
):
    """
    Recupera statistiche sui log.
    
    Richiede un API key valido per l'autenticazione.
    """
    stats = log_manager.get_stats(
        project=project,
        start_date=start_date,
        end_date=end_date
    )
    return stats

@router.delete("/cleanup")
async def cleanup_logs(
    days_to_keep: int = 30,
    project: Optional[LogProject] = None,
    level: Optional[LogLevel] = None,
    api_key: str = Depends(get_api_key),
    body: Optional[Dict[str, Any]] = Body(None)
):
    """
    Pulisce i log più vecchi di un certo numero di giorni.
    
    Richiede un API key valido per l'autenticazione.
    """
    # Se il client ha inviato un body JSON (es. fetch DELETE con JSON), usalo per sovrascrivere i parametri
    if body:
        try:
            if 'days_to_keep' in body:
                days_to_keep = int(body.get('days_to_keep', days_to_keep))
            if 'project' in body and body.get('project'):
                project = LogProject(body.get('project'))
            if 'level' in body and body.get('level'):
                level = LogLevel(body.get('level'))
        except Exception:
            # Se il parsing fallisce, mantieni i valori predefiniti e continua
            pass

    deleted_count = log_manager.cleanup_logs(
        days_to_keep=days_to_keep,
        project=project,
        level=level
    )
    return {"deleted_count": deleted_count, "message": f"Eliminati {deleted_count} log"}


@router.delete("/reset", status_code=status.HTTP_200_OK)
async def reset_logs(
    days: int = 1,
    project: Optional[LogProject] = None,
    api_key: str = Depends(get_api_key),
    body: Optional[Dict[str, Any]] = Body(None)
):
    """
    Resetta (elimina) i log più recenti fino al numero di giorni specificato.
    
    Richiede un API key valido per l'autenticazione.
    """
    from datetime import datetime, timedelta
    
    # Se il client ha inviato il body JSON, usa i valori forniti
    if body and 'days' in body:
        try:
            days = int(body.get('days', days))
        except Exception:
            pass

    # Calcola la data di cutoff
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Utilizza il log manager per eliminare i log
    deleted_count = log_manager.reset_logs(
        cutoff_date=cutoff_date,
        project=project
    )
    
    return {
        "deleted_count": deleted_count,
        "message": f"Eliminati {deleted_count} log degli ultimi {days} giorni"
    }


@router.delete("/cleanup/unarchived", status_code=status.HTTP_200_OK)
async def cleanup_unarchived(
    api_key: str = Depends(get_api_key),
    body: Optional[Dict[str, Any]] = Body(None)
):
    """
    Elimina tutti i log che NON sono stati archiviati (non presenti nella tabella compressed_logs).

    Richiede un'API key valida.
    """
    conn = log_manager._get_connection()
    cursor = conn.cursor()

    # Verifica se la tabella compressed_logs esiste
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='compressed_logs'")
    if not cursor.fetchone():
        # Se non esiste, allora non ci sono log archiviati: cancella tutto
        try:
            cursor.execute("DELETE FROM logs")
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            return {"deleted_count": deleted_count, "message": f"Eliminati {deleted_count} log (nessun archivio trovato)"}
        except Exception as e:
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # Se la tabella esiste, elimina i log il cui id non è presente in compressed_logs
    try:
        cursor.execute("DELETE FROM logs WHERE id NOT IN (SELECT log_id FROM compressed_logs)")
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        return {"deleted_count": deleted_count, "message": f"Eliminati {deleted_count} log non archiviati"}
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/cleanup/all", status_code=status.HTTP_200_OK)
async def cleanup_all(
    api_key: str = Depends(get_api_key),
    body: Optional[Dict[str, Any]] = Body(None)
):
    """
    Elimina TUTTI i log e gli archivi associati (rimuove le righe in `logs`, i riferimenti in `compressed_logs` e i file zip su disco).

    Richiede un'API key valida. Operazione distruttiva: eseguire backup prima di chiamarla.
    """
    conn = log_manager._get_connection()
    cursor = conn.cursor()

    try:
        # Recupera la lista di archive_path presenti (se la tabella esiste)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='compressed_logs'")
        archives = []
        if cursor.fetchone():
            cursor.execute("SELECT DISTINCT archive_path FROM compressed_logs")
            archives = [row[0] for row in cursor.fetchall() if row[0]]

        # Inizia transazione
        # 1) elimina riferimenti da compressed_logs
        try:
            cursor.execute("DELETE FROM compressed_logs")
        except Exception:
            # Se la tabella non esiste, ignora
            pass

        # 2) elimina tutti i logs
        cursor.execute("DELETE FROM logs")
        deleted_logs = cursor.rowcount

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # Rimuovi i file di archivio dal filesystem (fuori dalla transazione DB)
    removed_archives = 0
    for path in archives:
        try:
            import os
            if path and os.path.exists(path):
                os.remove(path)
                removed_archives += 1
        except Exception:
            # Ignora errori nell'eliminazione dei singoli file ma continua
            pass

    conn.close()
    return {"deleted_logs": deleted_logs, "deleted_compressed": len(archives), "removed_archives": removed_archives}
