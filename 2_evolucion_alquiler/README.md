# Mapa 2: trayectorias del alquiler

Este mapa responde a la pregunta de que provincias se estan encareciendo mas, pero lo hace con una lectura temporal mas rica que una subida acumulada simple. El color representa la variacion total del alquiler y el simbolo resume el patron de trayectoria de cada provincia.

## Metodologia

- Fuente de alquiler: `VDP001_01.csv` de MIVAU.
- Variable de precio: `ELEMENTO = PRECIO` y `TIPO_MEDIDA = MEDIANA`.
- Peso usado: `ELEMENTO = VIVIENDA` y `TIPO_MEDIDA = RECUENTO`.
- Agregacion municipal: media ponderada por tipo de vivienda usando el recuento de viviendas.
- Agregacion provincial: media ponderada de municipios con dato, usando viviendas observadas como peso.
- Periodo por defecto: primer ano comparable desde 2019 frente a 2024. Esto mantiene la comparacion 2019-2024 para la mayoria de provincias y usa el primer historico disponible para Navarra y Gipuzkoa. Araba/Alava y Bizkaia quedan marcadas como sin historico comparable porque solo tienen dato en 2024.
- Metricas temporales:
  - subida total desde el primer ano comparable >= 2019 hasta 2024;
  - subida reciente 2021-2024;
  - subida previa 2011-2019 cuando existe serie completa;
  - aceleracion en puntos porcentuales por ano: ritmo reciente menos ritmo 2011-2019.
- Clases de trayectoria: subida extrema, aceleracion reciente, rebote post-2021, subida sostenida, crecimiento contenido y sin historico comparable.
- Cartografia: NUTS3 2024 de Eurostat/GISCO, disuelta por codigo provincial para encajar Baleares y Canarias.
- Clasificacion de la coropleta: 5 cuantiles de crecimiento total.
- Paleta: divergente, con azul para subidas menores y rojo para subidas mayores.
- Extra visual: simbolos de trayectoria sobre el mapa, matriz lateral de subida total frente a aceleracion y mini-series indexadas de provincias destacadas.
- Interactividad: mapa Folium con coropleta, marcadores de trayectoria, popups con sparkline anual, capa temporal con slider, busqueda, minimapa, pantalla completa, medicion y control de capas.

## Ejecutar

```bash
/home/s/miniconda3/envs/VD/bin/python 2_evolucion_alquiler/mapa2_evolucion_alquiler.py
```

El script genera:

- `salidas/mapa2_evolucion_alquiler.png`
- `salidas/mapa2_evolucion_alquiler.pdf`
- `salidas/mapa2_evolucion_alquiler_interactivo.html`
- `salidas/mapa2_evolucion_alquiler_datos.csv`
- `salidas/mapa2_evolucion_alquiler_serie_anual.csv`
- `salidas/mapa2_evolucion_alquiler_serie_indexada.csv`

Tambien se puede forzar una comparacion exacta sin fallback:

```bash
/home/s/miniconda3/envs/VD/bin/python 2_evolucion_alquiler/mapa2_evolucion_alquiler.py --start-year 2019 --exact-start
```

## App Streamlit

La app complementaria permite cambiar ano inicial/final, activar o desactivar el fallback al primer historico comparable, filtrar por clase de trayectoria, consultar la matriz interactiva y ver la serie temporal de una provincia seleccionada.

```bash
/home/s/miniconda3/envs/VD/bin/python -m streamlit run app_streamlit/mapa2_evolucion_app.py --server.address 127.0.0.1 --server.port 8502
```
