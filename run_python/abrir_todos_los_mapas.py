from __future__ import annotations

import argparse
import os
import time

from _lanzar_mapa import launch_map_by_key


MAP_ORDER = ["mapa1", "mapa2", "mapa3", "mapa4", "mapa5"]


def env_float(name: str, default: float) -> float:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError:
        print(f"{name} no es un numero valido; se usa {default}.")
        return default


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Abre todos los mapas interactivos en orden.",
    )
    parser.add_argument(
        "--regen",
        action="store_true",
        help="Regenera cada mapa antes de abrirlo.",
    )
    parser.add_argument(
        "--no-abrir",
        action="store_true",
        help="Verifica/regenera los mapas, pero no abre el navegador.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    delay = env_float("OPEN_DELAY_SECONDS", 3)
    map2_delay = env_float("OPEN_DELAY_MAP2_SECONDS", 5)
    forwarded_args = []
    if args.regen:
        forwarded_args.append("--regen")
    if args.no_abrir:
        forwarded_args.append("--no-abrir")

    for key in MAP_ORDER:
        result = launch_map_by_key(key, forwarded_args)
        if result != 0:
            return result
        time.sleep(delay)
        if key == "mapa2":
            time.sleep(map2_delay)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
