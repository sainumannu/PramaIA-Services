"""
Test per creare un documento con embedding funzionante.
"""

import requests
import json

def test_document_with_embedding():
    """Crea un documento di test che dovrebbe avere similarity score > 0."""
    
    print("=== TEST CREAZIONE DOCUMENTO CON EMBEDDING ===")
    
    # Documento di test che dovrebbe essere indicizzato correttamente
    test_doc = {
        "id": "test_embedding_fix_001",
        "content": "Questo è un documento di test per PramaIA che dovrebbe funzionare correttamente con gli embedding. Il sistema di ricerca semantica dovrebbe trovare questo documento quando si cerca PramaIA.",
        "collection": "manuals",
        "metadata": {
            "source": "test_fix",
            "created_by": "similarity_debug",
            "type": "test"
        }
    }
    
    try:
        # 1. Crea il documento
        print("1. Creazione documento di test...")
        response = requests.post(
            "http://localhost:8090/documents/",
            json=test_doc,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 201]:
            print("✅ Documento creato con successo")
            result = response.json()
            print(f"   ID: {result.get('id')}")
        else:
            print(f"❌ Errore creazione documento: {response.status_code} - {response.text}")
            return
        
        # 2. Aspetta un momento per l'indicizzazione
        import time
        print("2. Attesa indicizzazione...")
        time.sleep(2)
        
        # 3. Test query semantica
        print("3. Test query semantica...")
        query_data = {
            "query_text": "PramaIA embedding test",
            "limit": 5
        }
        
        response = requests.post(
            "http://localhost:8090/documents/manuals/query",
            json=query_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Query completata: {len(results['matches'])} risultati")
            
            for match in results['matches']:
                score = match['similarity_score']
                is_our_doc = match['id'] == "test_embedding_fix_001"
                
                color = "🟢" if score > 0 else "🔴"
                marker = "👆 NOSTRO TEST" if is_our_doc else ""
                
                print(f"   {color} ID: {match['id']}")
                print(f"      Score: {score}")
                print(f"      Content: {match['document'][:80]}... {marker}")
                
                if is_our_doc and score > 0:
                    print("   🎉 SUCCESSO! Il nuovo documento ha similarity score > 0!")
                    print("   Questo conferma che il problema era nei documenti esistenti.")
                elif is_our_doc and score == 0:
                    print("   ⚠️ Anche il nuovo documento ha score = 0")
                    print("   Il problema è nell'indicizzazione embedding!")
        else:
            print(f"❌ Errore query: {response.status_code} - {response.text}")
        
    except Exception as e:
        print(f"❌ Errore nel test: {e}")

if __name__ == "__main__":
    test_document_with_embedding()