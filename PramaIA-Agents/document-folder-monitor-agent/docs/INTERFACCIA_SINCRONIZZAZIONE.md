# Interfaccia di Sincronizzazione PDF Monitor

## Interfaccia di Sincronizzazione

L'interfaccia di sincronizzazione fornisce una visione completa dello stato del sistema di monitoraggio e sincronizzazione. È organizzata in un pannello a schede che contiene:

1. **Stato del Monitoraggio**: Visualizza lo stato attuale delle cartelle monitorate, incluso quali sono attivamente monitorate
2. **Stato della Sincronizzazione**: Mostra lo stato della connessione al server e della sincronizzazione
3. **Log Eventi**: Visualizza un registro degli eventi recenti relativi alla sincronizzazione

### Componenti Principali

#### PDFMonitoringPanelWithSync

Questo è il componente principale che implementa l'interfaccia a schede, integrando tutte le funzionalità di monitoraggio e sincronizzazione.

#### SyncMonitoringPanel

Questo componente visualizza:

- **Stato della Connessione**: Mostra se l'agente è connesso al server
- **Statistiche di Sincronizzazione**: Mostra dati sulla sincronizzazione come ultima riconciliazione, eventi in coda, ecc.
- **Cartelle Monitorate**: Elenca tutte le cartelle configurate con indicazione di stato (attivo/inattivo)
- **Controlli di Sincronizzazione**: Fornisce pulsanti per forzare la riconciliazione manuale

### Indicatori di Stato delle Cartelle

L'interfaccia mostra chiaramente quali cartelle sono attivamente monitorate e quali no:

- **Attivo**: La cartella è attualmente monitorata e sarà inclusa nelle riconciliazioni periodiche
- **Inattivo**: La cartella è configurata ma il monitoraggio è disattivato; non sarà inclusa nelle riconciliazioni periodiche

Questa distinzione è fondamentale per comprendere quali cartelle verranno sincronizzate automaticamente.

### Funzionalità Principali

1. **Riconciliazione Manuale**: Possibilità di forzare la riconciliazione di una cartella specifica
2. **Visibilità Buffer Eventi**: Visualizzazione del numero di eventi in attesa di sincronizzazione
3. **Indicatore Connessione**: Stato della connessione al server in tempo reale
4. **Dettagli Monitoraggio**: Informazioni sullo stato attivo/inattivo di ogni cartella monitorata

### Utilizzo

L'interfaccia è progettata per essere intuitiva e fornire tutte le informazioni necessarie per gestire il sistema di sincronizzazione. Gli utenti possono:

1. Verificare rapidamente quali cartelle sono attivamente monitorate
2. Controllare lo stato della connessione al server
3. Forzare la riconciliazione manuale quando necessario
4. Monitorare gli eventi di sincronizzazione in tempo reale

Questo permette una gestione efficace del sistema di sincronizzazione, garantendo che i dati siano sempre aggiornati e che l'utente abbia visibilità completa sullo stato del sistema.

### Implementazione Tecnica

L'interfaccia è implementata utilizzando React con componenti funzionali e hooks per la gestione dello stato e degli effetti. Utilizza l'API di sincronizzazione per comunicare con il backend e recuperare informazioni sullo stato del sistema.

Il componente SyncMonitoringPanel si aggiorna periodicamente per mostrare sempre lo stato più recente del sistema di sincronizzazione e delle cartelle monitorate.
