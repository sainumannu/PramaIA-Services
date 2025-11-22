"""
Processore per il nodo File Input nel core-input-plugin
"""
import os

async def process(inputs, config):
    """
    Questo processore gestisce l'input di file in modo asincrono.
    
    In un'implementazione reale, questo bloccherebbe l'esecuzione fino
    a quando l'utente non carica un file tramite l'interfaccia utente.
    
    Args:
        inputs: Dict vuoto (questo nodo non ha input)
        config: Dict con la configurazione del nodo
            - allowed_extensions: Lista di estensioni permesse
            - max_size_mb: Dimensione massima del file in MB
    
    Returns:
        Dict con l'output del nodo:
            - content: Contenuto testuale del file
            - binary: Contenuto binario del file
            - metadata: Metadati del file
    """
    # Logging: inizio processo input file
    logger = None
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"[FileInputProcessor] Avvio process con config: {config}")
    except Exception:
        pass

    # Nella versione attuale, questo è un segnaposto.
    # In un workflow reale, il frontend gestirebbe il caricamento del file
    # e bloccherebbe l'esecuzione fino a quando l'utente non carica un file.

    # Valida la configurazione
    allowed_extensions = config.get("allowed_extensions", [])
    max_size_mb = config.get("max_size_mb", 10)
    if not allowed_extensions and logger:
        try:
            logger.warning("[FileInputProcessor] allowed_extensions non specificato, nessun filtro applicato.")
        except Exception:
            pass

    # Dati di esempio per la simulazione
    sample_filename = "example.txt"
    sample_content = "Questo è un esempio di contenuto di file."
    sample_binary = sample_content.encode('utf-8')

    sample_metadata = {
        "filename": sample_filename,
        "size": len(sample_binary),
        "content_type": "text/plain",
        "extension": os.path.splitext(sample_filename)[1]
    }

    if logger:
        try:
            logger.info(f"[FileInputProcessor] File simulato: {sample_metadata}")
        except Exception:
            pass

    return {
        "content": sample_content,
        "binary": sample_binary,
        "metadata": sample_metadata
    }
