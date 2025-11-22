"""
Processore per il nodo User Input nel core-input-plugin
"""

async def process(inputs, config):
    """
    Questo processore gestisce l'input dell'utente in modo asincrono.
    
    In un'implementazione reale, questo bloccherebbe l'esecuzione fino
    a quando l'utente non fornisce l'input tramite l'interfaccia utente.
    
    Args:
        inputs: Dict vuoto (questo nodo non ha input)
        config: Dict con la configurazione del nodo
            - prompt: Testo da mostrare all'utente
            - placeholder: Testo di esempio
    
    Returns:
        Dict con l'output del nodo
    """
    # Logging: inizio processo input utente
    logger = None
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"[UserInputProcessor] Avvio process con config: {config}")
    except Exception:
        pass

    # Nella versione attuale, questo è un segnaposto.
    # In un workflow reale, il frontend gestirebbe l'interazione con l'utente
    # e bloccherebbe l'esecuzione fino a quando l'utente non fornisce l'input.

    # Valida la configurazione
    prompt = config.get("prompt", "Inserisci il tuo testo qui:")
    if not prompt and logger:
        try:
            logger.warning("[UserInputProcessor] Prompt non fornito nella configurazione.")
        except Exception:
            pass

    # Questo valore dovrebbe essere fornito dall'utente durante l'esecuzione
    # Per ora restituiamo un valore di esempio
    user_input = "Questo è un esempio di input utente."

    if logger:
        try:
            logger.info(f"[UserInputProcessor] Input utente simulato: {user_input}")
        except Exception:
            pass

    return {
        "output": user_input
    }
