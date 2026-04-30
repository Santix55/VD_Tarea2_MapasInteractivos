# Mapa 1: precio actual del alquiler y dispersion interna

Este mapa representa el precio mensual del alquiler en España con dos niveles de lectura: una coropleta provincial y una capa de puntos municipales. La idea es ver no solo que provincias son mas caras, sino tambien donde hay focos municipales caros dentro de provincias que en promedio pueden parecer moderadas.

## Metodología

- Fuente de alquiler: `VDP001_01.csv` de MIVAU.
- Filtro principal: `ELEMENTO = PRECIO`, con `TIPO_MEDIDA = PERCENT25`, `MEDIANA` y `PERCENT75`.
- Peso usado: `ELEMENTO = VIVIENDA`, `TIPO_MEDIDA = RECUENTO`.
- Agregación municipal: media ponderada por tipo de vivienda (`COLECTIVA` y `UNIFAMILIAR`) usando el recuento de viviendas.
- Agregación provincial: media ponderada de los municipios con dato, usando viviendas observadas como peso.
- Dispersión: rango intercuartil aproximado `P75 - P25` y rango entre municipios de cada provincia.
- Cartografía provincial: NUTS3 2024 de Eurostat/GISCO. En Baleares y Canarias la geometría NUTS3 se disuelve a provincia.
- Cartografía municipal: LAU 2024 de Eurostat/GISCO. Los puntos se obtienen con `representative_point()` de cada municipio.
- Clasificación de la coropleta: cuantiles con 5 intervalos.
- Capa de puntos: color por alquiler mediano municipal y tamaño por viviendas observadas.
- Grafica de apoyo: boxplot de provincias caras e histograma estatal ponderado por viviendas observadas.

## Ejecutar

```bash
/home/s/miniconda3/envs/VD/bin/python 1_precio_medio_alquiler_provincia/mapa1_alquiler_provincias.py
```

El script descarga los datos en `datos/` si no existen y genera:

- `salidas/mapa1_alquiler_provincias.png`
- `salidas/mapa1_alquiler_provincias.pdf`
- `salidas/mapa1_alquiler_provincias_interactivo.html`
- `salidas/mapa1_alquiler_provincias_datos.csv`
- `salidas/mapa1_alquiler_municipios_2024.csv`
- `salidas/mapa1_alquiler_municipios_puntos_2024.csv`

El HTML interactivo incluye coropleta provincial, puntos municipales, popups con percentiles, busqueda, pantalla completa, minimapa, escala y control de capas.
