# Mapa 4: conectividad para teletrabajo e IA

Este mapa funciona como filtro tecnologico para evaluar que provincias permiten vivir y trabajar en remoto con una infraestructura fija robusta.

## Metodologia

- Fuente de cobertura: XLSX oficial `Cobertura Banda Ancha Espana 2021-2024` de SETELECO / Ministerio para la Transformacion Digital y de la Funcion Publica.
- Hoja usada: `Provincia_%hogar`.
- Variable principal: porcentaje de hogares con cobertura de banda ancha fija de al menos 1 Gbps en junio de 2024.
- Variable secundaria: mejora en puntos porcentuales entre junio de 2023 y junio de 2024.
- Cartografia: NUTS3 2024 de Eurostat/GISCO, disuelta por codigo provincial para encajar Baleares y Canarias con el dato provincial.
- Clasificacion de la coropleta: 5 umbrales operativos de cobertura (`<80`, `80-85`, `85-90`, `90-95`, `>=95`), traducidos a categorias intuitivas: riesgo alto, riesgo medio, revisar, apto y muy apto.

## Lectura visual

- En el mapa estatico, el color funciona como semaforo tecnologico: verde/azul significa destino apto, amarillo significa revisar, y naranja/granate indica riesgo.
- Los paneles laterales no repiten simbolos sobre el mapa: muestran la brecha absoluta de hogares sin 1 Gbps y un grafico de cambio 2023 -> 2024.
- En el mapa interactivo, el `LayerControl` muestra las tres lecturas principales como botones de radio, por lo que solo se ve una a la vez: aptitud actual, evolucion o hogares sin 1 Gbps.
- Como recurso adicional de los apuntes, se usa `MarkerCluster` para agrupar provincias que conviene revisar (`<90%`). Estos marcadores se pueden activar o apagar sin cambiar la vista principal.
- La leyenda de color se actualiza automaticamente segun la vista seleccionada en los radio buttons. Abajo a la derecha hay un texto explicativo dinamico que tambien cambia segun la vista activa.
- Tambien hay una capa apagable de etiquetas para provincias en riesgo (`<85%`) y un control de coordenadas. Los tooltips y popups incluyen una recomendacion directa.

## Ejecutar

```bash
/home/s/miniconda3/envs/VD/bin/python 4_conectividad_teletrabajo/mapa4_conectividad_teletrabajo.py
```

El script descarga los datos en `datos/` si no existen y genera:

- `salidas/mapa4_conectividad_teletrabajo.png`
- `salidas/mapa4_conectividad_teletrabajo.pdf`
- `salidas/mapa4_conectividad_teletrabajo_interactivo.html`
- `salidas/mapa4_conectividad_teletrabajo_datos.csv`
