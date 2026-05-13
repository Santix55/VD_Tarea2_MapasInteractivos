#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$RUN_DIR/_lanzar_mapa.sh" \
  "Mapa 3 - Conectividad y teletrabajo" \
  "3_conectividad_teletrabajo/mapa3_conectividad_teletrabajo.py" \
  "3_conectividad_teletrabajo/salidas/mapa3_conectividad_teletrabajo_interactivo.html" \
  "$@"
