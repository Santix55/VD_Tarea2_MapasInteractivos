#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$RUN_DIR/_lanzar_mapa.sh" \
  "Mapa 5 - Indice de destino tech" \
  "5_indice_destino_tech/mapa5_indice_destino_tech.py" \
  "5_indice_destino_tech/salidas/mapa5_indice_destino_tech_interactivo.html" \
  "$@"
