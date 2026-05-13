#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$RUN_DIR/_lanzar_mapa.sh" \
  "Mapa 2 - Movilidad y transporte" \
  "2_movilidad_y_transporte/mapa2_movilidad_y_transporte.py" \
  "2_movilidad_y_transporte/salidas/mapa2_movilidad_transportes_interactivo.html" \
  "$@"
