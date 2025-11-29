"""
Debug specifico per il calcolo della similarity nel VectorStore.
"""

import requests
import chromadb
import os

def test_direct_chromadb_query():
    """Test query diretta su ChromaDB senza passare dal VectorStore."""
    print("=== TEST DIRETTO CHROMADB ===")
    
    # Path ChromaDB
    chroma_path = os.path.join(os.getcwd(), "PramaIA-VectorstoreService", "data", "chroma_db")
    print(f"📁 ChromaDB path: {chroma_path}")
    
    # Connettiti a ChromaDB
    client = chromadb.PersistentClient(path=chroma_path)
    
    # Ottieni collezione
    collection = client.get_collection("prama_documents")
    print(f"📚 Collezione: {collection.name}")
    print(f"📊 Documenti totali: {collection.count()}")
    
    # Test query
    query_text = "PramaIA"
    print(f"\n🔍 QUERY: '{query_text}'")
    
    # Query con ChromaDB
    results = collection.query(
        query_texts=[query_text],
        n_results=5,
        include=['documents', 'metadatas', 'distances', 'embeddings']
    )
    
    print(f"\n📋 RISULTATI RAW:")
    print(f"   IDs: {len(results['ids'][0])}")
    print(f"   Documents: {len(results['documents'][0])}")
    print(f"   Distances: {results['distances'][0] if results['distances'] else 'None'}")
    
    # Calcola similarity manualmente
    if results['distances'] and results['distances'][0]:
        print(f"\n🧮 CALCOLO SIMILARITY:")
        for i, distance in enumerate(results['distances'][0]):
            similarity = max(0.0, 1.0 - distance)
            doc_id = results['ids'][0][i] if i < len(results['ids'][0]) else f"doc_{i}"
            print(f"   Doc {i} ({doc_id}): distance={distance}, similarity={similarity}")
    
    return results

def test_vectorstore_api_query():
    """Test query via API del VectorStore."""
    print("\n=== TEST API VECTORSTORE ===")
    
    query_data = {
        "query_text": "PramaIA",
        "limit": 5
    }
    
    response = requests.post(
        "http://localhost:8090/documents/prama_documents/query", 
        json=query_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"🔍 Query API: '{query_data['query_text']}'")
        print(f"📊 Risultati: {len(result.get('matches', []))}")
        
        for i, match in enumerate(result.get('matches', [])):
            score = match.get('similarity_score', 0)
            doc_id = match.get('id', 'unknown')
            print(f"   Match {i} ({doc_id}): similarity_score={score}")
    else:
        print(f"❌ API Error: {response.status_code} - {response.text}")

def compare_results():
    """Confronta i risultati diretti vs API."""
    print("\n=== CONFRONTO RISULTATI ===")
    
    # Test diretti
    direct_results = test_direct_chromadb_query()
    
    # Test API
    test_vectorstore_api_query()
    
    print("\n🔍 ANALISI:")
    if direct_results and direct_results['distances'] and direct_results['distances'][0]:
        distances = direct_results['distances'][0]
        print(f"   Distanze ChromaDB: {distances}")
        print(f"   Range distanze: {min(distances):.4f} - {max(distances):.4f}")
        
        # Controlla se le distanze sono normalizzate
        if any(d > 1.0 for d in distances):
            print("   ⚠️ PROBLEMA: Distanze > 1.0 trovate!")
        if any(d < 0.0 for d in distances):
            print("   ⚠️ PROBLEMA: Distanze negative trovate!")

if __name__ == "__main__":
    compare_results()