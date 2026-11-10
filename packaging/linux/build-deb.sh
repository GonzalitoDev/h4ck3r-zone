#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
PKG="acero-y-sal"
ARCH="all"

if ! command -v dpkg-deb >/dev/null 2>&1; then
  echo "dpkg-deb no está disponible. Ejecuta este script en Debian/Ubuntu/Linux Mint o en el workflow de GitHub Actions." >&2
  exit 1
fi

if [ ! -f "$ROOT/game/index.html" ]; then
  echo "No se encontró game/index.html." >&2
  exit 1
fi

VERSION="$(node -p "require('$ROOT/package.json').version" 2>/dev/null || echo "1.0.0")"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$STAGE/DEBIAN" \
  "$STAGE/opt/$PKG/www" \
  "$STAGE/usr/share/applications" \
  "$STAGE/usr/share/icons/hicolor/scalable/apps"

cp -R "$ROOT/game/." "$STAGE/opt/$PKG/www/"
cp "$HERE/launch.sh" "$STAGE/opt/$PKG/launch.sh"
chmod 755 "$STAGE/opt/$PKG/launch.sh"
cp "$HERE/acero-y-sal.desktop" "$STAGE/usr/share/applications/acero-y-sal.desktop"
cp "$HERE/acero-y-sal.svg" "$STAGE/usr/share/icons/hicolor/scalable/apps/acero-y-sal.svg"

INSTALLED_SIZE="$(du -sk "$STAGE" | cut -f1)"
sed -e "s/@VERSION@/$VERSION/g" -e "s/@INSTALLED_SIZE@/$INSTALLED_SIZE/g" \
  "$HERE/control" > "$STAGE/DEBIAN/control"
cp "$HERE/postinst" "$STAGE/DEBIAN/postinst"
cp "$HERE/postrm" "$STAGE/DEBIAN/postrm"
chmod 755 "$STAGE/DEBIAN/postinst" "$STAGE/DEBIAN/postrm"

mkdir -p "$ROOT/dist"
OUT="$ROOT/dist/${PKG}_${VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "$STAGE" "$OUT"

echo "Paquete creado: $OUT"
