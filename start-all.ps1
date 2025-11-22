# PramaIA - Script di avvio completo (versione semplificata)
# Avvia tutti i servizi dell'ecosistema PramaIA

param(
    [string]$PDKLogLevel = "INFO",
    [switch]$Verbose,
    [switch]$SkipDependencyCheck,
    [string]$ConfigFile = "PramaIAServer\.env"
)

Write-Host "PramaIA - Avvio completo dell'ecosistema" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# Funzione per fermare i servizi esistenti
function Stop-ExistingServices {
    param([string[]]$ServiceNames, [int[]]$Ports)

    Write-Host "Verifica e arresto dei servizi esistenti..." -ForegroundColor Yellow
    
    # 1. Ferma le finestre PowerShell con titoli specifici
    $processes = Get-Process -Name "powershell" -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -in $ServiceNames }
    
    if ($processes) {
        foreach ($proc in $processes) {
            Write-Host "   Trovato servizio PowerShell: $($proc.MainWindowTitle). Arresto in corso..." -ForegroundColor Gray
            Stop-Process -Id $proc.Id -Force
        }
    }
    
    # 2. Ferma tutti i processi che occupano le porte specificate
    foreach ($port in $Ports) {
        try {
            $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
            foreach ($conn in $connections) {
                $processId = $conn.OwningProcess
                $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                if ($process) {
                    Write-Host "   Uccisione processo sulla porta ${port}: PID $processId ($($process.ProcessName))" -ForegroundColor Gray
                    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                }
            }
        } catch {
            # Porta non in uso, ignora
        }
    }
    
    # 3. Aspetta che le porte si liberino
    Start-Sleep -Seconds 2
    
    Write-Host "   Pulizia completata." -ForegroundColor Green
    Write-Host ""
}

# Lista dei nomi dei servizi per la pulizia
$serviceNames = @(
    "Log Service",
    "PDK Server",
    "VectorStore Service",
    "PDF Monitor Agent",
    "Reconciliation Service",
    "Backend FastAPI",
    "Frontend React"
)

# Lista delle porte da liberare
$servicePorts = @(8000, 8001, 8081, 8090, 8091, 3000, 3001)

Stop-ExistingServices -ServiceNames $serviceNames -Ports $servicePorts


# Controllo prerequisiti
if (-not $SkipDependencyCheck) {
    Write-Host "Verifica prerequisiti..." -ForegroundColor Cyan
    
    # Verifica Node.js per PDK
    try {
        $nodeVersion = node --version 2>$null
        Write-Host "   Node.js: $nodeVersion" -ForegroundColor Green
    } catch {
        Write-Host "   Node.js non trovato (richiesto per PDK Server)" -ForegroundColor Red
    }
    
    # Verifica Python
    try {
        $pythonVersion = python --version 2>$null
        Write-Host "   Python: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "   Python non trovato" -ForegroundColor Red
    }
    
    # Verifica NPM (per frontend)
    try {
        $npmVersion = npm --version 2>$null
        Write-Host "   NPM: $npmVersion" -ForegroundColor Green
    } catch {
        Write-Host "   NPM non trovato (richiesto per Frontend React)" -ForegroundColor Red
    }
    
    Write-Host ""
}

# Funzione per caricare variabili d'ambiente dal file .env
function Load-EnvFile {
    param([string]$EnvFilePath)
    
    if (Test-Path $EnvFilePath) {
        Write-Host "Caricamento configurazioni da: $EnvFilePath" -ForegroundColor Yellow
        $envContent = Get-Content $EnvFilePath
        
        foreach ($line in $envContent) {
            if ($line -match '^\s*#' -or $line -match '^\s*$') { continue }
            
            if ($line -match '^([^#][^=]+)=(.*)$') {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                
                if ($value.StartsWith('"') -and $value.EndsWith('"')) {
                    $value = $value.Substring(1, $value.Length - 2)
                }
                
                [Environment]::SetEnvironmentVariable($name, $value, [EnvironmentVariableTarget]::Process)
                if ($Verbose) {
                    Write-Host "   $name=$value" -ForegroundColor Gray
                }
            }
        }
    } else {
        Write-Host "File .env non trovato: $EnvFilePath. Uso configurazioni predefinite." -ForegroundColor Yellow
    }
}

