#!/usr/bin/env python3
"""
Test script for Enhanced Yahoo Agent with LlamaIndex CSV capabilities
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yahoo_agent_enhanced import YahooAgentEnhanced
from shared_lib.schemas import MCPRequest, MCPContext

def test_enhanced_yahoo_agent():
    """Test the enhanced Yahoo agent with CSV and natural language capabilities"""

    print("Testing Enhanced Yahoo Agent with LlamaIndex")
    print("=" * 50)

    try:
        # Initialize the enhanced agent
        agent = YahooAgentEnhanced()
        print("✅ Enhanced Yahoo Agent initialized successfully")

        # Test queries with different scenarios
        test_scenarios = [
            {
                "name": "Single Stock Analysis",
                "query": "What's Apple's recent performance and key trends?",
                "companies": ["apple"],
                "tickers": ["AAPL"]
            },
            {
                "name": "Comparative Analysis",
                "query": "Compare Amazon and Microsoft stock performance",
                "companies": ["amazon", "microsoft"],
                "tickers": ["AMZN", "MSFT"]
            },
            {
                "name": "Risk Assessment",
                "query": "What's the volatility and risk profile of Tesla?",
                "companies": ["tesla"],
                "tickers": ["TSLA"]
            },
            {
                "name": "Historical Query",
                "query": "Show me the trading patterns for Google over the past months",
                "companies": ["google"],
                "tickers": ["GOOGL"]
            }
        ]

        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n🔍 Test {i}: {scenario['name']}")
            print(f"Query: {scenario['query']}")
            print("-" * 40)

            # Create MCP request
            context = MCPContext(
                user_query=scenario['query'],
                companies=scenario['companies'],
                tickers=scenario['tickers']
            )
            request = MCPRequest(context=context)

            # Run the agent
            response = agent.run(request)

            if response.status == "success":
                print("✅ Agent executed successfully")
                print(f"Response data keys: {list(response.data.keys())}")

                # Show some sample data
                yahoo_data = response.data.get('yahoo_enhanced', [])
                for item in yahoo_data[:2]:  # Show first 2 items
                    if isinstance(item, dict):
                        if 'ticker' in item:
                            print(f"  📊 {item.get('ticker')}: {item.get('company_name')}")
                            if 'summary_stats' in item:
                                stats = item['summary_stats']['price_stats']
                                print(f"     Current: ${stats['current_price']:.2f}, Range: ${stats['min_price']:.2f}-${stats['max_price']:.2f}")
                        elif 'analysis' in item:
                            print(f"  🧠 Analysis Preview: {item['analysis'][:100]}...")

            else:
                print(f"❌ Agent failed: {response.data}")

            print()

        # Test additional capabilities
        print("\n📁 Available Data Files:")
        files = agent.get_available_data()
        for file_info in files[:5]:  # Show first 5 files
            print(f"  - {file_info['filename']} ({file_info['size_bytes']} bytes)")

        print("\n🔍 Test Natural Language Query on Historical Data:")
        historical_query = "What stock had the best performance recently?"
        result = agent.query_historical_data(historical_query)
        print(f"Query: {historical_query}")
        print(f"Response: {result[:200]}...")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_yahoo_agent()