// plugin-routes.js - Gestione delle route per i plugin
// Parte estratta da plugin-api-server.js per migliorare la manutenibilità

import fs from 'fs';
import path from 'path';
import express from 'express';

/**
 * Converte una stringa in snake_case
 * @param {string} str - Stringa da convertire
 * @returns {string} Stringa convertita in snake_case
 */
function toSnakeCase(str) {
    return str
        .trim()
        .toLowerCase()
        .replace(/\s+/g, '_')
        .replace(/[^\w_]/g, '');
}

/**
 * Configura le route per la gestione dei plugin
 * @param {express.Router} router - Router Express su cui registrare le route
 * @param {string} PLUGIN_DIR - Directory contenente i plugin
 * @param {Function} executePythonPlugin - Funzione per eseguire i plugin Python
 * @param {Object} logger - Logger per messaggi diagnostici
 * @returns {express.Router} Router configurato
 */
export function configurePluginRoutes(router, PLUGIN_DIR, executePythonPlugin, logger) {
    // List all plugins (folders with plugin.json)
    router.get('/plugins', (req, res) => {
        logger.info('📦 GET /plugins - Lista di tutti i plugin');
        const plugins = [];
        fs.readdirSync(PLUGIN_DIR).forEach(folder => {
            const manifestPath = path.join(PLUGIN_DIR, folder, 'plugin.json');
            if (fs.existsSync(manifestPath)) {
                try {
                    const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
                    logger.debug(`Plugin trovato: ${folder} (${manifest.name})`);
                    plugins.push({
                        id: folder,
                        name: manifest.name,
                        description: manifest.description,
                        version: manifest.version,
                        author: manifest.author,
                        nodes: manifest.nodes || [],
                        manifest
                    });
                } catch (e) {
                    logger.error(`Errore lettura plugin ${folder}: ${e.message}`, e);
                }
            }
        });
        logger.info(`Restituiti ${plugins.length} plugin`);
        res.json(plugins);
    });
    
    // Endpoint API standard per plugin con supporto filtri tag
    router.get('/api/plugins', (req, res) => {
        logger.info(`🌐 GET /api/plugins - Lista di plugin con filtri`);
        const { tags, exclude_tags, mode = 'OR' } = req.query;
        
        const plugins = [];
        fs.readdirSync(PLUGIN_DIR).forEach(folder => {
            const manifestPath = path.join(PLUGIN_DIR, folder, 'plugin.json');
            if (fs.existsSync(manifestPath)) {
                try {
                    const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
                    const plugin = {
                        id: folder,
                        name: manifest.name,
                        description: manifest.description,
                        version: manifest.version,
                        author: manifest.author,
                        license: manifest.license,
                        tags: manifest.tags || [],
                        nodes: manifest.nodes || [],
                        configSchema: manifest.configSchema,
                        type: manifest.type || 'node'
                    };
                    plugins.push(plugin);
                } catch (e) {
                    logger.error(`Errore lettura plugin ${folder}: ${e.message}`, e);
                }
            }
        });
        
        // Applica filtri tag
        let filteredPlugins = plugins;
        
        // Filtro per tag inclusi
        if (tags) {
            const tagList = tags.split(',').map(t => t.trim().toLowerCase());
            logger.debug(`Filtro per tag inclusi: ${tagList.join(', ')}`);
            filteredPlugins = filteredPlugins.filter(plugin => {
                const pluginTags = (plugin.tags || []).map(t => t.toLowerCase());
                
                if (mode.toLowerCase() === 'and') {
                    return tagList.every(tag => pluginTags.includes(tag));
                } else {
                    return tagList.some(tag => pluginTags.includes(tag));
                }
            });
        }
        
        // Filtro per tag esclusi
        if (exclude_tags) {
            const excludeList = exclude_tags.split(',').map(t => t.trim().toLowerCase());
            logger.debug(`Filtro per tag esclusi: ${excludeList.join(', ')}`);
            filteredPlugins = filteredPlugins.filter(plugin => {
                const pluginTags = (plugin.tags || []).map(t => t.toLowerCase());
                return !excludeList.some(tag => pluginTags.includes(tag));
            });
        }
        logger.info(`Restituiti ${filteredPlugins.length} plugin filtrati da ${plugins.length} totali`);
        res.json({ plugins: filteredPlugins });
    });
    
    // Get all available tags from plugins and event sources
    router.get('/api/tags', (req, res) => {
        logger.info('🏷️ GET /api/tags - Recupero di tutti i tag disponibili');
        try {
            const allTags = new Set();
            const tagStats = {};
            
            // Raccogli tag dai plugin
            fs.readdirSync(PLUGIN_DIR).forEach(folder => {
                const manifestPath = path.join(PLUGIN_DIR, folder, 'plugin.json');
                if (fs.existsSync(manifestPath)) {
                    try {
                        const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
                        
                        // Tag del plugin
                        (manifest.tags || []).forEach(tag => {
                            allTags.add(tag);
                            tagStats[tag] = (tagStats[tag] || 0) + 1;
                        });
                        
                        // Tag dei nodi (se è un plugin node)
                        if (manifest.nodes) {
                            manifest.nodes.forEach(node => {
                                (node.tags || []).forEach(tag => {
                                    allTags.add(tag);
                                    tagStats[tag] = (tagStats[tag] || 0) + 1;
                                });
                            });
                        }
                        
                        // Tag degli event types (se è un event source)
                        if (manifest.eventTypes) {
                            manifest.eventTypes.forEach(eventType => {
                                (eventType.tags || []).forEach(tag => {
                                    allTags.add(tag);
                                    tagStats[tag] = (tagStats[tag] || 0) + 1;
                                });
                            });
                        }
                    } catch (e) {
                        logger.error(`Errore lettura plugin ${folder}:`, e);
                    }
                }
            });
            
            // Converti in formato statistiche
            const tagList = Array.from(allTags).sort();
            const statistics = tagList.map(tag => ({
                tag,
                count: tagStats[tag],
                percentage: ((tagStats[tag] / Object.keys(tagStats).length) * 100).toFixed(1)
            })).sort((a, b) => b.count - a.count);
            
            res.json({
                tags: tagList,
                count: tagList.length,
                statistics
            });
        } catch (error) {
            logger.error('Errore recupero tag:', error);
            res.status(500).json({ error: error.message });
        }
    });
    
    // Get details for a specific plugin
    router.get('/plugins/:id', (req, res) => {
        logger.info(`📦 GET plugin details for: ${req.params.id}`);
        const manifestPath = path.join(PLUGIN_DIR, req.params.id, 'plugin.json');
        if (!fs.existsSync(manifestPath)) {
            logger.error(`Plugin manifest non trovato: ${manifestPath}`);
            return res.status(404).json({ error: 'Plugin non trovato' });
        }
        const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
        // Includi configSchema in root se presente
        const response = {
            id: req.params.id,
            name: manifest.name,
            description: manifest.description,
            nodes: manifest.nodes || [],
            configSchema: manifest.configSchema || null,
            manifest
        };
        logger.debug(`Dettagli plugin: ${manifest.name}, nodi: ${manifest.nodes?.length || 0}`);
        res.json(response);
    });
    
    // (Optional) Execute a node
    router.post('/plugins/:id/execute', async (req, res) => {
        try {
            logger.info(`🚀 POST /plugins/${req.params.id}/execute - Esecuzione nodo`);
            
            let nodeId, inputs, config;
            
            // Gestione dei dati JSON che potrebbero essere nel formato json diretto o form
            if (req.headers['content-type'] && req.headers['content-type'].includes('multipart/form-data')) {
                logger.debug("Rilevato multipart/form-data");
                // Se è un form multipart, controlla se c'è un campo json
                if (req.body.json) {
                    try {
                        const jsonData = JSON.parse(req.body.json);
                        nodeId = jsonData.nodeId;
                        inputs = jsonData.inputs || {};
                        config = jsonData.config || {};
                        
                        // Gestisci i file caricati se presenti
                        if (req.files && req.files.file) {
                            // Aggiorna gli input con i file
                            inputs.file = req.files.file;
                        }
                        
                        logger.debug(`Dati estratti dal campo json del form per nodo ${nodeId}`);
                    } catch (e) {
                        logger.error(`Errore parsing JSON dal campo form: ${e.message}`, e);
                        return res.status(400).json({ 
                            success: false,
                            error: 'JSON non valido nel campo form' 
                        });
                    }
                } else {
                    // Form data senza campo json
                    nodeId = req.body.nodeId;
                    inputs = req.body.inputs ? JSON.parse(req.body.inputs) : {};
                    config = req.body.config ? JSON.parse(req.body.config) : {};
                }
            } else {
                // Formato JSON standard
                ({ nodeId, inputs, config } = req.body);
            }
            
            if (!nodeId) {
                logger.error("Richiesta di esecuzione nodo senza specificare nodeId");
                return res.status(400).json({ 
                    success: false,
                    error: 'nodeId richiesto' 
                });
            }
            
            logger.info(`Esecuzione plugin ${req.params.id}, nodo ${nodeId}`);
            logger.debug(`Inputs: ${JSON.stringify(inputs)}`);
            logger.debug(`Config: ${JSON.stringify(config)}`);
            
            const result = await executePythonPlugin(PLUGIN_DIR, req.params.id, nodeId, inputs || {}, config || {}, logger);
            logger.debug(`Esecuzione completata per plugin ${req.params.id}, nodo ${nodeId}`);
            
            // Aggiungiamo un ID documento generato se non esiste
            if (result && !result.id && !result.document_id) {
                // Genera un ID univoco per il documento basato sul timestamp e un numero casuale
                const documentId = `doc_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
                logger.debug(`Nessun ID documento trovato, genero ID: ${documentId}`);
                
                // Aggiungi l'ID al risultato
                result.document_id = documentId;
            }
            
            res.json({ success: true, result });
            
        } catch (error) {
            logger.error(`Errore esecuzione plugin ${req.params.id}: ${error.message}`, error);
            res.status(500).json({ 
                success: false, 
                error: error.message 
            });
        }
    });
    
    // Nuovo endpoint per ottenere tutti i nodi disponibili
    router.get('/api/nodes', (req, res) => {
        logger.info('📦 GET /api/nodes - Ottenendo tutti i nodi disponibili');
        const allNodes = [];
        
        fs.readdirSync(PLUGIN_DIR).forEach(folder => {
            const manifestPath = path.join(PLUGIN_DIR, folder, 'plugin.json');
            if (fs.existsSync(manifestPath)) {
                try {
                    logger.debug(`Lettura manifest plugin: ${manifestPath}`);
                    const manifestRaw = fs.readFileSync(manifestPath, 'utf-8');
                    
                    const manifest = JSON.parse(manifestRaw);
                    if (manifest.nodes && Array.isArray(manifest.nodes)) {
                        logger.debug(`Plugin "${folder}" ha ${manifest.nodes.length} nodi`);
                        manifest.nodes.forEach((node, index) => {
                            // Debug icone - solo in modalità TRACE
                            logger.debug(`Node ${node.name} icon: "${node.icon}" [chars: ${node.icon ? Array.from(node.icon).map(c => c.charCodeAt(0)).join(',') : 'NO ICON'}]`);
                            
                            // Verifica presenza di configSchema
                            const hasConfigSchema = node.configSchema && 
                                                  typeof node.configSchema === 'object' && 
                                                  node.configSchema.properties && 
                                                  Object.keys(node.configSchema.properties).length > 0;
                                                  
                            logger.debug(`ConfigSchema presente per nodo ${node.id}: ${hasConfigSchema ? 'SÌ' : 'NO'}`);
                            
                            // Debug per identificare nodi con titoli configSchema errati
                            if (hasConfigSchema && node.configSchema.title && 
                               !node.configSchema.title.includes(node.name)) {
                                logger.warn(`Possibile errore: Il titolo del configSchema "${node.configSchema.title}" non contiene il nome del nodo "${node.name}"`);
                            }
                            
                            // Se il nodo non ha configSchema valido, creiamo uno schema di base
                            if (!hasConfigSchema) {
                                logger.debug(`ConfigSchema non trovato o non valido per il nodo ${node.name}, creazione schema base`);
                                node.configSchema = {
                                    "title": `Configurazione ${node.name}`,
                                    "type": "object",
                                    "properties": {
                                        "description": {
                                            "type": "string",
                                            "title": "Descrizione",
                                            "description": "Descrizione personalizzata per questo nodo",
                                            "default": node.description || ""
                                        },
                                        "custom_name": {
                                            "type": "string", 
                                            "title": "Nome personalizzato",
                                            "description": "Nome personalizzato per identificare questo nodo",
                                            "default": node.name || ""
                                        }
                                    }
                                };
                            }
                            
                            // ENRICHMENT DEL NODO
                            const enrichedNode = {
                                ...node,
                                node_id: toSnakeCase(node.name),  // NUOVO - identificatore univoco
                                pluginId: folder,
                                pluginName: manifest.name
                            };
                            
                            // Soluzione per schemi di configurazione non coerenti
                            if (enrichedNode.configSchema && enrichedNode.configSchema.properties) {
                                logger.debug(`Ricostruzione schema di configurazione per nodo ${node.id}`);
                                
                                const originalProperties = enrichedNode.configSchema.properties;
                                const originalType = enrichedNode.configSchema.type || 'object';
                                
                                // Ricostruisci lo schema con riferimenti espliciti
                                enrichedNode.configSchema = {
                                    "title": `Configurazione ${enrichedNode.name} (ID: ${enrichedNode.id})`,
                                    "type": originalType,
                                    "properties": originalProperties,
                                    "nodeId": enrichedNode.id,
                                    "nodeName": enrichedNode.name,
                                    "uniqueKey": `${enrichedNode.pluginId}_${enrichedNode.id}_${Date.now()}`
                                };
                            }
                            
                            // AGGIUNGI IL NODO ALLA LISTA FINALE
                            allNodes.push(enrichedNode);
                            logger.debug(`Nodo ${node.id} aggiunto alla lista finale`);
                        });
                    } else {
                        logger.warn(`Nessun nodo trovato nel plugin: ${folder}`);
                    }
                } catch (e) {
                    logger.error(`Errore lettura manifest ${folder}: ${e.message}`, e);
                }
            }
        });
        
        logger.info(`Totale nodi trovati: ${allNodes.length}`);
        
        // Verifica se ci sono icone mancanti o danneggiate
        allNodes.forEach((node) => {
            if (!node.icon || (typeof node.icon === 'string' && node.icon.includes('�'))) {
                logger.warn(`Icona mancante o danneggiata per il nodo ${node.name} (${node.id})`);
            }
        });
    
        const responseData = { nodes: allNodes };
        
        // Forza encoding UTF-8 per preservare le emoji
        res.setHeader('Content-Type', 'application/json; charset=utf-8');
        res.json(responseData);
    });
    
    // Endpoint per ottenere i nodi di un plugin specifico
    router.get('/api/plugins/:id/nodes', (req, res) => {
        logger.info(`📦 GET /api/plugins/${req.params.id}/nodes - Recupero nodi per plugin specifico`);
        const manifestPath = path.join(PLUGIN_DIR, req.params.id, 'plugin.json');
        if (!fs.existsSync(manifestPath)) {
            logger.error(`Plugin manifest non trovato: ${manifestPath}`);
            return res.status(404).json({ error: 'Plugin non trovato' });
        }
        
        try {
            const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
            let nodes = manifest.nodes || [];
            
            // Assicuriamoci che ogni nodo abbia un configSchema valido
            nodes = nodes.map(node => {
                // Aggiunge node_id al nodo
                const nodeWithId = {
                    ...node,
                    node_id: toSnakeCase(node.name)  // NUOVO - identificatore univoco
                };
                
                // Verifica presenza di configSchema
                const hasConfigSchema = nodeWithId.configSchema && 
                                      typeof nodeWithId.configSchema === 'object' && 
                                      nodeWithId.configSchema.properties && 
                                      Object.keys(nodeWithId.configSchema.properties).length > 0;
                
                // Se non ha configSchema, aggiungiamo uno schema base
                if (!hasConfigSchema) {
                    logger.debug(`⚠️ Aggiunta configSchema di default al nodo ${nodeWithId.name} nel plugin ${req.params.id}`);
                    return {
                        ...nodeWithId,
                        configSchema: {
                            "title": `Configurazione ${nodeWithId.name}`,
                            "type": "object",
                            "properties": {
                                "description": {
                                    "type": "string",
                                    "title": "Descrizione",
                                    "description": "Descrizione personalizzata per questo nodo",
                                    "default": nodeWithId.description || ""
                                },
                                "custom_name": {
                                    "type": "string", 
                                    "title": "Nome personalizzato",
                                    "description": "Nome personalizzato per identificare questo nodo",
                                    "default": nodeWithId.name || ""
                                }
                            },
                            "nodeId": nodeWithId.id,  // Forziamo l'ID del nodo nel configSchema
                            "nodeName": nodeWithId.name  // Forziamo il nome del nodo nel configSchema
                        }
                    };
                }
                
                // Anche se ha configSchema, assicuriamo che il titolo sia corretto e che contenga l'ID del nodo
                if (nodeWithId.configSchema) {
                    // Correzione del titolo se necessario
                    if (!nodeWithId.configSchema.title || !nodeWithId.configSchema.title.includes(nodeWithId.name)) {
                        logger.debug(`🔧 Correzione titolo configSchema per ${nodeWithId.name} in plugin ${req.params.id}`);
                        nodeWithId.configSchema.title = `Configurazione ${nodeWithId.name}`;
                    }
                    
                    // Aggiungiamo ID e nome del nodo al configSchema
                    nodeWithId.configSchema.nodeId = nodeWithId.id;
                    nodeWithId.configSchema.nodeName = nodeWithId.name;
                }
                
                return nodeWithId;
            });
            
            const response = {
                pluginId: req.params.id,
                pluginName: manifest.name,
                nodes: nodes
            };
            
            logger.debug(`Trovati ${nodes.length} nodi per plugin ${req.params.id}`);
            res.json(response);
        } catch (e) {
            logger.error(`Errore lettura manifest ${req.params.id}: ${e.message}`);
            res.status(500).json({ error: 'Errore lettura manifest' });
        }
    });
    
    // Restituisci il router configurato
    return router;
}

// Esporta la funzione di configurazione
export default configurePluginRoutes;