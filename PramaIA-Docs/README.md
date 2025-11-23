# PramaIA-Docs - Documentazione Essenziale

Benvenuto nella documentazione essenziale di PramaIA. Questa cartella contiene i documenti fondamentali per comprendere, debuggare e sviluppare nell'ecosistema PramaIA, **senza ridondanze**.

## 📚 Indice Documenti

### 1. **[ECOSYSTEM_OVERVIEW.md](./ECOSYSTEM_OVERVIEW.md)**
Panoramica dell'ecosistema PramaIA e i suoi componenti.

**Contiene**:
- Architettura dei microservizi
- Stack tecnologico
- Flussi di dati principali
- Configurazione e variabili d'ambiente
- Startup sequence
- Health checks e debugging base

**Per chi**: Tutti - punto di partenza
**Tempo di lettura**: 15 minuti

---

### 2. **[EVENT_SOURCES_TRIGGERS_WORKFLOWS.md](./EVENT_SOURCES_TRIGGERS_WORKFLOWS.md)**
Il sistema event-driven: come gli eventi scatenano automazioni.

**Contiene**:
- Concetto di Event Source (sorgenti di eventi)
- Trigger (collegamento evento→workflow)
- Workflow e nodi (pipeline di elaborazione)
- DAG engine (orchestrazione)
- Integrazione completa: evento → trigger → workflow
- Operazioni comuni
- Troubleshooting

**Per chi**: Sviluppatori, DevOps
**Tempo di lettura**: 20 minuti

---

### 3. **[DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md)**
Guida per sviluppare nuovi nodi e event source.

**Contiene**:
- Come creare nuovi nodi (handler di elaborazione)
- Struttura plugin e nodes.json
- Implementare resolver function
- Testing dei nodi
- Come creare nuovi event source
- Retry logic e buffering
- Best practices
- Debugging durante sviluppo

**Per chi**: Sviluppatori backend, plugin developer
**Tempo di lettura**: 30 minuti

---

### 4. **[QUICK_START_EVENT_SOURCES.md](./QUICK_START_EVENT_SOURCES.md)** ✨ NEW
Guida veloce (10 minuti): creare e usare event sources.

**Contiene**:
- 30-secondo overview dei concetti
- Esempio completo di timer event source (5 minuti)
- Come usare emit_event() da qualunque servizio
- Manifest format e struttura evento
- Built-in event sources
- Comuni errori e best practices
- Debugging rapido
- Checklist per nuove event sources

**Per chi**: Developers che vogliono iniziare subito
**Tempo di lettura**: 10 minuti
**Dipendenze**: Nessuna (standalone)

---

### 5. **[EVENT_SOURCES_EXTENSIBILITY.md](./EVENT_SOURCES_EXTENSIBILITY.md)** ✨ NEW
Architettura e estensibilità del sistema Event Sources.

**Contiene**:
- Core concepts e lifecycle degli eventi
- PDK API: come funziona la scoperta automatica
- Creazione custom event sources (plugin pattern)
- Built-in event sources (system, webhook, upload, monitor)
- Event emission pattern e best practices
- Esempi completi di integrazione
- Checklist per sviluppatori

**Per chi**: Sviluppatori PDK, DevOps, system integrators
**Tempo di lettura**: 25 minuti
**Dipendenze**: EVENT_SOURCES_TRIGGERS_WORKFLOWS.md

---

### 6. **[IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md)** ✨ UPDATED
Current implementation status and next steps.

**Contains**:
- EventEmitter implementation status (✅ Complete)
- Current pipeline state and debugging
- Database status and event logging
- Trigger matching investigation
- Next steps and roadmap
- Consolidated session findings

**For who**: Project team, stakeholders, developers
**Tempo di lettura**: 10 minuti

---

## 🎯 Quick Navigation

**Se vuoi...**

