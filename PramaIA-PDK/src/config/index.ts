/**
 * Configurazione centralizzata per PramaIA-PDK
 * Gestisce tutte le porte e URL utilizzati nel sistema
 */

// Carica le variabili d'ambiente dal file .env se disponibile
// config(); // TODO: Uncomment after installing dotenv

export interface PdkConfig {
  ports: {
    backend: number;
    frontend: number;
    pluginDocumentMonitor: number;
    pdkServer: number;
  };
  urls: {
    backendBaseUrl: string;
    frontendBaseUrl: string;
    pluginDocumentMonitorBaseUrl: string;
    pdkServerBaseUrl: string;
  };
  timeouts: {
    defaultTimeout: number;
    pluginTimeout: number;
  };
}

// Legge la configurazione dalle variabili d'ambiente o usa i valori di default
export const PDK_CONFIG: PdkConfig = {
  ports: {
    backend: parseInt(process.env.BACKEND_PORT || '8000'),
    frontend: parseInt(process.env.FRONTEND_PORT || '3000'),
    pluginDocumentMonitor: parseInt(process.env.PLUGIN_DOCUMENT_MONITOR_PORT || '8001'),
    pdkServer: parseInt(process.env.PDK_SERVER_PORT || '3001'),
  },
  urls: {
    backendBaseUrl: process.env.BACKEND_BASE_URL || `http://localhost:${parseInt(process.env.BACKEND_PORT || '8000')}`,
    frontendBaseUrl: process.env.FRONTEND_BASE_URL || `http://localhost:${parseInt(process.env.FRONTEND_PORT || '3000')}`,
    pluginDocumentMonitorBaseUrl: process.env.PLUGIN_DOCUMENT_MONITOR_BASE_URL || `http://localhost:${parseInt(process.env.PLUGIN_DOCUMENT_MONITOR_PORT || '8001')}`,
    pdkServerBaseUrl: process.env.PDK_SERVER_BASE_URL || `http://localhost:${parseInt(process.env.PDK_SERVER_PORT || '3001')}`,
  },
  timeouts: {
    defaultTimeout: parseInt(process.env.DEFAULT_TIMEOUT || '30000'),
    pluginTimeout: parseInt(process.env.PLUGIN_TIMEOUT || '30000'),
  },
};

// Esporta le costanti per retrocompatibilità
export const BACKEND_PORT = PDK_CONFIG.ports.backend;
export const FRONTEND_PORT = PDK_CONFIG.ports.frontend;
export const PLUGIN_DOCUMENT_MONITOR_PORT = PDK_CONFIG.ports.pluginDocumentMonitor;
export const PDK_SERVER_PORT = PDK_CONFIG.ports.pdkServer;

export const BACKEND_BASE_URL = PDK_CONFIG.urls.backendBaseUrl;
export const FRONTEND_BASE_URL = PDK_CONFIG.urls.frontendBaseUrl;
export const PLUGIN_DOCUMENT_MONITOR_BASE_URL = PDK_CONFIG.urls.pluginDocumentMonitorBaseUrl;
export const PDK_SERVER_BASE_URL = PDK_CONFIG.urls.pdkServerBaseUrl;

export const DEFAULT_TIMEOUT = PDK_CONFIG.timeouts.defaultTimeout;
export const PLUGIN_TIMEOUT = PDK_CONFIG.timeouts.pluginTimeout;
