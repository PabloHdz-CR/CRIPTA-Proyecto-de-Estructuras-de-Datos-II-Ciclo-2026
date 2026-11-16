# Implementation Plan: Niebla de guerra e «ir a»

**Branch**: `002-niebla-guerra` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-niebla-guerra/spec.md`

## Summary

El jugador deja de ver la cripta entera: cada sala está explorada, avistada o
desconocida para él, y el mapa recuerda cada puerta como la vio la última vez.
La antorcha explora las vecinas al entrar. Con **M** se abre el mapa conocido
y desde ahí se ordena «ir a», un viaje paso a paso por la ruta más barata que
el jugador conoce, que se detiene por llegada, enemigos, daño, falta de ruta,
pergamino o interrupción.

Enfoque técnico (ver [research.md](research.md)):

- **Conocimiento como campos** de `Sala` (`conocimiento`) y `Salida`
  (`recordada`): consulta O(1) por referencia, sin dict ni set y sin buscar
  salas por id (R1).
- **Todo cambio pasa por el Mutador**, y solo si cambia: el pergamino lo
  revierte con el Diario existente y la feature 004 lo puede observar; una
  entrada con antorcha registra solo lo revelado (R2).
- **Observación de puertas** al entrar y al cambiar una puerta con el jugador
  presente, por un único `Partida.cambiar_puerta` (R3).
- **Registro de conocidas en orden de descubrimiento**, agregar y quitar al
  final en O(1), ordenado por id con la mezcla propia solo al abrir el panel.
  Se cambia la orientación de inserción ordenada porque haría que explorar
  dependiera del tamaño del mapa (FR-033) (R4).
- **Ruta**: Dijkstra hacia adelante con parada al fijar el destino, etiqueta
  lexicográfica (costo, primer paso) para el desempate de FR-020,
  `HeapMinimo` propio y sellos en campos propios de la sala. **Separado** del
  mapa del cazador. Mediciones previas: peor paso 0,65 ms en la cripta de
  referencia con todas las puertas abiertas (límite 5 ms) y 3,99 ms en la malla
  de 1024 salas, contra 7,47 ms de la alternativa hacia atrás (R5).
- **Viaje** dirigido por el Controlador, un paso por vuelta del bucle; cada
  paso es un `Mover` ordinario con su propio intervalo del Diario (R6).
- Comentario `# IR_A <id>` en `partida.log`, ignorado al leer (R7);
  `FORMATO_VERSION` 3 (R9); teclas M, I y H reservada (R8).

## Technical Context

**Language/Version**: Python 3.11+ (equipo local: 3.14.5 con `py`; las
mediciones de 001 se hicieron con 3.12.10)

**Primary Dependencies**: `arcade` (solo la Vista), `requests` (solo el
adaptador HTTP). Estructuras propias: `HeapMinimo`, `ListaEnlazada`,
`ListaDoble`, `ordenamiento.mezcla`. Prohibidos dict y set como índice, list
de Python, heapq, bisect, collections y bibliotecas de grafos.

**Storage**: partida binaria (`FORMATO_VERSION` 3: conocimiento por sala y
recuerdo por salida); `partida.log` de solo anexado con líneas de comentario
`#`; sin solicitudes de red nuevas.

**Testing**: scripts `pruebas/prueba_*.py` corridos por
`py pruebas/ejecutar_pruebas.py`, uno por proceso; `prueba_reglas` revisa el
AST contra la constitución. Oráculo de rutas propio en `pruebas/`.

**Target Platform**: escritorio, equipo local de la defensa (Windows 11).

**Project Type**: juego de escritorio MVC con puertos y adaptadores, y modos
`--offline`, `--replay`, `--bench` y `--verificar`.

**Performance Goals**: cada paso de «ir a» < 5 ms con el mapa conocido
completo de la cripta de referencia (FR-031, §6.1); consultas de estado de
sala y de cara recordada que no crecen con el mapa conocido (FR-032);
explorar y registrar/invertir proporcional a lo revelado (FR-033). El ciclo
de eventos sigue < 20 ms (001).

