// python-executor.js - Funzione per eseguire plugin Python
// Parte estratta da plugin-api-server.js per migliorare la manutenibilità

import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';

/**
 * Esegue un plugin Python tramite processo figlio
 * @param {string} PLUGIN_DIR - Directory base dei plugin
 * @param {string} pluginId - ID del plugin da eseguire
 * @param {string} nodeId - ID del nodo da eseguire
 * @param {Object} inputs - Input da passare al nodo
 * @param {Object} config - Configurazione del nodo
 * @param {Object} logger - Logger per messaggi diagnostici
 * @returns {Promise<Object>} Risultato dell'esecuzione del plugin
 */
export async function executePythonPlugin(PLUGIN_DIR, pluginId, nodeId, inputs, config, logger) {
    
    return new Promise((resolve, reject) => {
        const pluginPath = path.join(PLUGIN_DIR, pluginId, 'src', 'plugin.py');
        
        if (!fs.existsSync(pluginPath)) {
            logger.error(`Plugin ${pluginId} non trovato`);
            reject(new Error(`Plugin ${pluginId} non trovato`));
            return;
        }
        
        // Prepara i dati per il plugin Python
        const inputData = JSON.stringify({
            node_id: nodeId,
            inputs: inputs,
            config: config
        });
        
        logger.debug(`Esecuzione plugin Python: ${pluginId}, node: ${nodeId}`);
        
        // Esegue il plugin Python con logging disabilitato
        const pythonProcess = spawn('python', ['-c', `
import sys
import json
import asyncio
import logging
import os

# DISABILITA TUTTO IL LOGGING PER EVITARE CORRUZIONE STDOUT
logging.disable(logging.CRITICAL)
os.environ['PYTHONWARNINGS'] = 'ignore'

sys.path.append('${path.join(PLUGIN_DIR, pluginId, 'src').replace(/\\/g, '\\\\')}')

try:
    from plugin import process_node
    
    # Legge input da stdin
    input_data = json.loads('${inputData.replace(/'/g, "\\'")}')
    
    # Esegue il nodo
    async def main():
        result = await process_node(
            input_data['node_id'],
            input_data['inputs'], 
            input_data['config']
        )
        # Stampa SOLO JSON su stdout, nient'altro
        print(json.dumps(result))
    
    asyncio.run(main())
    
except Exception as e:
    error_result = {"error": str(e), "success": False}
    print(json.dumps(error_result))
`], {
            env: { 
                ...process.env, 
                PYTHONWARNINGS: 'ignore',
                PYTHONUNBUFFERED: '1'
            }
        });
        
        let output = '';
        let errorOutput = '';
        
        pythonProcess.stdout.on('data', (data) => {
            output += data.toString();
        });
        
        pythonProcess.stderr.on('data', (data) => {
            const error = data.toString();
            errorOutput += error;
            logger.warn(`Output stderr plugin ${pluginId}: ${error.trim()}`);
        });
        
        pythonProcess.on('close', (code) => {
            if (code === 0) {
                try {
                    // Prendi solo l'ULTIMA RIGA (dovrebbe essere il JSON pulito)
                    // Ignora tutto il logging precedente
                    const lines = output.trim().split('\n');
                    const lastLine = lines[lines.length - 1];
                    
                    logger.debug(`Output totale: ${lines.length} righe, parsing ultima riga`);
                    
                    const result = JSON.parse(lastLine);
                    logger.debug(`Plugin ${pluginId} completato con successo`);
                    resolve(result);
                } catch (e) {
                    const errorMsg = `Errore parsing output plugin ${pluginId}: ${e.message}`;
                    logger.error(errorMsg, e);
                    logger.error(`Output completo: ${output.length} caratteri`);
                    logger.error(`Prima riga: "${output.split('\n')[0].substring(0, 100)}"`);
                    logger.error(`Ultima riga: "${output.trim().split('\n').pop()}"`);
                    reject(new Error(errorMsg));
                }
            } else {
                const errorMsg = `Plugin ${pluginId} fallito (code ${code}): ${errorOutput}`;
                logger.error(errorMsg);
                reject(new Error(errorMsg));
            }
        });
        
        pythonProcess.on('error', (error) => {
            const errorMsg = `Errore esecuzione Python per plugin ${pluginId}: ${error.message}`;
            logger.error(errorMsg, error);
            reject(new Error(errorMsg));
        });
    });
}

// Esporta la funzione principale
export default executePythonPlugin;