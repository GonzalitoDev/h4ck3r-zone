# Nexus Machine Bot

Bot de Discord con Machine Learning. Analiza sentimiento, detecta spam,
modera automaticamente y chatea con IA. Todo offline, sin APIs externas.

## Comandos

| Comando | Descripcion |
|---------|-------------|
| !help | Muestra la ayuda |
| !ping | Latencia del bot |
| !sentiment <texto> | Analiza el sentimiento |
| !spam <texto> | Detecta spam |
| !chat <mensaje> | Chatea con la IA |
| !stats | Estadisticas del servidor |
| !user @usuario | Analisis de usuario |
| !clear N | Borra mensajes (admin) |
| !info | Info del bot |

## Hosteo en Render (gratis, 24/7)

1. Subi este proyecto a GitHub
2. Anda a https://dashboard.render.com/
3. New -> Web Service -> Conecta tu repo
4. Render detecta `render.yaml` automaticamente
5. Configura `DISCORD_TOKEN` en Environment Variables
6. Deploy! El bot queda online 24/7 gratis

## Hosteo en Railway (gratis, 24/7)

1. Subi a GitHub
2. Anda a https://railway.app/
3. New Project -> Deploy from GitHub repo
4. Agrega `DISCORD_TOKEN` como variable de entorno
5. Railway lo hostea automaticamente

## Hosteo local

```bash
pip install -r requirements.txt
set DISCORD_TOKEN=tu_token_aqui
python main.py
```