**Constraints**: determinismo (orden total en el heap, desempate numérico por
id y N, S, E, O; sin hora del sistema); todo lo que ve la Vista y usa «ir a»
sale del conocimiento; sin copias del estado para deshacer (principio V); sin
ids de criptas en el código.

**Scale/Scope**: criptas de 6 a 300 salas en `datos_offline/` (la de
referencia tiene 300), hasta 4 salidas por sala; estrés con la malla de 1024
salas de 001.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento del plan | Estado |
|---|---|---|
| I. Estructuras propias | Conocimiento en campos de objetos; registro de conocidas en `ListaDoble`; ruta con `HeapMinimo` propio y sellos; orden del panel con `ordenamiento.mezcla`; oráculo de pruebas con estructuras propias. Sin dict, set, list, heapq, bisect, collections ni bibliotecas de grafos | ✅ |
| II. Determinismo | Heap con orden total (costo, primer paso, id); desempate por id numérico y N, S, E, O; la ruta depende solo del conocimiento; sin azar nuevo, así las secuencias del Random propio no cambian | ✅ |
| III. MVC y puertos | Conocimiento, buscador, validación y pasos en el Modelo; el Controlador dirige el viaje y arma los DTOs; la Vista recibe `MapaConocidoVisible` y `ViajeVisible` y produce comandos; el comentario del log pasa por el puerto `RegistroAcciones`. `--replay`, `--bench` y `--verificar` no instancian la Vista | ✅ |
| IV. Sin datos concretos y presupuesto | La cripta de referencia del bench se elige en ejecución por cantidad de salas; no hay solicitudes HTTP nuevas | ✅ |
| V. Reversibilidad y persistencia | Cambios de conocimiento por el Mutador, registrando solo lo que cambia (sin copias); `FORMATO_VERSION` 3 y un archivo anterior se reporta incompatible sin migrar (FR-013); log de solo anexado con comentario, y `--replay` lo ignora | ✅ |
| VI. Medir antes de afirmar | Mediciones previas en research R1, R4 y R5; `benchNiebla` (R11) da la evidencia definitiva con la alternativa descartada de cada decisión. No se reutiliza la ruta entre pasos (se recalcula), así que no hay reutilización que demostrar | ✅ |
| VII. La spec precede al código | spec.md con aclaraciones confirmada en git (`7814ba6`, `bb99dee`); el plan no exige enmiendas de la spec | ✅ |
| Restricciones | Anotaciones de tipo, docstrings y `_` con propiedades; archivos en camelCase (`conocimiento.py`, `buscadorRuta.py`, `viajeIrA.py`, `benchNiebla.py`); errores con la jerarquía `ErrorCripta` | ✅ |
| Flujo y hecho | Cada FR tiene una prueba que lo cita (quickstart.md); los 30 escenarios mapeados (SC-001); DECISIONES.md con el siguiente número D libre (hoy D81) después de `git pull` de `main`; PROMPTS_LLM.md registrado | ✅ |

**Resultado del gate (antes y después del diseño)**: pasa, sin violaciones.

## Cambios por capa

### Modelo

- `mundo/conocimiento.py` (nuevo): constantes, `RegistroConocidas` y
  `ConocimientoJugador` (iniciar, entrar con o sin antorcha, observar cara).
- `mundo/sala.py`: `conocimiento` y los campos de búsqueda de «ir a».
- `mundo/salida.py`: `recordada`.
- `mundo/mundo.py`: `conocidas` y `_sello_ruta` con `nuevo_sello_ruta()`.
- `mundo/buscadorRuta.py` (nuevo): `EntradaRuta` y `BuscadorRuta.primer_paso`.
- `nucleo/mutador.py` y `nucleo/diario.py`: tipo `CONOCIDA_AGREGAR` y su
  inverso.
