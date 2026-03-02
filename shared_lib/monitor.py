import json
import os
from datetime import datetime
from typing import Optional


class MonitorAgent:
    def __init__(self, log_file="working_dir/logs/monitor_logs.json"):
        self.log_file = log_file
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

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
