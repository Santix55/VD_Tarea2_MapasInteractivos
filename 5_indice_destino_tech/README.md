# Mapa 5: indice final de destino residencial tech

Este mapa sintetiza los resultados del proyecto en un ranking provincial pensado para una persona que termina el Master de IA y busca un destino razonable para vivir, trabajar en remoto o moverse en un entorno tecnologico.

## Metodologia

El indice final se calcula con cuatro componentes normalizados en una escala 0-100:

- 41.18% alquiler bajo: cuanto menor es el alquiler mensual medio ponderado, mejor puntuacion.
- 23.53% movilidad relativa: acceso a nodos de alta velocidad, larga distancia, media distancia o aeropuerto, volumen ponderado de nodos y densidad de nodos ponderados por 100.000 habitantes.
- 23.53% conectividad: porcentaje de hogares con cobertura fija de al menos 1 Gbps en junio de 2024.
- 11.76% confort climatico: combina el confort termico del mapa 4 con la lluvia anual. Dentro de este componente, 70% depende de la cercania a una temperatura media anual de referencia y 30% de una precipitacion equilibrada, penalizando tanto provincias muy secas como excesivamente lluviosas frente a la mediana provincial.

La formula es una decision metodologica: favorece provincias con alquiler contenido, buena movilidad intermodal, buena infraestructura digital y confort de vida. La disponibilidad del mercado se conserva como dato informativo, pero no entra en la media final. El CSV de salida conserva cada componente, la lluvia anual, los sub-scores climaticos y su aportacion ponderada para poder justificar o cambiar los pesos.

## Lectura visual

- El mapa estatico usa una coropleta provincial con 5 cuantiles del indice final.
- La derecha del mapa muestra el top 10 y un desglose ponderado de los mejores destinos.
- El HTML interactivo permite buscar provincias, consultar tooltips y abrir popups con el detalle de puntuaciones.
- El HTML incluye sliders de pesos ponderados: al moverlos se normalizan a 100%, se recalculan la coropleta, el top 5, la leyenda dinamica y las etiquetas del top 10.

## Ejecutar

```bash
/home/s/miniconda3/envs/VD/bin/python 5_indice_destino_tech/mapa5_indice_destino_tech.py
```

El script genera:

- `salidas/mapa5_indice_destino_tech.png`
- `salidas/mapa5_indice_destino_tech.pdf`
- `salidas/mapa5_indice_destino_tech_interactivo.html`
- `salidas/mapa5_indice_destino_tech_datos.csv`

## App Streamlit

El mapa 5 tambien tiene una app complementaria con sliders de pesos, filtros, ranking dinamico, selector de provincia, graficos de desglose y mapa Folium recalculado.

```bash
/home/s/miniconda3/envs/VD/bin/python -m streamlit run app_streamlit/app.py --server.address 127.0.0.1 --server.port 8501
```
