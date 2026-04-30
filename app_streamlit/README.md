# App Streamlit: indice final de destino tech

App complementaria del mapa 6. Permite recalcular el indice final con pesos ajustables, aplicar filtros, consultar un ranking dinamico, explorar el mapa Folium recalculado y revisar el perfil de cada provincia.

## Ejecutar

```bash
/home/s/miniconda3/envs/VD/bin/python -m streamlit run app_streamlit/app.py --server.address 127.0.0.1 --server.port 8501
```

La app reutiliza el script `6_indice_destino_tech/mapa6_indice_destino_tech.py`, por lo que no duplica la preparacion de datos del mapa 6.
