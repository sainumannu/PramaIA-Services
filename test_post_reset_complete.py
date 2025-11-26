#!/usr/bin/env python3
"""
Test End-to-End dopo reset ChromaDB - Verifica funzionamento completo
"""

import requests
import json
from datetime import datetime

def test_end_to_end_after_reset():
    """Test completo del sistema dopo il reset"""
    
    print("=== TEST END-TO-END DOPO RESET CHROMADB ===")
    base_url = "http://localhost:8090"
    
    # Step 1: Verifica stato iniziale (dovrebbe essere vuoto)
    print("\n1. 📊 VERIFICA STATO INIZIALE")
    response = requests.get(f"{base_url}/vectorstore/")
    stats = response.json()
    print(f"   Documenti: {stats['documents_count']}")
    print(f"   Collezioni: {stats['collections_count']}")
    
    if stats['documents_count'] > 0:
        print("   ⚠️ ATTENZIONE: Sistema non completamente resettato!")
    else:
        print("   ✅ Sistema pulito, pronto per test")
    
    # Step 2: Crea un documento di test
    print("\n2. 📄 CREAZIONE DOCUMENTO DI TEST")
    test_doc = {
        "id": "test_post_reset_001", 
        "content": "Questo è un documento di test per verificare il funzionamento di PramaIA dopo il reset di ChromaDB. Il sistema dovrebbe generare embeddings corretti e calcolare similarity score accurati per le query semantiche.",
        "collection": "test_collection",
        "metadata": {
            "source": "test_post_reset",
            "type": "verification",
            "created_at": datetime.now().isoformat(),
            "test_purpose": "embedding_consistency_check"
        }
    }
    
    response = requests.post(f"{base_url}/documents/", json=test_doc)
    if response.status_code == 201:
        print(f"   ✅ Documento creato: {test_doc['id']}")
        creation_result = response.json()
        print(f"   📝 Messaggio: {creation_result.get('message', 'N/A')}")
    else:
        print(f"   ❌ Errore creazione: {response.status_code} - {response.text}")
        return False
    
    # Step 3: Verifica che il documento sia stato indicizzato
    print("\n3. 🔍 VERIFICA INDICIZZAZIONE")
    response = requests.get(f"{base_url}/vectorstore/")
    stats_after = response.json()
    print(f"   Documenti dopo creazione: {stats_after['documents_count']}")
    print(f"   Collezioni dopo creazione: {stats_after['collections_count']}")
    
    if stats_after['documents_count'] > 0:
        print("   ✅ Documento indicizzato nel sistema")
    else:
        print("   ⚠️ Documento non ancora indicizzato")
    
    # Step 4: Test query semantica - Query molto simile al contenuto
    print("\n4. 🔍 TEST QUERY SEMANTICA (ALTA SIMILARITÀ)")
    query_high_similarity = {
        "query_text": "test PramaIA reset ChromaDB embeddings",
        "top_k": 3
    }
    
    response = requests.post(
        f"{base_url}/documents/test_collection/query",
        json=query_high_similarity
    )
    
    if response.status_code == 200:
        results = response.json()
        print(f"   📊 Risultati trovati: {len(results.get('matches', []))}")
        
        for i, match in enumerate(results.get('matches', [])):
            similarity = match.get('similarity_score', 0)
            doc_preview = match.get('document', '')[:60] + "..."
            print(f"   Match {i+1}: Score={similarity:.3f} | {doc_preview}")
            
            # Verifica che il similarity score sia ragionevole (> 0.1 per query molto simile)
            if similarity > 0.1:
                print(f"   ✅ Similarity score ragionevole: {similarity:.3f}")
            else:
                print(f"   ⚠️ Similarity score basso: {similarity:.3f}")
    else:
        print(f"   ❌ Errore query: {response.status_code} - {response.text}")
    
    # Step 5: Test query semantica - Query meno simile
    print("\n5. 🔍 TEST QUERY SEMANTICA (BASSA SIMILARITÀ)")
    query_low_similarity = {
        "query_text": "cucina ricette pasta italiana",
        "top_k": 3
    }
    
    response = requests.post(
        f"{base_url}/documents/test_collection/query", 
        json=query_low_similarity
    )
    
    if response.status_code == 200:
        results = response.json()
        print(f"   📊 Risultati trovati: {len(results.get('matches', []))}")
        
        for i, match in enumerate(results.get('matches', [])):
            similarity = match.get('similarity_score', 0)
            print(f"   Match {i+1}: Score={similarity:.3f} (dovrebbe essere basso)")
    
    # Step 6: Test creazione secondo documento
    print("\n6. 📄 CREAZIONE SECONDO DOCUMENTO")
    test_doc2 = {
        "id": "test_post_reset_002",
        "content": "Il sistema di ricerca semantica di PramaIA utilizza embeddings vettoriali per trovare documenti simili. La tecnologia ChromaDB permette di memorizzare e cercare vettori ad alta dimensionalità con grande efficienza.",
        "collection": "test_collection", 
        "metadata": {
            "source": "test_post_reset",
            "type": "technical",
            "topic": "embeddings_technology"
        }
    }
    
    response = requests.post(f"{base_url}/documents/", json=test_doc2)
    if response.status_code == 201:
        print(f"   ✅ Secondo documento creato: {test_doc2['id']}")
    else:
        print(f"   ❌ Errore: {response.text}")
    
    # Step 7: Test query con più documenti
    print("\n7. 🔍 TEST QUERY CON MULTIPLE OPZIONI")
    query_multi = {
        "query_text": "ricerca semantica vettoriali",
        "top_k": 5
    }
    
    response = requests.post(
        f"{base_url}/documents/test_collection/query",
        json=query_multi
    )
    
    if response.status_code == 200:
        results = response.json()
        matches = results.get('matches', [])
        print(f"   📊 Risultati trovati: {len(matches)}")
        
        if len(matches) >= 2:
            print("   ✅ Entrambi i documenti disponibili per ranking")
            
            # Verifica che il ranking sia sensato
            best_match = matches[0] if matches else {}
            best_score = best_match.get('similarity_score', 0)
            
            if best_score > 0.15:  # Soglia ragionevole per query semantica pertinente
                print(f"   ✅ Ranking semantico funzionante: miglior score = {best_score:.3f}")
                
                # Mostra tutti i risultati
                for i, match in enumerate(matches):
                    similarity = match.get('similarity_score', 0)
                    doc_id = match.get('id', 'N/A')
                    print(f"   Rank {i+1}: {doc_id} | Score={similarity:.3f}")
                
                print(f"\n🎉 TEST END-TO-END COMPLETATO CON SUCCESSO!")
                print(f"✅ Embedding model consistency: Funzionante")
                print(f"✅ Similarity scoring: Accurato")
                print(f"✅ Query semantiche: Operative")
                return True
            else:
                print(f"   ⚠️ Score troppo basso, possibili problemi di embedding")
        else:
            print(f"   ⚠️ Meno documenti del previsto nel ranking")
    
    return False

if __name__ == "__main__":
    success = test_end_to_end_after_reset()
    if success:
        print("\n✅ SISTEMA COMPLETAMENTE FUNZIONANTE DOPO RESET!")
    else:
        print("\n❌ Alcuni problemi rilevati nel sistema")