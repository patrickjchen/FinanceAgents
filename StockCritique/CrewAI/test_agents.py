#!/usr/bin/env python3
"""
Test script for BankerAI agents
"""

print("Testing Agent Imports")
print("=" * 30)

# Test GeneralAgent
try:
    from agents.general_agent import GeneralAgent
    print("✅ GeneralAgent imported successfully")
except Exception as e:
    print(f"❌ GeneralAgent import failed: {e}")

# Test FinanceAgent
try:
    from agents.finance_agent import FinanceAgent
    print("✅ FinanceAgent imported successfully")
except Exception as e:
    print(f"❌ FinanceAgent import failed: {e}")

# Test YahooAgent
try:
    from agents.yahoo_agent import YahooAgent
    print("✅ YahooAgent imported successfully")
except Exception as e:
    print(f"❌ YahooAgent import failed: {e}")

# Test SECAgent
try:
    from agents.sec_agent import SECAgent
    print("✅ SECAgent imported successfully")
except Exception as e:
    print(f"❌ SECAgent import failed: {e}")

# Test RedditAgent
try:
    from agents.reddit_agent import RedditAgent
    print("✅ RedditAgent imported successfully")
except Exception as e:
    print(f"❌ RedditAgent import failed: {e}")

# Test Router
try:
    from agents.crewai_router import RouterCrew
    print("✅ RouterCrew imported successfully")
except Exception as e:
    print(f"❌ RouterCrew import failed: {e}")

print("\nAgent import tests completed.")