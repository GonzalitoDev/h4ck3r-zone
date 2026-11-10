#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_DIR="$APP_DIR/www"
REQUESTED_PORT="${ACERO_PORT:-8787}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 no está instalado. Abriendo la versión en línea..." >&2
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "https://h4ck3r-zone--juego-e0d5f.us-east4.hosted.app/" >/dev/null 2>&1 &
  fi
  exit 0
fi

is_ours() {
  local url="$1"
  if command -v curl >/dev/null 2>&1; then
    curl -fsS --max-time 2 "$url" 2>/dev/null | grep -q "ACERO Y SAL"
  else
    return 1
  fi
}

PORT="$REQUESTED_PORT"
URL="http://127.0.0.1:${PORT}/"

if is_ours "$URL"; then
  :
else
  if command -v curl >/dev/null 2>&1; then
    for candidate in $(seq "$REQUESTED_PORT" $((REQUESTED_PORT + 12))); do
      cand_url="http://127.0.0.1:${candidate}/"
      if is_ours "$cand_url"; then
        PORT="$candidate"
        URL="$cand_url"
        break
      fi
      if ! curl -fsS --max-time 1 "$cand_url" >/dev/null 2>&1; then
        PORT="$candidate"
        URL="$cand_url"
        break
      fi
    done
  fi

  (cd "$WEB_DIR" && nohup python3 -m http.server "$PORT" --bind 127.0.0.1 \
    >"${TMPDIR:-/tmp}/acero-y-sal-${PORT}.log" 2>&1 &)

  if command -v curl >/dev/null 2>&1; then
    for _ in $(seq 1 15); do
      sleep 0.2
      is_ours "$URL" && break
    done
  else
    sleep 1
  fi
fi

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 &
else
  echo "Abre $URL en tu navegador."
fi