- `nucleo/partida.py`: crea `ConocimientoJugador` en `iniciar` y en
  `reconstruir_tras_cargar`; `_mover_jugador` llama a `entrar` y anota
  `entro_con_enemigos` antes de activar; `cambiar_puerta` (usado por
  `_abrir_puerta`); `danar` anota `dano_recibido` si es el jugador;
  `validar_ir_a` y `primer_paso_ir_a`.
- `reloj/eventos.py`: `EventoCierrePuerta` usa `partida.cambiar_puerta`.
- `nucleo/resultadoAccion.py`: `entro_con_enemigos`, `dano_recibido`.
- `nucleo/viajeIrA.py` (nuevo): estado del viaje y motivos.
- `puertos/registroAcciones.py`: `registrar_comentario`.

### Adaptadores

- `partidaBinaria.py`: `FORMATO_VERSION = 3`, escribe y lee `conocimiento`
  y `recordada` (también en `cargar_sala`).
- `registroArchivo.py`: `registrar_comentario` y `leer()` que salta `#`.

### Controlador

- `controladorJuego.py`: verbos `alternar_mapa`, `ir_a`, `interrumpir`;
  viaje en curso con un paso por `procesar(None)`; cualquier otro comando
  detiene el viaje antes de procesarse; comentario en el log; motivo con
  `mostrar_mensajes`.
- `controladorMenu.py`: entrega `None` a la partida cuando hay un viaje en
  curso.
- `constructorEstadoVista.py`: `MapaConocidoVisible` (solo con el panel
  abierto), `ViajeVisible`, y `SalidaVisible.estado` desde `recordada`.
- `bench/benchNiebla.py` (nuevo), `bench/alternativasNiebla.py` (nuevo, solo
  para medir: búsqueda hacia atrás, búsqueda lineal, inserción ordenada) y
  registro en `benchTodo`.

### Vista

- `estadoVista.py`: DTOs nuevos (data-model.md).
- `pantallaJuego.py`: teclas M, I, flechas/RePág/AvPág/Enter con el panel
  abierto (contracts/vista.md).
- `hudJuego.py`: panel del mapa con `partirLineas` y desplazamiento; línea de
  viaje en curso.
- README: tabla de teclas (M, I, H reservada) y nota del formato 3.

## Project Structure

### Documentation (this feature)

```text
specs/002-niebla-guerra/
├── spec.md
├── plan.md              # este archivo
├── research.md          # Fase 0
├── data-model.md        # Fase 1
├── quickstart.md        # Fase 1
├── contracts/           # Fase 1
│   ├── partida-binaria.md
│   ├── registro.md
│   └── vista.md
├── checklists/requirements.md
└── tasks.md             # Fase 2 (/speckit-tasks; no lo crea este comando)
```

### Source Code (repository root)

