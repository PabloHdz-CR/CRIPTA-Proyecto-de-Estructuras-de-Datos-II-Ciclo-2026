# Contrato del archivo de partida guardada: versión de formato 2

Cambio respecto de la versión 1 (`cripta/adaptadores/partidaBinaria.py`):

```text
SALA (por cada una de las 4 direcciones):
  hay_salida: booleano
  si hay_salida:
    destino:           entero
    cerrada:           booleano
    llave:             texto opcional
    cierre_automatico: entero opcional
    costo:             entero          # NUEVO en v2: costo EFECTIVO (≥ 1)
```

- `FORMATO_VERSION = 2`.
- Al cargar un archivo de versión 1 se lanza `VersionIncompatible("formato de
  archivo de partida", 2, 1)`, el comportamiento que ya existe para cualquier
  versión distinta. No hay migración silenciosa (principio V).
- Se guarda el costo efectivo, no el declarado. Al cargar, `Mundo.enlazar()`
  vuelve a validar las caras: si fueron guardadas por esta versión, siempre
  coinciden.
- `cargar_sala()` (carga de una sola sala por el índice) lee el costo, pero no
  enlaza: esa sala no se usa para buscar rutas.
- El cazador no necesita campos propios: su `rango` sale de la ficha, que se
  guarda por id y se resuelve contra la versión del catálogo del encabezado.
- El `partida.log` no cambia: las acciones siguen registrándose como hoy
  (`MOVER N`, `ESPERAR`, ...).
