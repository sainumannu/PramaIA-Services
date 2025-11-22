# Guida ai Workflow e agli Event Source in PramaIA PDK

Questa sezione della documentazione fornisce informazioni dettagliate su come creare, gestire e automatizzare i workflow utilizzando gli event source in PramaIA PDK.

## Indice dei Documenti

### 1. Workflow e Pipeline di Elaborazione

- [**Guida alla Creazione e Gestione di Workflow**](WORKFLOW_CREATION_GUIDE.md)  
  Istruzioni dettagliate su come creare template di workflow, importarli nel database e collegarli con i trigger degli eventi.

- [**Tutorial: Creazione e Configurazione di un Workflow**](WORKFLOW_TUTORIAL.md)  
  Tutorial pratico passo-passo che mostra come creare, importare e configurare un workflow completo.

### 2. Event Source e Automazione

- [**Documentazione Event Sources PDK**](PDK-EVENT-SOURCES-DOCUMENTATION.md)  
  Panoramica completa degli event source disponibili, come configurarli e integrarli con i workflow.

### 3. Script di Utilità

I seguenti script sono disponibili nella directory principale per aiutarti a gestire workflow ed event source:

- **insert_optimized_workflows.py**  
  Importa workflow ottimizzati nel database.

- **insert_workflows_simple.py**  
  Importa workflow semplici nel database.

- **setup_pdf_monitor_triggers.py**  
  Configura i trigger per il monitoraggio dei file PDF (aggiunta, modifica, eliminazione).

- **setup_metadata_triggers.py**  
  Script di esempio che accompagna il tutorial per configurare i trigger per l'analisi dei metadati PDF.

## Architettura del Sistema

Il sistema di workflow di PramaIA PDK è composto da diversi componenti chiave:

1. **Template di Workflow** (file JSON)  
   Definiscono la struttura e il comportamento dei workflow.

2. **Database**  
   Memorizza i workflow importati, i nodi, le connessioni e i trigger.

3. **Event Source**  
   Componenti che generano eventi in risposta a specifiche azioni o condizioni.

4. **Trigger**  
   Collegamenti tra event source e workflow che definiscono quando e come avviare un workflow.

5. **Runtime di Esecuzione**  
   Ambiente che esegue i workflow in risposta ai trigger o alle richieste manuali.

## Best Practice

1. **Naming Consistente**: Utilizza nomi descrittivi e coerenti per workflow, nodi e porte.
2. **Documentazione**: Fornisci descrizioni dettagliate per ogni componente.
3. **Modularità**: Progetta workflow modulari che possono essere riutilizzati.
4. **Test Incrementali**: Testa ciascun nodo separatamente prima di collegare l'intero workflow.
5. **Gestione degli Errori**: Considera come il workflow gestirà gli errori e le eccezioni.
6. **Backup**: Mantieni backup dei template di workflow al di fuori del database.
7. **Versioning**: Utilizza un sistema di controllo versione per i template di workflow.

## Riferimenti

- [Documentazione Completa di PramaIA PDK](README.md)
- [README dei Template di Workflow](../workflows/README.md)
