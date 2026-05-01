#!/usr/bin/env python3
"""Exporta memoria.md a PDF usando Pandoc.

Uso basico:
    ./memoria/exportar_pdf.py

Uso con nombre de entrega:
    ./memoria/exportar_pdf.py -o memoria/TusApellidosTuNombre.pdf
"""

from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DEFAULT_INPUT = SCRIPT_DIR / "memoria.md"
DEFAULT_OUTPUT = SCRIPT_DIR / "memoria.pdf"


def existing_command(*names: str) -> str | None:
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Exporta memoria/memoria.md a PDF.",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Markdown de entrada. Por defecto: memoria/memoria.md",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="PDF de salida. Por defecto: memoria/memoria.pdf",
    )
    parser.add_argument(
        "--pdf-engine",
        default=None,
        help="Motor LaTeX para Pandoc. Por defecto: xelatex si existe, si no lualatex.",
    )
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return (Path.cwd() / path).resolve()


def main() -> int:
    args = parse_args()
    input_path = resolve_path(args.input)
    output_path = resolve_path(args.output)

    if not input_path.exists():
        print(f"Error: no existe el archivo de entrada: {input_path}", file=sys.stderr)
        return 1

    pandoc = existing_command("pandoc")
    if pandoc is None:
        print(
            "Error: no encuentro pandoc en el PATH. Instala pandoc o anadelo al PATH.",
            file=sys.stderr,
        )
        return 1

    pdf_engine = args.pdf_engine or existing_command("xelatex", "lualatex")
    if pdf_engine is None:
        print(
            "Error: no encuentro xelatex ni lualatex. Instala una distribucion LaTeX "
            "o ejecuta: quarto install tinytex",
            file=sys.stderr,
        )
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    resource_path = f"{input_path.parent}:{PROJECT_DIR}"
    command = [
        pandoc,
        str(input_path.name),
        "-o",
        str(output_path),
        "--pdf-engine",
        pdf_engine,
        "--toc",
        "--number-sections",
        f"--resource-path={resource_path}",
    ]

    print("Ejecutando:")
    print(shlex.join(command))

    result = subprocess.run(command, cwd=input_path.parent)
    if result.returncode != 0:
        return result.returncode

    print(f"\nPDF generado: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
