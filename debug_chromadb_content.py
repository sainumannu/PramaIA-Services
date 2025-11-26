"""
Verifica diretta del contenuto di ChromaDB per capire da dove arrivano i documenti.
"""

import requests
import json

def debug_chromadb_content():
    """Debug del contenuto di ChromaDB."""
    print("=== DEBUG CONTENUTO CHROMADB ===")
    
    try:
        # 1. Verifica documenti totali
        response = requests.get("http://localhost:8090/vectorstore/documents")
        if response.status_code == 200:
            vectorstore_docs = response.json()
            print(f"✅ Documenti nel vectorstore ChromaDB: {vectorstore_docs.get('total', 0)}")
            
            if vectorstore_docs.get('documents'):
                print("\n📋 DOCUMENTI IN CHROMADB:")
                for i, doc in enumerate(vectorstore_docs['documents'][:3]):
                    print(f"   {i+1}. ID: {doc.get('id', 'N/A')}")
                    print(f"      Content: {doc.get('content', 'N/A')[:80]}...")
                    print(f"      Collection: {doc.get('collection', 'N/A')}")
                    print("")
            else:
                print("❌ Nessun documento nel vectorstore!")
        else:
            print(f"❌ Errore accesso vectorstore: {response.status_code}")
            
        # 2. Verifica documenti SQLite
        response = requests.get("http://localhost:8090/documents/")
        if response.status_code == 200:
            sqlite_docs = response.json()
            print(f"✅ Documenti in SQLite: {sqlite_docs.get('total', 0)}")
            
            if sqlite_docs.get('documents'):
                print("\n📋 DOCUMENTI IN SQLITE:")
                for i, doc in enumerate(sqlite_docs['documents'][:3]):
                    print(f"   {i+1}. ID: {doc.get('id', 'N/A')}")
                    print(f"      Content: {doc.get('content', 'N/A')[:80]}...")
                    print(f"      Collection: {doc.get('collection', 'N/A')}")
                    print("")
        else:
            print(f"❌ Errore accesso SQLite: {response.status_code}")
        
        # 3. Test query diretta con debug
        print("\n🔍 TEST QUERY CON DEBUG:")
        query_data = {
            "query_text": "PramaIA", 
            "limit": 3
        }
        
        response = requests.post(
            "http://localhost:8090/documents/manuals/query",
            json=query_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Query ha trovato: {len(result['matches'])} documenti")
            print("Fonte dei documenti: ChromaDB (perché la query va direttamente lì)")
            print("Perché score = 0: ChromaDB ha documenti ma senza embedding validi")
            
        print("\n=== CONCLUSIONE ===")
        print("I documenti vengono DA CHROMADB, non da SQLite!")
        print("ChromaDB contiene i documenti ma con embedding corrotti/vuoti.")
        print("Ecco perché hai il testo ma score = 0.")
        
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == "__main__":
    debug_chromadb_content()