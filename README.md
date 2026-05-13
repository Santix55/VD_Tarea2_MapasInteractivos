# VD Tarea 2 - Mapas interactivos

Proyecto de visualizacion de datos georreferenciados sobre la pregunta:

**Donde vivir despues del Master de IA en la UPV**

El repositorio genera cinco mapas sobre alquiler, movilidad y transporte,
conectividad, confort climatico e indice final de destino residencial. Tambien incluye una app Streamlit y una memoria en
Markdown/PDF.

## Estructura

```text
.
|-- 1_precio_medio_alquiler_provincia/
|-- 2_movilidad_y_transporte/
|-- 3_conectividad_teletrabajo/
|-- 4_confort_climatico/
|-- 5_indice_destino_tech/
|-- app_streamlit/
|-- datos/
|-- memoria/
|-- run/
`-- fuentes.md
```

Cada carpeta de mapa contiene:

- un script Python principal;
- una carpeta `salidas/` con PNG, PDF, HTML interactivo y CSV generados;
- un `README.md` especifico con la metodologia de ese mapa.

## Requisitos

El proyecto esta pensado para ejecutarse con Python 3. Se ha usado un entorno
Conda llamado `VD`, pero tambien puede funcionar con otro entorno si tiene las
dependencias instaladas.

Dependencias principales:

```bash
pip install pandas geopandas folium branca mapclassify matplotlib requests shapely openpyxl streamlit streamlit-folium plotly
```

Para exportar la memoria a PDF tambien hace falta:

- `pandoc`
- `xelatex` o `lualatex`

Si ya tienes el entorno Conda del proyecto:

```bash
conda activate VD
```

O usa directamente el Python del entorno:

```bash
PYTHON_BIN=/home/s/miniconda3/envs/VD/bin/python ./run/regenerar_todos_los_mapas.sh
```

## Uso rapido

Desde la raiz del proyecto:

```bash
cd /home/s/Escritorio/VD_Tarea2_MapasInteractivos
```

Abrir todos los mapas interactivos ya generados:

```bash
./run/abrir_todos_los_mapas.sh
```

Abrir un mapa concreto:

```bash
./run/mapa1_alquiler_provincias.sh
./run/mapa2_movilidad_y_transporte.sh
./run/mapa3_conectividad_teletrabajo.sh
./run/mapa4_confort_climatico.sh
./run/mapa5_indice_destino_tech.sh
```

Los lanzadores abren el HTML existente. Si el HTML no existe, ejecutan el script
Python correspondiente para generarlo.

## Regenerar mapas

Regenerar todos los mapas sin abrir el navegador:

```bash
./run/regenerar_todos_los_mapas.sh
```

Regenerar y abrir un mapa concreto:

```bash
./run/mapa3_conectividad_teletrabajo.sh --regen
```

Regenerar un mapa sin abrirlo:

```bash
./run/mapa3_conectividad_teletrabajo.sh --regen --no-abrir
```

Usar un Python concreto:

```bash
PYTHON_BIN=/home/s/miniconda3/envs/VD/bin/python ./run/mapa3_conectividad_teletrabajo.sh --regen
```

## Lanzadores Python / Windows

La carpeta `run_python/` contiene una version equivalente de los lanzadores,
hecha solo con Python para poder usarla tambien en Windows.

Abrir todos los mapas:

```bash
python run_python/abrir_todos_los_mapas.py
```

Abrir o regenerar un mapa concreto:

```bash
python run_python/mapa2_movilidad_y_transporte.py
python run_python/mapa2_movilidad_y_transporte.py --regen
```

Regenerar todos sin abrir el navegador:

```bash
python run_python/regenerar_todos_los_mapas.py
```

## Ejecutar scripts Python directamente

Tambien puedes ejecutar cada mapa sin los lanzadores:

```bash
python 1_precio_medio_alquiler_provincia/mapa1_alquiler_provincias.py
python 2_movilidad_y_transporte/mapa2_movilidad_y_transporte.py
python 3_conectividad_teletrabajo/mapa3_conectividad_teletrabajo.py
python 4_confort_climatico/mapa4_confort_climatico_estacional.py
python 5_indice_destino_tech/mapa5_indice_destino_tech.py
```

## Salidas generadas

Cada mapa deja sus resultados dentro de su carpeta `salidas/`.

Archivos habituales:

- `*.html`: mapa interactivo para abrir en navegador;
- `*.png`: imagen estatica;
- `*.pdf`: version estatica en PDF;
- `*.csv`: datos preparados usados por el mapa.

Ejemplo:

```text
3_conectividad_teletrabajo/salidas/
|-- mapa3_conectividad_teletrabajo.png
|-- mapa3_conectividad_teletrabajo.pdf
|-- mapa3_conectividad_teletrabajo_interactivo.html
`-- mapa3_conectividad_teletrabajo_datos.csv
```

## Apps Streamlit

### App del mapa 5

Permite recalcular el indice final cambiando pesos, filtros y provincia.

```bash
python -m streamlit run app_streamlit/app.py --server.address 127.0.0.1 --server.port 8501
```

Despues abre:

```text
http://127.0.0.1:8501
```

## Memoria

La memoria principal esta en:

```text
memoria/memoria.md
```

Exportar a PDF con el script incluido:

```bash
python memoria/exportar_pdf.py
```

Exportar con nombre de entrega:

```bash
python memoria/exportar_pdf.py -o memoria/TusApellidosTuNombre.pdf
```

Si prefieres usar Pandoc directamente:

```bash
pandoc memoria/memoria.md -o memoria/TusApellidosTuNombre.pdf --pdf-engine=xelatex --toc --number-sections --resource-path=memoria:.
```

## Datos

La carpeta `datos/` contiene datasets descargados o cacheados. Algunos scripts
pueden descargar datos si no los encuentran localmente, por ejemplo fuentes de
MIVAU, SETELECO, Eurostat/GISCO o NASA POWER.

Si una ejecucion falla por red, revisa que los archivos necesarios ya existan en
`datos/` o vuelve a ejecutar con conexion.

## Orden recomendado de ejecucion

Para rehacer todo el proyecto:

```bash
./run/regenerar_todos_los_mapas.sh
python memoria/exportar_pdf.py
```

Para revisar el resultado final:

```bash
./run/abrir_todos_los_mapas.sh
python -m streamlit run app_streamlit/app.py --server.address 127.0.0.1 --server.port 8501
```

## Problemas comunes

Si aparece `ModuleNotFoundError`, falta alguna dependencia en el entorno activo.
Instalala con `pip install ...` o activa el entorno `VD`.

Si los lanzadores no se ejecutan, revisa permisos:

```bash
chmod +x run/*.sh
```

Si no se abre el navegador automaticamente, abre manualmente el archivo HTML que
aparece por pantalla.

Si la exportacion a PDF falla, comprueba que `pandoc` y un motor LaTeX
(`xelatex` o `lualatex`) estan instalados.
