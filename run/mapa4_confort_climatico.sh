#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$RUN_DIR/_lanzar_mapa.sh" \
  "Mapa 4 - Confort climatico estacional" \
  "4_confort_climatico/mapa4_confort_climatico_estacional.py" \
  "4_confort_climatico/salidas/mapa4_confort_climatico_estacional_interactivo.html" \
  "$@"
