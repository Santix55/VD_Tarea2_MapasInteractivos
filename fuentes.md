# Fuentes utilizadas

## Mapa 1: precio actual del alquiler y dispersion interna

- **MIVAU - Sistema Estatal de Referencia del Precio del Alquiler de Vivienda**  
  Dataset CSV: `VDP001_01.csv`  
  URL: https://cdn.mivau.gob.es/portal-web-mivau/Datos_MIVAU/CSV/VDP001_01.csv  
  Uso: precios municipales de alquiler, percentiles 25/50/75 y recuento de viviendas para calcular medias ponderadas, dispersion y puntos municipales.

- **Eurostat/GISCO - NUTS 2024, escala 1:1M, nivel 3**  
  Dataset GeoJSON: `NUTS_RG_01M_2024_4326_LEVL_3.geojson`  
  URL: https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson  
  Uso: geometría provincial equivalente a NUTS3; en Baleares y Canarias se disuelve la geometría insular a provincia.

- **Eurostat/GISCO - LAU 2024, escala 1:1M**  
  Dataset GeoJSON: `LAU_RG_01M_2024_4326.geojson`  
  URL: https://gisco-services.ec.europa.eu/distribution/v2/lau/geojson/LAU_RG_01M_2024_4326.geojson  
  Uso: geometria municipal para crear puntos representativos reales de los municipios con dato de alquiler.

## Mapa 4: conectividad para teletrabajo e IA por provincia

- **Ministerio para la Transformación Digital y de la Función Pública / SETELECO - Cobertura Banda Ancha España 2021-2024**  
  Dataset XLSX: `cobertura_ba_espana_2021-2024_mun_prov_ccaa_nacional_datosgob.xlsx`  
  URL: https://digital.gob.es/content/dam/portal-mtdfp/avance-digital/telecomunicacion-e-infraestructuras-digitales/areas_interes/banda-ancha/cobertura/documents/cobertura_ba_espana_2021-2024_mun_prov_ccaa_nacional_datosgob.xlsx  
  Uso: porcentaje provincial de hogares con cobertura de banda ancha fija de al menos 1 Gbps en condiciones de maxima demanda, junio de 2024, y mejora entre junio de 2023 y junio de 2024.

- **Eurostat/GISCO - NUTS 2024, escala 1:1M, nivel 3**  
  Dataset GeoJSON: `NUTS_RG_01M_2024_4326_LEVL_3.geojson`  
  URL: https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson  
  Uso: geometría provincial equivalente a NUTS3; en Baleares y Canarias se disuelve la geometría insular a provincia.

## Mapa 5: confort climatico estacional por provincia

- **NASA POWER - Monthly API**  
  API JSON: parametro `T2M`, comunidad `SB`, periodo 1995-2024  
  URL base: https://power.larc.nasa.gov/api/temporal/monthly/point  
  Documentacion: https://power.larc.nasa.gov/docs/services/api/temporal/monthly/  
  Uso: temperatura media mensual del aire a 2 metros para el punto representativo de cada provincia; se calculan medias ponderadas por dias para invierno, primavera, verano, otono y media anual.

- **Eurostat/GISCO - NUTS 2024, escala 1:1M, nivel 3**  
  Dataset GeoJSON: `NUTS_RG_01M_2024_4326_LEVL_3.geojson`  
  URL: https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson  
  Uso: geometría provincial equivalente a NUTS3; en Baleares y Canarias se disuelve la geometría insular a provincia.

## Mapa 6: indice final de destino residencial tech

- **MIVAU - Sistema Estatal de Referencia del Precio del Alquiler de Vivienda**  
  Dataset CSV: `VDP001_01.csv`  
  URL: https://cdn.mivau.gob.es/portal-web-mivau/Datos_MIVAU/CSV/VDP001_01.csv  
  Uso: alquiler medio ponderado provincial en 2024, evolucion anualizada desde el primer ano comparable a partir de 2019 y recuento de viviendas de alquiler observadas.

- **Ministerio para la Transformación Digital y de la Función Pública / SETELECO - Cobertura Banda Ancha España 2021-2024**  
  Dataset XLSX: `cobertura_ba_espana_2021-2024_mun_prov_ccaa_nacional_datosgob.xlsx`  
  URL: https://digital.gob.es/content/dam/portal-mtdfp/avance-digital/telecomunicacion-e-infraestructuras-digitales/areas_interes/banda-ancha/cobertura/documents/cobertura_ba_espana_2021-2024_mun_prov_ccaa_nacional_datosgob.xlsx  
  Uso: hogares, poblacion y porcentaje provincial de hogares con cobertura fija de al menos 1 Gbps en junio de 2024.

- **NASA POWER - Monthly API**  
  API JSON: parametro `T2M`, comunidad `SB`, periodo 1995-2024  
  URL base: https://power.larc.nasa.gov/api/temporal/monthly/point  
  Uso: indice de confort climatico calculado en el mapa 5 y reutilizado como componente secundario del indice final.

- **Eurostat/GISCO - NUTS 2024, escala 1:1M, nivel 3**  
  Dataset GeoJSON: `NUTS_RG_01M_2024_4326_LEVL_3.geojson`  
  URL: https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson  
  Uso: geometría provincial equivalente a NUTS3; en Baleares y Canarias se disuelve la geometría insular a provincia.
