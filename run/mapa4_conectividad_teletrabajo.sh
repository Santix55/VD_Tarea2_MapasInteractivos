#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$RUN_DIR/_lanzar_mapa.sh" \
  "Mapa 4 - Conectividad y teletrabajo" \
  "4_conectividad_teletrabajo/mapa4_conectividad_teletrabajo.py" \
  "4_conectividad_teletrabajo/salidas/mapa4_conectividad_teletrabajo_interactivo.html" \
  "$@"
