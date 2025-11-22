"""
Test per simulare un evento da un event source e verificare che venga inoltrato al PramaIAServer.
"""

import requests
import json
import time

print("=== Test Inoltro Eventi PDK → PramaIAServer ===\n")

# URL del PDK server
pdk_url = "http://localhost:3001"

# URL del PramaIAServer
server_url = "http://localhost:8000"

# Step 1: Verifica che entrambi i server siano attivi
print("--- Step 1: Verifica connettività ---")
try:
    pdk_health = requests.get(f"{pdk_url}/health", timeout=5)
    print(f"✅ PDK Server: {pdk_health.status_code}")
except Exception as e:
    print(f"❌ PDK Server non raggiungibile: {e}")
    exit(1)

try:
    server_health = requests.get(f"{server_url}/health", timeout=5)
    print(f"✅ PramaIAServer: {server_health.status_code}")
except Exception as e:
    print(f"❌ PramaIAServer non raggiungibile: {e}")
    exit(1)

# Step 2: Simula un evento inviato al sistema di eventi del PramaIAServer
print("\n--- Step 2: Invio evento di test diretto al PramaIAServer ---")
event_payload = {
    "event_type": "test_pdk_event",
    "data": {
        "test_field": "test_value",
        "document_id": "test-doc-001",
        "file_name": "test.pdf"
    },
    "metadata": {
        "source": "pdk-test-script",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "additional_data": {
            "test_mode": True
        }
    }
}

try:
    response = requests.post(
        f"{server_url}/api/events/process",
        json=event_payload,
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Evento processato dal server")
        print(f"   Event ID: {result.get('event_id')}")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        print(f"   Triggers matched: {len(result.get('results', []))}")
    else:
        print(f"⚠️  Risposta: {response.status_code}")
        print(f"   {response.text}")
        
except Exception as e:
    print(f"❌ Errore invio evento: {e}")

# Step 3: Verifica i log sul LogService
print("\n--- Step 3: Verifica log sul LogService ---")
time.sleep(2)  # Aspetta che i log vengano inviati

try:
    log_response = requests.get(
        "http://localhost:8081/api/logs",
        params={
            "project": "PramaIA-PDK",
            "level": "lifecycle",
            "limit": 5
        },
        headers={
            "X-API-Key": "pramaialog_o6hlpft585hkykgb"
        },
        timeout=5
    )
    
    if log_response.status_code == 200:
        logs = log_response.json()
        print(f"✅ Log trovati: {len(logs)}")
        
        for log in logs[:3]:
            print(f"\n   [{log['timestamp']}] {log['level'].upper()}")
            print(f"   Module: {log['module']}")
            print(f"   Message: {log['message'][:80]}...")
            if 'event_type' in log.get('details', {}):
                print(f"   Event Type: {log['details']['event_type']}")
    else:
        print(f"⚠️  Errore recupero log: {log_response.status_code}")
        
except Exception as e:
    print(f"❌ Errore verifica log: {e}")

print("\n✅ Test completato!")
print("\nPer testare con un event source reale:")
print("1. Avvia un event source dal PDK")
print("2. Triggera un evento (es. crea un file nella cartella monitorata)")
print("3. Verifica i log sul LogService dashboard: http://localhost:8081/dashboard")
