#!/usr/bin/env python3
"""
Simple test script for LlamaIndex FinanceAgents implementation
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared_lib.schemas import MCPRequest, MCPContext

def test_agents():
    """Test individual agents without full execution"""
    print("\nTesting Agent Imports")
    print("=" * 30)

    try:
        from shared_lib.agents.general_agent import GeneralAgent
        print("✅ GeneralAgent imported successfully")
    except Exception as e:
        print(f"❌ GeneralAgent import failed: {e}")

    try:
        from finance_agent import FinanceAgent
        print("✅ FinanceAgent imported successfully")
    except Exception as e:
        print(f"❌ FinanceAgent import failed: {e}")

    try:
        from yahoo_agent_enhanced import YahooAgentEnhanced
        print("✅ YahooAgentEnhanced imported successfully")
    except Exception as e:
        print(f"❌ YahooAgentEnhanced import failed: {e}")

    try:
        from shared_lib.agents.sec_agent import SECAgent
        print("✅ SECAgent imported successfully")
    except Exception as e:
        print(f"❌ SECAgent import failed: {e}")

    try:
        from reddit_agent import RedditAgent
        print("✅ RedditAgent imported successfully")
    except Exception as e:
        print(f"❌ RedditAgent import failed: {e}")

def test_schemas():
    """Test schema imports and creation"""
    print("\nTesting Schemas")
    print("=" * 20)

    try:
        from shared_lib.schemas import MCPRequest, MCPResponse, MCPContext

        # Test context creation
        context = MCPContext(
            user_query="test query",
            companies=["apple"],
            tickers=["AAPL"]
        )
        print("✅ MCPContext created successfully")

        # Test request creation
        request = MCPRequest(context=context)
        print("✅ MCPRequest created successfully")

        # Test response creation
        response = MCPResponse(
            request_id=request.request_id,
            data={"test": "data"},
            status="success"
        )
        print("✅ MCPResponse created successfully")

    except Exception as e:
        print(f"❌ Schema test failed: {e}")

def check_environment():
    """Check environment setup"""
    print("\nChecking Environment")
    print("=" * 25)

    # Check for required environment variables
    required_vars = ["OPENAI_API_KEY", "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"]

    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var} is set")
        else:
            print(f"⚠️  {var} is not set")

    # Check for raw data directory
    raw_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw_data")
    if os.path.exists(raw_data_dir):
        files = [f for f in os.listdir(raw_data_dir) if f.endswith(('.pdf', '.htm', '.html'))]
        print(f"✅ Raw data directory exists with {len(files)} PDF files")
    else:
        print("⚠️  Raw data directory not found")

    # Check for vector storage directory
    vector_dir = "./vector_db/llamaindex_storage"
    if os.path.exists(vector_dir):
        print("✅ Vector storage directory exists")
    else:
        print("ℹ️  Vector storage directory will be created on first run")

async def main():
    """Main test function"""
    print("FinanceAgents LlamaIndex Implementation Test")
    print("=" * 45)
    print(f"Test started at: {datetime.now().isoformat()}")

    # Run tests
    check_environment()
    test_schemas()
    test_agents()

    print("\n" + "=" * 45)
    print("Test completed!")
    print("If all tests passed, you can run 'python main.py' to start the system.")

if __name__ == "__main__":
    asyncio.run(main())
