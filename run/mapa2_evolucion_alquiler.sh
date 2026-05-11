#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$RUN_DIR/_lanzar_mapa.sh" \
  "Mapa 2 - Movilidad y transporte" \
  "2_evolucion_alquiler/mapa2_evolucion_alquiler.py" \
  "2_evolucion_alquiler/salidas/mapa2_movilidad_transportes_interactivo.html" \
  "$@"
