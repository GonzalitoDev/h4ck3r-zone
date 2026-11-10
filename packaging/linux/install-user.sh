#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
DEST="$DATA_HOME/acero-y-sal"
APPS="$DATA_HOME/applications"
ICONS="$DATA_HOME/icons/hicolor/scalable/apps"

if [ ! -f "$ROOT/game/index.html" ]; then
  echo "No se encontró game/index.html. Ejecuta este script desde el repositorio." >&2
  exit 1
fi

rm -rf "$DEST"
mkdir -p "$DEST/www" "$APPS" "$ICONS"
cp -R "$ROOT/game/." "$DEST/www/"
cp "$HERE/launch.sh" "$DEST/launch.sh"
chmod +x "$DEST/launch.sh"
cp "$HERE/acero-y-sal.svg" "$ICONS/acero-y-sal.svg"

cat >"$APPS/acero-y-sal.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=ACERO Y SAL
Comment=RPG naval por turnos con buques reales
Exec=$DEST/launch.sh
Icon=acero-y-sal
Terminal=false
Categories=Game;StrategyGame;
StartupNotify=true
EOF
chmod +x "$APPS/acero-y-sal.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APPS" >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f -t "$DATA_HOME/icons/hicolor" >/dev/null 2>&1 || true
fi

echo "ACERO Y SAL instalado en: $DEST"
echo "Búscalo en el menú de Linux Mint como \"ACERO Y SAL\"."
echo "Para desinstalar: rm -rf \"$DEST\" \"$APPS/acero-y-sal.desktop\" \"$ICONS/acero-y-sal.svg\""
