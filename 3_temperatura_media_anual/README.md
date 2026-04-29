# Mapa 3: temperatura media anual por provincia

Este mapa representa la temperatura media anual estimada por provincia en Espana, usando el promedio del periodo 1995-2024. La visualizacion se ha planteado de forma distinta a los mapas 1 y 2: combina coropleta, circulos proporcionales, ranking lateral e histograma.

## Metodologia

- Fuente climatica: NASA POWER, API mensual, parametro `T2M`.
- Variable principal: temperatura media del aire a 2 metros.
- Unidad: grados Celsius.
- Agregacion: media anual ponderada por dias de cada mes para el punto representativo de cada provincia.
- Cartografia: NUTS3 2024 de Eurostat/GISCO. En Baleares y Canarias la geometria NUTS3 se disuelve a provincia para que encaje con el resto de mapas.
- Clasificacion de la coropleta: cortes naturales de Jenks con 5 intervalos.
- Metricas derivadas: anomalia termica respecto a la media provincial espanola, superficie provincial proyectada y un indice sencillo de ajuste a clima templado.
- Elementos de los apuntes usados: `dissolve`, `to_crs`, `representative_point`, leyendas, etiquetas, capas GeoJSON, `CircleMarker`, popups HTML, control de capas, escala, minimapa, pantalla completa, herramienta de medida, dibujo interactivo, busqueda y `LatLngPopup`.

## Ejecutar

```bash
/home/s/miniconda3/envs/VD/bin/python 3_temperatura_media_anual/mapa3_temperatura_media_anual_provincias.py
```

El script guarda una cache climatica en `datos/` para no repetir las peticiones a NASA POWER y genera:

- `salidas/mapa3_temperatura_media_anual_provincias.png`
- `salidas/mapa3_temperatura_media_anual_provincias.pdf`
- `salidas/mapa3_temperatura_media_anual_provincias_interactivo.html`
- `salidas/mapa3_temperatura_media_anual_provincias_datos.csv`
