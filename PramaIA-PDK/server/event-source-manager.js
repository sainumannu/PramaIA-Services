// Event Source Manager per PDK Server
// Gestisce il lifecycle degli Event Sources come processi persistent

import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { EventEmitter } from 'events';
import logger from './logger.js';  // Import nuovo modulo di logging

export class EventSourceManager extends EventEmitter {
    constructor(pluginDir, eventSourceDir = null) {
        super();
        this.pluginDir = pluginDir;
        this.eventSourceDir = eventSourceDir || pluginDir; // Directory separata per event sources
        this.activeSources = new Map(); // sourceId -> { process, config, status }
        this.eventHandlers = new Map(); // sourceId -> event handler function
    }

    /**
     * Get all available event sources
     */
    getAvailableSources() {
        const sources = [];
        
        // Scansiona la directory event-sources
        try {
            if (fs.existsSync(this.eventSourceDir)) {
                const eventSourceFolders = fs.readdirSync(this.eventSourceDir);
                
                for (const folder of eventSourceFolders) {
                    const manifestPath = path.join(this.eventSourceDir, folder, 'plugin.json');
                    
                    if (fs.existsSync(manifestPath)) {
                        try {
                            const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
                            
                            // Check if it's an event source
                            if (manifest.type === 'event-source') {
                                sources.push({
                                    id: manifest.name,
                                    name: manifest.name,
                                    version: manifest.version,
                                    description: manifest.description,
                                    lifecycle: manifest.lifecycle,
                                    eventTypes: manifest.eventTypes,
                                    configSchema: manifest.configSchema,
                                    status: this.getSourceStatus(manifest.name),
                                    path: folder
                                });
                            }
                        } catch (error) {
                            logger.warn(`Errore caricamento manifest event source da ${folder}: ${error.message}`);
                        }
                    }
                }
            }
        } catch (error) {
            logger.error(`Errore nella scansione degli event sources: ${error.message}`, error);
        }
        
        return sources;
    }

    /**
     * Get status of a specific event source
     */
    getSourceStatus(sourceId) {
        const source = this.activeSources.get(sourceId);
        if (!source) {
            return 'stopped';
        }
        return source.status;
    }

    /**
     * Get detailed status of a specific event source
     */
    getDetailedSourceStatus(sourceId) {
        const source = this.activeSources.get(sourceId);
        if (!source) {
            return {
                running: false,
                status: 'stopped'
            };
        }

        return {
            running: source.status === 'running',
            status: source.status,
            pid: source.process?.pid,
            startTime: source.startTime,
            lastActivity: source.lastActivity,
            eventsEmitted: source.eventsEmitted || 0,
            errors: source.errors || []
        };
    }

