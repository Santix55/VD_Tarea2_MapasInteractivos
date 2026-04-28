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
