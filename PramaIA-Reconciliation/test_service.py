#!/usr/bin/env python3
"""
Test script for PramaIA-Reconciliation service
"""

import asyncio
import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

try:
    from main import app, reconciliation_service
    print("✅ Main module imported successfully")
except Exception as e:
    print(f"❌ Failed to import main module: {e}")
    sys.exit(1)

async def test_service():
    """Test the reconciliation service components"""
    print("🔄 Testing ReconciliationService...")
    
    try:
        # Test service initialization
        print(f"Current job: {reconciliation_service.current_job}")
        print(f"Job history: {len(reconciliation_service.job_history)} items")
        print(f"Settings: {reconciliation_service.settings}")
        
        # Test status endpoint
        status = reconciliation_service.get_status()
        print(f"Status: {status}")
        
        print("✅ Service components working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing PramaIA-Reconciliation Service")
    
    result = asyncio.run(test_service())
    
    if result:
        print("\n✅ All tests passed! Service is ready to run.")
    else:
        print("\n❌ Tests failed! Check the errors above.")
        sys.exit(1)