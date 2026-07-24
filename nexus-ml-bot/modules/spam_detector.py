"""
Detector de spam usando reglas heuristicas y ML basico.
"""
import re, time
from collections import defaultdict
from datetime import datetime

class SpamDetector:
    def __init__(self):
        self.user_history = defaultdict(list)
        self.user_msg_count = defaultdict(int)
        self.BURST_LIMIT = 5
        self.BURST_WINDOW = 3

    def check(self, text: str, user_id: str) -> dict:
        if not text:
            return {"is_spam": False, "score": 0.0, "reason": "No content"}

        score = 0.0
        reasons = []
        now = time.time()

        # 1. Mensajes repetidos
        history = self.user_history[user_id]
        history.append((text.lower(), now))
        self.user_history[user_id] = [h for h in history if now - h[1] < 60]

        repeat_count = sum(1 for h in self.user_history[user_id] if h[0] == text.lower())
        if repeat_count > 2:
            score += 0.3
            reasons.append("Mensaje repetido")

        # 2. Burst de mensajes
        recent = [h for h in history if now - h[1] < self.BURST_WINDOW]
        if len(recent) > self.BURST_LIMIT:
            score += 0.4
            reasons.append("Muchos mensajes seguidos")

        # 3. Links sospechosos
        links = re.findall(r'https?://[^\s]+', text)
        if links:
            score += 0.15
            for link in links:
                if any(domain in link for domain in [".xyz", ".top", ".gq", ".ml", ".tk", ".cf", ".click", ".download", ".review"]):
                    score += 0.2
                    reasons.append("Link sospechoso")
                    break

        # 4. TODO MAYUSCULAS
        if len(text) > 10 and text.isupper():
            score += 0.15
            reasons.append("Texto en mayusculas")

        # 5. Mensajes con solo emojis
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F9FF\u2600-\u27BF\u2700-\u27BF]')
        emojis = emoji_pattern.findall(text)
        emoji_ratio = len(emojis) / max(len(text), 1)
        if emoji_ratio > 0.5 and len(text) > 5:
            score += 0.2
            reasons.append("Muchos emojis")

        # 6. Palabras prohibidas
        banned_words = [
            "discord.gg/", "discord.com/invite/", "@everyone", "@here",
            "free nitro", "free steam", "free gift", "click here",
            "win a", "congratulations you won", "you are the winner",
            "claim your", "get free", "http://", "bit.ly/", "tinyurl.com/",
        ]
        for word in banned_words:
            if word in text.lower():
                score += 0.3
                reasons.append(f"Palabra prohibida: {word}")
                break

        # 7. Caracteres repetidos
        if re.search(r'(.)\1{5,}', text):
            score += 0.1
            reasons.append("Caracteres repetidos")

        score = min(1.0, score)

        return {
            "is_spam": score >= 0.35,
            "score": score,
            "reason": ", ".join(reasons) if reasons else "Normal",
            "links": bool(links),
        }
