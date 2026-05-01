#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Uso interno: _lanzar_mapa.sh TITULO SCRIPT_PY HTML [--regen] [--no-abrir]" >&2
  exit 2
fi

TITLE="$1"
PY_SCRIPT_REL="$2"
HTML_REL="$3"
shift 3

RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$RUN_DIR/.." && pwd)"
PY_SCRIPT="$ROOT_DIR/$PY_SCRIPT_REL"
HTML_FILE="$ROOT_DIR/$HTML_REL"
PYTHON_BIN="${PYTHON_BIN:-python3}"

REGENERATE=0
OPEN_HTML=1

usage() {
  cat <<EOF
Uso: $(basename "$0") [opciones]

Abre el HTML interactivo de:
  $TITLE

Opciones:
  --regen      Regenera primero el mapa ejecutando el script Python.
  --no-abrir   Regenera/verifica el mapa, pero no abre el navegador.
  -h, --help   Muestra esta ayuda.

Tambien puedes elegir Python con:
  PYTHON_BIN=/ruta/a/python $(basename "$0") --regen
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --regen)
      REGENERATE=1
      ;;
    --no-abrir)
      OPEN_HTML=0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Opcion no reconocida: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

open_file() {
  local target="$1"

  case "$(uname -s)" in
    Darwin*)
      open "$target"
      ;;
    Linux*)
      if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$target" >/dev/null 2>&1
      elif command -v gio >/dev/null 2>&1; then
        gio open "$target" >/dev/null 2>&1
      else
        echo "No encuentro xdg-open ni gio. Abre este archivo en tu navegador:"
        echo "$target"
      fi
      ;;
    CYGWIN*|MINGW*|MSYS*)
      local win_target
      win_target="$(cygpath -w "$target" 2>/dev/null || printf '%s' "$target")"
      cmd.exe /c start "" "$win_target" >/dev/null 2>&1
      ;;
    *)
      echo "Sistema no reconocido. Abre este archivo en tu navegador:"
      echo "$target"
      ;;
  esac
}

if [[ ! -f "$PY_SCRIPT" ]]; then
  echo "No se encontro el script Python: $PY_SCRIPT" >&2
  exit 1
fi

if [[ "$REGENERATE" -eq 1 || ! -f "$HTML_FILE" ]]; then
  echo "Generando $TITLE..."
  (
    cd "$ROOT_DIR"
    "$PYTHON_BIN" "$PY_SCRIPT"
  )
fi

if [[ ! -f "$HTML_FILE" ]]; then
  echo "No se encontro el HTML interactivo esperado: $HTML_FILE" >&2
  exit 1
fi

if [[ "$OPEN_HTML" -eq 1 ]]; then
  echo "Abriendo $TITLE"
  echo "$HTML_FILE"
  open_file "$HTML_FILE"
else
  echo "HTML listo:"
  echo "$HTML_FILE"
fi
