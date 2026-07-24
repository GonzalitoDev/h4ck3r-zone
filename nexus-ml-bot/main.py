"""
Nexus Machine Bot - Bot de Discord con Machine Learning
Hosteado automaticamente en Render/Railway
"""
import os, sys, json, time, random, re, asyncio, logging
from collections import defaultdict
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from modules.sentiment import SentimentAnalyzer
from modules.spam_detector import SpamDetector
from modules.chat_ai import ChatAI
from modules.auto_mod import AutoModerator
from modules.analytics import Analytics

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NexusML")

TOKEN = os.environ.get("DISCORD_TOKEN")
PREFIX = os.environ.get("BOT_PREFIX", "!")

if not TOKEN:
    logger.error("DISCORD_TOKEN no configurado. Ponelo en las variables de entorno.")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

sentiment = SentimentAnalyzer()
spam = SpamDetector()
chat_ai = ChatAI()
mod = AutoModerator()
analytics = Analytics()

user_cooldowns = defaultdict(lambda: defaultdict(float))

@bot.event
async def on_ready():
    logger.info(f"Conectado como {bot.user} (ID: {bot.user.id})")
    logger.info(f"Prefijo: {PREFIX}")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name=f"{PREFIX}help | ML Bot"))
    analytics.bot_started = time.time()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    now = time.time()

    # Cooldown anti-spam
    if now - user_cooldowns[user_id]["last_msg"] < 0.5:
        return
    user_cooldowns[user_id]["last_msg"] = now

    # Analisis de sentimiento
    sent = sentiment.analyze(message.content)
    analytics.track_message(user_id, sent)

    # Deteccion de spam
    spam_result = spam.check(message.content, user_id)
    if spam_result["is_spam"]:
        mod.log_action(user_id, "spam", message.content)
        try:
            await message.delete()
            warn = await message.channel.send(
                f"{message.author.mention} No envies spam. (Score: {spam_result['score']:.0%})",
                delete_after=5
            )
        except:
            pass
        return

    await bot.process_commands(message)

    # Respuesta automatica si mencionan al bot
    if bot.user in message.mentions:
        response = chat_ai.respond(message.content)
        if response:
            await message.channel.send(f"{message.author.mention} {response}")

# ─── COMANDOS ───

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(
        title="Nexus Machine Bot",
        description="Bot con IA y Machine Learning",
        color=0x8b5cf6
    )
    embed.add_field(name=f"{PREFIX}help", value="Este mensaje", inline=False)
    embed.add_field(name=f"{PREFIX}ping", value="Latencia del bot", inline=False)
    embed.add_field(name=f"{PREFIX}sentiment <texto>", value="Analiza el sentimiento del texto", inline=False)
    embed.add_field(name=f"{PREFIX}spam <texto>", value="Analiza si el texto es spam", inline=False)
    embed.add_field(name=f"{PREFIX}chat <mensaje>", value="Chatea con la IA", inline=False)
    embed.add_field(name=f"{PREFIX}stats", value="Estadisticas del servidor", inline=False)
    embed.add_field(name=f"{PREFIX}user @usuario", value="Analisis de un usuario", inline=False)
    embed.add_field(name=f"{PREFIX}clear N", value="Borra N mensajes (admin)", inline=False)
    embed.add_field(name=f"{PREFIX}info", value="Info del bot", inline=False)
    embed.set_footer(text="Powered by Machine Learning")
    await ctx.send(embed=embed)

