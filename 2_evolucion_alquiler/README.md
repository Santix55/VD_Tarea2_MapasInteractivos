# Mapa 2: seguridad y poblacion

Este mapa sustituye la evolucion del alquiler por una lectura de seguridad relativa. La coropleta provincial muestra la tasa de infracciones penales conocidas por 1.000 habitantes en 2024, y la capa de puntos representa municipios agregados disponibles en el Balance de Criminalidad.

## Metodologia

- Fuente de criminalidad: Portal Estadistico de Criminalidad del Ministerio del Interior, Balance de Criminalidad 2024, 4º trimestre.
- Variable usada: `III. TOTAL INFRACCIONES PENALES`, periodo `enero-diciembre 2024`.
- Normalizacion: `hechos_delictivos / poblacion * 1000`.
- Poblacion: hoja municipal y provincial del XLSX de cobertura SETELECO, usada aqui como fuente auxiliar de habitantes.
- Cartografia: provincias NUTS3 2024 y municipios LAU 2024 de Eurostat/GISCO.
- Clasificacion: 5 cuantiles para la tasa provincial.

## Lectura visual

- La coropleta compara provincias por tasa delictiva relativa.
- Los puntos no representan delitos individuales: son municipios del balance oficial, principalmente capitales, municipios de mas de 20.000 habitantes e islas.
- El tamano del punto indica hechos conocidos y el color indica tasa por 1.000 habitantes.
- Los popups incluyen poblacion, hechos conocidos, tasa y lectura cualitativa.

## Ejecutar

```bash
/home/s/miniconda3/envs/VD/bin/python 2_evolucion_alquiler/mapa2_evolucion_alquiler.py
```

El script genera:

- `salidas/mapa2_seguridad_poblacion.png`
- `salidas/mapa2_seguridad_poblacion.pdf`
- `salidas/mapa2_seguridad_poblacion_interactivo.html`
- `salidas/mapa2_seguridad_poblacion_datos.csv`
- `salidas/mapa2_seguridad_poblacion_municipios.csv`

Tambien mantiene copias con el nombre antiguo `mapa2_evolucion_alquiler.*` para que los scripts de ejecucion existentes sigan funcionando.
