"""
Router per il tracciamento del ciclo di vita dei documenti.
Definisce gli endpoint per filtrare e visualizzare i log relativi al ciclo di vita di documenti specifici.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from core.models import LogLevel, LogProject
from core.log_manager import LogManager
from core.auth import get_api_key

router = APIRouter()
log_manager = LogManager()

@router.get("/document/{document_id}", response_model=List[Dict[str, Any]])
async def get_document_lifecycle(
    document_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    level: Optional[str] = None,  # Aggiunto parametro per filtrare per livello di log
    limit: int = 100,
    offset: int = 0,
    api_key: str = Depends(get_api_key)
):
    """
    Recupera tutti i log del ciclo di vita relativi a un documento specifico.
    
    Il documento viene identificato tramite document_id.
    Può essere filtrato per livello di log (es. lifecycle, error, info, ecc.)
    """
    # Se non è specificata una data di inizio, usa gli ultimi 30 giorni
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    
    # Se non è specificata una data di fine, usa la data attuale
    if not end_date:
        end_date = datetime.now()
    
    # Connessione al database
    conn = log_manager._get_connection()
    cursor = conn.cursor()
    
    try:
        # Costruisci la query di base
        query_parts = [
            "SELECT * FROM logs",
            "WHERE (",
            "   -- Cerca nei log che hanno il campo document_id nel JSON dei dettagli",
            "   (details LIKE ? OR details LIKE ?)",
            "   -- O che hanno file_hash nei dettagli (per documenti rinominati)",
            "   OR (details LIKE ?)",
            ")",
            "AND timestamp BETWEEN ? AND ?"
        ]
        
        # Parametri base per la query
        params = [
            f'%"document_id":"{document_id}"%',  # Cerca document_id come stringa
            f'%"document_id":{document_id}%',    # Cerca document_id come numero
            f'%"file_hash":"{document_id}"%',    # Cerca il document_id come file_hash
            start_date.isoformat(),
            end_date.isoformat()
        ]
        
        # Aggiungi filtro per livello di log se specificato
        if level and level != "all":
            query_parts.append("AND level = ?")
            params.append(level)
            
        # Completa la query
        query_parts.extend([
            "ORDER BY timestamp ASC",
            "LIMIT ? OFFSET ?"
        ])
        
        # Aggiungi parametri per limit e offset
        params.append(str(limit))
        params.append(str(offset))
        
        # Componi la query finale
        query = "\n".join(query_parts)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Converti righe in dizionari
        logs = []
        for row in rows:
            log_dict = dict(row)
            
            # Parse JSON fields
            try:
                if log_dict["details"]:
                    log_dict["details"] = json.loads(log_dict["details"])
            except Exception:
                log_dict["details"] = {"error": "Invalid JSON", "raw": log_dict["details"]}
                
            try:
                if log_dict["context"]:
                    log_dict["context"] = json.loads(log_dict["context"])
            except Exception:
                log_dict["context"] = {"error": "Invalid JSON", "raw": log_dict["context"]}
                
            logs.append(log_dict)
            
        return logs
    
    finally:
        conn.close()

@router.get("/file/{file_name}", response_model=List[Dict[str, Any]])
async def get_file_lifecycle(
    file_name: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    level: Optional[str] = None,  # Aggiunto parametro per filtrare per livello di log
    limit: int = 100,
    offset: int = 0,
    api_key: str = Depends(get_api_key)
):
    """
    Recupera tutti i log del ciclo di vita relativi a un file specifico.
    
    Il file viene identificato tramite nome file.
    Può essere filtrato per livello di log (es. lifecycle, error, info, ecc.)
    """
    # Se non è specificata una data di inizio, usa gli ultimi 30 giorni
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    
    # Se non è specificata una data di fine, usa la data attuale
    if not end_date:
        end_date = datetime.now()
    
    # Connessione al database
    conn = log_manager._get_connection()
    cursor = conn.cursor()
    
    try:
        # Costruisci la query di base
        query_parts = [
            "SELECT * FROM logs",
            "WHERE (",
            "   -- Cerca nei log che hanno il campo file_name nel JSON dei dettagli",
            "   details LIKE ?",
            "   -- O che contengono il nome file nel messaggio",
            "   OR message LIKE ?",
            ")",
            "AND timestamp BETWEEN ? AND ?"
        ]
        
        # Parametri base per la query
        params = [
            f'%"file_name":"{file_name}"%',  # Cerca file_name nei dettagli
            f'%{file_name}%',                # Cerca il nome file nel messaggio
            start_date.isoformat(),
            end_date.isoformat()
        ]
        
        # Aggiungi filtro per livello di log se specificato
        if level and level != "all":
            query_parts.append("AND level = ?")
            params.append(level)
            
        # Completa la query
        query_parts.extend([
            "ORDER BY timestamp ASC",
            "LIMIT ? OFFSET ?"
        ])
        
        # Aggiungi parametri per limit e offset
        params.append(str(limit))
        params.append(str(offset))
        
        # Componi la query finale
        query = "\n".join(query_parts)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Converti righe in dizionari
        logs = []
        for row in rows:
            log_dict = dict(row)
            
            # Parse JSON fields
            try:
                if log_dict["details"]:
                    log_dict["details"] = json.loads(log_dict["details"])
            except Exception:
                log_dict["details"] = {"error": "Invalid JSON", "raw": log_dict["details"]}
                
            try:
                if log_dict["context"]:
                    log_dict["context"] = json.loads(log_dict["context"])
            except Exception:
                log_dict["context"] = {"error": "Invalid JSON", "raw": log_dict["context"]}
                
            logs.append(log_dict)
            
        return logs
    
    finally:
        conn.close()

@router.get("/hash/{file_hash}", response_model=List[Dict[str, Any]])
async def get_lifecycle_by_hash(
    file_hash: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    level: Optional[str] = None,  # Aggiunto parametro per filtrare per livello di log
    limit: int = 100,
    offset: int = 0,
    api_key: str = Depends(get_api_key)
):
    """
    Recupera tutti i log del ciclo di vita relativi a un file specifico tramite il suo hash.
    
    Utile per tracciare documenti che sono stati rinominati.
    Può essere filtrato per livello di log (es. lifecycle, error, info, ecc.)
    """
    # Se non è specificata una data di inizio, usa gli ultimi 30 giorni
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    
    # Se non è specificata una data di fine, usa la data attuale
    if not end_date:
        end_date = datetime.now()
    
    # Connessione al database
    conn = log_manager._get_connection()
    cursor = conn.cursor()
    
    try:
        # Costruisci la query di base
        query_parts = [
            "SELECT * FROM logs",
            "WHERE details LIKE ?",
            "AND timestamp BETWEEN ? AND ?"
        ]
        
        # Parametri base per la query
        params = [
            f'%"file_hash":"{file_hash}"%',  # Cerca file_hash nei dettagli
            start_date.isoformat(),
            end_date.isoformat()
        ]
        
        # Aggiungi filtro per livello di log se specificato
        if level and level != "all":
            query_parts.append("AND level = ?")
            params.append(level)
            
        # Completa la query
        query_parts.extend([
            "ORDER BY timestamp ASC",
            "LIMIT ? OFFSET ?"
        ])
        
        # Aggiungi parametri per limit e offset
        params.append(str(limit))
        params.append(str(offset))
        
        # Componi la query finale
        query = "\n".join(query_parts)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Converti righe in dizionari
        logs = []
        for row in rows:
            log_dict = dict(row)
            
            # Parse JSON fields
            try:
                if log_dict["details"]:
                    log_dict["details"] = json.loads(log_dict["details"])
            except Exception:
                log_dict["details"] = {"error": "Invalid JSON", "raw": log_dict["details"]}
                
            try:
                if log_dict["context"]:
                    log_dict["context"] = json.loads(log_dict["context"])
            except Exception:
                log_dict["context"] = {"error": "Invalid JSON", "raw": log_dict["context"]}
                
            logs.append(log_dict)
            
        return logs
    
    finally:
        conn.close()