@bot.command(name="ping")
async def ping_cmd(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! Latencia: {latency}ms")

@bot.command(name="sentiment")
async def sentiment_cmd(ctx, *, texto):
    result = sentiment.analyze(texto)
    emoji = {"positivo": "😊", "negativo": "😞", "neutral": "😐"}
    color = {"positivo": 0x22c55e, "negativo": 0xef4444, "neutral": 0xeab308}
    embed = discord.Embed(
        title=f"Analisis de Sentimiento {emoji.get(result['label'], '🤖')}",
        description=f"`{texto[:100]}{'...' if len(texto) > 100 else ''}`",
        color=color.get(result["label"], 0x8b5cf6)
    )
    embed.add_field(name="Sentimiento", value=result["label"].title(), inline=True)
    embed.add_field(name="Confianza", value=f"{result['confidence']:.1%}", inline=True)
    embed.add_field(name="Score", value=f"{result['score']:.2f}", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="spam")
async def spam_cmd(ctx, *, texto):
    result = spam.check(texto, str(ctx.author.id))
    color = 0xef4444 if result["is_spam"] else 0x22c55e
    embed = discord.Embed(
        title="Analisis Anti-Spam",
        description=f"`{texto[:100]}{'...' if len(texto) > 100 else ''}`",
        color=color
    )
    embed.add_field(name="Spam?", value="SI 🚫" if result["is_spam"] else "NO ✅", inline=True)
    embed.add_field(name="Score", value=f"{result['score']:.0%}", inline=True)
    embed.add_field(name="Razon", value=result.get("reason", "Normal"), inline=False)
    await ctx.send(embed=embed)

@bot.command(name="chat")
async def chat_cmd(ctx, *, mensaje):
    async with ctx.typing():
        await asyncio.sleep(0.5)
        response = chat_ai.respond(mensaje)
        if len(response) > 2000:
            response = response[:1997] + "..."
        await ctx.send(response)

@bot.command(name="stats")
async def stats_cmd(ctx):
    stats = analytics.get_server_stats(ctx.guild.id if ctx.guild else 0)
    embed = discord.Embed(title="Estadisticas del Servidor", color=0x8b5cf6)
    embed.add_field(name="Mensajes Analizados", value=stats["total_messages"], inline=True)
    embed.add_field(name="Usuarios Activos", value=stats["active_users"], inline=True)
    embed.add_field(name="Spam Detectado", value=stats["spam_count"], inline=True)
    embed.add_field(name="Sentimiento Promedio", value=stats["avg_sentiment"].title(), inline=True)
    embed.add_field(name="Uptime", value=analytics.get_uptime(), inline=True)
    embed.add_field(name="Latencia", value=f"{round(bot.latency * 1000)}ms", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="user")
async def user_cmd(ctx, miembro: discord.Member = None):
    if not miembro:
        miembro = ctx.author
    stats = analytics.get_user_stats(str(miembro.id))
    embed = discord.Embed(
        title=f"Analisis de {miembro.display_name}",
        color=miembro.color if miembro.color.value != 0 else 0x8b5cf6
    )
    embed.set_thumbnail(url=miembro.display_avatar.url)
    embed.add_field(name="Mensajes", value=stats["messages"], inline=True)
    embed.add_field(name="Sentimiento", value=stats["avg_sentiment"].title(), inline=True)
    embed.add_field(name="Alertas", value=stats["alerts"], inline=True)
    embed.add_field(name="Cuenta Creada", value=miembro.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="Se Unio", value=miembro.joined_at.strftime("%d/%m/%Y") if miembro.joined_at else "?", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear_cmd(ctx, cantidad: int = 10):
    if cantidad < 1 or cantidad > 100:
        await ctx.send("Usa entre 1 y 100 mensajes.", delete_after=5)
        return
    deleted = await ctx.channel.purge(limit=cantidad + 1)
    await ctx.send(f"Eliminados {len(deleted) - 1} mensajes.", delete_after=3)

@bot.command(name="info")
async def info_cmd(ctx):
    embed = discord.Embed(
        title="Nexus Machine Bot",
        description="Bot con inteligencia artificial y machine learning",
        color=0x8b5cf6
    )
    embed.add_field(name="Version", value="2.0.0", inline=True)
    embed.add_field(name="Libreria", value="discord.py", inline=True)
    embed.add_field(name="ML Engine", value="Sentiment + Spam + Chat AI", inline=True)
    embed.add_field(name="Servidores", value=len(bot.guilds), inline=True)
    embed.add_field(name="Usuarios", value=len(bot.users), inline=True)
    embed.add_field(name="Uptime", value=analytics.get_uptime(), inline=True)
    embed.set_footer(text="Hosteado en Render/Railway 24/7")
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("No tenes permisos para usar este comando.", delete_after=5)
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Argumento invalido. Revisa el uso del comando.", delete_after=5)
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        logger.error(f"Error: {error}")
        try:
            await ctx.send(f"Error: {error}", delete_after=10)
        except:
            pass

if __name__ == "__main__":
    logger.info("Iniciando Nexus Machine Bot...")
    bot.run(TOKEN)
