"""
Chat AI - Respuestas automaticas con matching contextual.
No necesita API, funciona offline con base de conocimiento local.
"""
import re, random, json
from difflib import SequenceMatcher

class ChatAI:
    def __init__(self):
        self.knowledge = [
            # Saludos
            (["hola", "buenas", "hey", "que tal", "hello", "hi"],
             ["Hola! Como estas?", "Buenas! En que puedo ayudarte?", "Hey! Todo bien?",
              "Holaa! Que necesitas?"]),

            (["como estas", "como andas", "como va", "que haces", "como te va"],
             ["Bien, gracias por preguntar! Y vos?", "Todo bien aca, ready para ayudar!",
              "Excelente! Como vos?", "De 10! En que te ayudo?"]),

            # Quien eres
            (["quien eres", "quien sos", "que eres", "tu nombre", "como te llamas"],
             ["Soy Nexus Machine Bot, un bot con inteligencia artificial creado para ayudar!",
              "Me llamo Nexus ML Bot. Uso machine learning para analizar mensajes y conversar.",
              "Soy un bot con IA! Analizo sentimiento, detecto spam y respondo preguntas."]),

            # Que haces
            (["que haces", "que puedes hacer", "que sabes hacer", "funciones", "comandos"],
             ["Puedo analizar sentimiento de mensajes, detectar spam, moderar el servidor y chatear con IA.",
              "Mis funciones: analisis de sentimiento, deteccion de spam, moderacion automatica, y chat.",
              "Uso IA para entender mensajes, detectar spam, analizar emociones y responder preguntas."]),

            # Agradecimientos
            (["gracias", "thanks", "thank you", "te agradezco", "muchas gracias"],
             ["De nada! Para eso estoy :)", "No hay de que! Cualquier cosa aca estoy.",
              "A vos! Un placer ayudar.", "De nada! Si necesitas algo mas, avisame."]),

            # Despedidas
            (["chau", "adios", "bye", "nos vemos", "hasta luego", "see you"],
             ["Chau! Que tengas un buen dia!", "Nos vemos! Cuídate!",
              "Hasta luego! Vuelve cuando quieras.", "Bye! Fue un placer charlar."]),

            # Discord
            (["discord", "bot", "comandos", "server", "servidor"],
             ["Estoy en este servidor de Discord! Uso machine learning para analizar mensajes en tiempo real.",
              "Soy un bot de Discord con IA integrada. Mis comandos principales son sentiment, spam, chat, stats, user."]),

            # Machine Learning / IA
            (["ia", "inteligencia", "machine learning", "ml", "aprendizaje", "ai"],
             ["Uso machine learning para analizar sentimiento, detectar patrones de spam y generar respuestas.",
              "Mi IA se basa en procesamiento de lenguaje natural (NLP) con analisis de palabras clave y contexto.",
              "Funciono con inteligencia artificial offline - no necesito internet para analizar mensajes."]),

            # Estado de animo
            (["triste", "deprimido", "mal", "angustiado", "solo", "tristeza"],
             ["Lamento que te sientas asi. Recorda que siempre podes hablar con alguien de confianza.",
              "No estas solo. Si necesitas ayuda, hablar con un profesional de la salud es lo mejor.",
              "Los momentos dificiles pasan. Cuidate, descansa y pedi ayuda si la necesitas."]),

            (["feliz", "contento", "alegre", "excelente", "bien", "genial"],
             ["Me alegra mucho! Que bueno que estes bien :)",
              "Excelente! Eso es lo que queremos escuchar!",
              "Me pone feliz saber que estas bien! Segui asi!"]),

            # Ayuda
            (["ayuda", "help", "necesito ayuda", "puedes ayudarme", "ayudame"],
             ["Claro! Decime que necesitas y te ayudo.",
              "Para eso estoy! Contame tu consulta.",
              "Por supuesto! Que necesitas?"]),

            # Random
            (["clima", "tiempo", "lluvia", "sol", "temperatura"],
             ["No tengo acceso al clima en tiempo real. Pero espero que este lindo el dia donde estas!",
              "No puedo consultar el clima, pero ojala este haciendo buen tiempo!"]),

            (["musica", "cancion", "musica", "playlist", "spotify"],
             ["Me gusta la musica electronica y lo-fi para programar. Que musica te gusta?",
              "La musica es vida! Que genero te gusta?"]),

            (["juego", "jugar", "videojuego", "gaming", "game"],
             ["Los videojuegos son geniales! Cual es tu juego favorito?",
              "Buenos juegos! Te gusta mas single player o multiplayer?"]),

            (["edad", "años", "viejo", "creado", "naciste"],
             ["Fui creado en 2026! Soy joven pero aprendo rapido.",
              "Tengo pocos meses de vida! Pero ya aprendi mucho."]),

            # Creator
            (["quien te creo", "quien te hizo", "tu creador", "quien te programo"],
             ["Me creo Gonza Dev! Formo parte del ecosistema NexusBot.",
              "Mi creador es Gonza. El me entreno con datos y algoritmos de machine learning.",
              "Fui desarrollado por Gonza como parte de NexusBot, una plataforma de herramientas digitales."]),
        ]

        self.fallbacks = [
            "Interesante! Contame mas sobre eso.",
            "No tengo mucha info sobre ese tema, pero puedo ayudarte con otras cosas.",
            "Buena pregunta! No estoy seguro, pero puedo intentar ayudarte con lo que se.",
            "No conozco ese tema en profundidad. Queres preguntarme otra cosa?",
            "Mmm, no se mucho de eso. Pero pregunta lo que quieras!",
            "No encontre informacion sobre eso en mi base de conocimiento.",
        ]

    def respond(self, text: str) -> str:
        text_lower = text.lower().strip()
        text_lower = re.sub(r'<@!?\d+>', '', text_lower).strip()

        best_score = 0
        best_responses = []

        for keywords, responses in self.knowledge:
            for kw in keywords:
                kw_lower = kw.lower()
                # Exact match
                if kw_lower in text_lower:
                    score = len(kw_lower) / max(len(text_lower), 1)
                else:
                    # Fuzzy match
                    score = SequenceMatcher(None, kw_lower, text_lower).ratio() * 0.5

                if score > best_score:
                    best_score = score
                    best_responses = responses

        if best_score > 0.2 and best_responses:
            return random.choice(best_responses)

        if best_responses and best_score > 0.15:
            return random.choice(best_responses)

        return random.choice(self.fallbacks)
