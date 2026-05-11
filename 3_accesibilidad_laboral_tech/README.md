# Mapa 3: accesibilidad laboral hibrida tech/IA

Este mapa mide la distancia euclidea desde cada provincia espanola al hub de trabajo tech/IA mas cercano y la cruza con el alquiler provincial de 2024. La idea es separar una pregunta nueva dentro del estudio: que territorios permiten vivir con un alquiler relativamente bajo sin quedar demasiado lejos de ecosistemas donde es razonable esperar mas empleo tecnologico, networking, eventos, universidades o empresas.

## Metodologia

- Variable principal: distancia euclidea en kilometros al hub tech/IA mas cercano.
- Hubs usados: UPV/Valencia, Madrid, Barcelona, Malaga, Bilbao, Sevilla y Zaragoza.
- La capa de hubs es metodologica y propia del proyecto. No representa una fuente oficial de empleo ni mide ofertas laborales reales.
- Lectura hibrida: se marca como candidata la provincia situada a `<=175 km` del hub mas cercano y con alquiler medio ponderado igual o inferior a la media nacional ponderada.
- Campos derivados:
  - `access_mode`: presencial frecuente, hibrido semanal, hibrido puntual, contacto ocasional o principalmente remoto;
  - `rent_gap_eur` y `rent_gap_label`: diferencia frente al alquiler medio nacional ponderado;
  - `tradeoff_group`: cerca y asequible, cerca pero caro, barato pero lejano, lejano y caro;
  - `hybrid_candidate`: indicador booleano de candidata cercana y con alquiler bajo media.
- Cartografia provincial: NUTS3 2024 de Eurostat/GISCO. En Baleares y Canarias la geometria NUTS3 se disuelve a provincia.
- Calculo espacial:
  - `representative_point()` para obtener un punto interior de cada provincia;
  - reproyeccion a `EPSG:3035` para medir distancias en metros;
  - `sjoin_nearest()` para asignar el hub mas cercano;
  - `buffer()` y `clip()` para crear anillos de influencia de 50, 100, 175 y 250 km, coloreados por hub;
  - lineas vectoriales coloreadas entre cada provincia y su hub mas cercano.
- Clasificacion de la coropleta: 5 intervalos definidos por usuario: `0-50`, `50-100`, `100-175`, `175-250` y `>250 km`.
- Alquiler 2024 de MIVAU: se usa como contexto en popups, como eje del grafico distancia/alquiler y como criterio para detectar candidatas hibridas asequibles.

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

El HTML interactivo incluye coropleta provincial, capa de candidatas cerca + alquiler bajo, hubs, anillos por hub, lineas al hub mas cercano, busqueda, medicion, minimapa, pantalla completa, control de capas y herramienta de dibujo sin boton de exportacion.
