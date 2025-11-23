"""
Test rapido per verificare l'estrazione e invio metadati
Script semplificato per debug veloce
"""
import os
import json
import tempfile
import sys
from pathlib import Path

# Aggiungi il percorso src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_metadata_extraction():
    """Test rapido dell'estrazione metadati"""
    print("🔍 Test estrazione metadati...")
    
    try:
        from src.unified_file_handler import UnifiedFileHandler
        from src.event_buffer import EventBuffer
        
        # Crea file di test temporaneo
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test file per estrazione metadati")
            test_file = f.name
            
        # Test estrazione
        event_buffer = EventBuffer()
        handler = UnifiedFileHandler([], os.path.dirname(test_file), event_buffer)
        metadata = handler._extract_file_metadata(test_file)
        
        # Verifica risultati - solo campi obbligatori
        required_fields = ["filename_original", "file_size_original", "date_created", "date_modified"]
        missing = [field for field in required_fields if field not in metadata]
        
        if not missing:
            print(f"✅ Metadati estratti correttamente: {len(metadata)} campi")
            print(f"   📄 File: {metadata.get('filename_original')}")
            print(f"   📦 Dimensione: {metadata.get('file_size_original')} bytes")
            print(f"   📅 Creato: {metadata.get('date_created')}")
            print(f"   📝 Modificato: {metadata.get('date_modified')}")
            # Mostra campi opzionali se presenti
            optional_fields = [k for k in metadata.keys() if k not in required_fields]
            if optional_fields:
                print(f"   ➕ Campi opzionali: {', '.join(optional_fields)}")
            result = True
        else:
            print(f"❌ Campi mancanti: {missing}")
            result = False
            
        # Cleanup
        os.unlink(test_file)
        return result
        
    except Exception as e:
        print(f"❌ Errore test metadati: {str(e)}")
        return False

def test_payload_format():
    """Test formato payload per backend"""
    print("📦 Test formato payload...")
    
    try:
        # Metadati simulati con campi obbligatori e alcuni opzionali
        metadata = {
            # Campi obbligatori
            "filename_original": "test.pdf",
            "file_size_original": 1024,
            "date_created": "2024-01-01T12:00:00",
            "date_modified": "2024-01-01T12:00:00",
            # Campi opzionali (solo se disponibili)
            "author": "Test Author",
            "title": "Test Document"
        }
        
        # Costruisci payload come farebbe l'agent
        client_id = os.getenv("CLIENT_ID", "test-agent")
        metadata_payload = {
            "client_id": client_id,
            "original_path": "/test/path/test.pdf",
            "source": "agent",
            "metadata": metadata
        }
        
        data = {
            "action": "created",
            "metadata": json.dumps(metadata_payload),
            "filter_action": "process",
            "extract_metadata": json.dumps(True),
            "filter_name": "test_filter",
            "should_process_content": True
        }
        
        # Verifica formato
        try:
            # Test parsing JSON
            parsed_metadata = json.loads(data["metadata"])
            required_keys = ["client_id", "original_path", "source", "metadata"]
            missing_keys = [key for key in required_keys if key not in parsed_metadata]
            
            if not missing_keys:
                print("✅ Formato payload corretto")
                print(f"   🆔 Client ID: {parsed_metadata['client_id']}")
                print(f"   📁 Path originale: {parsed_metadata['original_path']}")
                print(f"   🔄 Source: {parsed_metadata['source']}")
                print(f"   📋 Campi metadati: {len(parsed_metadata['metadata'])}")
                return True
            else:
                print(f"❌ Chiavi mancanti nel payload: {missing_keys}")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Errore parsing JSON: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ Errore test payload: {str(e)}")
        return False

def test_environment_config():
    """Test configurazione ambiente"""
    print("⚙️ Test configurazione ambiente...")
    
    config_items = [
        ("CLIENT_ID", os.getenv("CLIENT_ID", "MISSING")),
        ("BACKEND_URL", os.getenv("BACKEND_URL", "MISSING")),
        ("BACKEND_PORT", os.getenv("BACKEND_PORT", "8000")),
        ("BACKEND_BASE_URL", os.getenv("BACKEND_BASE_URL", "MISSING"))
    ]
    
    all_good = True
    for key, value in config_items:
        status = "✅" if value != "MISSING" else "⚠️"
        print(f"   {status} {key}: {value}")
        if value == "MISSING" and key in ["CLIENT_ID"]:
            all_good = False
            
    return all_good

def main():
    """Esegui test rapidi"""
    print("🧪 Test rapido metadati agent")
    print("="*50)
    
    tests = [
        ("Configurazione ambiente", test_environment_config),
        ("Estrazione metadati", test_metadata_extraction),
        ("Formato payload", test_payload_format)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        result = test_func()
        results.append((test_name, result))
        
    print("\n" + "="*50)
    print("📊 RISULTATI:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
            
    success_rate = (passed / len(results)) * 100
    print(f"\n🎯 Successo: {passed}/{len(results)} ({success_rate:.0f}%)")
    
    if success_rate >= 80:
        print("🎉 Test completati con successo!")
        return 0
    else:
        print("⚠️ Alcuni test falliti - verificare configurazione")
        return 1

if __name__ == "__main__":
    exit(main())