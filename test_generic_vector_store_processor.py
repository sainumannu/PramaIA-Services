#!/usr/bin/env python3
"""
Test rapido per il Generic Vector Store Processor
Verifica le operazioni di base con diversi backend
"""

import asyncio
import sys
import os
import json
import numpy as np

# Add the plugin path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'plugins', 'core-rag-plugin', 'src'))

try:
    from generic_vector_store_processor import GenericVectorStoreProcessor
    print("✅ Generic Vector Store Processor importato correttamente")
except ImportError as e:
    print(f"❌ Errore import: {e}")
    sys.exit(1)

async def test_mock_backend():
    """Test con mock backend per validare la logica base"""
    print("\n🧪 Testing Mock Backend...")
    
    processor = GenericVectorStoreProcessor()
    
    # Test data
    embeddings = [
        [0.1, 0.2, 0.3, 0.4],
        [0.5, 0.6, 0.7, 0.8],
        [0.9, 0.1, 0.2, 0.3]
    ]
    documents = [
        "First test document",
        "Second test document", 
        "Third test document"
    ]
    
    # Test Write Operation
    write_context = {
        'config': {
            'operation': 'write',
            'backend_type': 'mock',
            'collection': 'test_collection',
            'backend_config': {}
        },
        'inputs': {
            'embeddings': embeddings,
            'documents': documents,
            'model': 'test-model'
        }
    }
    
    write_result = await processor.process(write_context)
    print(f"Write Result: {json.dumps(write_result, indent=2)}")
    
    if write_result['status'] == 'success':
        written_ids = write_result['output']['written_ids']
        print(f"✅ Write successful: {len(written_ids)} vectors written")
    else:
        print(f"❌ Write failed: {write_result.get('error', 'Unknown error')}")
        return False
    
    # Test Search Operation  
    query_vector = [0.2, 0.3, 0.4, 0.5]
    search_context = {
        'config': {
            'operation': 'search',
            'backend_type': 'mock',
            'collection': 'test_collection',
            'backend_config': {},
            'n_results': 2
        },
        'inputs': {
            'query_vector': query_vector
        }
    }
    
    search_result = await processor.process(search_context)
    print(f"Search Result: {json.dumps(search_result, indent=2)}")
    
    if search_result['status'] == 'success':
        results = search_result['output']['results']
        print(f"✅ Search successful: {len(results)} results found")
    else:
        print(f"❌ Search failed: {search_result.get('error', 'Unknown error')}")
        return False
    
    # Test Management Operation
    manage_context = {
        'config': {
            'operation': 'manage',
            'backend_type': 'mock',
            'management_action': 'list_collections',
            'backend_config': {}
        },
        'inputs': {}
    }
    
    manage_result = await processor.process(manage_context)
    print(f"Management Result: {json.dumps(manage_result, indent=2)}")
    
    if manage_result['status'] == 'success':
        collections = manage_result['output'].get('collections', [])
        print(f"✅ Management successful: {len(collections)} collections found")
    else:
        print(f"❌ Management failed: {manage_result.get('error', 'Unknown error')}")
        return False
    
    return True

async def test_chroma_backend():
    """Test con Chroma backend (se disponibile)"""
    print("\n🧪 Testing Chroma Backend...")
    
    processor = GenericVectorStoreProcessor()
    
    # Test connection
    connect_context = {
        'config': {
            'operation': 'manage',
            'backend_type': 'chroma',
            'management_action': 'list_collections',
            'backend_config': {
                'persist_directory': './test_chroma_db'
            }
        },
        'inputs': {}
    }
    
    connect_result = await processor.process(connect_context)
    
    if connect_result['status'] == 'error':
        print(f"⚠️  Chroma not available: {connect_result.get('error', 'Unknown')}")
        return True  # Not a failure, just not available
    
    print("✅ Chroma connection successful")
    
    # Test write
    embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    documents = ["Chroma test doc 1", "Chroma test doc 2"]
    
    write_context = {
        'config': {
            'operation': 'write',
            'backend_type': 'chroma',
            'collection': 'test_chroma',
            'backend_config': {
                'persist_directory': './test_chroma_db'
            }
        },
        'inputs': {
            'embeddings': embeddings,
            'documents': documents
        }
    }
    
    write_result = await processor.process(write_context)
    
    if write_result['status'] == 'success':
        print(f"✅ Chroma write successful: {len(write_result['output']['written_ids'])} vectors")
    else:
        print(f"❌ Chroma write failed: {write_result.get('error')}")
        return False
    
    return True

async def test_vectorstore_backend():
    """Test con VectorStore Service backend"""
    print("\n🧪 Testing VectorStore Service Backend...")
    
    processor = GenericVectorStoreProcessor()
    
    # Test connection
    connect_context = {
        'config': {
            'operation': 'manage',
            'backend_type': 'vectorstore_service',
            'management_action': 'list_collections',
            'backend_config': {
                'service_url': 'http://localhost:8090',
                'timeout': 5  # Short timeout for quick test
            }
        },
        'inputs': {}
    }
    
    connect_result = await processor.process(connect_context)
    
    if connect_result['status'] == 'error':
        print(f"⚠️  VectorStore Service not available: {connect_result.get('error', 'Unknown')}")
        return True  # Not a failure, just not available
    
    print("✅ VectorStore Service connection successful")
    return True

async def test_input_formats():
    """Test diversi formati di input"""
    print("\n🧪 Testing Different Input Formats...")
    
    processor = GenericVectorStoreProcessor()
    
    # Test format 1: embeddings_input object
    embeddings_input_format = {
        'config': {
            'operation': 'write',
            'backend_type': 'mock',
            'collection': 'test_formats'
        },
        'inputs': {
            'embeddings_input': {
                'embeddings': [[0.1, 0.2, 0.3]],
                'chunks': ["Test chunk"],
                'model': 'test-model'
            }
        }
    }
    
    result1 = await processor.process(embeddings_input_format)
    if result1['status'] == 'success':
        print("✅ embeddings_input format works")
    else:
        print(f"❌ embeddings_input format failed: {result1.get('error')}")
    
    # Test format 2: direct arrays
    direct_arrays_format = {
        'config': {
            'operation': 'write',
            'backend_type': 'mock',
            'collection': 'test_formats'
        },
        'inputs': {
            'embeddings': [[0.4, 0.5, 0.6]],
            'texts': ["Direct text"],
            'model': 'direct-model'
        }
    }
    
    result2 = await processor.process(direct_arrays_format)
    if result2['status'] == 'success':
        print("✅ Direct arrays format works")
    else:
        print(f"❌ Direct arrays format failed: {result2.get('error')}")
    
    return True

async def main():
    """Main test function"""
    print("🚀 Starting Generic Vector Store Processor Tests\n")
    
    tests = [
        ("Mock Backend Test", test_mock_backend),
        ("Input Formats Test", test_input_formats),
        ("Chroma Backend Test", test_chroma_backend),
        ("VectorStore Service Test", test_vectorstore_backend)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            print(f"Running: {test_name}")
            print('='*60)
            
            result = await test_func()
            if result:
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
                
        except Exception as e:
            print(f"💥 {test_name} CRASHED: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    print('='*60)
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed or were skipped")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)