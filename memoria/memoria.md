---
title: "Dónde vivir después del Máster de IA en la UPV"
subtitle: "Análisis geoespacial de vivienda, conectividad y calidad de vida en España"
author: "TODO: Nombre Apellidos"
date: "Visualización de datos - Tarea 2"
lang: es-ES
toc: true
numbersections: true
geometry: margin=2.5cm
---

\newpage

# Resumen

Este trabajo estudia qué provincias españolas ofrecen un equilibrio razonable para una persona que termina el Máster de IA en la UPV y se plantea dónde vivir. La pregunta no se reduce a encontrar el alquiler más barato: también importa si el mercado residencial es estable, si existe infraestructura suficiente para teletrabajar, si se está cerca de ecosistemas tecnológicos y si las condiciones climáticas son habitables a largo plazo.

Para responderla se integran datos de alquiler municipal del MIVAU, cobertura de banda ancha del Ministerio para la Transformación Digital, temperatura histórica de NASA POWER y cartografía administrativa de Eurostat/GISCO. El resultado son seis mapas provinciales, todos con coropletas de al menos cinco clases, acompañados por capas interactivas, gráficas de apoyo y un índice sintético final.

La lectura principal es que las grandes provincias tecnológicas no siempre son las mejores desde el punto de vista residencial. Madrid, Barcelona, Bizkaia, Gipuzkoa o Málaga concentran oportunidades y buena conectividad, pero también soportan precios elevados o trayectorias de encarecimiento. En cambio, provincias como Asturias, Jaén, Ciudad Real, Zamora u Ourense aparecen como alternativas competitivas cuando se ponderan alquiler, estabilidad, disponibilidad, conectividad y confort climático.

# Introducción

## Problema de análisis

La decisión de dónde vivir después de un máster en inteligencia artificial tiene una dimensión espacial clara. Un perfil técnico puede buscar empleo presencial o híbrido en hubs consolidados, pero también puede teletrabajar si la infraestructura digital del territorio lo permite. Al mismo tiempo, el alquiler condiciona la viabilidad real de cualquier destino: una provincia con mucha actividad tecnológica puede no ser atractiva si el coste de entrada es demasiado alto o si el mercado se está tensionando con rapidez.

El objetivo del informe es construir una lectura geográfica integrada de España a escala provincial. La escala provincial permite combinar fuentes heterogéneas con menos ruido que la escala municipal, mantiene suficiente detalle territorial y facilita la comparación entre mapas. Cuando los datos originales son municipales, se agregan mediante pesos para no perder la información de base.

La pregunta de trabajo es:

> Qué provincias ofrecen mejor equilibrio entre coste de vivienda, evolución del alquiler, accesibilidad a ecosistemas tecnológicos, conectividad para teletrabajo y confort climático para un perfil universitario de IA.

## Fuentes de datos

Las fuentes utilizadas combinan repositorios oficiales, una API científica y cartografía administrativa europea:

| Ámbito | Fuente | Escala original | Rango | Uso en el informe |
|---|---:|---:|---:|---|
| Alquiler | MIVAU, Sistema Estatal de Referencia del Precio del Alquiler de Vivienda | Municipal | 2011-2024 | Precio actual, percentiles, viviendas observadas y evolución temporal |
| Conectividad | SETELECO / Ministerio para la Transformación Digital | Provincial y otras escalas | 2021-2024 | Cobertura de hogares con banda ancha fija >= 1 Gbps |
| Clima | NASA POWER, parámetro T2M | Punto representativo provincial | 1995-2024 | Temperatura media estacional y confort climático |
| Cartografía | Eurostat/GISCO NUTS 2024 y LAU 2024 | Provincia y municipio | 2024 | Geometrías para coropletas, puntos y cálculos espaciales |

El fichero principal de alquiler contiene 531.585 registros, 9 columnas, 7.331 municipios y 52 provincias. Sus columnas principales son código de provincia, provincia, código municipal, nombre del municipio, elemento medido, tipo de vivienda, tipo de medida, año y valor. Para la conectividad se usa un libro Excel oficial de cobertura 2021-2024. Para el clima se construye una tabla provincial de 52 filas a partir de la API mensual de NASA POWER. La cartografía provincial se toma de NUTS3 2024, y la municipal de LAU 2024 se usa para ubicar puntos representativos.

