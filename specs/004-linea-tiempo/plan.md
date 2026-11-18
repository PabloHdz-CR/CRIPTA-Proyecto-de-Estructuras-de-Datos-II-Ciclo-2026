# Implementation Plan: Línea de tiempo

**Branch**: `004-linea-tiempo` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-linea-tiempo/spec.md`

## Summary

El jugador consulta el estado de cualquier instante pasado con «historia <t>»
o «historia #k» (tecla H en la ventana) y, sin interacción, con
`--replay partida.log --hasta t`. La consulta no modifica la partida, respeta
los pergaminos (lo revertido deja de existir) y se conserva al guardar.

Enfoque técnico (ver [research.md](research.md)):

- **Bloques de K acciones** con un **punto de control** al inicio de cada uno:
  los bytes del mismo escritor de `PartidaBinaria`, en memoria (incluye el azar
  y el conocimiento de la 002) (R1).
- **Reconstruir re-simulando hacia adelante** sobre una copia, con el mismo
  `Partida.aplicar_accion`, desde el punto de control del bloque (R2); el bucle
  de eventos de la copia acepta un **límite** para detenerse en "tiempo ≤ t"
  (R3). Mediciones previas: restaurar 13 ms + 1,2 ms por acción; con **K = 25**
  la consulta peor es de unos 24 ms (límite 50 ms).
- **Bloques en un arreglo por árbol** propio (O(log n) por posición, como D23):
  #k en O(log n), t por búsqueda binaria en O(log² n) (R4).
- La copia usa un **servicio de solo lectura** con los contenidos iniciales que
  la línea registró: sin red ni presupuesto (R5).
- **Pergamino**: quita la última acción (y el bloque si queda sin su primera
  acción) en O(1 + log n), y agrega un **ajuste** con el inventario y los
  pergaminos en el suelo para que FR-008 y la regla D50 se reproduzcan (R6).
- **Formato 4** con la línea completa; la versión 3 o anterior es incompatible
  (R7). `--hasta` y `--checkpoint-cada` en `main.py` (R8); tecla H (R9).

## Technical Context

**Language/Version**: Python 3.11+ (equipo local: 3.14.5 con `py`)

**Primary Dependencies**: `arcade` (solo la Vista), `requests` (solo el
adaptador HTTP). Estructuras propias: `ListaEnlazada`, `ListaDoble`,
`ArregloArbol` (nueva). Prohibidos dict, set, list de Python, heapq, bisect,
collections, pickle y copy.deepcopy como sustituto de la estructura.

**Storage**: partida binaria `FORMATO_VERSION` 4 (formato 3 + sección de la
línea); puntos de control como `bytes` en memoria; `partida.log` sin cambios.

**Testing**: `pruebas/prueba_*.py` con `py pruebas/ejecutar_pruebas.py`;
`prueba_reglas` sobre `cripta/`. Oráculo: resúmenes capturados en vivo en cada
decisión de la partida real, quitando los de acciones revertidas (R6).

**Target Platform**: escritorio, Windows 11 (equipo de la defensa).

**Project Type**: juego de escritorio MVC con puertos y adaptadores; modos
`--offline`, `--replay`, `--bench` y `--verificar`.

**Performance Goals**: consulta < 50 ms con 5000 acciones y el K por defecto
(FR-019, §6.1); memoria = cambios registrados + un punto de control cada K
acciones (FR-020); ubicar el bloque sublineal (FR-023); recorte del pergamino
proporcional a lo revertido (FR-023). El ciclo de eventos sigue < 20 ms: la
línea agrega O(1) por acción y 2,4 ms cada K acciones.

**Constraints**: determinismo (la re-simulación es exacta porque la partida es
determinista y el punto de control trae el estado del azar); la consulta nunca
toca la partida real ni la red (FR-011, FR-012); sin datos de criptas en el
código.

**Scale/Scope**: criptas de 6 a 300 salas; partidas de miles de acciones
(5000 en el bench); unos 57 KB por punto de control con 300 salas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento del plan | Estado |
|---|---|---|
| I. Estructuras propias | `ArregloArbol` propio para los bloques; entradas en `ListaDoble`; contenidos en `ListaEnlazada`; puntos de control como `bytes` (almacenamiento de bajo nivel, como el archivo). Sin dict, set, list, heapq, bisect, collections, pickle ni deepcopy | ✅ |
| II. Determinismo | La consulta re-simula con el mismo código y el azar restaurado; resultado independiente de K y de la hora (FR-026) | ✅ |
| III. MVC y puertos | `LineaTiempo` en el Modelo; puntos de control por el puerto `CopiadorEstado` (adaptador `PartidaBinaria`); el Controlador arma `ResumenInstante`; la Vista solo lo dibuja; `--replay` y `--bench` sin Vista | ✅ |
| IV. Sin datos concretos y presupuesto | La copia usa `ServicioSoloLectura`: sin red ni presupuesto; el bench elige la cripta por cantidad de salas | ✅ |
| V. Reversibilidad y persistencia | Copias completas solo como puntos de control, una cada K acciones (K por `--checkpoint-cada`, justificado con mediciones); fuera de ellos, acciones y ajustes; formato 4 y la versión 3 se reporta incompatible | ✅ |
| VI. Medir antes de afirmar | Mediciones previas en research; `benchLineaTiempo` con K = 10, 25, 50, sin puntos de control, adelante contra atrás, búsqueda del bloque y §5.6 | ✅ |
| VII. La spec precede al código | spec.md con aclaraciones confirmada (`07d142e`, `24f7602`); la referencia de SC-002 y de las pruebas independientes de US1 y US3 se corrigió en su propio commit (`67c1a83`, research R6) antes de `/speckit-tasks` | ✅ |
| Restricciones | Tipos, docstrings y `_` con propiedades; archivos en camelCase; errores con `ErrorCripta` | ✅ |

**Resultado del gate**: pasa. La corrección de la spec que pedía el diseño
(referencia de las pruebas = estado real de la historia que quedó, R6) quedó
confirmada en `67c1a83` antes de `/speckit-tasks`.

## Cambios por capa

### Modelo

- `estructuras/arregloArbol.py` (nuevo): `ArregloArbol`.
- `nucleo/lineaTiempo.py` (nuevo): `LineaTiempo`, `Bloque`, `EntradaAccion`,
  `AjustePergamino`.
- `nucleo/partida.py`: `linea`; `aplicar_accion(..., limite=None)` y
  `_procesar_eventos(limite=None)`; llamadas a la línea en `aplicar_accion`,
  `_usar_pergamino` y `_asegurar_contenido`; aplicar un `AjustePergamino` a la
  copia.
- `datos/servicioSoloLectura.py` (nuevo) y `datos/servicioDatos.py`:
  `resolver_fichas_sin_red`.
- `puertos/copiadorEstado.py` (nuevo).

### Adaptadores

- `partidaBinaria.py`: `a_bytes` / `desde_bytes`; `FORMATO_VERSION = 4` con la
  sección de la línea (contracts/partida-binaria.md).
- `registroArchivo.py`: el intérprete de acciones se expone para leer las
  acciones de la línea.

### Controlador

- `controladorJuego.py`: crea la línea con K y la conecta; verbo `historia`
  (interpretar t/#k, validar, consultar, `EstadoVista.historia`).
- `constructorResumen.py` (nuevo): `ResumenInstante` desde una Partida, con el
  mapa conocido de la 002; texto del resumen para la salida de texto.
- `modoReplay.py`: línea conectada y `--hasta`.
- `fabricaAplicacion.py`, `main.py`: `--hasta`, `--checkpoint-cada`.
- `bench/benchLineaTiempo.py` (nuevo), `bench/benchHistorial.py` (tabla con la
  carga nueva) y `benchTodo`.

### Vista

- `estadoVista.py`: `ResumenInstante` y `EstadoVista.historia`.
- `pantallaJuego.py`: tecla H, modo historia (entrada de texto), detener el
  viaje y cerrar el mapa antes de abrir.
- `hudJuego.py`: panel del resumen con `partirLineas` y desplazamiento.

## Project Structure

### Documentation (this feature)

```text
specs/004-linea-tiempo/
├── spec.md
├── plan.md              # este archivo
├── research.md          # Fase 0
├── data-model.md        # Fase 1
├── quickstart.md        # Fase 1
├── contracts/           # Fase 1
│   ├── cli.md
│   ├── partida-binaria.md
│   └── vista.md
├── checklists/requirements.md
└── tasks.md             # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
cripta/
├── modelo/
│   ├── estructuras/arregloArbol.py        # NUEVO
│   ├── nucleo/lineaTiempo.py              # NUEVO
│   ├── nucleo/partida.py                  # línea, límite, ajuste del pergamino
│   ├── datos/servicioSoloLectura.py       # NUEVO
│   ├── datos/servicioDatos.py             # resolver_fichas_sin_red
│   └── puertos/copiadorEstado.py          # NUEVO
├── adaptadores/
│   ├── partidaBinaria.py                  # a_bytes/desde_bytes, formato 4
│   └── registroArchivo.py                 # intérprete de acciones reutilizable
├── controlador/
│   ├── constructorResumen.py              # NUEVO
│   ├── controladorJuego.py                # verbo historia, línea conectada
│   ├── modoReplay.py                      # --hasta
│   ├── fabricaAplicacion.py               # K y --hasta
│   └── bench/
│       ├── benchLineaTiempo.py            # NUEVO
│       ├── benchHistorial.py              # carga nueva (§5.6)
│       └── benchTodo.py
└── vista/
    ├── estadoVista.py                     # ResumenInstante
    ├── pantallaJuego.py                   # tecla H, modo historia
    └── hudJuego.py                        # panel del resumen
