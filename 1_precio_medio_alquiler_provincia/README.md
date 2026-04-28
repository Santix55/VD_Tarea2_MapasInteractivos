# Mapa 1: precio medio de alquiler por provincia

Este mapa representa el precio medio mensual del alquiler por provincia en España con el último año disponible en MIVAU.

## Metodología

- Fuente de alquiler: `VDP001_01.csv` de MIVAU.
- Filtro usado: `ELEMENTO = PRECIO`, `TIPO_MEDIDA = MEDIANA`.
- Agregación: media ponderada provincial del precio mediano municipal, usando `ELEMENTO = VIVIENDA` y `TIPO_MEDIDA = RECUENTO` como peso.
- Cartografía: NUTS3 2024 de Eurostat/GISCO. En Baleares y Canarias la geometría NUTS3 se disuelve a provincia para que encaje con los datos de MIVAU.
- Clasificación de la coropleta: cuantiles con 5 intervalos.

## Ejecutar

```bash
python 1_precio_medio_alquiler_provincia/mapa1_alquiler_provincias.py
```

El script descarga los datos en `datos/` si no existen y genera:

- `salidas/mapa1_alquiler_provincias.png`
- `salidas/mapa1_alquiler_provincias.pdf`
- `salidas/mapa1_alquiler_provincias_interactivo.html`
- `salidas/mapa1_alquiler_provincias_datos.csv`
