# Mapa 6: indice final de destino residencial tech

Este mapa sintetiza los resultados del proyecto en un ranking provincial pensado para una persona que termina el Master de IA y busca un destino razonable para vivir, trabajar en remoto o moverse en un entorno tecnologico.

## Metodologia

El indice final se calcula con cinco componentes normalizados en una escala 0-100:

- 35% alquiler bajo: cuanto menor es el alquiler mensual medio ponderado, mejor puntuacion.
- 20% movilidad: acceso a nodos de alta velocidad, larga distancia, media distancia o aeropuerto y densidad de nodos ponderados por 100.000 habitantes.
- 15% disponibilidad del mercado: viviendas de alquiler observadas por cada 1.000 hogares.
- 20% conectividad: porcentaje de hogares con cobertura fija de al menos 1 Gbps en junio de 2024.
- 10% confort climatico: combina el confort termico del mapa 5 con la lluvia anual. Dentro de este componente, 70% depende de la cercania a una temperatura media anual de referencia y 30% de una precipitacion equilibrada, penalizando tanto provincias muy secas como excesivamente lluviosas frente a la mediana provincial.

La formula es una decision metodologica: favorece provincias con alquiler contenido, buena movilidad intermodal y buena infraestructura digital, sin dejar fuera mercado residencial y confort de vida. El CSV de salida conserva cada componente, la lluvia anual, los sub-scores climaticos y su aportacion ponderada para poder justificar o cambiar los pesos.

## Lectura visual

- El mapa estatico usa una coropleta provincial con 5 cuantiles del indice final.
- La derecha del mapa muestra el top 10 y un desglose ponderado de los mejores destinos.
- El HTML interactivo permite buscar provincias, consultar tooltips y abrir popups con el detalle de puntuaciones.
- El HTML incluye sliders de pesos ponderados: al moverlos se normalizan a 100%, se recalculan la coropleta, el top 5, la leyenda dinamica y las etiquetas del top 10.

## Ejecutar

```bash
/home/s/miniconda3/envs/VD/bin/python 6_indice_destino_tech/mapa6_indice_destino_tech.py
```

El script genera:

- `salidas/mapa6_indice_destino_tech.png`
- `salidas/mapa6_indice_destino_tech.pdf`
- `salidas/mapa6_indice_destino_tech_interactivo.html`
- `salidas/mapa6_indice_destino_tech_datos.csv`

## App Streamlit

El mapa 6 tambien tiene una app complementaria con sliders de pesos, filtros, ranking dinamico, selector de provincia, graficos de desglose y mapa Folium recalculado.

```bash
/home/s/miniconda3/envs/VD/bin/python -m streamlit run app_streamlit/app.py --server.address 127.0.0.1 --server.port 8501
```
