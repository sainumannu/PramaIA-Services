"""
Esempio di utilizzo del client Python per PramaIA-LogService.
"""

import time
import random
import traceback
import os
from pramaialog import PramaIALogger, LogLevel, LogProject

def simulate_workflow_execution():
    """Simula l'esecuzione di un workflow con vari livelli di log."""
    
    # Crea un'istanza del logger
    # Risolvi host dal .env / variabili d'ambiente se presenti
    resolved_host = os.getenv('PRAMAIALOG_HOST') or os.getenv('BACKEND_URL') or 'http://localhost:8081'
    port_env = os.getenv('PRAMAIALOG_PORT')
    if port_env and ':' not in resolved_host.split('//')[-1]:
        resolved_host = f"{resolved_host.rstrip('/')}:{port_env}"

    logger = PramaIALogger(
        api_key="pramaiaserver_api_key_123456",
        project=LogProject.SERVER,
        module="workflow_execution_service",
        host=resolved_host
    )
    
    # Simula l'avvio di un workflow
    workflow_id = f"wf-{random.randint(1000, 9999)}"
    logger.info(
        f"Avvio workflow {workflow_id}",
        context={"workflow_id": workflow_id, "user_id": "admin"}
    )
    
    # Simula alcuni log di debug durante l'esecuzione
    logger.debug(
        "Caricamento configurazione workflow",
        details={"config_file": f"/workflows/{workflow_id}/config.json"},
        context={"workflow_id": workflow_id}
    )
    
    time.sleep(1)  # Simula un po' di elaborazione
    
    # Simula un warning
    if random.random() < 0.7:
        logger.warning(
            "Configurazione non ottimale rilevata nel workflow",
            details={"issue": "memory_allocation", "recommended": "Aumentare l'allocazione di memoria"},
            context={"workflow_id": workflow_id}
        )
    
    time.sleep(1)  # Altra elaborazione
    
    # Simula occasionalmente un errore
    if random.random() < 0.3:
        try:
            # Simula un'eccezione
            raise ValueError("Errore durante l'elaborazione del nodo di input")
        except Exception as e:
            stack_trace = traceback.format_exc()
            logger.error(
                f"Errore durante l'esecuzione del workflow {workflow_id}",
                details={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "stack_trace": stack_trace
                },
                context={"workflow_id": workflow_id}
            )
            
            # Log critico per errori gravi
            if random.random() < 0.5:
                logger.critical(
                    "Workflow terminato con errore critico",
                    details={"error_type": "ExecutionFailure", "node_id": "input-node-1"},
                    context={"workflow_id": workflow_id}
                )
                return False
    
    # Log di completamento
    logger.info(
        f"Workflow {workflow_id} completato con successo",
        details={"execution_time": f"{random.randint(2, 10)} secondi"},
        context={"workflow_id": workflow_id}
    )
    
    # Assicurati che tutti i log vengano inviati
    logger.flush()
    return True

if __name__ == "__main__":
    print("Simulazione di esecuzione workflow con logging...")
    
    # Esegui diverse simulazioni
    for i in range(5):
        print(f"\nEsecuzione workflow {i+1}/5...")
        result = simulate_workflow_execution()
        print(f"Workflow completato {'con successo' if result else 'con errori'}")
        time.sleep(2)
    
    print("\nSimulazione completata. Controlla il servizio di logging per vedere i log generati.")
