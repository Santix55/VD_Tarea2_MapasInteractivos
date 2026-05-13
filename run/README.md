# Lanzadores de mapas

Esta carpeta contiene ejecutables para abrir los HTML interactivos de cada mapa.

## Uso rapido

Desde la raiz del proyecto:

```bash
./run/mapa1_alquiler_provincias.sh
./run/mapa2_movilidad_y_transporte.sh
./run/mapa3_conectividad_teletrabajo.sh
./run/mapa4_confort_climatico.sh
./run/mapa5_indice_destino_tech.sh
```

Para abrir todos:

```bash
./run/abrir_todos_los_mapas.sh
```

Los abre en orden del mapa 1 al mapa 5, dejando una pausa entre pestanas para que el navegador respete mejor el orden. Puedes cambiar esa pausa asi:

```bash
OPEN_DELAY_SECONDS=1.5 ./run/abrir_todos_los_mapas.sh
```

Tambien puedes pasar opciones a todos los lanzadores:

```bash
./run/abrir_todos_los_mapas.sh --regen
```

## Regenerar salidas

Cada lanzador abre el HTML ya generado. Si el HTML no existe, lo genera con el script Python correspondiente.

Para forzar la regeneracion de un mapa y abrirlo:

```bash
./run/mapa3_conectividad_teletrabajo.sh --regen
```

Para regenerar todos sin abrir el navegador:

```bash
./run/regenerar_todos_los_mapas.sh
```

Si necesitas usar un Python concreto:

```bash
PYTHON_BIN=/ruta/a/python ./run/mapa3_conectividad_teletrabajo.sh --regen
```
