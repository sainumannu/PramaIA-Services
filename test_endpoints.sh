#!/bin/bash
# test_endpoints.sh - Test bash per endpoint VectorstoreService

SERVICE_URL="http://localhost:8090"
COLLECTION="test_bash_$(date +%Y%m%d_%H%M%S)"
TEST_DOC_ID="bash_test_doc_$(date +%s)"

echo "=== Test Bash Endpoint VectorstoreService ==="
echo "Service URL: $SERVICE_URL"
echo "Collection: $COLLECTION"
echo ""

# Funzione helper per test HTTP
test_endpoint() {
    local method=$1
    local url=$2
    local data=$3
    local description=$4
    
    echo "Testing: $description"
    echo "  → $method $url"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "%{http_code}" -o /tmp/response.json "$url" 2>/dev/null)
    else
        response=$(curl -s -w "%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$data" -o /tmp/response.json "$url" 2>/dev/null)
    fi
    
    http_code="${response: -3}"
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo "  ✅ Success ($http_code)"
        cat /tmp/response.json | python3 -m json.tool 2>/dev/null || cat /tmp/response.json
    else
        echo "  ❌ Failed ($http_code)"
        cat /tmp/response.json 2>/dev/null || echo "  No response body"
    fi
    echo ""
}

# Test 1: Health Check
echo "1. Health Check"
test_endpoint "GET" "$SERVICE_URL/health" "" "Service health status"

# Test 2: Documents List
echo "2. Current Documents"
test_endpoint "GET" "$SERVICE_URL/vectorstore/documents" "" "List existing documents"

# Test 3: Collections List  
echo "3. Collections"
test_endpoint "GET" "$SERVICE_URL/collections/" "" "List collections"

# Test 4: Upload Test Document
echo "4. Upload Test Document"
TEST_DOCUMENT='{
    "id": "'$TEST_DOC_ID'",
    "content": "Test document from bash script to verify upload and retrieval functionality. This document contains sample content about coordinate system management and semantic processing in PramaIA.",
    "collection": "'$COLLECTION'",
    "metadata": {
        "author": "Bash Test Script",
        "document_type": "integration_test",
        "created_at": "'$(date -Iseconds)'",
        "test_framework": "bash_curl",
        "keywords": ["bash", "test", "upload", "retrieval"]
    },
    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
}'

test_endpoint "POST" "$SERVICE_URL/vectorstore/documents" "$TEST_DOCUMENT" "Upload test document"

# Test 5: Verify Upload
echo "5. Verify Upload (wait 2s for indexing)"
sleep 2
test_endpoint "GET" "$SERVICE_URL/vectorstore/documents" "" "Verify document was uploaded"

# Test 6: Test Query
echo "6. Test Query"
QUERY='{
    "query_text": "coordinate system management",
    "limit": 5
}'

test_endpoint "POST" "$SERVICE_URL/documents/$COLLECTION/query" "$QUERY" "Query uploaded document"

# Test 7: Test Semantic Query
echo "7. Test Semantic Query"
SEMANTIC_QUERY='{
    "query_text": "semantic processing PramaIA",
    "limit": 3
}'

test_endpoint "POST" "$SERVICE_URL/documents/$COLLECTION/query" "$SEMANTIC_QUERY" "Semantic query test"

# Test 8: Statistics
echo "8. System Statistics"
test_endpoint "GET" "$SERVICE_URL/api/database-management/vectorstore/statistics" "" "Get system statistics"

# Test 9: Dependencies
echo "9. Dependencies Health"
test_endpoint "GET" "$SERVICE_URL/health/dependencies" "" "Check dependencies"

# Cleanup note
echo "=== Test Completed ==="
echo "Test document ID: $TEST_DOC_ID"
echo "Test collection: $COLLECTION"
echo ""
echo "To cleanup manually:"
echo "curl -X DELETE '$SERVICE_URL/vectorstore/document/$TEST_DOC_ID'"
echo ""

# Clean up temp file
rm -f /tmp/response.json

echo "✅ Bash endpoint tests completed!"