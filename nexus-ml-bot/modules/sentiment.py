"""
Analizador de sentimiento basado en lexicon.
No necesita internet, funciona offline con palabras clave en español/ingles.
"""
import re, math

POSITIVAS_ES = set([
    "feliz", "alegre", "contento", "genial", "excelente", "bueno", "bien", "wow",
    "increible", "maravilloso", "fantastico", "hermoso", "perfecto", "amor", "gracias",
    "mejor", "felicidad", "sonrisa", "divertido", "encantador", "espectacular",
    "asombroso", "magnifico", "estupendo", "brillante", "guay", "chido", "piola",
    "hermosa", "bonito", "lindo", "bella", "te amo", "te quiero", "me encanta",
    "me gusta", "win", "exito", "triunfo", "victoria", "celebrar", "festejar",
    "alegria", "felicidades", "bien hecho", "orgullo", "satisfecho", "tranquilo",
    "paz", "calma", "relajado", "agradable", "amable", "generoso", "bonito",
    "simpatia", "cariño", "abrazo", "beso", "amistad", "esperanza", "sueno",
    "cumplido", "motivacion", "inspirador", "optimista", "positivo", "confianza",
    "apoyo", "ayuda", "compartir", "sonrisa", "risa", "jaja", "jeje", "lol",
])

NEGATIVAS_ES = set([
    "triste", "enojado", "enfadado", "molesto", "horrible", "pesimo", "malo", "mal",
    "terrible", "odio", "odiar", "asco", "feo", "horroroso", "desastre", "pesadilla",
    "deprimente", "aburrido", "frustrado", "estresado", "ansioso", "preocupado",
    "solo", "soledad", "llorar", "gritar", "pelear", "discutir", "problema",
    "dificil", "complicado", "imposible", "fracaso", "perder", "perdida", "error",
    "fallo", "falla", "bug", "roto", "muerto", "muerte", "enfermo", "dolor",
    "sufrir", "sufrimiento", "odioso", "detesto", "aborrezco", "canse", "harto",
    "fastidio", "incomodo", "desagradable", "pesado", "insoportable", "intolerable",
    "basura", "mierda", "puta", "puto", "estupido", "idiota", "tonto", "imbecil",
    "tarado", "boludo", "pelotudo", "gil", "mogolico", "cagon", "forro",
    "resentido", "amargado", "depresion", "ansiedad", "estres", "panico",
    "miedo", "temor", "horror", "terror", "angustia", "desesperacion",
    "desconfianza", "inseguridad", "timido", "culpa", "arrepentimiento",
    "no", "nunca", "jamas", "nadie", "nada", "tampoco",
])

POSITIVAS_EN = set([
    "happy", "great", "awesome", "amazing", "excellent", "good", "wonderful",
    "fantastic", "beautiful", "love", "thanks", "best", "perfect", "fun",
    "brilliant", "magnificent", "splendid", "superb", "nice", "glad",
    "joy", "joyful", "cheerful", "delightful", "pleased", "grateful",
    "excited", "fantastic", "marvelous", "terrific", "wonderful",
    "congratulations", "celebrate", "success", "victory", "win", "achievement",
    "happy", "lovely", "charming", "enjoy", "enjoying", "amused",
    "hilarious", "funny", "lol", "lmao", "rofl", "xd",
])

NEGATIVAS_EN = set([
    "sad", "angry", "mad", "upset", "horrible", "terrible", "bad", "worst",
    "hate", "disgust", "ugly", "disaster", "nightmare", "depressed", "boring",
    "frustrated", "stressed", "anxious", "worried", "lonely", "cry", "scream",
    "fight", "argue", "problem", "difficult", "impossible", "fail", "failure",
    "lose", "lost", "error", "wrong", "broken", "dead", "death", "sick",
    "pain", "suffer", "detest", "abhor", "tired", "sick", "annoying",
    "uncomfortable", "disgusting", "unbearable", "trash", "shit", "fuck",
    "stupid", "idiot", "dumb", "moron", "depression", "anxiety",
    "stress", "panic", "fear", "scared", "afraid", "terror", "horror",
    "anguish", "despair", "distrust", "insecurity", "guilt", "regret",
    "no", "never", "nobody", "nothing", "neither", "nor", "not",
])

INTENSIFICADORES = set([
    "muy", "tan", "bastante", "demasiado", "extremadamente", "increiblemente",
    "super", "re", "recontra", "ultra", "mega", "súper",
    "very", "so", "quite", "too", "extremely", "incredibly", "really",
    "absolutely", "totally", "completely", "highly", "deeply",
])

INVERSORES = set(["no", "nunca", "jamas", "not", "never", "dont", "don't", "wont", "won't"])

class SentimentAnalyzer:
    def analyze(self, text):
        if not text or not text.strip():
            return {"label": "neutral", "confidence": 0.5, "score": 0.0}

        text_lower = text.lower().strip()
        words = re.findall(r'\w+', text_lower)

        score = 0.0
        pos_count = 0
        neg_count = 0
        intensifier = 1.0
        invert = 1

        for word in words:
            if word in INTENSIFICADORES:
                intensifier = 1.5
                continue
            if word in INVERSORES:
                invert = -1
                continue

            multiplier = intensifier * invert
            found = False

            if word in POSITIVAS_ES or word in POSITIVAS_EN:
                score += 0.15 * multiplier
                pos_count += 1
                found = True
            elif word in NEGATIVAS_ES or word in NEGATIVAS_EN:
                score -= 0.2 * multiplier
                neg_count += 1
                found = True

            intensifier = 1.0
            if found:
                invert = 1

        # Verificar patrones de emojis/expresiones
        if ":)" in text or ":D" in text or "=)" in text or "<3" in text:
            score += 0.2
            pos_count += 1
        if ":(" in text or ":'(" in text or "=(" in text or ":/" in text:
            score -= 0.2
            neg_count += 1

        total = pos_count + neg_count
        if total == 0:
            return {"label": "neutral", "confidence": 0.5, "score": 0.0}

        # Normalizar a [-1, 1]
        score = max(-1.0, min(1.0, score))

        if score > 0.15:
            label = "positivo"
        elif score < -0.15:
            label = "negativo"
        else:
            label = "neutral"

        confidence = min(1.0, total * 0.15 + abs(score) * 0.5)

        return {
            "label": label,
            "confidence": confidence,
            "score": score,
            "positive_words": pos_count,
            "negative_words": neg_count,
        }
