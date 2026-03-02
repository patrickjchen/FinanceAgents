# Shared constants used across all framework implementations
# Loaded from config/companies.json

import json
import os

_CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config")
_CONFIG_FILE = os.path.join(_CONFIG_DIR, "companies.json")

with open(_CONFIG_FILE, "r") as f:
    _config = json.load(f)

COMPANY_TICKER_MAP = _config["company_ticker_map"]
FINANCIAL_KEYWORDS = _config["financial_keywords"]
