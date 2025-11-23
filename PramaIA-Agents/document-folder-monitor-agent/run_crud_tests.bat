@echo off
echo 🧪 Avvio test CRUD metadati PramaIA Agent
echo ============================================

REM Imposta variabili d'ambiente di test se non presenti
if not defined CLIENT_ID (
    set CLIENT_ID=test-agent-crud
    echo ⚙️ Impostato CLIENT_ID=test-agent-crud
)

if not defined BACKEND_URL (
    set BACKEND_URL=http://localhost:8000
    echo ⚙️ Impostato BACKEND_URL=http://localhost:8000
)

echo.
echo 📋 Configurazione test:
echo    CLIENT_ID: %CLIENT_ID%
echo    BACKEND_URL: %BACKEND_URL%
echo.

REM Verifica se Python è disponibile
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python non trovato nel PATH
    pause
    exit /b 1
)

echo 🐍 Python trovato - avvio test...
echo.

REM Esegui test rapido prima
echo 🚀 Esecuzione test rapido...
python test_metadata_quick.py
set QUICK_RESULT=%ERRORLEVEL%

echo.
echo ================================================

REM Esegui test completo solo se il rapido passa
if %QUICK_RESULT% equ 0 (
    echo ✅ Test rapido superato - avvio test completo...
    echo.
    python test_crud_metadata.py
    set FULL_RESULT=%ERRORLEVEL%
) else (
    echo ⚠️ Test rapido fallito - skipping test completo
    set FULL_RESULT=1
)

echo.
echo ================================================
echo 📊 RISULTATO FINALE:

if %QUICK_RESULT% equ 0 (
    echo ✅ Test rapido: SUPERATO
) else (
    echo ❌ Test rapido: FALLITO
)

if %FULL_RESULT% equ 0 (
    echo ✅ Test completo: SUPERATO
) else (
    echo ❌ Test completo: FALLITO/SKIPPED
)

if %QUICK_RESULT% equ 0 if %FULL_RESULT% equ 0 (
    echo.
    echo 🎉 TUTTI I TEST SUPERATI!
    echo L'agent è pronto per l'uso con il nuovo formato metadati.
) else (
    echo.
    echo ⚠️ ALCUNI TEST FALLITI
    echo Verificare la configurazione e le dipendenze.
)

echo.
echo 📁 I report sono salvati nella directory corrente
echo 💡 Per debug dettagliato, controllare i file di log generati

echo.
pause