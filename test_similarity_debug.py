"""
Test script per diagnosticare il problema del similarity score = 0.
Verifica se i documenti hanno embedding in ChromaDB.
"""

import requests
import json

def test_chromadb_embeddings():
    """Test per verificare la presenza di embedding in ChromaDB."""
    print("=== DIAGNOSI SIMILARITY SCORE = 0 ===")
    
    # 1. Verifica documenti in SQLite
    try:
        response = requests.get("http://localhost:8090/documents/")
        documents = response.json()
        print(f"✅ Documenti in SQLite: {documents['total']}")
        
        if documents['documents']:
            first_doc = documents['documents'][0]
            print(f"   Primo documento: {first_doc['id']}")
            print(f"   Contenuto: {first_doc.get('content', 'N/A')[:100]}...")
    except Exception as e:
        print(f"❌ Errore verifica SQLite: {e}")
        return
    
    # 2. Verifica stato vectorstore
    try:
        response = requests.get("http://localhost:8090/vectorstore/")
        vectorstore = response.json()
        print(f"✅ Vectorstore ChromaDB:")
        print(f"   Documenti: {vectorstore['documents_count']}")
        print(f"   Collezioni: {vectorstore['collections_count']}")
    except Exception as e:
        print(f"❌ Errore verifica vectorstore: {e}")
        return
    
    # 3. Test query diretta per debug
    try:
        query_data = {
            "query_text": "PramaIA",
            "limit": 3
        }
        
        response = requests.post(
            "http://localhost:8090/documents/manuals/query",
            json=query_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Query semantica riuscita: {len(results['matches'])} risultati")
            
            for i, match in enumerate(results['matches']):
                print(f"   Risultato {i+1}:")
                print(f"     ID: {match['id']}")
                print(f"     Score: {match['similarity_score']}")
                print(f"     Contenuto: {match['document'][:80]}...")
                
                if match['similarity_score'] == 0.0:
                    print(f"     ⚠️ PROBLEMA: Score = 0.0 indica distanza ChromaDB = 1.0")
                    print(f"     Causa probabile: Documento senza embedding nel vectorstore")
        else:
            print(f"❌ Query semantica fallita: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Errore query semantica: {e}")
    
    # 4. Raccomandazioni
    print("\n=== DIAGNOSI ===")
    print("Se tutti i similarity_score sono 0.0, il problema è:")
    print("1. 📄 I documenti sono salvati solo in SQLite")
    print("2. 🔍 I documenti NON hanno embedding nel vectorstore ChromaDB")
    print("3. 🔧 La sincronizzazione SQLite -> ChromaDB non funziona")
    print("\n=== SOLUZIONI ===")
    print("1. Verificare che i documenti vengano indicizzati in ChromaDB")
    print("2. Controllare i log del VectorstoreService per errori di embedding")
    print("3. Testare la creazione di un nuovo documento con embedding")

if __name__ == "__main__":
    test_chromadb_embeddings()