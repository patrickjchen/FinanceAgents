import os
import re
from typing import List, Optional, Callable

from shared_lib.constants import COMPANY_TICKER_MAP, FINANCIAL_KEYWORDS


def extract_companies(
    query: str,
    company_ticker_map: Optional[dict] = None,
    raw_data_dir: Optional[str] = None,
    on_error: Optional[Callable[[str], None]] = None,
) -> List[str]:
    """Extract company names from a query string.

    Args:
        query: The user query to analyse.
        company_ticker_map: Override the default company-ticker mapping.
        raw_data_dir: Absolute path to the raw_data directory for file-based
            company extraction.  Caller is responsible for computing the
            correct path relative to its own location.
        on_error: Optional callback invoked with an error message string.
    """
    if not query:
        return []

    ctm = company_ticker_map or COMPANY_TICKER_MAP
    companies: set = set()
    query_lower = query.lower()

    # Check against known companies
    for name in ctm.keys():
        try:
            if re.search(rf'\b{re.escape(name)}\b', query_lower):
                companies.add(name)
        except re.error:
            if name in query_lower:
                companies.add(name)

    # Also check for ticker symbols directly (e.g. "MSFT", "AAPL")
    ticker_to_company: dict = {}
    for comp, tick in ctm.items():
        ticker_to_company.setdefault(tick.lower(), comp)
    for ticker_lower, comp in ticker_to_company.items():
        try:
            if re.search(rf'\b{re.escape(ticker_lower)}\b', query_lower):
                companies.add(comp)
        except re.error:
            if ticker_lower in query_lower:
                companies.add(comp)

    # Check raw data directory
    if raw_data_dir and os.path.exists(raw_data_dir):
        try:
            for fname in os.listdir(raw_data_dir):
                if fname.lower().endswith((".pdf", ".htm", ".html")):
                    base = os.path.splitext(fname)[0]
                    company = base.split("-")[0] if "-" in base else base
                    company_lower = company.lower()
                    try:
                        if re.search(rf'\b{re.escape(company_lower)}\b', query_lower):
                            companies.add(company_lower)
                    except re.error:
                        if company_lower in query_lower:
                            companies.add(company_lower)
        except Exception as e:
            if on_error:
                on_error(f"Error extracting companies from files: {e}")

    return list(companies)


def map_to_tickers(
    companies: List[str],
    company_ticker_map: Optional[dict] = None,
) -> List[str]:
    """Map company names to stock ticker symbols."""
    if not companies:
        return []

    ctm = company_ticker_map or COMPANY_TICKER_MAP
    tickers = []
    for name in companies:
        try:
            ticker = ctm.get(name.lower())
            if ticker:
                tickers.append(ticker)
        except Exception:
            continue
    return list(set(tickers))


def is_financial_query(
    query: str,
    companies: List[str],
    tickers: List[str],
    financial_keywords: Optional[List[str]] = None,
) -> bool:
    """Smart two-step check to determine if query is financial.

    Step 1: If companies/tickers found, check if the surrounding context is
            financial.  If query is just a company name (e.g. "APPLE"), treat
            as financial.  If remaining words are non-financial (e.g. "apple
            pie"), return False.
    Step 2: If no companies found, check for financial keywords.
    """
    kw = financial_keywords or FINANCIAL_KEYWORDS
    query_lower = query.lower().strip()

    if companies or tickers:
        remaining = query_lower
        for company in companies:
            remaining = re.sub(rf'\b{re.escape(company)}\b', '', remaining).strip()
        for ticker in tickers:
            remaining = re.sub(rf'\b{re.escape(ticker.lower())}\b', '', remaining).strip()

        if not remaining or len(remaining.strip()) <= 2:
            return True

        for keyword in kw:
            if keyword in remaining:
                return True

        return False

    for keyword in kw:
        if keyword in query_lower:
            return True

    return False


def determine_agents(
    query: str,
    companies: List[str],
    tickers: List[str],
    agent_order: str = "reddit_first",
    on_error: Optional[Callable[[str], None]] = None,
) -> List[str]:
    """Determine which agents to run based on smart query classification.

    Args:
        agent_order: ``"reddit_first"`` (crewai/langchain) puts RedditAgent
            first; ``"finance_first"`` (llamaindex) puts FinanceAgent first.
        on_error: Optional callback invoked with an error message string.
    """
    try:
        is_finance = is_financial_query(query, companies, tickers)
        if is_finance:
            if tickers:
                if agent_order == "finance_first":
                    return ["FinanceAgent", "YahooAgent", "SECAgent", "RedditAgent"]
                else:
                    return ["RedditAgent", "FinanceAgent", "YahooAgent", "SECAgent"]
            else:
                if agent_order == "finance_first":
                    return ["FinanceAgent", "RedditAgent"]
                else:
                    return ["RedditAgent", "FinanceAgent"]
        else:
            return ["GeneralAgent"]
    except Exception as e:
        if on_error:
            on_error(f"Error determining agents: {e}")
        if agent_order == "finance_first":
            return ["FinanceAgent", "RedditAgent"]
        else:
            return ["RedditAgent", "FinanceAgent"]
