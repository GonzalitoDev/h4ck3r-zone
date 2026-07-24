"""
Analytics y estadisticas del bot.
"""
import time, json, os
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

class Analytics:
    def __init__(self):
        self.bot_started = time.time()
        self.message_count = 0
        self.spam_count = 0
        self.user_messages = defaultdict(lambda: {"count": 0, "sentiments": []})
        self.sentiment_distribution = {"positivo": 0, "negativo": 0, "neutral": 0}

    def track_message(self, user_id: str, sentiment: dict):
        self.message_count += 1
        self.user_messages[user_id]["count"] += 1
        label = sentiment.get("label", "neutral")
        self.sentiment_distribution[label] = self.sentiment_distribution.get(label, 0) + 1
        self.user_messages[user_id]["sentiments"].append(sentiment.get("score", 0))
        if len(self.user_messages[user_id]["sentiments"]) > 100:
            self.user_messages[user_id]["sentiments"] = self.user_messages[user_id]["sentiments"][-100:]

    def track_spam(self):
        self.spam_count += 1

    def get_user_stats(self, user_id: str) -> dict:
        data = self.user_messages.get(user_id, {"count": 0, "sentiments": []})
        sentiments = data.get("sentiments", [])
        avg_sent = sum(sentiments) / max(len(sentiments), 1)
        if avg_sent > 0.15:
            label = "positivo"
        elif avg_sent < -0.15:
            label = "negativo"
        else:
            label = "neutral"
        return {
            "messages": data["count"],
            "avg_sentiment": label,
            "alerts": 0,
        }

    def get_server_stats(self, guild_id: int) -> dict:
        total = self.message_count
        active_users = len(self.user_messages)
        sentiments = self.sentiment_distribution
        max_label = max(sentiments, key=sentiments.get) if sentiments else "neutral"
        return {
            "total_messages": total,
            "active_users": active_users,
            "spam_count": self.spam_count,
            "avg_sentiment": max_label,
        }

    def get_uptime(self) -> str:
        elapsed = time.time() - self.bot_started
        days = int(elapsed // 86400)
        hours = int((elapsed % 86400) // 3600)
        minutes = int((elapsed % 3600) // 60)
        parts = []
        if days > 0: parts.append(f"{days}d")
        if hours > 0: parts.append(f"{hours}h")
        parts.append(f"{minutes}m")
        return " ".join(parts)
