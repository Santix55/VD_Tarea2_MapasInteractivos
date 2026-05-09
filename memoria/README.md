# Memoria de la Tarea 2

Esta carpeta contiene la base de la memoria del proyecto **"Donde vivir despues del Master de IA en la UPV"**.

## Archivos

- `memoria.md`: borrador principal del informe. Esta preparado para exportarse a PDF con Pandoc, Typora, VS Code o cualquier editor Markdown compatible.

## Como trabajarla

1. Completar en la portada el nombre y apellidos del autor.
2. Revisar los parrafos marcados como `TODO`.
3. Comprobar que las imagenes enlazadas existen en las carpetas `salidas/` de cada mapa.
4. Exportar a PDF con el nombre exigido en el enunciado: `TusApellidosTuNombre.pdf`.
5. Subir el PDF a `Informes_Tarea2` y entregar tambien scripts, datasets y presentacion 16:9.

## Exportacion sugerida

Si tienes Pandoc instalado:

```bash
pandoc memoria/memoria.md -o memoria/TusApellidosTuNombre.pdf --pdf-engine=xelatex --toc --number-sections --resource-path=memoria:.
```

Si no tienes Pandoc, abre `memoria.md` en un editor Markdown y exporta a PDF desde la interfaz grafica.

## Checklist de requisitos

- [x] Introduccion con problema, fuentes de datos, rango temporal y cartografia.
- [x] Preparacion de datos: limpieza, agregacion, uniones espaciales y tratamiento de CRS.
- [x] Visualizacion de datos: seis mapas, al menos cinco exigidos.
- [x] Al menos tres parametros distintos: vivienda, seguridad, accesibilidad, conectividad y clima.
- [x] Coropletas con al menos cinco intervalos.
- [x] Conclusiones orientadas a decision.
- [x] Apendice tecnico con librerias, ejecucion y metodos especiales.
- [ ] Sustituir los datos personales de la portada.
- [ ] Revisar estilo final antes de entregar para que suene personal y no mecanico.