main.py                                    # --hasta, --checkpoint-cada

pruebas/
├── apoyo_linea.py                 # NUEVO: partidas con oráculo de resúmenes en vivo
├── prueba_arreglo_arbol.py        # NUEVO
├── prueba_linea_consulta.py       # NUEVO (US1)
├── prueba_linea_pergamino.py      # NUEVO (US2)
├── prueba_replay_hasta.py         # NUEVO (US3)
├── prueba_persistencia_linea.py   # NUEVO (US4)
├── prueba_vista_historia.py       # NUEVO (US5)
├── prueba_rendimiento_linea.py    # NUEVO (US6)
└── ejecutar_pruebas.py
```

**Structure Decision**: un solo proyecto con la estructura MVC existente. La
línea vive en `modelo/nucleo/` junto a la Partida porque la alimenta la propia
Partida (acciones, pergaminos, contenidos) igual en vivo y en el replay; el
punto de control pasa por un puerto para que el Modelo no dependa del
adaptador binario.

## Riesgos y cómo se cubren

| Riesgo | Mitigación |
|---|---|
| La re-simulación difiere de la partida real (alguna fuente de no determinismo) | Oráculo de resúmenes en vivo en 1000 consultas (SC-002) y la comparación `--hasta` contra «historia» (SC-006) |
| Re-simular necesita datos que no están en memoria (después de cargar) | Contenidos iniciales registrados y guardados con la línea; fichas desde disco; si falta algo, error claro y nunca red (R5) |
| El ajuste del pergamino no reproduce D50 en casos raros (pergamino que soltó un enemigo dentro del tramo revertido) | El ajuste crea el objeto desde su ficha con el mismo id; prueba específica en `prueba_linea_pergamino` |
| El archivo de guardado crece (unos 11 MB con 5000 acciones y K = 25) | Se mide el tiempo de guardar y cargar en el bench; queda como límite documentado |
| La consulta peor se acerca a 50 ms en otra máquina | K por defecto 25 con margen de 2×; `--checkpoint-cada` permite bajarlo |
| La spec usa una referencia que no reproduce el pergamino | Corrección de la spec en su propio commit antes de `/speckit-tasks` (R6) |

## Complexity Tracking

No hay violaciones de la constitución que justificar.
