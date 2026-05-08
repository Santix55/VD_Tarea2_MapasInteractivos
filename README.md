# VD Tarea 2 - Mapas interactivos

Proyecto de visualizacion de datos georreferenciados sobre la pregunta:

**Donde vivir despues del Master de IA en la UPV**

El repositorio genera seis mapas sobre alquiler, evolucion temporal,
accesibilidad laboral tech, conectividad, confort climatico e indice final de
destino residencial. Tambien incluye dos apps Streamlit y una memoria en
Markdown/PDF.

## Estructura

```text
.
|-- 1_precio_medio_alquiler_provincia/
|-- 2_evolucion_alquiler/
|-- 3_accesibilidad_laboral_tech/
|-- 4_conectividad_teletrabajo/
|-- 5_confort_climatico/
|-- 6_indice_destino_tech/
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
./run/mapa2_evolucion_alquiler.sh
./run/mapa3_accesibilidad_laboral_tech.sh
./run/mapa4_conectividad_teletrabajo.sh
./run/mapa5_confort_climatico.sh
./run/mapa6_indice_destino_tech.sh
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
./run/mapa4_conectividad_teletrabajo.sh --regen
```

Regenerar un mapa sin abrirlo:

```bash
./run/mapa4_conectividad_teletrabajo.sh --regen --no-abrir
```

Usar un Python concreto:

```bash
PYTHON_BIN=/home/s/miniconda3/envs/VD/bin/python ./run/mapa4_conectividad_teletrabajo.sh --regen
```

## Ejecutar scripts Python directamente

Tambien puedes ejecutar cada mapa sin los lanzadores:

```bash
python 1_precio_medio_alquiler_provincia/mapa1_alquiler_provincias.py
python 2_evolucion_alquiler/mapa2_evolucion_alquiler.py
python 3_accesibilidad_laboral_tech/mapa3_accesibilidad_laboral_tech.py
python 4_conectividad_teletrabajo/mapa4_conectividad_teletrabajo.py
python 5_confort_climatico/mapa5_confort_climatico_estacional.py
python 6_indice_destino_tech/mapa6_indice_destino_tech.py
```

El mapa 2 permite una comparacion exacta de anos:

```bash
python 2_evolucion_alquiler/mapa2_evolucion_alquiler.py --start-year 2019 --exact-start
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
4_conectividad_teletrabajo/salidas/
|-- mapa4_conectividad_teletrabajo.png
|-- mapa4_conectividad_teletrabajo.pdf
|-- mapa4_conectividad_teletrabajo_interactivo.html
`-- mapa4_conectividad_teletrabajo_datos.csv
```

## Apps Streamlit

### App del mapa 2

Permite explorar la evolucion del alquiler con filtros y seleccion de anos.

```bash
python -m streamlit run app_streamlit/mapa2_evolucion_app.py --server.address 127.0.0.1 --server.port 8502
```

Despues abre:

```text
http://127.0.0.1:8502
```

### App del mapa 6

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
