# Mapa 2: cobertura de internet de alta velocidad por provincia

Este mapa representa el porcentaje de hogares cubiertos por banda ancha fija con velocidad de descarga de al menos 1 Gbps en 2024.

## Metodología

- Fuente de cobertura: XLSX oficial `Cobertura Banda Ancha España 2021-2024` de SETELECO / Ministerio para la Transformación Digital y de la Función Pública.
- Hoja usada: `Provincia_%hogar`.
- Variable principal: `Cob. 1Gbps descarga condiciones máxima demanda (junio 2024)`.
- Unidad: porcentaje de hogares cubiertos.
- Cartografía: NUTS3 2024 de Eurostat/GISCO. En Baleares y Canarias la geometría NUTS3 se disuelve a provincia para que encaje con los datos provinciales.
- Clasificación de la coropleta: cuantiles con 5 intervalos.

## Ejecutar

```bash
/home/s/miniconda3/envs/VD/bin/python 2_cobertura_internet_alta_velocidad/mapa2_cobertura_1gbps_provincias.py
```

El script descarga los datos en `datos/` si no existen y genera:

- `salidas/mapa2_cobertura_1gbps_provincias.png`
- `salidas/mapa2_cobertura_1gbps_provincias.pdf`
- `salidas/mapa2_cobertura_1gbps_provincias_interactivo.html`
- `salidas/mapa2_cobertura_1gbps_provincias_datos.csv`
