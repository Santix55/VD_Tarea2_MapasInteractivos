from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import webbrowser


RUN_DIR = Path(__file__).resolve().parent
ROOT_DIR = RUN_DIR.parent

MAPS = {
    "mapa1": {
        "title": "Mapa 1 - Precio medio de alquiler por provincia",
        "script": "1_precio_medio_alquiler_provincia/mapa1_alquiler_provincias.py",
        "html": "1_precio_medio_alquiler_provincia/salidas/mapa1_alquiler_provincias_interactivo.html",
    },
    "mapa2": {
        "title": "Mapa 2 - Movilidad y transporte",
        "script": "2_movilidad_y_transporte/mapa2_movilidad_y_transporte.py",
        "html": "2_movilidad_y_transporte/salidas/mapa2_movilidad_transportes_interactivo.html",
    },
    "mapa3": {
        "title": "Mapa 3 - Conectividad y teletrabajo",
        "script": "3_conectividad_teletrabajo/mapa3_conectividad_teletrabajo.py",
        "html": "3_conectividad_teletrabajo/salidas/mapa3_conectividad_teletrabajo_interactivo.html",
    },
    "mapa4": {
        "title": "Mapa 4 - Confort climatico estacional",
        "script": "4_confort_climatico/mapa4_confort_climatico_estacional.py",
        "html": "4_confort_climatico/salidas/mapa4_confort_climatico_estacional_interactivo.html",
    },
    "mapa5": {
        "title": "Mapa 5 - Indice de destino tech",
        "script": "5_indice_destino_tech/mapa5_indice_destino_tech.py",
        "html": "5_indice_destino_tech/salidas/mapa5_indice_destino_tech_interactivo.html",
    },
}


def python_command() -> list[str]:
    configured_python = os.environ.get("PYTHON_BIN")
    if configured_python:
        return [configured_python]
    return [sys.executable]


def parse_args(title: str, argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"Abre el HTML interactivo de: {title}",
    )
    parser.add_argument(
        "--regen",
        action="store_true",
        help="Regenera primero el mapa ejecutando el script Python.",
    )
    parser.add_argument(
        "--no-abrir",
        action="store_true",
        help="Regenera/verifica el mapa, pero no abre el navegador.",
    )
    return parser.parse_args(argv)


def launch_map(
    title: str,
    script_rel: str,
    html_rel: str,
    argv: list[str] | None = None,
) -> int:
    args = parse_args(title, argv)
    script_path = ROOT_DIR / script_rel
    html_path = ROOT_DIR / html_rel

    if not script_path.is_file():
        print(f"No se encontro el script Python: {script_path}", file=sys.stderr)
        return 1

    if args.regen or not html_path.is_file():
        print(f"Generando {title}...")
        subprocess.run(
            [*python_command(), str(script_path)],
            cwd=ROOT_DIR,
            check=True,
        )

    if not html_path.is_file():
        print(f"No se encontro el HTML interactivo esperado: {html_path}", file=sys.stderr)
        return 1

    if args.no_abrir:
        print("HTML listo:")
        print(html_path)
        return 0

    print(f"Abriendo {title}")
    print(html_path)
    opened = webbrowser.open(html_path.resolve().as_uri())
    if not opened:
        print("No se pudo abrir automaticamente. Abre este archivo en tu navegador:")
        print(html_path)
    return 0


def launch_map_by_key(key: str, argv: list[str] | None = None) -> int:
    config = MAPS[key]
    return launch_map(
        config["title"],
        config["script"],
        config["html"],
        argv,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lanzador Python de mapas interactivos.")
    parser.add_argument("mapa", choices=sorted(MAPS), help="Mapa que se quiere abrir.")
    args, remaining = parser.parse_known_args(argv)
    return launch_map_by_key(args.mapa, remaining)


if __name__ == "__main__":
    raise SystemExit(main())
