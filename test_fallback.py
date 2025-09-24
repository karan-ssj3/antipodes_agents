#!/usr/bin/env python3
"""
Test script to safely test fallback data behavior
This script temporarily disables the API key to test fallback functionality
"""

import os
import sys
from pathlib import Path
from datetime import date

# IMPORTANT: Disable API key BEFORE any imports that might load it
# Store original API key
original_api_key = os.environ.get('FINANCIAL_DATASETS_API_KEY')

# Temporarily remove API key
if 'FINANCIAL_DATASETS_API_KEY' in os.environ:
    del os.environ['FINANCIAL_DATASETS_API_KEY']

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

def test_fallback_data():
    """Test fallback data with different as-of-date values"""
    
    print("🔑 API Key disabled for testing")
    print("=" * 50)
    
    # Test different dates to find what works with fallback data
    test_dates = [
        "2025-03-01",  # Should work (within fallback range)
        "2025-04-01",  # Should work
        "2025-05-01",  # Should work
        "2025-06-01",  # Might work
        "2025-07-01",  # Might not work (outside range)
    ]
    
    for test_date in test_dates:
        print(f"\n📅 Testing date: {test_date}")
        print("-" * 30)
        
        try:
            # Import and run the workflow
            from src.workflow import AgentWorkflow
            
            workflow = AgentWorkflow()
            result = workflow.run(date.fromisoformat(test_date))
            
            if result:
                print(f"✅ SUCCESS: {test_date} works with fallback data")
                print(f"   Portfolio Return: {result.get('portfolio_return', 'N/A')}%")
                print(f"   Active Return: {result.get('active_return', 'N/A')}%")
            else:
                print(f"❌ FAILED: {test_date} doesn't work with fallback data")
                
        except Exception as e:
            print(f"❌ ERROR: {test_date} - {str(e)}")
    
    # Restore original API key
    if original_api_key:
        os.environ['FINANCIAL_DATASETS_API_KEY'] = original_api_key
        print(f"\n🔑 API Key restored")
    else:
        print(f"\n🔑 No original API key to restore")

if __name__ == "__main__":
    test_fallback_data()