| Obiettivo | Documento | Sezione |
|-----------|-----------|---------|
| Capire l'architettura generale | ECOSYSTEM_OVERVIEW | Section 2-3 |
| Risolvere un problema | ECOSYSTEM_OVERVIEW | Section 10 |
| Configurare servizi | ECOSYSTEM_OVERVIEW | Section 8 |
| Creare un trigger | EVENT_SOURCES_TRIGGERS_WORKFLOWS | Section 6.1 |
| Capire come funzionano gli eventi | EVENT_SOURCES_TRIGGERS_WORKFLOWS | Section 2-5 |
| Creare un nuovo nodo | DEVELOPMENT_GUIDE | Section 2 |
| Creare un event source | DEVELOPMENT_GUIDE \| EVENT_SOURCES_EXTENSIBILITY | Section 3 \| Section 3-4 |
| Debuggare | DEVELOPMENT_GUIDE | Section 4 |
| Testare | DEVELOPMENT_GUIDE | Section 2.9, 3.3 |
| **Estendere il sistema con custom event sources** | **EVENT_SOURCES_EXTENSIBILITY** | **Section 3-6** |
| **Capire lo stato attuale del sistema** | **IMPLEMENTATION_STATUS.md** | **All sections** |
| **Debuggare problemi di trigger matching** | **UPLOAD_EVENT_PIPELINE.md** | **Debugging Guide** |
| **Capire come registra event sources** | **EVENT_SOURCES_EXTENSIBILITY** | **Section 2** |
| **Emettere eventi da servizi** | **EVENT_SOURCES_EXTENSIBILITY** | **Section 5** |

---

## 🚀 Common Workflows

### Setup Iniziale
1. Leggi **ECOSYSTEM_OVERVIEW.md** per capire come i servizi comunicano
2. Verifica che tutti i servizi siano attivi (Section 10)
3. Consulta le variabili d'ambiente (ECOSYSTEM_OVERVIEW, Section 8)

### Sviluppo di Nuovo Nodo
1. Leggi **DEVELOPMENT_GUIDE.md** Section 2.1-2.8
2. Crea la struttura plugin
3. Definisci `nodes.json`
4. Implementa resolver
5. Testa (Section 2.9)

### Aggiunta Event Source
1. Leggi **DEVELOPMENT_GUIDE.md** Section 3.1-3.4
2. Implementa event source
3. Aggiungi retry/buffering (Section 3.4)
4. Integra in startup (Section 3.7)

### Creazione Workflow Automatizzato
1. Leggi **EVENT_SOURCES_TRIGGERS_WORKFLOWS.md** Section 2-5
2. Identifica l'evento trigger
3. Crea il workflow
4. Configurar il trigger (Section 6.1)
5. Test

### Debugging Issue
1. Consulta **ECOSYSTEM_OVERVIEW.md** Section 10
2. Verifica health check (Section 10)
3. Se è un trigger/evento: **EVENT_SOURCES_TRIGGERS_WORKFLOWS.md** Section 7
4. Se è un nodo: **DEVELOPMENT_GUIDE.md** Section 4
5. Controllare log centralizzati (port 8081)

---

## 🔗 Relazioni tra Documenti

```
ECOSYSTEM_OVERVIEW (foundation)
        ↓
        ├─→ EVENT_SOURCES_TRIGGERS_WORKFLOWS (come usare)
        │        ↓
        │        ├─→ EVENT_SOURCES_EXTENSIBILITY (come estendere)
        │        │        ↓
        │        │        ├─→ UPLOAD_EVENT_PIPELINE (debugging)
        │        │        │
        │        │        └─→ IMPLEMENTATION_STATUS (stato attuale)
        │        │
        │        └─→ DEVELOPMENT_GUIDE (come estendere)
        │
        └─→ DEVELOPMENT_GUIDE (come estendere)
                ↓
                ├─→ EVENT_SOURCES_EXTENSIBILITY (custom sources)
                │
                └─→ EVENT_SOURCES_TRIGGERS_WORKFLOWS (testing)
```

---

## 📚 Glossario Rapido

| Termine | Significato |
|---------|-----------|
| **Event Source** | Componente che genera eventi (file system, webhook, timer) |
| **Event** | Occorrenza nel sistema (file creato, API chiamata, timer scattato) |
| **Trigger** | Regola che collega evento a workflow (quando X accade, esegui workflow Y) |
| **Workflow** | Pipeline di elaborazione composto da nodi |
| **Nodo** | Unità di computazione con input/output (trasforma dati) |
| **Plugin** | Contenitore di nodi (es. pdf-semantic-plugin) |
| **PDK** | Plugin Development Kit - server che orchestra nodi |
| **Resolver** | Funzione che implementa la logica di un nodo |
| **Connection** | Link tra nodi che trasmette dati |
| **DAG** | Directed Acyclic Graph - struttura workflow |

---

## 🛠️ Troubleshooting Rapido

