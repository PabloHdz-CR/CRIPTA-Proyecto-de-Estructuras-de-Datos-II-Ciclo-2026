# Contrato del archivo de partida guardada: conocimiento del jugador

Cambio respecto del formato de la feature 001 (`FORMATO_VERSION = 2` en
`cripta/adaptadores/partidaBinaria.py`).

**Número de versión**: esta feature usa `FORMATO_VERSION = 3`. La feature 004
(línea de tiempo) también cambiará el formato: la que llegue segunda a `main`
toma el 4 y actualiza su contrato (mismo acuerdo que T048 de 001).

```text
SALA:
  id, nombre, ...                    (sin cambios)
  conocimiento:      uentero32       # NUEVO en la versión 3: 0 desconocida, 1 avistada, 2 explorada
  por cada una de las 4 direcciones:
    hay_salida: booleano
    si hay_salida:
      destino:           entero
      cerrada:           booleano
      llave:             texto opcional
      cierre_automatico: entero opcional
      costo:             entero      # versión 2
      recordada:         uentero32   # NUEVO en la versión 3: 0 no observada, 1 abierta, 2 cerrada
```

- No se guarda el registro de conocidas ni el viaje en curso. Al cargar,
  `Partida.reconstruir_tras_cargar()` reconstruye el registro recorriendo el
  mundo una vez (research R4).
- `cargar_sala` (lectura de una sola sala por el índice) lee los mismos campos.
- Un archivo con una versión distinta de 3 (1 de la primera parte, 2 de la
  feature 001) lanza `VersionIncompatible("formato de archivo de partida", 3,
  version_leida)`: "Versión incompatible de formato de archivo de partida: se
  esperaba 3 y se encontró 2." La partida no se carga y no hay migración
  (FR-013, clarificación 4, principio V).
- Un valor fuera de rango en `conocimiento` o `recordada` es un archivo
  corrupto: se lanza `ErrorCripta` con la sala y la dirección.
- Guardar y cargar conserva los recuerdos desactualizados (una cara recordada
  abierta que está cerrada sigue así, FR-012).
