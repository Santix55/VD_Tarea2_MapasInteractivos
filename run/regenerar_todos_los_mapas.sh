#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$RUN_DIR/mapa1_alquiler_provincias.sh" --regen --no-abrir
"$RUN_DIR/mapa2_movilidad_y_transporte.sh" --regen --no-abrir
"$RUN_DIR/mapa3_conectividad_teletrabajo.sh" --regen --no-abrir
"$RUN_DIR/mapa4_confort_climatico.sh" --regen --no-abrir
"$RUN_DIR/mapa5_indice_destino_tech.sh" --regen --no-abrir

echo "Todos los mapas se han regenerado."
