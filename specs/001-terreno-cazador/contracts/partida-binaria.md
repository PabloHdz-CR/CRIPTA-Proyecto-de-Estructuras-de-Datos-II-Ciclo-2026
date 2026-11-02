# Contrato del archivo de partida guardada: costo por salida

Cambio respecto del formato anterior (`FORMATO_VERSION = 1` en
`cripta/adaptadores/partidaBinaria.py`).

**Acuerdo (T048, 01/11/2026):** esta feature usa `FORMATO_VERSION = 2`, de
forma **provisional según el orden de merge a `main`**. Si otra feature que
cambia el formato llega antes a `main` y toma el 2, esta se ajusta al
siguiente número libre (o se suma a esa versión) al integrarse, y este
contrato se actualiza (plan.md, "Formato de guardado").

```text
SALA (por cada una de las 4 direcciones):
  hay_salida: booleano
  si hay_salida:
    destino:           entero
    cerrada:           booleano
    llave:             texto opcional
    cierre_automatico: entero opcional
    costo:             entero          # NUEVO en la versión 2: costo EFECTIVO (≥ 1)
```

- `FORMATO_VERSION = 2` (provisional, ver el acuerdo de arriba).
- Al cargar un archivo de una versión distinta (por ejemplo, la 1) se lanza
  `VersionIncompatible("formato de archivo de partida", 2, version_leida)`,
  el comportamiento que ya existe para cualquier versión distinta. No hay
  migración silenciosa (principio V).
- Se guarda el costo efectivo, no el declarado. Al cargar, `Mundo.enlazar()`
  vuelve a validar las caras: si fueron guardadas por esta versión, siempre
  coinciden.
- `cargar_sala()` (carga de una sola sala por el índice) lee el costo, pero no
  enlaza: esa sala no se usa para buscar rutas.
- El cazador no necesita campos propios: su `rango` sale de la ficha, que se
  guarda por id y se resuelve contra la versión del catálogo del encabezado.
- El `partida.log` no cambia: las acciones siguen registrándose como hoy
  (`MOVER N`, `ESPERAR`, ...).