## Criterio metodológico

La memoria no busca producir seis mapas independientes, sino una narrativa de decisión. Por eso cada mapa responde a una pregunta distinta:

1. Cuánto cuesta alquilar ahora y dónde hay dispersión interna.
2. Dónde se está encareciendo más el alquiler.
3. Qué provincias quedan cerca de hubs tecnológicos o de IA.
4. Dónde la conectividad permite teletrabajo avanzado.
5. Qué provincias tienen condiciones climáticas más confortables.
6. Qué destinos salen mejor al integrar todos los criterios.

# Preparación de los datos

## Limpieza y normalización

La preparación se realizó con `pandas` y `GeoPandas`. En primer lugar, se homogeneizaron códigos territoriales, nombres de provincia y tipos numéricos. Esta fase es importante porque las fuentes no comparten exactamente el mismo formato: los datos de MIVAU están a escala municipal y separados por tipo de vivienda y medida; la conectividad llega en hojas de Excel; la cartografía NUTS3 tiene códigos europeos; y NASA POWER devuelve series temporales por coordenadas.

En el alquiler se filtraron los registros de precio y vivienda observada. Para el precio actual se utilizaron percentiles 25, mediana y 75; para la evolución se usó la mediana; y como peso de agregación se empleó el recuento de viviendas. Este criterio evita que municipios con pocos registros tengan la misma influencia que mercados mucho mayores.

## Agregación espacial

Los datos municipales de alquiler se agregaron a provincia mediante medias ponderadas. También se calcularon medidas de dispersión, como el rango intercuartil aproximado y la diferencia entre municipios extremos dentro de cada provincia. Esto permite detectar provincias cuyo promedio oculta tensiones locales.

La cartografía NUTS3 se preparó para coincidir con el dato provincial. En territorios insulares se usó `dissolve` cuando era necesario agrupar geometrías. Para las capas municipales se utilizaron puntos interiores con `representative_point()`, una opción más estable que el centroide cuando la geometría es irregular o multipoligonal.

## Reproyecciones y cálculos geométricos

Para representar mapas web se mantuvo `EPSG:4326`, pero los cálculos de distancia del mapa 3 se hicieron en `EPSG:3035`, una proyección adecuada para medir distancias en Europa. Después se devolvieron las capas a coordenadas geográficas para publicarlas en Folium.

El mapa de accesibilidad a hubs tecnológicos utiliza `sjoin_nearest()` para asignar a cada provincia el hub más cercano, `buffer()` para crear áreas de influencia y `clip()` para recortarlas al contorno de España. Estos pasos no son decorativos: hacen explícita la hipótesis espacial de proximidad a ecosistemas tecnológicos.

## Clasificación de coropletas

Todos los mapas de coropletas usan al menos cinco intervalos, como exige el enunciado. Se aplican criterios distintos según la variable:

- Cuantiles para comparar distribuciones relativas, como precio de alquiler o índice final.
- Intervalos definidos por usuario cuando existe una lectura operativa, como la cobertura de 1 Gbps o la distancia a hubs.
- Cortes naturales de Jenks para el confort climático, porque la temperatura presenta agrupaciones territoriales no lineales.
- Escalas divergentes cuando interesa distinguir intensidad de crecimiento, como en la evolución del alquiler.

# Visualización de datos

## Mapa 1. Precio actual del alquiler y dispersión interna

![Mapa 1. Precio actual del alquiler y dispersión interna](../1_precio_medio_alquiler_provincia/salidas/mapa1_alquiler_provincias.png)

El primer mapa representa el precio mensual del alquiler en 2024. La coropleta provincial se complementa con puntos municipales cuyo color indica precio y cuyo tamaño resume viviendas observadas. Esta combinación permite evitar una lectura demasiado plana del territorio: una provincia puede parecer moderada en promedio y, aun así, contener municipios muy tensionados.

Las provincias más caras en el cálculo ponderado son Madrid, Barcelona, Gipuzkoa, Illes Balears y Bizkaia. En el extremo inferior aparecen Lugo, Ourense, Ciudad Real, Zamora y Teruel. La diferencia entre ambos grupos muestra que el coste residencial sigue una lógica metropolitana y litoral, pero también que el interior conserva mercados más asequibles.