# Carica configurazioni dal file specificato
if (Test-Path $ConfigFile) {
    Load-EnvFile $ConfigFile
}

# Configurazioni con fallback ai valori di default
$FRONTEND_PORT = [Environment]::GetEnvironmentVariable("FRONTEND_PORT")
if (-not $FRONTEND_PORT) { $FRONTEND_PORT = "3000" }
$PDK_SERVER_PORT = [Environment]::GetEnvironmentVariable("PDK_SERVER_PORT")
if (-not $PDK_SERVER_PORT) { $PDK_SERVER_PORT = "3001" }
$PLUGIN_PDF_MONITOR_PORT = [Environment]::GetEnvironmentVariable("PLUGIN_PDF_MONITOR_PORT")
if (-not $PLUGIN_PDF_MONITOR_PORT) { $PLUGIN_PDF_MONITOR_PORT = "8001" }
$VECTORSTORE_SERVICE_PORT = [Environment]::GetEnvironmentVariable("VECTORSTORE_SERVICE_PORT")
if (-not $VECTORSTORE_SERVICE_PORT) { $VECTORSTORE_SERVICE_PORT = "8090" }
$LOG_SERVICE_PORT = [Environment]::GetEnvironmentVariable("LOG_SERVICE_PORT")
if (-not $LOG_SERVICE_PORT) { $LOG_SERVICE_PORT = "8081" }
$RECONCILIATION_SERVICE_PORT = [Environment]::GetEnvironmentVariable("RECONCILIATION_SERVICE_PORT")
if (-not $RECONCILIATION_SERVICE_PORT) { $RECONCILIATION_SERVICE_PORT = "8091" }

# URL calcolati
$FRONTEND_BASE_URL = [Environment]::GetEnvironmentVariable("FRONTEND_BASE_URL")
if (-not $FRONTEND_BASE_URL) { $FRONTEND_BASE_URL = "http://localhost:$FRONTEND_PORT" }
$PDK_SERVER_BASE_URL = [Environment]::GetEnvironmentVariable("PDK_SERVER_BASE_URL")
if (-not $PDK_SERVER_BASE_URL) { $PDK_SERVER_BASE_URL = "http://localhost:$PDK_SERVER_PORT" }

Write-Host "Configurazioni attive:" -ForegroundColor Cyan
Write-Host "   Frontend React:     $FRONTEND_BASE_URL" -ForegroundColor White
Write-Host "   PDK Server:         $PDK_SERVER_BASE_URL" -ForegroundColor White
Write-Host "   PDK Log Level:      $PDKLogLevel" -ForegroundColor White
Write-Host ""

