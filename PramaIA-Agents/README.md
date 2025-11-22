# PramaIA-Agents
Agents per PramaIA - Componenti indipendenti che si integrano con il sistema principale

## Che cosa sono gli Agents?

Gli Agents sono componenti software indipendenti che estendono le funzionalità di PramaIA agendo come sistemi autonomi che interagiscono con il framework principale. A differenza dei plugins che vengono caricati ed eseguiti all'interno del PDK, gli agents operano come processi separati comunicando tramite API.

### Caratteristiche principali

- **Autonomia**: Esecuzione come processi indipendenti
- **Comunicazione API**: Interazione con il sistema principale via REST API
- **Specializzazione**: Ogni agent si concentra su compiti specifici
- **Scalabilità**: Possono essere distribuiti su diverse macchine
- **Filtri Intelligenti**: Sistema avanzato per ottimizzare il traffico di rete
- **Event-Trigger System**: Architettura generica per gestire eventi e trigger personalizzati

## Agents disponibili

### PDF Folder Monitor Agent
Monitor di cartelle con sistema di filtri intelligenti per ottimizzare il traffico di rete e evitare trasferimenti inutili di file non processabili.

- [Documentazione](./pdf-folder-monitor-agent/README.md)
- [Guida Utente](./pdf-folder-monitor-agent/docs/PDF_MONITORING_AUTOSTART.md)
- [Documentazione Tecnica](./pdf-folder-monitor-agent/docs/TECHNICAL_DOCUMENTATION.md)
- **Funzionalità principali**: 
  - Monitoraggio file system in tempo reale
  - **Sistema di filtri intelligenti** con risparmio banda del 95%+
  - Notifiche eventi file con metadata extraction
  - Configurazione cartelle con autostart
  - Gestione differenziata per tipo di file (PROCESS_FULL/METADATA_ONLY/SKIP)
  - Fallback locale quando il server di filtri non è disponibile

## 🔍 Sistema di Filtri Intelligenti

Il sistema di filtri è progettato per evitare il trasferimento di file non processabili (es. video MP4 da GB) che sprecherebbero banda senza valore per la vectorizzazione.

### Come funziona

1. **Valutazione server-side**: L'agent interroga il server di filtri prima di trasferire ogni file
2. **Decisioni intelligenti**: Basate su estensione, dimensione e tipo di contenuto
3. **Azioni differenziate**:
   - `PROCESS_FULL`: Trasferimento e processamento completo (documenti, codice)
   - `METADATA_ONLY`: Solo metadati del file (immagini medie, database)
   - `SKIP`: Nessun trasferimento (video, archivi, eseguibili)
4. **Fallback locale**: Regole di sicurezza quando il server non è raggiungibile

### Benefici

- **Risparmio banda 95%+**: Evita trasferimenti di file giganti non processabili
- **Velocità**: Solo i file utili vengono trasferiti
- **Resilienza**: Funziona anche offline con regole locali
- **Configurabilità**: Regole personalizzabili lato server