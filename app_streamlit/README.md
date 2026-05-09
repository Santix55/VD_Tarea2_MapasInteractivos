# Apps Streamlit del proyecto

## Mapa 2: seguridad y poblacion

El mapa 2 actual se presenta como HTML generado por Folium. La antigua app del mapa 2 queda fuera de la presentacion porque esa variable ha sido sustituida por seguridad relativa.

## Mapa 6: indice final de destino tech

App complementaria del mapa 6. Permite recalcular el indice final con pesos ajustables, aplicar filtros, consultar un ranking dinamico, explorar el mapa Folium recalculado y revisar el perfil de cada provincia. El componente de seguridad forma parte de la formula final.


```bash
/home/s/miniconda3/envs/VD/bin/python -m streamlit run app_streamlit/app.py --server.address 127.0.0.1 --server.port 8501
```

La app reutiliza el script `6_indice_destino_tech/mapa6_indice_destino_tech.py`, por lo que no duplica la preparacion de datos del mapa 6.
