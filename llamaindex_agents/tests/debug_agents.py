#!/usr/bin/env python3
"""
Debug script to test agent loading
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_individual_imports():
    """Test importing each agent individually"""
    print("🔍 Testing individual agent imports...")

    agents_to_test = [
        ("finance_agent", "FinanceAgent"),
        ("yahoo_agent_enhanced", "YahooAgentEnhanced"),
        ("reddit_agent", "RedditAgent"),
        ("sec_agent", "SECAgent"),
        ("general_agent", "GeneralAgent")
    ]

    successful_imports = []
    failed_imports = []

    for module_name, class_name in agents_to_test:
        try:
            print(f"  Testing {module_name}.{class_name}...")
            module = __import__(module_name)
            agent_class = getattr(module, class_name)
            agent_instance = agent_class()
            print(f"  ✅ {class_name} imported and initialized successfully")
            successful_imports.append(class_name)
        except Exception as e:
            print(f"  ❌ {class_name} failed: {e}")
            failed_imports.append((class_name, str(e)))

    print(f"\n📊 Import Results:")
    print(f"  ✅ Successful: {len(successful_imports)} - {successful_imports}")
    print(f"  ❌ Failed: {len(failed_imports)} - {[name for name, _ in failed_imports]}")

    if failed_imports:
        print(f"\n🔍 Error Details:")
        for name, error in failed_imports:
            print(f"  {name}: {error}")

    return len(failed_imports) == 0

def test_workflow_initialization():
    """Test workflow initialization"""
    print("\n🔧 Testing workflow initialization...")

    try:
        from financeagents_workflow import FinanceAgentsWorkflow

        print("  Creating workflow instance...")
        workflow = FinanceAgentsWorkflow(timeout=60)

        print(f"  ✅ Workflow created successfully")
        print(f"  🤖 Available agents: {list(workflow.agent_instances.keys())}")
        print(f"  📊 Agent count: {len(workflow.agent_instances)}")

        return True

    except Exception as e:
        print(f"  ❌ Workflow initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic workflow functionality"""
    print("\n⚡ Testing basic functionality...")

    try:
        from financeagents_workflow import FinanceAgentsWorkflow

        workflow = FinanceAgentsWorkflow(timeout=60)

        # Test query analysis
        test_query = "What's Apple's stock performance?"
        companies = workflow.extract_companies(test_query)
        tickers = workflow.map_to_tickers(companies)
        is_finance = workflow.is_finance_query(test_query)
        agents = workflow.determine_agents(test_query, tickers)

        print(f"  📝 Test Query: {test_query}")
        print(f"  🏢 Companies: {companies}")
        print(f"  📊 Tickers: {tickers}")
        print(f"  💰 Finance Query: {is_finance}")
        print(f"  🤖 Selected Agents: {agents}")

        # Check if selected agents are available
        missing_agents = [agent for agent in agents if agent not in workflow.agent_instances]
        if missing_agents:
            print(f"  ⚠️  Missing agents: {missing_agents}")
            print(f"  📋 Available agents: {list(workflow.agent_instances.keys())}")
            return False
        else:
            print(f"  ✅ All selected agents are available")
            return True

    except Exception as e:
        print(f"  ❌ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main debug function"""
    print("🐛 FinanceAgents Agent Debug Suite")
    print("=" * 50)

    # Test 1: Individual imports
    imports_ok = test_individual_imports()

    # Test 2: Workflow initialization
    workflow_ok = test_workflow_initialization()

    # Test 3: Basic functionality
    basic_ok = test_basic_functionality()

    print(f"\n{'=' * 50}")
    print("🎯 Debug Summary:")
    print(f"  Agent Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"  Workflow Init: {'✅ PASS' if workflow_ok else '❌ FAIL'}")
    print(f"  Basic Functions: {'✅ PASS' if basic_ok else '❌ FAIL'}")

    if imports_ok and workflow_ok and basic_ok:
        print(f"\n🎉 All tests passed! Ready to run full workflow.")
        print(f"   Next: python test_workflow.py")
    else:
        print(f"\n⚠️  Some tests failed. Please fix the issues above.")

if __name__ == "__main__":
    main()