### Servizio non risponde
```bash
# Health check
curl http://127.0.0.1:8000/health      # Backend
curl http://127.0.0.1:3001/health      # PDK
curl http://127.0.0.1:8081/health      # LogService
curl http://127.0.0.1:8090/health      # VectorstoreService
```
→ Vedi: ECOSYSTEM_OVERVIEW Section 10

### Trigger non esegue
1. Verifica che trigger sia active
2. Verifica event_type e source
3. Verifica condizioni
→ Vedi: EVENT_SOURCES_TRIGGERS_WORKFLOWS Section 7.1

### Nodo non trovato
```bash
# Verifica nodi disponibili
curl http://127.0.0.1:3001/api/nodes | grep "nome_nodo"
```
→ Vedi: DEVELOPMENT_GUIDE Section 2.6

### Errore type mismatch
Gli output di un nodo non matchano gli input del successivo
→ Vedi: EVENT_SOURCES_TRIGGERS_WORKFLOWS Section 4.4

---

## 🔄 Ciclo di Vita: Da Evento a Risultato

```
1. Event Source genera evento
   ↓
2. Invia a Backend: POST /api/events/process
   ↓
3. Backend trova Trigger matching
   ↓
4. Valuta condizioni
   ↓
5. Esegue Workflow via WorkflowEngine
   ↓
6. WorkflowEngine orchestra Nodi via PDK
   ↓
7. Ogni Nodo esegue Resolver function
   ↓
8. Risultati passati ai nodi successivi
   ↓
9. Output finale salvato in DB/VectorStore
```

Consultare **EVENT_SOURCES_TRIGGERS_WORKFLOWS.md** Section 5 per dettagli.

---

## 📊 Decision Tree: Quale Documento Leggere?

```
START
  |
  ├─ Devo capire l'architettura?
  │  └─ SI → ECOSYSTEM_OVERVIEW
  │
  ├─ Ho un problema da risolvere?
  │  ├─ è un trigger/evento? → EVENT_SOURCES_TRIGGERS_WORKFLOWS Section 7
  │  ├─ è un nodo? → DEVELOPMENT_GUIDE Section 4
  │  ├─ è una configurazione? → ECOSYSTEM_OVERVIEW Section 8
  │  └─ è un event source? → EVENT_SOURCES_EXTENSIBILITY Section 2
  │
  ├─ Devo sviluppare qualcosa?
  │  ├─ Nodo? → DEVELOPMENT_GUIDE Section 2
  │  ├─ Event Source? → EVENT_SOURCES_EXTENSIBILITY Section 3
  │  └─ Upload → Workflow pipeline? → UPLOAD_EVENT_PIPELINE Section 3
  │
  └─ Altro? → Leggi indice sopra
```

---

## 🎓 Percorsi di Apprendimento

### Per Principianti
1. ECOSYSTEM_OVERVIEW (20 min)
2. EVENT_SOURCES_TRIGGERS_WORKFLOWS Section 1-3 (10 min)
3. Provare ad avviare sistema (10 min)
4. Leggere il resto come necessario

### Per Sviluppatori
1. ECOSYSTEM_OVERVIEW Section 2-3 (10 min)
2. EVENT_SOURCES_TRIGGERS_WORKFLOWS (20 min)
3. DEVELOPMENT_GUIDE Section 2 (nodi) o 3 (event source)
4. Pratica con esempio

### Per DevOps/SRE
1. ECOSYSTEM_OVERVIEW (20 min, focus Section 8-10)
2. DEVELOPMENT_GUIDE Section 4 (debugging)
3. Documentazione specifica servizi

---

## 📝 Note di Utilizzo

- ✅ Documenti sono concisi, senza ridondanze
- ✅ Ogni sezione è autocontenuta
- ✅ Codice di esempio è completo e testato
- ✅ Glossario e cross-reference facilitano navigazione
- ✅ Aggiornato a: 18 Novembre 2025

---

## 🔗 Documentazione Aggiuntiva

Per documentazione specifica di componenti:
- **PramaIA-LogService/docs/**: Logging centralizzato
- **PramaIA-VectorstoreService/docs/**: Ricerca semantica
- **PramaIA-PDK/docs/**: Dettagli plugin system
- **PramaIA-Agents/document-folder-monitor-agent/docs/**: Folder monitor specifics

---

**Buona lettura e buona programmazione!** 🚀
