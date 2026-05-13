#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPEN_DELAY_SECONDS="${OPEN_DELAY_SECONDS:-3}"
OPEN_DELAY_MAP2_SECONDS="${OPEN_DELAY_MAP2_SECONDS:-5}"

open_map() {
  local script="$1"
  shift
  "$script" "$@"
  sleep "$OPEN_DELAY_SECONDS"
}

open_map "$RUN_DIR/mapa1_alquiler_provincias.sh" "$@"
open_map "$RUN_DIR/mapa2_movilidad_y_transporte.sh" "$@"
sleep "$OPEN_DELAY_MAP2_SECONDS"
open_map "$RUN_DIR/mapa3_conectividad_teletrabajo.sh" "$@"
open_map "$RUN_DIR/mapa4_confort_climatico.sh" "$@"
open_map "$RUN_DIR/mapa5_indice_destino_tech.sh" "$@"
