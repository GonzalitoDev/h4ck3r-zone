"""
Panel web de configuración del Nexus Host Bot.
Editalo desde el navegador sin tocar código.
"""
import os, json, threading, time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

CONFIG_FILE = Path(__file__).parent / "config.json"
DASHBOARD_HTML = Path(__file__).parent / "dashboard.html"

app = FastAPI(title="Nexus Host Bot Panel")


def read_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def write_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


@app.get("/", response_class=HTMLResponse)
async def index():
    return DASHBOARD_HTML.read_text(encoding="utf-8")


@app.get("/api/config")
async def get_config():
    return read_config()


@app.post("/api/config")
async def update_config(req: Request):
    cfg = await req.json()
    write_config(cfg)
    return {"ok": True, "message": "Configuración guardada. El bot se actualizó."}


@app.get("/health")
async def health():
    return {"status": "ok", "time": time.time()}


@app.get("/api/status")
async def status():
    return {
        "bot_online": os.environ.get("DISCORD_TOKEN", "").strip() != "",
        "config_file": CONFIG_FILE.exists(),
    }
