# Fuentes utilizadas

## Mapa 1: precio medio de alquiler por provincia

- **MIVAU - Sistema Estatal de Referencia del Precio del Alquiler de Vivienda**  
  Dataset CSV: `VDP001_01.csv`  
  URL: https://cdn.mivau.gob.es/portal-web-mivau/Datos_MIVAU/CSV/VDP001_01.csv  
  Uso: precios municipales de alquiler y recuento de viviendas para calcular la media ponderada provincial.

- **Eurostat/GISCO - NUTS 2024, escala 1:1M, nivel 3**  
  Dataset GeoJSON: `NUTS_RG_01M_2024_4326_LEVL_3.geojson`  
  URL: https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson  
  Uso: geometría provincial equivalente a NUTS3; en Baleares y Canarias se disuelve la geometría insular a provincia.

## Mapa 2: cobertura de internet de alta velocidad por provincia

- **Ministerio para la Transformación Digital y de la Función Pública / SETELECO - Cobertura Banda Ancha España 2021-2024**  
  Dataset XLSX: `cobertura_ba_espana_2021-2024_mun_prov_ccaa_nacional_datosgob.xlsx`  
  URL: https://digital.gob.es/content/dam/portal-mtdfp/avance-digital/telecomunicacion-e-infraestructuras-digitales/areas_interes/banda-ancha/cobertura/documents/cobertura_ba_espana_2021-2024_mun_prov_ccaa_nacional_datosgob.xlsx  
  Uso: porcentaje provincial de hogares con cobertura de banda ancha fija de al menos 1 Gbps en condiciones de maxima demanda, junio de 2024.

- **Eurostat/GISCO - NUTS 2024, escala 1:1M, nivel 3**  
  Dataset GeoJSON: `NUTS_RG_01M_2024_4326_LEVL_3.geojson`  
  URL: https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson  
  Uso: geometría provincial equivalente a NUTS3; en Baleares y Canarias se disuelve la geometría insular a provincia.

## Mapa 3: temperatura media anual por provincia

- **NASA POWER - Monthly API**  
  API JSON: parametro `T2M`, comunidad `SB`, periodo 1995-2024  
  URL base: https://power.larc.nasa.gov/api/temporal/monthly/point  
  Documentacion: https://power.larc.nasa.gov/docs/services/api/temporal/monthly/  
  Uso: temperatura media mensual del aire a 2 metros para el punto representativo de cada provincia; se calcula una media anual ponderada por dias del mes.

- **Eurostat/GISCO - NUTS 2024, escala 1:1M, nivel 3**  
  Dataset GeoJSON: `NUTS_RG_01M_2024_4326_LEVL_3.geojson`  
  URL: https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson  
  Uso: geometría provincial equivalente a NUTS3; en Baleares y Canarias se disuelve la geometría insular a provincia.
