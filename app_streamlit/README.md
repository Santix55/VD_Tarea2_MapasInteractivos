# Apps Streamlit del proyecto

## Mapa 2: trayectorias del alquiler

App complementaria del mapa 2. Permite cambiar ano inicial y final, activar o desactivar el uso del primer historico comparable, filtrar por clase de trayectoria, explorar el mapa Folium, consultar la matriz subida-aceleracion y revisar la serie temporal de cada provincia.

```bash
/home/s/miniconda3/envs/VD/bin/python -m streamlit run app_streamlit/mapa2_evolucion_app.py --server.address 127.0.0.1 --server.port 8502
```

La app reutiliza el script `2_evolucion_alquiler/mapa2_evolucion_alquiler.py`.

## Mapa 6: indice final de destino tech

App complementaria del mapa 6. Permite recalcular el indice final con pesos ajustables, aplicar filtros, consultar un ranking dinamico, explorar el mapa Folium recalculado y revisar el perfil de cada provincia.


```bash
/home/s/miniconda3/envs/VD/bin/python -m streamlit run app_streamlit/app.py --server.address 127.0.0.1 --server.port 8501
```

La app reutiliza el script `6_indice_destino_tech/mapa6_indice_destino_tech.py`, por lo que no duplica la preparacion de datos del mapa 6.
