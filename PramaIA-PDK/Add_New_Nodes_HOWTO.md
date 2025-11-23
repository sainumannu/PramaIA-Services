# Add New Nodes How-to

Questa guida rapida spiega come aggiungere un nuovo nodo al PDK. I nodi sono accessibili direttamente tramite API del server PDK.

## 1. Dove vanno i nodi?
- I nodi sono **sempre** definiti all'interno di un plugin, nella cartella `plugins/NOME-PLUGIN/`.
- Ogni plugin può contenere uno o più nodi.

## 2. Struttura minima di un plugin
```
plugins/
  nome-plugin/
    plugin.json         # Metadati e definizione dei nodi
    src/
      resolvers/        # Implementazione dei resolver dei nodi
        mioNodoResolver.py
        index.js        # (per plugin JS)
    README.md           # (opzionale)
```

## 3. File chiave
- **plugin.json**: contiene sia i metadati del plugin sia l'array `nodes` con la definizione di tutti i nodi del plugin.
- **src/resolvers/**: contiene i file Python (o JS) che implementano la logica dei nodi (resolver).

## 4. Come aggiungere un nuovo nodo
1. Scegli il plugin in cui aggiungere il nodo (o creane uno nuovo in `plugins/`).
2. Aggiungi la definizione del nodo nell'array `nodes` di `plugin.json`.
3. Implementa il resolver nella cartella `src/resolvers/`.
4. Il nodo sarà automaticamente disponibile tramite API del server PDK.

## 5. API del server PDK
- I nodi sono accessibili via HTTP tramite il server PDK (porta 3001 di default).
- Endpoint principale: `GET /api/nodes` - lista tutti i nodi disponibili
- Esecuzione nodi: `POST /api/nodes/{nodeType}/execute` - esegue un nodo specifico

## 6. Esempio di definizione nodo in plugin.json
```json
{
  "id": "file_cleanup_node",
  "name": "File Cleanup / Archiver",
  "type": "file-system",
  "category": "File System",
  "description": "Rimuove o archivia file dal filesystem.",
  "entry": "src/resolvers/file_cleanup_resolver.py",
  "inputs": [
    { "name": "file_path", "type": "string", "required": true },
    { "name": "mode", "type": "string", "required": false },
    { "name": "backup_dir", "type": "string", "required": false },
    { "name": "log", "type": "boolean", "required": false }
  ],
  "outputs": [
    { "name": "result", "type": "string" }
  ],
  "configSchema": {
    "type": "object",
    "properties": {
      "default_mode": { "type": "string", "enum": ["delete", "archive"], "default": "archive" },
      "default_backup_dir": { "type": "string" }
    }
  }
}
```

## 7. Note pratiche
- Non usare più file `nodes.json`: tutto va in `plugin.json`.
- Ogni nodo deve avere un campo `entry` che punta al resolver.
- I resolver Python vanno in `src/resolvers/`.
- I nodi sono automaticamente disponibili via API del server PDK.
- Non è necessario riavviare il server: i nodi vengono caricati dinamicamente dalle API.

---
Ultimo aggiornamento: novembre 2025
