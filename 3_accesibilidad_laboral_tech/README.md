# Mapa 3: accesibilidad laboral tech/IA

Este mapa mide la distancia euclidea desde cada provincia espanola al hub de trabajo tech/IA mas cercano. La idea es separar una pregunta nueva dentro del estudio: no cuanto cuesta vivir, sino que tan cerca queda cada territorio de un ecosistema urbano donde es razonable esperar mas empleo tecnologico, networking, eventos, universidades o empresas.

## Metodologia

- Variable principal: distancia euclidea en kilometros al hub tech/IA mas cercano.
- Hubs usados: UPV/Valencia, Madrid, Barcelona, Malaga, Bilbao, Sevilla y Zaragoza.
- La capa de hubs es metodologica y propia del proyecto. No representa una fuente oficial de empleo ni mide ofertas laborales reales.
- Cartografia provincial: NUTS3 2024 de Eurostat/GISCO. En Baleares y Canarias la geometria NUTS3 se disuelve a provincia.
- Calculo espacial:
  - `representative_point()` para obtener un punto interior de cada provincia;
  - reproyeccion a `EPSG:3035` para medir distancias en metros;
  - `sjoin_nearest()` para asignar el hub mas cercano;
  - `buffer()` y `clip()` para crear anillos de influencia de 50, 100, 175 y 250 km, coloreados por hub;
  - lineas vectoriales coloreadas entre cada provincia y su hub mas cercano.
- Clasificacion de la coropleta: 5 intervalos definidos por usuario: `0-50`, `50-100`, `100-175`, `175-250` y `>250 km`.
- Alquiler 2024 de MIVAU: se usa solo como contexto en popups y en el grafico lateral distancia vs alquiler.

Importante: las distancias son euclideas, no tiempos reales de viaje, ni distancia por carretera, ni probabilidad directa de encontrar empleo.

## Ejecutar

```bash
/home/s/miniconda3/envs/VD/bin/python 3_accesibilidad_laboral_tech/mapa3_accesibilidad_laboral_tech.py
```

El script usa los datos ya cacheados en `datos/` y genera:

- `salidas/mapa3_accesibilidad_laboral_tech.png`
- `salidas/mapa3_accesibilidad_laboral_tech.pdf`
- `salidas/mapa3_accesibilidad_laboral_tech_interactivo.html`
- `salidas/mapa3_accesibilidad_laboral_tech_datos.csv`
- `salidas/mapa3_hubs_tech.csv`

El HTML interactivo incluye coropleta provincial, hubs, anillos por hub, lineas al hub mas cercano, busqueda, medicion, minimapa, pantalla completa, control de capas y herramienta de dibujo sin boton de exportacion.
