# Mapa 5: confort climatico estacional

Este mapa representa la temperatura media por epoca del ano en las provincias espanolas y mantiene puntos con la temperatura media anual. La version interactiva incluye un slider estacional para comparar invierno, primavera, verano y otono, y etiquetas dinamicas con la temperatura exacta de la estacion seleccionada.

## Metodologia

- Fuente climatica: NASA POWER, API mensual, parametro `T2M`.
- Periodo: 1995-2024.
- Agregacion: medias ponderadas por dias de mes para cada estacion.
- Estaciones:
  - invierno: diciembre, enero y febrero.
  - primavera: marzo, abril y mayo.
  - verano: junio, julio y agosto.
  - otono: septiembre, octubre y noviembre.
- Cartografia: NUTS3 2024 de Eurostat/GISCO, disuelta a provincia cuando es necesario.
- Clasificacion: cortes naturales de Jenks con 5 intervalos.
- Elementos usados de los apuntes: `dissolve`, `to_crs`, `representative_point`, coropletas, capas, `CircleMarker`, etiquetas dinamicas, tooltips, popups, `LayerControl`, minimapa, pantalla completa, busqueda, escala y slider temporal con `TimeSliderChoropleth`.

## Ejecutar

```bash
/home/s/miniconda3/envs/VD/bin/python 5_confort_climatico/mapa5_confort_climatico_estacional.py
```

La primera ejecucion crea una cache en `datos/nasa_power_temperatura_estacional_provincias_1995_2024.csv`. Despues reutiliza ese CSV para no repetir las peticiones a NASA POWER.

El script genera:

- `salidas/mapa5_confort_climatico_estacional.png`
- `salidas/mapa5_confort_climatico_estacional.pdf`
- `salidas/mapa5_confort_climatico_estacional_interactivo.html`
- `salidas/mapa5_confort_climatico_estacional_datos.csv`