Técnicas principales: `merge` entre datos y geometría, agregación ponderada, cálculo de percentiles, cuantiles de cinco clases, puntos municipales con `representative_point()`, tooltips y popups HTML en Folium.

Salida interactiva: `../1_precio_medio_alquiler_provincia/salidas/mapa1_alquiler_provincias_interactivo.html`.

## Mapa 2. Evolución del alquiler

![Mapa 2. Evolución del alquiler](../2_evolucion_alquiler/salidas/mapa2_evolucion_alquiler.png)

El segundo mapa introduce temporalidad. Compara el alquiler actual con el primer año comparable desde 2019 hasta 2024 y clasifica las provincias según su trayectoria. La visualización no solo mide cuánto ha subido el precio, sino si el crecimiento reciente se acelera respecto a la etapa anterior.

Las subidas más intensas se concentran en València/Valencia, Castellón/Castelló, Málaga, Alicante y Guadalajara. En cambio, Gipuzkoa, Melilla, Ceuta, Palencia y Zamora muestran crecimientos más contenidos. Esta lectura es relevante porque un alquiler moderado hoy puede dejar de serlo si el ritmo de subida es alto.

Técnicas principales: serie temporal anual, comparación flexible por año base, clases de trayectoria, coropleta divergente de cinco cuantiles, gráficas laterales y mapa interactivo con capas temporales.

Salida interactiva: `../2_evolucion_alquiler/salidas/mapa2_evolucion_alquiler_interactivo.html`.

## Mapa 3. Accesibilidad laboral a hubs tech/IA

![Mapa 3. Accesibilidad laboral a hubs tech/IA](../3_accesibilidad_laboral_tech/salidas/mapa3_accesibilidad_laboral_tech.png)

El tercer mapa cambia el foco desde la vivienda hacia la accesibilidad laboral. Se define una capa metodológica de hubs tecnológicos o de IA: Valencia/UPV, Madrid, Barcelona, Málaga, Bilbao, Sevilla y Zaragoza. A partir de ella se calcula la distancia euclídea de cada provincia al hub más cercano.

Madrid, Bizkaia, Sevilla y Málaga quedan en el primer intervalo de proximidad inmediata. La interpretación debe ser prudente: el mapa no mide ofertas de empleo reales ni tiempos de viaje por carretera, sino una accesibilidad espacial simplificada a entornos donde es razonable esperar más actividad tecnológica, universidades, eventos y empresas.

Técnicas principales: reproyección a `EPSG:3035`, `sjoin_nearest()`, anillos de influencia de 50, 100, 175 y 250 km coloreados por hub, líneas provincia-hub, capas apagables, herramienta de medición y `Draw(export=True)` en Folium.

Salida interactiva: `../3_accesibilidad_laboral_tech/salidas/mapa3_accesibilidad_laboral_tech_interactivo.html`.

## Mapa 4. Conectividad para teletrabajo e IA

![Mapa 4. Conectividad para teletrabajo e IA](../4_conectividad_teletrabajo/salidas/mapa4_conectividad_teletrabajo.png)

El cuarto mapa funciona como filtro tecnológico. Utiliza el porcentaje de hogares con cobertura fija de al menos 1 Gbps en junio de 2024 y añade la mejora anual como información secundaria. Para un perfil de IA, esta variable no sustituye a la oferta laboral, pero condiciona la posibilidad de trabajar en remoto con estabilidad.

Madrid, Barcelona, Melilla, Araba/Álava y Sevilla muestran coberturas muy altas. Lugo, Ourense, Huesca, Teruel y Soria aparecen como provincias que requieren más cautela. La conectividad revela una tensión interesante: algunas provincias baratas no son necesariamente las más preparadas para teletrabajo intensivo.

Técnicas principales: umbrales operativos de cinco clases, lectura tipo semáforo, capas alternativas en Folium, `LayerControl`, `MarkerCluster` para provincias a revisar y popups con recomendación.

Salida interactiva: `../4_conectividad_teletrabajo/salidas/mapa4_conectividad_teletrabajo_interactivo.html`.

## Mapa 5. Confort climático estacional

![Mapa 5. Confort climático estacional](../5_confort_climatico/salidas/mapa5_confort_climatico_estacional.png)

El quinto mapa incorpora una dimensión de calidad de vida. Se calcula la temperatura media estacional entre 1995 y 2024 y se deriva un índice de confort climático. Esta variable tiene menos peso que la vivienda o la conectividad, pero ayuda a distinguir destinos que serían similares en términos económicos.

