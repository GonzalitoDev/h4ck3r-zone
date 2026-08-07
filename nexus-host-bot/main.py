"""
Nexus Host Bot - Lanzador.
Corre el bot de Discord Y el panel web en el mismo proceso.
"""
import os, threading, logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NexusHost")

PORT = int(os.environ.get("PORT", 8080))

# Importar la app FastAPI
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from pathlib import Path
CONFIG_FILE = Path(__file__).parent / "config.json"
DASHBOARD_HTML = Path(__file__).parent / "dashboard.html"

web_app = FastAPI(title="Nexus Host Bot Panel")


def read_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def write_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


@web_app.get("/", response_class=HTMLResponse)
async def index():
    return DASHBOARD_HTML.read_text(encoding="utf-8")


@web_app.get("/api/config")
async def get_config():
    return read_config()


@web_app.post("/api/config")
async def update_config(req: Request):
    cfg = await req.json()
    write_config(cfg)
    return {"ok": True, "message": "Configuración guardada."}


@web_app.get("/health")
async def health():
    return {"status": "ok"}


def run_bot():
    """Corre el bot de Discord en un thread."""
    from bot import main as bot_main
    try:
        bot_main()
    except Exception as e:
        logger.error(f"Bot terminó: {e}")


def main():
    logger.info("Iniciando Nexus Host Bot...")
    logger.info(f"Panel web en puerto {PORT}")

    # Iniciar bot en thread
    if os.environ.get("DISCORD_TOKEN", "").strip():
        t = threading.Thread(target=run_bot, daemon=True)
        t.start()
        logger.info("Bot de Discord iniciado.")
    else:
        logger.warning("DISCORD_TOKEN no configurado. El panel web corre igual, agrega el token después.")

    # Iniciar panel web
    uvicorn.run(web_app, host="0.0.0.0", port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