```text
cripta/
├── modelo/
│   ├── mundo/
│   │   ├── conocimiento.py         # NUEVO: constantes, RegistroConocidas, ConocimientoJugador
│   │   ├── buscadorRuta.py         # NUEVO: Dijkstra hacia adelante sobre el conocimiento
│   │   ├── sala.py                 # conocimiento + campos de búsqueda de «ir a»
│   │   ├── salida.py               # recordada
│   │   └── mundo.py                # conocidas, sello de ruta
│   ├── nucleo/
│   │   ├── viajeIrA.py             # NUEVO: estado del viaje y motivos
│   │   ├── partida.py              # conocimiento, cambiar_puerta, anotaciones, validar_ir_a
│   │   ├── mutador.py              # CONOCIDA_AGREGAR
│   │   ├── diario.py               # inverso de CONOCIDA_AGREGAR
│   │   └── resultadoAccion.py      # entro_con_enemigos, dano_recibido
│   ├── reloj/eventos.py            # EventoCierrePuerta usa cambiar_puerta
│   └── puertos/registroAcciones.py # registrar_comentario
├── adaptadores/
│   ├── partidaBinaria.py           # FORMATO_VERSION 3
│   └── registroArchivo.py          # comentario y lectura que lo salta
├── controlador/
│   ├── controladorJuego.py         # M, ir_a, interrumpir, viaje por vuelta
│   ├── controladorMenu.py          # None a la partida con viaje en curso
│   ├── constructorEstadoVista.py   # MapaConocidoVisible, ViajeVisible
│   └── bench/
│       ├── alternativasNiebla.py   # NUEVO (solo para medir)
│       ├── benchNiebla.py          # NUEVO
│       └── benchTodo.py            # registra benchNiebla
└── vista/
    ├── estadoVista.py              # DTOs nuevos
    ├── pantallaJuego.py            # M, I, panel con cursor y Enter
    └── hudJuego.py                 # panel del mapa y línea de viaje

pruebas/
├── apoyo_niebla.py                 # NUEVO: criptas sintéticas, huella del conocimiento
├── oraculo_ir_a.py                 # NUEVO: Bellman-Ford hacia adelante con el desempate de FR-020
├── prueba_niebla_conocimiento.py   # NUEVO
├── prueba_niebla_puertas.py        # NUEVO
├── prueba_niebla_antorcha.py       # NUEVO
├── prueba_ir_a.py                  # NUEVO
├── prueba_ir_a_equivalencia.py     # NUEVO
├── prueba_niebla_retroceso.py      # NUEVO
├── prueba_persistencia_niebla.py   # NUEVO
├── prueba_replay_ir_a.py           # NUEVO
├── prueba_vista_mapa.py            # NUEVO
├── prueba_rendimiento_ir_a.py      # NUEVO
├── prueba_conteo_niebla.py         # NUEVO
├── generar_guardado_formato_anterior.py  # genera también un guardado de la versión 2
└── ejecutar_pruebas.py             # registra las nuevas
```

**Structure Decision**: un solo proyecto con la estructura MVC existente. El
conocimiento y el buscador viven en `modelo/mundo/` porque dependen solo de
salas, salidas y puertas, igual que el mapa de distancias de 001; el viaje
vive en `modelo/nucleo/` junto a la Partida, porque sus motivos dependen de
actores, combate y fin de partida.

## Riesgos y cómo se cubren

| Riesgo | Mitigación |
|---|---|
| Algún camino escribe `cerrada` sin observar | Hoy hay dos escrituras en el Modelo; ambas pasan por `cambiar_puerta`. `prueba_niebla_puertas` cubre abrir y el cierre automático con el jugador presente y ausente; una prueba busca en el AST otras escrituras de `cerrada` fuera de `cambiar_puerta`, el Diario y la carga |
| Una lectura de la vista o de «ir a» se salta el conocimiento | SC-002: DTOs revisados contra salas con nombres marca; buscador instrumentado en la prueba (research R10) |
| El Diario revierte el registro de conocidas fuera de orden | El inverso verifica que la última sea la sala esperada y lanza error si no; la prueba de 1000 secuencias lo ejercita (SC-003) |
| Pruebas existentes que arman `Sala`, `Salida`, `ResultadoAccion` o DTOs a mano | Campos nuevos con valores por omisión |
| Guardados existentes de la versión 2 | Se reportan incompatibles (FR-013); el README lo dice |
| 002 y 004 toman el mismo `FORMATO_VERSION` | Acuerdo en contracts/partida-binaria.md: la segunda en llegar a `main` toma el 4 |
| La letra de 004 choca con las de esta feature | M e I asignadas aquí; H reservada para 004 y anotada en el README |
| Viaje en curso al guardar o cargar | Cualquier comando detiene el viaje antes de procesarse; el viaje no se guarda |
| La prueba de 5 ms es sensible a la carga de la máquina | Mínimo de varias repeticiones, como `Medidor`, y la cifra medida en el mensaje al fallar |
| `ControladorMenu` descarta los `None` | Se cambia para entregarlos a la partida solo con viaje en curso; lo cubre `prueba_vista_mapa` con una vista registradora |

## Complexity Tracking

No hay violaciones de la constitución que justificar.
