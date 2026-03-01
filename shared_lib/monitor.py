import json
from datetime import datetime
from typing import Optional


class MonitorAgent:
    def __init__(self, log_file="monitor_logs.json"):
        self.log_file = log_file

    def log_health(self, agent_name: str, status: str, details: str = ""):
        """Logs agent health status with timestamps."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "status": status,
            "details": details
        }

        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"[MonitorAgent] Failed to log: {e}")

    def log_error(self, agent_name: str, error: str, context: Optional[dict] = None):
        """Log agent errors."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "error": error,
            "context": context or {}
        }

        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"[MonitorAgent] Failed to log error: {e}")
