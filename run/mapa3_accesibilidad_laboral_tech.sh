#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$RUN_DIR/_lanzar_mapa.sh" \
  "Mapa 3 - Accesibilidad laboral tech" \
  "3_accesibilidad_laboral_tech/mapa3_accesibilidad_laboral_tech.py" \
  "3_accesibilidad_laboral_tech/salidas/mapa3_accesibilidad_laboral_tech_interactivo.html" \
  "$@"