    /**
     * Start an event source
     */
    async startSource(sourceId, config = {}) {
        logger.info(`Avvio event source: ${sourceId}`);
        
        // Check if already running
        if (this.activeSources.has(sourceId)) {
            const source = this.activeSources.get(sourceId);
            if (source.status === 'running') {
                throw new Error(`Event source ${sourceId} è già in esecuzione`);
            }
        }

        // Find the event source manifest
        const availableSources = this.getAvailableSources();
        const sourceManifest = availableSources.find(s => s.id === sourceId);
        
        if (!sourceManifest) {
            throw new Error(`Event source ${sourceId} non trovato`);
        }

        const sourcePath = path.join(this.pluginDir, sourceManifest.path);
        const entryPoint = path.join(sourcePath, sourceManifest.entry || 'src/event_source.py');
        
        if (!fs.existsSync(entryPoint)) {
            throw new Error(`Event source entry point non trovato: ${entryPoint}`);
        }

        try {
            // Create source entry in registry
            const sourceEntry = {
                status: 'starting',
                config: config,
                startTime: new Date(),
                eventsEmitted: 0,
                errors: []
            };
            
            this.activeSources.set(sourceId, sourceEntry);

            // Prepare config for the Python process
            const processConfig = {
                source_id: sourceId,
                config: config,
                event_types: sourceManifest.eventTypes
            };

            logger.debug(`Configurazione event source ${sourceId}: ${JSON.stringify(processConfig)}`);

            // Start the Python event source process
            const pythonProcess = spawn('python', ['-c', `
import sys
import json
import asyncio
import os
sys.path.append('${sourcePath.replace(/\\/g, '\\\\')}')

try:
    # Import the event source
    if os.path.exists('${entryPoint.replace(/\\/g, '\\\\')}'):
        exec(open('${entryPoint.replace(/\\/g, '\\\\')}').read())
    else:
        from src.event_source import EventSource
    
    # Configuration
    config = ${JSON.stringify(processConfig)}
    
    # Create and run event source
    async def main():
        event_source = EventSource()
        await event_source.initialize(config['config'])
        await event_source.start()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
    
    asyncio.run(main())
    
except Exception as e:
    error = {"error": str(e), "success": False}
    print(json.dumps(error))
`], {
                env: { ...process.env }
            });

            sourceEntry.process = pythonProcess;
            sourceEntry.status = 'running';

            // Handle process output
            pythonProcess.stdout.on('data', (data) => {
                const output = data.toString().trim();
                if (output) {
                    try {
                        // Try to parse as event JSON
                        const eventData = JSON.parse(output);
                        this.handleEventFromSource(sourceId, eventData);
                    } catch (e) {
                        // Regular log output
                        logger.info(`[${sourceId}] ${output}`);
                    }
                }
            });

            pythonProcess.stderr.on('data', (data) => {
                const error = data.toString().trim();
                logger.error(`[${sourceId}] ${error}`);
                sourceEntry.errors.push(error);
            });

            pythonProcess.on('close', (code) => {
                logger.info(`[${sourceId}] Processo terminato con codice ${code}`);
                sourceEntry.status = code === 0 ? 'stopped' : 'error';
                
                if (code !== 0) {
                    sourceEntry.errors.push(`Processo terminato con codice ${code}`);
                }
            });

            pythonProcess.on('error', (error) => {
                logger.error(`[${sourceId}] Errore processo: ${error.message}`, error);
                sourceEntry.status = 'error';
                sourceEntry.errors.push(error.message);
            });

            logger.info(`Event source ${sourceId} avviato con successo`);
            this.emit('sourceStarted', { sourceId, config });

        } catch (error) {
            logger.error(`Impossibile avviare event source ${sourceId}: ${error.message}`, error);
            this.activeSources.delete(sourceId);
            throw error;
        }
    }

    /**
     * Stop an event source
     */
    async stopSource(sourceId) {
        logger.info(`Arresto event source: ${sourceId}`);
        
        const source = this.activeSources.get(sourceId);
        if (!source) {
            throw new Error(`Event source ${sourceId} non è in esecuzione`);
        }

        if (source.process) {
            source.status = 'stopping';
            
            // Try graceful shutdown first
            source.process.kill('SIGTERM');
            
            // Force kill after timeout
            setTimeout(() => {
                if (source.process && !source.process.killed) {
                    logger.warn(`Forza arresto event source ${sourceId}`);
                    source.process.kill('SIGKILL');
                }
            }, 5000);
        }

        this.activeSources.delete(sourceId);
        logger.info(`Event source ${sourceId} arrestato`);
        this.emit('sourceStopped', { sourceId });
    }

    /**
     * Handle event received from event source
     */
    handleEventFromSource(sourceId, eventData) {
        const source = this.activeSources.get(sourceId);
        if (source) {
            source.eventsEmitted = (source.eventsEmitted || 0) + 1;
            source.lastActivity = new Date();
        }

        logger.debug(`Evento ricevuto da ${sourceId}: ${JSON.stringify(eventData)}`);
        
        // Emit event for external listeners
        this.emit('eventReceived', {
            sourceId,
            eventType: eventData.eventType,
            data: eventData.data,
            timestamp: new Date()
        });
    }

    /**
     * Stop all running event sources
     */
    async stopAll() {
        logger.info('Arresto di tutti gli event sources...');
        const stopPromises = [];
        
        for (const sourceId of this.activeSources.keys()) {
            stopPromises.push(this.stopSource(sourceId).catch(err => 
                logger.error(`Errore arresto ${sourceId}: ${err.message}`, err)
            ));
        }
        
        await Promise.all(stopPromises);
        logger.info('Tutti gli event sources arrestati');
    }
}

export default EventSourceManager;
