#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPEN_DELAY_SECONDS="${OPEN_DELAY_SECONDS:-1.5}"

open_map() {
  local script="$1"
  shift
  "$script" "$@"
  sleep "$OPEN_DELAY_SECONDS"
}

open_map "$RUN_DIR/mapa1_alquiler_provincias.sh" "$@"
open_map "$RUN_DIR/mapa2_evolucion_alquiler.sh" "$@"
open_map "$RUN_DIR/mapa3_accesibilidad_laboral_tech.sh" "$@"
open_map "$RUN_DIR/mapa4_conectividad_teletrabajo.sh" "$@"
open_map "$RUN_DIR/mapa5_confort_climatico.sh" "$@"
open_map "$RUN_DIR/mapa6_indice_destino_tech.sh" "$@"
