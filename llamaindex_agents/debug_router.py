#!/usr/bin/env python3
"""
Debug script to test query classification logic
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from shared_lib.query_classification import extract_companies, map_to_tickers, is_financial_query, determine_agents

def test_amazon_query():
    raw_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw_data")
    query = "amazon"

    print(f"Testing query: '{query}'")
    print("=" * 50)

    companies = extract_companies(query, raw_data_dir=raw_data_dir)
    print(f"Extracted companies: {companies}")

    tickers = map_to_tickers(companies)
    print(f"Mapped tickers: {tickers}")

    is_finance = is_financial_query(query, companies, tickers)
    print(f"Is finance query: {is_finance}")

    agents = determine_agents(query, companies, tickers)
    print(f"Selected agents: {agents}")

    print("\nExpected agents for Amazon query:")
    print("Should include: FinanceAgent, YahooAgent, SECAgent, RedditAgent")

if __name__ == "__main__":
    test_amazon_query()