Córdoba, Alicante/Alacant, Almería, València/Valencia y Jaén obtienen las puntuaciones climáticas más altas según el criterio usado. Cantabria, León, Burgos, Palencia y Soria quedan en la parte baja. Conviene interpretar este resultado como confort térmico medio, no como evaluación completa de riesgos climáticos, humedad, olas de calor o preferencias personales.

Técnicas principales: consulta a API, medias ponderadas por días de mes, cortes naturales de Jenks, `TimeSliderChoropleth`, marcadores circulares, etiquetas dinámicas y tooltips estacionales.

Salida interactiva: `../5_confort_climatico/salidas/mapa5_confort_climatico_estacional_interactivo.html`.

## Mapa 6. Índice final de destino residencial tech

![Mapa 6. Índice final de destino residencial tech](../6_indice_destino_tech/salidas/mapa6_indice_destino_tech.png)

El sexto mapa sintetiza el proyecto. El índice final combina cinco componentes normalizados entre 0 y 100: alquiler bajo, subida moderada del alquiler, disponibilidad del mercado, conectividad de 1 Gbps y confort climático. Los pesos iniciales son 35%, 20%, 15%, 20% y 10%, respectivamente.

El ranking resultante sitúa en cabeza a Asturias, Jaén, Ciudad Real, Zamora y Ourense. En la parte baja aparecen Bizkaia, Araba/Álava, Gipuzkoa, Málaga y Navarra. Esta salida no significa que las provincias peor clasificadas sean malas opciones absolutas: muchas tienen ecosistemas laborales fuertes. Lo que indica es que, bajo los pesos elegidos, el equilibrio residencial favorece provincias de coste más contenido y conectividad suficiente.

Técnicas principales: normalización min-max, inversión de variables cuando un valor bajo es favorable, índice compuesto ponderado, coropleta de cinco cuantiles, ranking top 10, popups con desglose de componentes y app Streamlit con pesos ajustables.

Salida interactiva: `../6_indice_destino_tech/salidas/mapa6_indice_destino_tech_interactivo.html`.

# Conclusiones

La primera conclusión es que el precio del alquiler sigue siendo el factor que más condiciona la decisión residencial. Madrid, Barcelona y varias provincias vascas concentran precios altos, mientras que Lugo, Ourense, Ciudad Real, Zamora y Teruel mantienen niveles más accesibles. Para un egresado reciente, esta diferencia puede ser más determinante que pequeñas variaciones en clima o conectividad.

La segunda conclusión es que no basta con mirar el precio actual. La Comunidad Valenciana y el litoral mediterráneo muestran dinámicas de encarecimiento intensas, especialmente València/Valencia, Castellón/Castelló, Málaga y Alicante. Estos territorios pueden ser atractivos por clima, servicios y actividad económica, pero el crecimiento reciente reduce su margen de asequibilidad.

La tercera conclusión es que la conectividad abre oportunidades fuera de los grandes hubs. Muchas provincias no metropolitanas tienen cobertura de 1 Gbps suficientemente alta para teletrabajo o trabajo híbrido. Sin embargo, todavía hay territorios que combinan alquiler bajo con brecha digital, por lo que el mapa de conectividad actúa como filtro necesario antes de recomendar un destino.

La cuarta conclusión es que la proximidad a hubs tecnológicos y el índice final no siempre coinciden. Estar cerca de Madrid, Barcelona, Bilbao, Málaga o Valencia puede mejorar la exposición a empleo, eventos y redes profesionales, pero suele venir acompañado de costes residenciales más altos. El índice final favorece una estrategia distinta: vivir en provincias con buena relación coste-infraestructura y mantener conexión laboral remota o puntual con los hubs.

Como recomendación general, Asturias, Jaén, Ciudad Real, Zamora y Ourense forman un grupo de destinos competitivos bajo los pesos propuestos. No son necesariamente los lugares con más empleo tecnológico presencial, pero sí representan una combinación atractiva de alquiler contenido, estabilidad relativa, conectividad aceptable y calidad de vida. La decisión final dependería de preferencias personales y del tipo de empleo buscado, pero el análisis muestra que las alternativas al eje Madrid-Barcelona son reales y medibles.

# Limitaciones

