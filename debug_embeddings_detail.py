#!/usr/bin/env python3
"""
Debug specifico per embeddings in ChromaDB - verifica se esistono e sono validi
"""

import chromadb
from chromadb.config import Settings
import os

def debug_chromadb_embeddings():
    """Debug dettagliato degli embeddings in ChromaDB"""
    
    print("=== DEBUG EMBEDDINGS CHROMADB ===")
    
    # Connettiti a ChromaDB - PERCORSO CORRETTO!
    chroma_path = os.path.abspath("./PramaIA-VectorstoreService/data/chroma_db")
    print(f"📁 ChromaDB path: {chroma_path}")
    
    try:
        client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Lista collezioni
        collections = client.list_collections()
        print(f"📚 Collezioni trovate: {len(collections)}")
        
        for collection in collections:
            print(f"\n🔍 ANALISI COLLEZIONE: {collection.name}")
            print(f"   📊 Documenti totali: {collection.count()}")
            
            # Ottieni tutti i documenti con embeddings
            try:
                result = collection.get(
                    include=['embeddings', 'documents', 'metadatas']  # Rimosso 'distances' 
                )
                
                print(f"   📋 IDs: {len(result.get('ids', []))}")
                print(f"   📄 Documents: {len(result.get('documents', []))}")
                print(f"   🧠 Embeddings: {len(result.get('embeddings', []))}")
                print(f"   🏷️ Metadatas: {len(result.get('metadatas', []))}")
                
                # Analizza embeddings
                embeddings = result.get('embeddings', [])
                if embeddings:
                    print(f"\n   🧠 ANALISI EMBEDDINGS:")
                    for i, embedding in enumerate(embeddings[:3]):  # Solo primi 3
                        if embedding:
                            print(f"      Doc {i}: {len(embedding)} dimensioni")
                            print(f"               Primi 5 valori: {embedding[:5]}")
                            print(f"               Tutti zero?: {all(x == 0.0 for x in embedding)}")
                        else:
                            print(f"      Doc {i}: EMBEDDING VUOTO/NULL")
                else:
                    print("   ❌ NESSUN EMBEDDING TROVATO!")
                
                # Prova una query di test
                print(f"\n   🔍 TEST QUERY:")
                try:
                    query_result = collection.query(
                        query_texts=["test PramaIA"],
                        n_results=2,
                        include=['documents', 'distances', 'embeddings']
                    )
                    
                    distances = query_result.get('distances', [[]])[0]
                    print(f"      Distanze ottenute: {distances}")
                    
                    if distances:
                        for i, dist in enumerate(distances):
                            similarity = max(0.0, 1.0 - dist)
                            print(f"      Doc {i}: distanza={dist}, similarità={similarity}")
                    
                except Exception as e:
                    print(f"      ❌ Errore query: {e}")
                        
            except Exception as e:
                print(f"   ❌ Errore accesso collezione: {e}")
    
    except Exception as e:
        print(f"❌ Errore connessione ChromaDB: {e}")

if __name__ == "__main__":
    debug_chromadb_embeddings()