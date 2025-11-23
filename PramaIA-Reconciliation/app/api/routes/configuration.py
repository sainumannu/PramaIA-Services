"""
Endpoint di configurazione dinamica per ReconciliationService scheduler.
"""

import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
import json
import os
from datetime import datetime, time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config")

class SchedulerDailyConfig(BaseModel):
    """Configurazione scheduler giornaliero."""
    enabled: bool = Field(default=True, description="Abilita scheduler giornaliero")
    hour: int = Field(default=2, ge=0, le=23, description="Ora di esecuzione (0-23)")
    minute: int = Field(default=0, ge=0, le=59, description="Minuti di esecuzione (0-59)")

class SchedulerPeriodicConfig(BaseModel):
    """Configurazione scheduler periodico."""
    enabled: bool = Field(default=False, description="Abilita scheduler periodico")
    interval_minutes: int = Field(default=60, ge=1, le=1440, description="Intervallo in minuti (1-1440)")

class SchedulerConfig(BaseModel):
    """Configurazione completa dello scheduler."""
    daily: SchedulerDailyConfig = SchedulerDailyConfig()
    periodic: SchedulerPeriodicConfig = SchedulerPeriodicConfig()

class SchedulerResponse(BaseModel):
    """Modello per la risposta di configurazione scheduler."""
    success: bool
    message: str
    config: SchedulerConfig
    next_execution: Optional[str] = None

@router.post("/schedule", response_model=SchedulerResponse)
async def update_scheduler_configuration(config: SchedulerConfig):
    """
    Aggiorna la configurazione dello scheduler di riconciliazione.
    
    Args:
        config: Nuova configurazione dello scheduler
        
    Returns:
        SchedulerResponse: Risultato dell'aggiornamento
    """
    try:
        logger.info(f"Aggiornamento configurazione scheduler: {config.dict()}")
        
        # Percorso del file di configurazione
        config_file = os.path.join(os.getcwd(), "config", "scheduler_config.json")
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        # Salva la configurazione
        config_data = config.dict()
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        logger.info(f"Configurazione scheduler salvata in: {config_file}")
        
        # TODO: Riapplica la configurazione al scheduler in esecuzione
        # Questo richiede l'accesso all'istanza del scheduler
        
        # Calcola prossima esecuzione se scheduler giornaliero abilitato
        next_execution = None
        if config.daily.enabled:
            next_execution = calculate_next_daily_execution(config.daily)
        
        return SchedulerResponse(
            success=True,
            message="Configurazione scheduler aggiornata con successo. Riavvio del servizio consigliato.",
            config=config,
            next_execution=next_execution
        )
        
    except Exception as e:
        logger.error(f"Errore aggiornamento configurazione scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore interno durante l'aggiornamento della configurazione scheduler: {str(e)}"
        )

@router.get("/schedule", response_model=SchedulerConfig)
async def get_scheduler_configuration():
    """
    Ottiene la configurazione corrente dello scheduler.
    
    Returns:
        SchedulerConfig: Configurazione corrente
    """
    try:
        # Configurazione da file
        config_file = os.path.join(os.getcwd(), "config", "scheduler_config.json")
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    return SchedulerConfig(**config_data)
            except Exception as e:
                logger.warning(f"Errore lettura configurazione scheduler: {e}")
        
        # Configurazione di default se il file non esiste
        logger.info("Utilizzo configurazione scheduler di default")
        return SchedulerConfig()
        
    except Exception as e:
        logger.error(f"Errore lettura configurazione scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore interno durante la lettura della configurazione scheduler: {str(e)}"
        )

@router.get("/schedule/status")
async def get_scheduler_status():
    """
    Ottiene lo stato corrente dello scheduler.
    
    Returns:
        Dict: Stato dello scheduler
    """
    try:
        # TODO: Implementare il check dello stato reale dello scheduler
        # Per ora restituiamo informazioni di base
        
        config = await get_scheduler_configuration()
        
        status_info = {
            "scheduler_running": True,  # TODO: Check reale
            "daily_scheduler": {
                "enabled": config.daily.enabled,
                "next_run": calculate_next_daily_execution(config.daily) if config.daily.enabled else None
            },
            "periodic_scheduler": {
                "enabled": config.periodic.enabled,
                "interval_minutes": config.periodic.interval_minutes if config.periodic.enabled else None
            },
            "last_execution": None,  # TODO: Tracciare ultima esecuzione
            "uptime": "N/A"  # TODO: Calcolare uptime
        }
        
        return status_info
        
    except Exception as e:
        logger.error(f"Errore lettura stato scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore interno durante la lettura dello stato scheduler: {str(e)}"
        )

@router.post("/schedule/restart")
async def restart_scheduler():
    """
    Riavvia lo scheduler per applicare le nuove configurazioni.
    
    Returns:
        Dict: Stato del riavvio
    """
    try:
        logger.info("Riavvio dello scheduler richiesto")
        
        # TODO: Implementare riavvio del solo scheduler senza fermare tutto il servizio
        
        return {
            "success": True,
            "message": "Riavvio dello scheduler richiesto. Implementare meccanismo di riavvio scheduler.",
            "restart_required": True
        }
        
    except Exception as e:
        logger.error(f"Errore riavvio scheduler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore interno durante il riavvio scheduler: {str(e)}"
        )

def calculate_next_daily_execution(daily_config: SchedulerDailyConfig) -> str:
    """
    Calcola la prossima esecuzione dello scheduler giornaliero.
    
    Args:
        daily_config: Configurazione scheduler giornaliero
        
    Returns:
        str: Timestamp della prossima esecuzione
    """
    try:
        from datetime import datetime, time, timedelta
        
        now = datetime.now()
        scheduled_time = time(daily_config.hour, daily_config.minute)
        
        # Prossima esecuzione oggi se ancora non è passata l'ora
        next_execution = datetime.combine(now.date(), scheduled_time)
        
        # Se l'ora è già passata oggi, programma per domani
        if next_execution <= now:
            next_execution = next_execution + timedelta(days=1)
        
        return next_execution.isoformat()
        
    except Exception as e:
        logger.error(f"Errore calcolo prossima esecuzione: {e}")
        return "N/A"