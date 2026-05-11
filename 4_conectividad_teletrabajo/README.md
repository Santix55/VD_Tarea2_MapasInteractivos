# Mapa 4: conectividad multitecnologia para teletrabajo e IA

Este mapa funciona como filtro tecnologico municipal para evaluar la cobertura terrestre disponible y superponer una lectura satelital general. La version interactiva se simplifica a dos planos: conexion terrestre configurable y bandas diagonales de satelite.

## Metodologia

- Fuente de cobertura: XLSX oficial `Cobertura Banda Ancha Espana 2021-2024` de SETELECO / Ministerio para la Transformacion Digital y de la Funcion Publica.
- Hoja usada: `Municipio_%hogar`.
- Cartografia: LAU 2024 de Eurostat/GISCO, unida por `CMUN` normalizado a 5 digitos (`ES_XXXXX` en `GISCO_ID`).
- Tecnologias interactivas: WiFi/fijo, 4G y 5G.
- El modo WiFi/fijo usa un slider discreto de velocidad con los umbrales oficiales disponibles: 30 Mbps, 100 Mbps y 1 Gbps.
- Respaldo satelital: bandas diagonales conceptuales basadas en Conectate35/Hispasat. No sustituye a la fibra ni mide huellas fisicas exactas; solo comunica cobertura satelital general.

## Lectura visual

- En el mapa estatico se resume el caso inicial: fijo >=100 Mbps con umbral del 90%.
- En el mapa interactivo, el panel izquierdo permite elegir WiFi/fijo, 4G o 5G. Si se elige WiFi/fijo aparece el slider de velocidad.
- Los municipios se clasifican por cobertura alta, media, limitada o baja.
- La capa satelital se activa con un checkbox y aparece como franjas diagonales rojas semitransparentes sobre el mapa.
- Los popups HTML incluyen barras simples para WiFi/fijo, 4G y 5G.
- Tambien se usan `Search`, `MiniMap`, `Fullscreen`, `MeasureControl` y coordenadas.

## Validacion

La salida `salidas/mapa4_conectividad_teletrabajo_validacion_union.csv` resume el encaje municipal entre datos y geometria. En la ultima generacion: 8.131 municipios con dato, 1 geometria sin dato y 0 datos sin geometria.

## Ejecutar

```bash
/home/s/miniconda3/envs/VD/bin/python 4_conectividad_teletrabajo/mapa4_conectividad_teletrabajo.py
```

El script descarga los datos en `datos/` si no existen y genera:

- `salidas/mapa4_conectividad_teletrabajo.png`
- `salidas/mapa4_conectividad_teletrabajo.pdf`
- `salidas/mapa4_conectividad_teletrabajo_interactivo.html`
- `salidas/mapa4_conectividad_teletrabajo_datos.csv`
- `salidas/mapa4_conectividad_teletrabajo_validacion_union.csv`
