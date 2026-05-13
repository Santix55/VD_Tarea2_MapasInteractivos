from __future__ import annotations

from _lanzar_mapa import launch_map_by_key


MAP_ORDER = ["mapa1", "mapa2", "mapa3", "mapa4", "mapa5"]


def main() -> int:
    for key in MAP_ORDER:
        result = launch_map_by_key(key, ["--regen", "--no-abrir"])
        if result != 0:
            return result

    print("Todos los mapas se han regenerado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
