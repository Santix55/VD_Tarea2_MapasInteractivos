#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$RUN_DIR/_lanzar_mapa.sh" \
  "Mapa 5 - Confort climatico estacional" \
  "5_confort_climatico/mapa5_confort_climatico_estacional.py" \
  "5_confort_climatico/salidas/mapa5_confort_climatico_estacional_interactivo.html" \
  "$@"