El estudio tiene varias limitaciones que conviene reconocer. En primer lugar, la distancia a hubs tecnológicos es euclídea y no incorpora tiempos reales de transporte, frecuencia ferroviaria, aeropuertos ni red viaria. En segundo lugar, el índice final depende de pesos metodológicos; por eso se incluye una app Streamlit que permite modificarlos. En tercer lugar, el alquiler observado por MIVAU puede no capturar todo el mercado informal o anuncios en tiempo real. Por último, el confort climático se aproxima mediante temperatura media y no incorpora humedad, extremos, calidad del aire ni preferencias subjetivas.

Estas limitaciones no invalidan el análisis, pero delimitan su alcance. El objetivo es apoyar una comparación territorial razonada, no predecir la decisión óptima de cada persona.

# Apéndice técnico

## Librerías utilizadas

Las librerías principales son:

- `pandas` para lectura, limpieza, agregación y normalización.
- `GeoPandas` para lectura de cartografía, uniones espaciales, reproyecciones y geometría.
- `matplotlib` y `seaborn` para mapas estáticos y gráficas de apoyo.
- `mapclassify` para clasificación de coropletas.
- `folium` y plugins de Folium para mapas interactivos.
- `streamlit`, `streamlit_folium` y `plotly` para las apps complementarias.
- `requests` para obtener datos de APIs cuando es necesario.
- `openpyxl` para leer el libro Excel de conectividad.

## Métodos especiales

Los métodos menos básicos usados en el proyecto son:

- `dissolve()` para agrupar geometrías y ajustar la cartografía a la escala provincial.
- `representative_point()` para ubicar etiquetas y marcadores dentro de la geometría real.
- `to_crs()` para cambiar de sistema de referencia antes de calcular distancias.
- `sjoin_nearest()` para asignar cada provincia al hub tecnológico más cercano.
- `buffer()` y `clip()` para construir áreas de influencia y recortarlas al territorio español.
- `TimeSliderChoropleth` para comparar estaciones climáticas en el mapa interactivo.
- Popups HTML para explicar valores, rankings y recomendaciones sin saturar el mapa.
- Normalización min-max e inversión de indicadores para construir el índice final.

## Reproducibilidad

Cada mapa vive en su propia carpeta y puede ejecutarse de forma independiente:

```bash
/home/s/miniconda3/envs/VD/bin/python 1_precio_medio_alquiler_provincia/mapa1_alquiler_provincias.py
/home/s/miniconda3/envs/VD/bin/python 2_evolucion_alquiler/mapa2_evolucion_alquiler.py
/home/s/miniconda3/envs/VD/bin/python 3_accesibilidad_laboral_tech/mapa3_accesibilidad_laboral_tech.py
/home/s/miniconda3/envs/VD/bin/python 4_conectividad_teletrabajo/mapa4_conectividad_teletrabajo.py
/home/s/miniconda3/envs/VD/bin/python 5_confort_climatico/mapa5_confort_climatico_estacional.py
/home/s/miniconda3/envs/VD/bin/python 6_indice_destino_tech/mapa6_indice_destino_tech.py
```

Las apps complementarias se lanzan con:

```bash
/home/s/miniconda3/envs/VD/bin/python -m streamlit run app_streamlit/mapa2_evolucion_app.py --server.address 127.0.0.1 --server.port 8502
/home/s/miniconda3/envs/VD/bin/python -m streamlit run app_streamlit/app.py --server.address 127.0.0.1 --server.port 8501
```

## Entregables asociados

La entrega completa debe incluir:

- Scripts de Python de los seis mapas.
- Carpeta `datos/` con los datasets necesarios o cacheados.
- Salidas PNG, PDF, HTML y CSV de cada mapa.
- PDF final de esta memoria.
- Presentación 16:9 de entre 5 y 10 minutos.

# Referencias de datos

- MIVAU. Sistema Estatal de Referencia del Precio del Alquiler de Vivienda. `VDP001_01.csv`.
- Ministerio para la Transformación Digital y de la Función Pública / SETELECO. Cobertura Banda Ancha España 2021-2024.
- NASA POWER. Monthly API, parámetro `T2M`, período 1995-2024.
- Eurostat/GISCO. NUTS 2024, nivel 3, escala 1:1M.
- Eurostat/GISCO. LAU 2024, escala 1:1M.
