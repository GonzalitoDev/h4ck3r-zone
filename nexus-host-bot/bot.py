"""
Nexus Host Bot - Bot de Discord configurable 100% desde un panel web.
No necesitás programar: editá el config desde el navegador.
"""
import os, json, asyncio, random, re, logging
from datetime import datetime

import discord
from discord.ext import commands

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NexusHost")

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
CONFIG_LOCK = asyncio.Lock()


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def get_token():
    token = os.environ.get("DISCORD_TOKEN") or ""
    return token.strip()


class NexusHostBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        self.cfg = load_config()
        self._levels = {}
        self._setup_commands()

    # ── Helpers ──
    def _find_channel(self, ctx, channel_id):
        if channel_id:
            ch = ctx.guild.get_channel(int(channel_id)) if str(channel_id).isdigit() else None
            if ch:
                return ch
        return None

    def _replace_vars(self, text, user=None, level=None, guild=None):
        text = text.replace("{user}", user.mention if user else "@usuario")
        text = text.replace("{username}", user.name if user else "usuario")
        text = text.replace("{guild}", guild.name if guild else "servidor")
        text = text.replace("{level}", str(level) if level is not None else "?")
        return text

    # ── Eventos ──
    async def on_ready(self):
        logger.info(f"Conectado como {self.user} (ID: {self.user.id})")
        cfg = self.cfg
        activity_type = {
            "watching": discord.ActivityType.watching,
            "playing": discord.ActivityType.playing,
            "listening": discord.ActivityType.listening,
        }.get(cfg.get("activity", {}).get("type"), discord.ActivityType.watching)
        activity = discord.Activity(
            type=activity_type,
            name=cfg.get("activity", {}).get("text", "Nexus Host Bot"),
        )
        status = {"online": discord.Status.online, "idle": discord.Status.idle,
                  "dnd": discord.Status.dnd}.get(cfg.get("status", "online"), discord.Status.online)
        await self.change_presence(activity=activity, status=status)
        logger.info("Listo! Usa el panel web para configurar.")

    async def on_member_join(self, member):
        cfg = self.cfg
        if not cfg.get("welcome", {}).get("enabled"):
            return
        ch = self._find_channel(member, cfg["welcome"].get("channel"))
        if ch:
            msg = self._replace_vars(cfg["welcome"]["message"], user=member, guild=member.guild)
            try:
                await ch.send(msg)
            except Exception as e:
                logger.warning(f"Welcome error: {e}")

    async def on_member_remove(self, member):
        cfg = self.cfg
        if not cfg.get("goodbye", {}).get("enabled"):
            return
        ch = self._find_channel(member, cfg["goodbye"].get("channel"))
        if ch:
            msg = self._replace_vars(cfg["goodbye"]["message"], user=member, guild=member.guild)
            try:
                await ch.send(msg)
            except Exception as e:
                logger.warning(f"Goodbye error: {e}")

    async def on_message(self, message):
        if message.author.bot:
            return

        # Auto-mod
        cfg = self.cfg
        if cfg.get("auto_mod", {}).get("enabled"):
            content = message.content.lower()
            for word in cfg["auto_mod"].get("banned_words", []):
                if word.lower() in content:
                    if cfg["auto_mod"].get("delete_message"):
                        try:
                            await message.delete()
                        except:
                            pass
                    warn_msg = self._replace_vars(cfg["auto_mod"].get("warning_message", "Eso no está permitido."),
                                                  user=message.author, guild=message.guild)
                    try:
                        await message.channel.send(f"{message.author.mention} {warn_msg}", delete_after=5)
                    except:
                        pass
                    break

        # Auto-replies
        for ar in cfg.get("auto_replies", []):
            trigger = ar.get("trigger", "").lower()
            if trigger and trigger in message.content.lower():
                await message.channel.send(ar.get("response", ""))
                break

        # Levels / XP
        if cfg.get("levels", {}).get("enabled"):
            uid = str(message.author.id)
            self._levels[uid] = self._levels.get(uid, 0) + int(cfg["levels"].get("xp_per_message", 15))
            if self._levels[uid] >= 100:
                level = self._levels[uid] // 100
                self._levels[uid] %= 100
                if level > 0:
                    msg = self._replace_vars(cfg["levels"].get("level_up_message", "¡{user} subió al nivel {level}!"),
                                             user=message.author, level=level, guild=message.guild)
                    try:
                        await message.channel.send(msg)
                    except:
                        pass

        await self.process_commands(message)

    # ── Comandos ──
    def _setup_commands(self):
        bot = self

        @bot.command(name="help")
        async def help_cmd(ctx):
            cfg = self.cfg
            cmds = cfg.get("commands", {})
            lines = ["**Nexus Host Bot** — Comandos disponibles:", ""]
            if cmds.get("ping"): lines.append("`!ping` — Latencia del bot")
            if cmds.get("say"): lines.append("`!say <texto>` — El bot repite")
            if cmds.get("avatar"): lines.append("`!avatar [@usuario]` — Avatar de un usuario")
            if cmds.get("embed"): lines.append("`!embed <título> | <descripción>` — Envía un embed")
            if cmds.get("kick") or cmds.get("ban") or cmds.get("mute"): lines.append("`!kick @user` `!ban @user` `!mute @user` — Moderación")
            if cmds.get("clear"): lines.append("`!clear N` — Borra mensajes")
            if cfg.get("fun", {}).get("coinflip"): lines.append("`!coinflip` — Cara o cruz")
            if cfg.get("fun", {}).get("dice"): lines.append("`!dice` — Tirar dado")
            if cfg.get("fun", {}).get("8ball"): lines.append("`!8ball <pregunta>` — Bola 8")
            await ctx.send("\n".join(lines))

        @bot.command(name="ping")
        async def ping_cmd(ctx):
            await ctx.send(f"🏓 Pong! {round(bot.latency * 1000)}ms")

        @bot.command(name="say")
        async def say_cmd(ctx, *, text):
            await ctx.send(text)

        @bot.command(name="avatar")
        async def avatar_cmd(ctx, member: discord.Member = None):
            member = member or ctx.author
            embed = discord.Embed(title=f"Avatar de {member.display_name}", color=0x8b5cf6)
            embed.set_image(url=member.display_avatar.url)
            await ctx.send(embed=embed)

        @bot.command(name="embed")
        async def embed_cmd(ctx, *, content):
            parts = content.split("|")
            title = parts[0].strip() if parts else "Embed"
            desc = parts[1].strip() if len(parts) > 1 else ""
            embed = discord.Embed(title=title, description=desc, color=0x8b5cf6)
            await ctx.send(embed=embed)

        @bot.command(name="kick")
        @commands.has_permissions(kick_members=True)
        async def kick_cmd(ctx, member: discord.Member, *, reason="Sin razón"):
            await member.kick(reason=reason)
            await ctx.send(f"👢 {member.mention} fue expulsado ({reason})")

        @bot.command(name="ban")
        @commands.has_permissions(ban_members=True)
        async def ban_cmd(ctx, member: discord.Member, *, reason="Sin razón"):
            await member.ban(reason=reason)
            await ctx.send(f"🔨 {member.mention} fue baneado ({reason})")

        @bot.command(name="mute")
        @commands.has_permissions(moderate_members=True)
        async def mute_cmd(ctx, member: discord.Member, minutes: int = 10, *, reason="Sin razón"):
            await member.timeout(discord.utils.utcnow() + datetime.timedelta(minutes=minutes), reason=reason)
            await ctx.send(f"🔇 {member.mention} muteado por {minutes} minutos")

        @bot.command(name="clear")
        @commands.has_permissions(manage_messages=True)
        async def clear_cmd(ctx, amount: int = 10):
            if 1 <= amount <= 100:
                await ctx.channel.purge(limit=amount + 1)
                await ctx.send(f"🧹 Borrados {amount} mensajes", delete_after=3)

        @bot.command(name="coinflip")
        async def coinflip_cmd(ctx):
            await ctx.send("🪙 " + random.choice(["Cara!", "Cruz!"]))

        @bot.command(name="dice")
        async def dice_cmd(ctx):
            await ctx.send(f"🎲 Sacaste: **{random.randint(1, 6)}**")

        @bot.command(name="8ball")
        async def ball8_cmd(ctx, *, question):
            answers = ["Sí.", "No.", "Puede ser.", "Definitivamente sí.",
                       "No lo creo.", "Preguntá de nuevo.", "Claro que sí.", "Mejor no te digo."]
            await ctx.send(f"🎱 {random.choice(answers)}")


def main():
    token = get_token()
    if not token:
        logger.error("DISCORD_TOKEN no configurado.")
        logger.error("Agregalo como variable de entorno (env) en tu hosting.")
        return

    bot = NexusHostBot()
    try:
        bot.run(token)
    except discord.LoginFailure:
        logger.error("Token inválido. Revisá el DISCORD_TOKEN.")
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    main()
