"""
Gestione dell'autenticazione per il servizio di logging.
"""

from fastapi import Depends, HTTPException, status, Security
from fastapi.security.api_key import APIKeyHeader
from typing import Dict, Optional, Any, List
import os
import json
import logging
from datetime import datetime, timedelta

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
API_KEYS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "api_keys.json")

logger = logging.getLogger(__name__)

# Carica le API key dal file di configurazione
def load_api_keys() -> Dict[str, Dict]:
    """Carica le API key dal file di configurazione."""
    if not os.path.exists(API_KEYS_FILE):
        # Crea un file di configurazione di default se non esiste
        default_keys = {
            "server_key": {
                "name": "PramaIAServer",
                "key": "pramaiaserver_api_key_123456",
                "projects": ["PramaIAServer"],
                "expiry": None
            },
            "pdk_key": {
                "name": "PramaIA-PDK",
                "key": "pramaiapdk_api_key_123456",
                "projects": ["PramaIA-PDK"],
                "expiry": None
            },
            "agents_key": {
                "name": "PramaIA-Agents",
                "key": "pramaiaagents_api_key_123456",
                "projects": ["PramaIA-Agents"],
                "expiry": None
            },
            "admin_key": {
                "name": "Admin",
                "key": "pramaiaadmin_api_key_123456",
                "projects": ["PramaIAServer", "PramaIA-PDK", "PramaIA-Agents", "PramaIA-Plugins", "other"],
                "expiry": None
            }
        }
        
        # Assicurati che la directory config esista
        os.makedirs(os.path.dirname(API_KEYS_FILE), exist_ok=True)
        
        with open(API_KEYS_FILE, "w") as f:
            json.dump(default_keys, f, indent=4)
        
        return default_keys
    
    try:
        with open(API_KEYS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Errore nel parsing del file JSON delle API keys: {str(e)}")
        # Ritorna un dizionario vuoto in caso di errore
        return {}
    except Exception as e:
        logger.error(f"Errore durante il caricamento del file delle API keys: {str(e)}")
        return {}

def get_api_key_info(api_key: str) -> Optional[Dict]:
    """Verifica e restituisce le informazioni sull'API key."""
    api_keys = load_api_keys()
    
    # Primo tentativo: cerca direttamente la chiave
    for key_id, key_info in api_keys.items():
        if isinstance(key_info, dict):
            if key_info.get("key") == api_key:
                # Verifica se la chiave è scaduta
                if key_info.get("expiry"):
                    try:
                        expiry_date = datetime.fromisoformat(key_info["expiry"])
                        if datetime.now() > expiry_date:
                            logger.debug(f"API key scaduta: {mask_api_key(api_key)}")
                            return None
                    except ValueError as e:
                        logger.warning(f"Formato data di scadenza non valido: {key_info['expiry']}, errore: {str(e)}")
                
                return key_info
        elif isinstance(key_info, str) and key_info == api_key:  # Formato legacy
            # Converti al nuovo formato
            new_key_info = {
                "name": key_id,
                "key": key_info,
                "projects": [key_id],
                "expiry": None
            }
            return new_key_info
    
    # Secondo tentativo: controlla se è una chiave nel formato di sviluppo (pramaialog_pdk_dev_key_12345)
    if api_key.startswith("pramaialog_") and "_dev_key_" in api_key:
        parts = api_key.split("_")
        if len(parts) >= 4:
            project = parts[1].upper()
            if project == "PDK":
                return {
                    "name": f"PramaIA-PDK Dev Key",
                    "key": api_key,
                    "projects": ["PramaIA-PDK"],
                    "expiry": None,
                    "dev": True
                }
    
    logger.debug(f"API key non trovata: {mask_api_key(api_key)}")
    return None

async def get_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """
    Dipendenza per verificare l'API key nelle richieste.
    
    Solleva un'eccezione HTTPException se l'API key è mancante o non valida.
    """
    if not api_key:
        logger.warning("Tentativo di accesso senza API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key mancante"
        )
    
    key_info = get_api_key_info(api_key)
    if not key_info:
        logger.warning(f"Tentativo di accesso con API key non valida: {mask_api_key(api_key)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key non valida o scaduta"
        )
    
    return api_key

def create_api_key(name: str, projects: List[str], expiry_days: Optional[int] = None) -> Dict[str, Any]:
    """
    Crea una nuova API key.
    
    Args:
        name: Nome dell'API key (di solito il nome del progetto o del client)
        projects: Lista dei progetti a cui l'API key ha accesso
        expiry_days: Giorni di validità della chiave (None per chiave senza scadenza)
        
    Returns:
        Dizionario con le informazioni sulla nuova API key
    """
    import uuid
    import string
    import random
    
    # Genera una chiave casuale
    key = f"pramaialog_{''.join(random.choices(string.ascii_lowercase + string.digits, k=16))}"
    
    # Calcola la data di scadenza se richiesta
    expiry = None
    if expiry_days:
        expiry = (datetime.now() + timedelta(days=expiry_days)).isoformat()
    
    # Crea le informazioni sulla chiave
    key_id = str(uuid.uuid4())
    key_info = {
        "name": name,
        "key": key,
        "projects": projects,
        "expiry": expiry,
        "created": datetime.now().isoformat()
    }
    
    # Salva la chiave
    api_keys = load_api_keys()
    api_keys[key_id] = key_info
    
    try:
        with open(API_KEYS_FILE, "w") as f:
            json.dump(api_keys, f, indent=4)
        logger.info(f"Creata nuova API key con nome: {name}, ID: {key_id}")
    except Exception as e:
        logger.error(f"Errore durante il salvataggio della nuova API key: {str(e)}")
    
    return key_info

def mask_api_key(api_key: str) -> str:
    """Maschera una API key per la visualizzazione nei log."""
    if not api_key:
        return "N/A"
    
    if len(api_key) <= 8:
        return f"{api_key[:2]}{'*' * (len(api_key) - 2)}"
    
    return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"