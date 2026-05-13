# Lanzadores Python de mapas

Esta carpeta contiene una version multiplataforma de los lanzadores de `run/`.
Funciona con Python en Windows, Linux y macOS, sin usar Bash.

## Uso rapido

Desde la raiz del proyecto:

```bash
python run_python/mapa1_alquiler_provincias.py
python run_python/mapa2_movilidad_y_transporte.py
python run_python/mapa3_conectividad_teletrabajo.py
python run_python/mapa4_confort_climatico.py
python run_python/mapa5_indice_destino_tech.py
```

Para abrir todos:

```bash
python run_python/abrir_todos_los_mapas.py
```

En Windows, si `python` no apunta al entorno correcto, usa el ejecutable del
entorno Conda o define `PYTHON_BIN`.

## Opciones

Cada lanzador acepta:

```bash
python run_python/mapa2_movilidad_y_transporte.py --regen
python run_python/mapa2_movilidad_y_transporte.py --regen --no-abrir
```

Para regenerar todos sin abrir el navegador:

```bash
python run_python/regenerar_todos_los_mapas.py
```

Para cambiar la pausa entre pestanas:

```bash
OPEN_DELAY_SECONDS=1.5 python run_python/abrir_todos_los_mapas.py
```

En PowerShell:

```powershell
$env:OPEN_DELAY_SECONDS = "1.5"
python run_python/abrir_todos_los_mapas.py
```
