import json
from datetime import datetime

class MonitorAgent:
    def __init__(self, log_file="monitor_logs.json"):
        self.log_file = log_file

    def log_health(self, agent_name: str, status: str, error: str = ""):
        """Logs agent health status with timestamps."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "status": status,
            "error": error
        }

        try:
            # Read existing logs
            with open(self.log_file, "r") as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []

        # Append new log
        logs.append(log_entry)

        # Write back to file
        with open(self.log_file, "w") as f:
            json.dump(logs, f, indent=2)