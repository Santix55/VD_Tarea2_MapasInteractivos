# Mapa 2: movilidad y transporte

Este mapa sustituye la evolucion del alquiler por una lectura de movilidad intermodal. La coropleta provincial muestra un `mobility_score` de 0 a 100 y la capa de puntos agrupa nodos ferroviarios y aeroportuarios para ver rapidamente que provincias permiten vivir fuera de los grandes hubs sin quedar aislado.

## Metodologia

- Estaciones ferroviarias: Renfe Data, listado completo de estaciones.
- Recorridos ferroviarios: Renfe Data GTFS de alta velocidad, larga distancia y media distancia.
- Aeropuertos: nodos AENA/ENAIRE incorporados como puntos estrategicos, no como rutas aereas.
- Poblacion: hoja provincial del XLSX de cobertura SETELECO, usada para normalizar nodos por 100.000 habitantes.
- Cartografia: provincias NUTS3 2024 de Eurostat/GISCO.
- Indice provincial: 60% cercania al nodo estrategico mas cercano y 40% nodos ponderados por 100.000 habitantes.

## Lectura visual

- La coropleta compara provincias por accesibilidad relativa al transporte.
- Los recorridos se separan en capas checkbox: alta velocidad, larga distancia y media distancia.
- Los puntos se agrupan con `MarkerCluster` y se separan por capas: alta velocidad, larga distancia, media distancia, Cercanias, FEVE y aeropuertos.
- Alta velocidad, larga distancia, media distancia y aeropuertos estan activos en la vista inicial; Cercanias y FEVE quedan disponibles para activar si se quiere mas detalle.
- Los popups incluyen nombre, modo, provincia, poblacion local cuando existe y fuente.

## Ejecutar

```bash
/home/s/miniconda3/envs/VD/bin/python 2_evolucion_alquiler/mapa2_evolucion_alquiler.py
```

El script genera:

- `salidas/mapa2_movilidad_transportes.png`
- `salidas/mapa2_movilidad_transportes.pdf`
- `salidas/mapa2_movilidad_transportes_interactivo.html`
- `salidas/mapa2_movilidad_transportes_datos.csv`
- `salidas/mapa2_movilidad_transportes_nodos.csv`
- `salidas/mapa2_movilidad_transportes_recorridos.csv`

Tambien mantiene copias con el nombre antiguo `mapa2_evolucion_alquiler.*` para que los scripts de ejecucion existentes sigan funcionando.
