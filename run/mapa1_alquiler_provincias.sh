#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$RUN_DIR/_lanzar_mapa.sh" \
  "Mapa 1 - Precio medio de alquiler por provincia" \
  "1_precio_medio_alquiler_provincia/mapa1_alquiler_provincias.py" \
  "1_precio_medio_alquiler_provincia/salidas/mapa1_alquiler_provincias_interactivo.html" \
  "$@"
