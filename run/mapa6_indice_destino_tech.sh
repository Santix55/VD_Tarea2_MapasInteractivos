#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$RUN_DIR/_lanzar_mapa.sh" \
  "Mapa 6 - Indice de destino tech" \
  "6_indice_destino_tech/mapa6_indice_destino_tech.py" \
  "6_indice_destino_tech/salidas/mapa6_indice_destino_tech_interactivo.html" \
  "$@"
