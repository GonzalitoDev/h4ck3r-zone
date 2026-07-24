"""
Moderacion automatica con registro de acciones.
"""
import json, os, time
from collections import defaultdict
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
LOG_FILE = os.path.join(DATA_DIR, "mod_logs.json")

class AutoModerator:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.logs = self._load_logs()

    def _load_logs(self):
        try:
            with open(LOG_FILE) as f:
                return json.load(f)
        except:
            return {"actions": [], "total": 0}

    def _save_logs(self):
        with open(LOG_FILE, "w") as f:
            json.dump(self.logs, f, indent=2)

    def log_action(self, user_id, action_type, content=""):
        entry = {
            "user_id": user_id,
            "type": action_type,
            "content": content[:100],
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.logs["actions"].append(entry)
        self.logs["total"] += 1
        if len(self.logs["actions"]) > 1000:
            self.logs["actions"] = self.logs["actions"][-1000:]
        self._save_logs()

    def get_user_alerts(self, user_id):
        count = sum(1 for a in self.logs["actions"] if a["user_id"] == user_id)
        recent = [a for a in self.logs["actions"]
                  if a["user_id"] == user_id
                  and time.time() - datetime.fromisoformat(a["timestamp"]).timestamp() < 3600]
        return {
            "total": count,
            "recent_hour": len(recent),
        }
