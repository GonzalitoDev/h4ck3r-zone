"""
KeepAlive Bot - Bot MÍNIMO que solo se mantiene prendido 24/7.
Sin comandos ni config. Solo conectado y respondiendo ping.
"""
import os, logging, json, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import discord
from discord.ext import commands

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("KeepAlive")

TOKEN = os.environ.get("DISCORD_TOKEN", "").strip()
PORT = int(os.environ.get("PORT", 8080))

if not TOKEN:
    logger.error("DISCORD_TOKEN no configurado")
    raise SystemExit(1)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    logger.info(f"Bot prendido como {bot.user} (ID: {bot.user.id})")
    activity = discord.Activity(type=discord.ActivityType.watching, name="24/7")
    await bot.change_presence(activity=activity, status=discord.Status.online)

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🟢 Online! Latencia: {round(bot.latency * 1000)}ms")

@bot.command(name="status")
async def status(ctx):
    await ctx.send(f"🤖 {bot.user.name} — online 24/7. Uptime: {uptime_str()}")

_start = __import__("time").time()
def uptime_str():
    s = int(__import__("time").time() - _start)
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{d}d {h}h {m}m {s}s"

class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "uptime": uptime_str()}).encode())
    def log_message(self, *a, **k): pass

def start_health():
    HTTPServer(("0.0.0.0", PORT), Health).serve_forever()

if __name__ == "__main__":
    logger.info("Iniciando KeepAlive Bot...")
    threading.Thread(target=start_health, daemon=True).start()
    bot.run(TOKEN)
