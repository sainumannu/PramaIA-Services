// event-source-routes.js - Gestione delle route per Event Source
// Parte estratta da plugin-api-server.js per migliorare la manutenibilità

import express from 'express';

/**
 * Configura le route per la gestione delle Event Source
 * @param {express.Router} router - Router Express su cui registrare le route
 * @param {Object} eventSourceManager - Gestore delle event source
 * @param {Object} logger - Logger per messaggi diagnostici
 * @returns {express.Router} Router configurato
 */
export function configureEventSourceRoutes(router, eventSourceManager, logger) {
    // Get all available event sources with tag filtering
    router.get('/api/event-sources', (req, res) => {
        logger.info('🔌 GET /api/event-sources - Recupero sorgenti eventi');
        const { tags, exclude_tags, mode = 'OR' } = req.query;
        
        try {
            let sources = eventSourceManager.getAvailableSources();
            
            // Applica filtri tag
            if (tags) {
                const tagList = tags.split(',').map(t => t.trim().toLowerCase());
                sources = sources.filter(source => {
                    const sourceTags = (source.tags || []).map(t => t.toLowerCase());
                    
                    if (mode.toLowerCase() === 'and') {
                        return tagList.every(tag => sourceTags.includes(tag));
                    } else {
                        return tagList.some(tag => sourceTags.includes(tag));
                    }
                });
            }
            
            // Filtro per tag esclusi
            if (exclude_tags) {
                const excludeList = exclude_tags.split(',').map(t => t.trim().toLowerCase());
                sources = sources.filter(source => {
                    const sourceTags = (source.tags || []).map(t => t.toLowerCase());
                    return !excludeList.some(tag => sourceTags.includes(tag));
                });
            }
            
            logger.debug(`Trovate ${sources.length} sorgenti eventi (dopo filtraggio)`);
            res.json(sources);
        } catch (error) {
            logger.error(`Errore recupero event sources: ${error.message}`);
            res.status(500).json({ error: error.message });
        }
    });

    // Get specific event source details
    router.get('/api/event-sources/:id', (req, res) => {
        const sourceId = req.params.id;
        logger.info(`🔌 GET /api/event-sources/${sourceId} - Dettagli sorgente eventi`);
        
        try {
            const sources = eventSourceManager.getAvailableSources();
            const source = sources.find(s => s.id === sourceId);
            
            if (!source) {
                return res.status(404).json({ error: `Event source ${sourceId} non trovata` });
            }
            
            // Add detailed status
            const detailedStatus = eventSourceManager.getDetailedSourceStatus(sourceId);
            const enrichedSource = {
                ...source,
                ...detailedStatus
            };
            
            res.json(enrichedSource);
        } catch (error) {
            logger.error(`Errore recupero event source ${sourceId}: ${error.message}`);
            res.status(500).json({ error: error.message });
        }
    });

    // Start an event source
    router.post('/api/event-sources/:id/start', async (req, res) => {
        const sourceId = req.params.id;
        const config = req.body.config || {};
        
        logger.info(`🔌 POST /api/event-sources/${sourceId}/start - Avvio sorgente eventi`);
        logger.debug(`Configurazione: ${JSON.stringify(config)}`);
        
        try {
            await eventSourceManager.startSource(sourceId, config);
            res.json({ 
                success: true, 
                message: `Event source ${sourceId} avviata con successo`,
                status: 'running'
            });
        } catch (error) {
            logger.error(`Errore avvio event source ${sourceId}: ${error.message}`);
            res.status(500).json({ 
                success: false, 
                error: error.message 
            });
        }
    });

    // Stop an event source
    router.post('/api/event-sources/:id/stop', async (req, res) => {
        const sourceId = req.params.id;
        
        logger.info(`🔌 POST /api/event-sources/${sourceId}/stop - Arresto sorgente eventi`);
        
        try {
            await eventSourceManager.stopSource(sourceId);
            res.json({ 
                success: true, 
                message: `Event source ${sourceId} arrestata con successo`,
                status: 'stopped'
            });
        } catch (error) {
            logger.error(`Errore arresto event source ${sourceId}: ${error.message}`);
            res.status(500).json({ 
                success: false, 
                error: error.message 
            });
        }
    });

    // Get event source status
    router.get('/api/event-sources/:id/status', (req, res) => {
        const sourceId = req.params.id;
        
        logger.info(`🔌 GET /api/event-sources/${sourceId}/status - Stato sorgente eventi`);
        
        try {
            const status = eventSourceManager.getDetailedSourceStatus(sourceId);
            res.json(status);
        } catch (error) {
            logger.error(`Errore recupero stato event source ${sourceId}: ${error.message}`);
            res.status(500).json({ error: error.message });
        }
    });

    // Get event types for a specific event source
    router.get('/api/event-sources/:id/event-types', (req, res) => {
        const sourceId = req.params.id;
        
        logger.info(`🔌 GET /api/event-sources/${sourceId}/event-types - Tipi di eventi`);
        
        try {
            const sources = eventSourceManager.getAvailableSources();
            const source = sources.find(s => s.id === sourceId);
            
            if (!source) {
                return res.status(404).json({ error: `Event source ${sourceId} non trovata` });
            }
            
            res.json(source.eventTypes || []);
        } catch (error) {
            logger.error(`Errore recupero tipi di evento per ${sourceId}: ${error.message}`);
            res.status(500).json({ error: error.message });
        }
    });

    // Alias endpoint for compatibility - same as event-types
    router.get('/api/event-sources/:id/events', (req, res) => {
        const sourceId = req.params.id;
        
        logger.info(`🔌 GET /api/event-sources/${sourceId}/events - Eventi (alias per event-types)`);
        
        try {
            const sources = eventSourceManager.getAvailableSources();
            const source = sources.find(s => s.id === sourceId);
            
            if (!source) {
                return res.status(404).json({ error: `Event source ${sourceId} non trovata` });
            }
            
            // Return in the format expected by the frontend
            res.json({ eventTypes: source.eventTypes || [] });
        } catch (error) {
            logger.error(`Errore recupero eventi per ${sourceId}: ${error.message}`);
            res.status(500).json({ error: error.message });
        }
    });

    // Get all event types from all event sources
    router.get('/api/event-sources/events/all', (req, res) => {
        logger.info('🔌 GET /api/event-sources/events/all - Tutti i tipi di eventi da tutte le sorgenti');
        
        try {
            const sources = eventSourceManager.getAvailableSources();
            const allEventTypes = [];
            
            sources.forEach(source => {
                if (source.eventTypes && source.eventTypes.length > 0) {
                    source.eventTypes.forEach(eventType => {
                        allEventTypes.push({
                            ...eventType,
                            sourceId: source.id,
                            sourceName: source.name
                        });
                    });
                }
            });
            
            res.json({ eventTypes: allEventTypes });
        } catch (error) {
            logger.error(`Errore recupero tutti i tipi di evento: ${error.message}`);
            res.status(500).json({ error: error.message });
        }
    });
    
    // Restituisci il router configurato
    return router;
}

// Esporta la funzione di configurazione
export default configureEventSourceRoutes;