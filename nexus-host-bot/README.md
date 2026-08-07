# Nexus Host Bot — Bot sin código

Bot de Discord 100% configurable desde un **panel web**. Sin programar.

## Qué incluye

- 🎮 12+ comandos (ping, say, avatar, embed, kick, ban, mute, clear, coinflip, dice, 8ball)
- 👋 Mensajes automáticos de bienvenida y despedida
- 🤖 Auto-respuestas configurables
- 🛡️ Auto-moderación (palabras prohibidas)
- 📊 Sistema de niveles y XP
- 🎛️ Panel web para configurar todo sin tocar código

## Hosteo (queda prendido 24/7 gratis)

### Railway (recomendado)
1. Subí esta carpeta a GitHub
2. https://railway.app/ → New Project → Deploy from GitHub
3. Agregá variable de entorno: `DISCORD_TOKEN` = tu token
4. Deploy. Ya queda online.

### Render
1. https://dashboard.render.com/ → New → Web Service → conecta tu repo
2. Render detecta `render.yaml`
3. Agregá `DISCORD_TOKEN` como variable de entorno
4. Deploy

## Uso

- Después de desplegar, abrí la URL del servicio → te muestra el **panel web**
- Configurá todo desde ahí (bienvenidas, auto-respuestas, moderación, comandos)
- Guardá → el bot se actualiza solo
- Invitá al bot a tu servidor con el link de Discord Developer Portal

## Token del bot

1. https://discord.com/developers/applications
2. New Application → Bot → Reset Token → copiá
3. Pegalo como `DISCORD_TOKEN`

## Invitar el bot

```
https://discord.com/api/oauth2/authorize?client_id=TU_BOT_ID&permissions=8&scope=bot%20applications.commands
```