# Funzione per avviare un servizio
function Start-PramaService {
    param(
        [string]$Name,
        [string]$Path,
        [string]$Command,
        [int]$StartupDelay = 2,
        [switch]$Critical
    )
    
    Write-Host "Avvio $Name in una nuova finestra..." -ForegroundColor Green
    
    if (Test-Path $Path) {
        
        # Costruisce il comando da eseguire nella nuova finestra, impostando il titolo
        $fullCommand = "`$Host.UI.RawUI.WindowTitle = '$Name'; Set-Location -Path `"$Path`"; $Command"
        Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $fullCommand
        
        Write-Host "   $Name avviato." -ForegroundColor Gray
        
        # Attendi startup del servizio
        if ($StartupDelay -gt 0) {
            Start-Sleep -Seconds $StartupDelay
        }
        
        return $true # Ritorna successo
    } else {
        $message = "   Percorso non trovato: $Path"
        if ($Critical) {
            Write-Host $message -ForegroundColor Red
            Write-Host "   ERRORE CRITICO: Servizio essenziale non disponibile!" -ForegroundColor Red
        } else {
            Write-Host $message -ForegroundColor Yellow
        }
        return $false # Ritorna fallimento
    }
}

# Array per tenere traccia dei processi avviati
$processes = @()
$criticalServices = 0
$optionalServices = 0

Write-Host "Avvio servizi in sequenza..." -ForegroundColor Cyan
Write-Host ""

# 1. Avvio Log Service (Opzionale)
Write-Host "1. Log Service" -ForegroundColor Blue
if (Test-Path "PramaIA-LogService") {
    if (Start-PramaService -Name "Log Service" -Path "PramaIA-LogService" -Command ".\venv\Scripts\python.exe main.py" -StartupDelay 5) { 
        $optionalServices++
    }
} else {
    Write-Host "   Log Service non trovato" -ForegroundColor Yellow
}

# 2. Avvio PDK Server (Critico)
Write-Host "2. PDK Server (Critico)" -ForegroundColor Magenta
if (Test-Path "PramaIA-PDK\server") {
    if (Start-PramaService -Name "PDK Server" -Path "PramaIA-PDK\server" -Command "node plugin-api-server.js" -StartupDelay 5 -Critical) { 
        $criticalServices++
    }
} else {
    Write-Host "   PDK Server non trovato in PramaIA-PDK\server" -ForegroundColor Yellow
}

# 3. Avvio VectorStore Service (Opzionale)
Write-Host "3. VectorStore Service" -ForegroundColor Blue
if (Test-Path "PramaIA-VectorstoreService") {
    if (Start-PramaService -Name "VectorStore Service" -Path "PramaIA-VectorstoreService" -Command "python main.py" -StartupDelay 5) { 
        $optionalServices++
    }
} else {
    Write-Host "   VectorStore Service non trovato" -ForegroundColor Yellow
}

# 4. Avvio Reconciliation Service (Opzionale)
Write-Host "4. Reconciliation Service" -ForegroundColor Blue
if (Test-Path "PramaIA-Reconciliation") {
    if (Start-PramaService -Name "Reconciliation Service" -Path "PramaIA-Reconciliation" -Command "python main.py" -StartupDelay 5) { 
        $optionalServices++
    }
} else {
    Write-Host "   Reconciliation Service non trovato" -ForegroundColor Yellow
}



# 6. Avvio PDF Monitor Agent (Opzionale)
Write-Host "6. PDF Monitor Agent" -ForegroundColor Blue
if (Test-Path "PramaIA-Agents\document-folder-monitor-agent") {
    if (Start-PramaService -Name "PDF Monitor Agent" -Path "PramaIA-Agents\document-folder-monitor-agent" -Command "uvicorn src.main:app --reload --host 0.0.0.0 --port $PLUGIN_PDF_MONITOR_PORT" -StartupDelay 5) { 
        $optionalServices++
    }
} else {
    Write-Host "   PDF Monitor Agent non trovato" -ForegroundColor Yellow
}

# 7. Avvio Frontend React (Critico)
Write-Host "7. Frontend React (Critico)" -ForegroundColor Magenta
if (Test-Path "PramaIAServer\frontend\client") {
    if (Start-PramaService -Name "Frontend React" -Path "PramaIAServer\frontend\client" -Command "npm start" -StartupDelay 5 -Critical) { 
        $criticalServices++
    }
} elseif (Test-Path "frontend\client") {
    if (Start-PramaService -Name "Frontend React" -Path "frontend\client" -Command "npm start" -StartupDelay 5 -Critical) { 
        $criticalServices++
    }
} else {
    Write-Host "   Frontend non trovato" -ForegroundColor Red
}

# Controllo salute servizi critici
if ($criticalServices -lt 3) {
    Write-Host "ATTENZIONE: Non tutti i servizi critici sono stati avviati!" -ForegroundColor Red
    Write-Host "Verifica i percorsi e le dipendenze dei servizi mancanti." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Comandi utili:" -ForegroundColor Yellow
Write-Host "   - Ctrl+C per fermare questo script" -ForegroundColor Gray
Write-Host "   - Chiudi manualmente le finestre dei servizi per fermarli" -ForegroundColor Gray
Write-Host ""

Write-Host "Script principale in attesa. Premi Ctrl+C per terminare questo script." -ForegroundColor Green

try {
    # Mantieni lo script principale in attesa
    while ($true) {
        Start-Sleep -Seconds 60
    }
}
catch {
    Write-Host "Script principale interrotto." -ForegroundColor Yellow
}
finally {
    Write-Host ""
    Write-Host "Le finestre dei servizi rimangono aperte. Chiudile manualmente." -ForegroundColor Yellow
}