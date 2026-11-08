# Implementation Plan: Resolubilidad

**Branch**: `003-resolubilidad` | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-resolubilidad/spec.md`

## Summary

Antes de iniciar una partida nueva, el programa decide si la cripta puede
ganarse con su esqueleto y con la ubicación de sus llaves (consulta nueva
`GET /criptas/<id>/llaves`). Si se puede, entrega el orden de obtención
lexicográficamente menor. Si no, explica por qué: motivo, llaves no
obtenibles con sus ubicaciones, frontera bloqueada y un ciclo por grupo de
llaves que se encierran entre sí. Sin `--forzar`, una cripta no resoluble no
inicia. `--verificar ID` hace solo la verificación por terminal, con códigos
de salida 0, 1 y 2.

Enfoque técnico (ver [research.md](research.md)):

- **Grafo propio**: la verificación arma un grafo propio, enlazado por
  ordenamiento y fusión, sin dict (R1).
- **Fase 1**: un solo recorrido en anchura con puertas pendientes por llave y
  un `HeapMinimo` de llaves disponibles. Da el orden menor, el veredicto y la
  frontera. Cada salida se examina como máximo dos veces (R2, R3).
- **Fase 2** (solo si no es resoluble): una pasada de Tarjan iterativo sobre
  las salas no alcanzadas y un relleno por prioridad, que dan los grupos y la
  dependencia mínima de cada llave para construir los ciclos de FR-015 (R4).
- **Costo**: O((S + E + L) log(S + E + L)) en total, independiente de cuántas
  llaves se obtienen. El bench lo compara con la alternativa ingenua (R11).

## Technical Context

**Language/Version**: Python 3.11 o superior.

**Primary Dependencies**: `arcade` (solo la Vista), `requests` (solo el
adaptador HTTP). Estructuras propias: `ListaEnlazada`, `HeapMinimo`, `Pila`,
`Cola` y `ordenamiento.mezcla`. Sin dict, set ni list de Python como índice,
sin heapq, bisect, collections ni bibliotecas de grafos.

**Storage**: caché JSON de ubicación de llaves por versión de cripta en la
carpeta de fichas (`llaves/<id>.json`). El encabezado de `partida.log` gana un
quinto campo opcional, compatible hacia atrás. El archivo binario de partida
**no cambia**.

**Testing**: scripts `pruebas/prueba_*.py` ejecutados por
`py pruebas/ejecutar_pruebas.py`, uno por proceso, más `prueba_reglas`. Las
criptas sintéticas van en `pruebas/apoyo_resolubilidad.py` y en el paquete
`pruebas/datos/resolubilidad/`.

**Target Platform**: escritorio, en el equipo local de la defensa (Windows 11).

**Project Type**: juego de escritorio MVC con puertos y adaptadores; modos
`--offline`, `--replay`, `--bench` y ahora `--verificar`.

**Performance Goals**: verificación < 200 ms en la cripta más grande de
`datos_offline/` sin red ni renderizado (FR-032, medido en **tiempo**; SIN
DATOS si no hay `llaves.json`). SC-003 se mide en **salidas examinadas**, un
contador determinista, no en tiempo: el cociente al duplicar las llaves es
≤ 2,5 en la verificación y ≥ 3,5 en la alternativa ingenua. El tiempo de las
cadenas se reporta solo como información.

**Constraints**: determinismo sin azar, con orden canónico por id
independiente del orden de llegada (FR-010). Ninguna cripta concreta en el
código (FR-036). Una sola solicitud nueva por versión, dentro del presupuesto
(FR-026, FR-027).

**Scale/Scope**: criptas de decenas a pocos cientos de salas, con hasta 4
salidas por sala y decenas de llaves. Estrés sintético con 400 llaves
encadenadas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento del plan | Estado |
|---|---|---|
| I. Estructuras propias | Grafo con nodos y referencias directas; ids resueltos ordenando con `mezcla` y fusionando, nunca con dict ni búsqueda cuadrática. `HeapMinimo` de disponibles, `Cola` del recorrido y `Pila` de Tarjan propios. Sin heapq, sorted, set ni bibliotecas de grafos | ✅ |
| II. Determinismo | Sin azar. Orden canónico (salas por id, llaves por id como texto, salidas N, S, E, O); desempates fijados por la spec (FR-009, FR-015). Ni hora ni orden de llegada HTTP | ✅ |
| III. MVC y puertos | La verificación vive en el Modelo y recibe datos por `ServicioDatos`. La consulta es un método nuevo del puerto `FuenteDatos` con dos adaptadores. El Controlador formatea y decide el inicio; la Vista recibe un DTO inmutable y V es estado local de la Vista. `--verificar`, `--replay` y `--bench` no instancian la Vista | ✅ |
| IV. Sin datos concretos y presupuesto | Cripta de referencia elegida en ejecución por cantidad de salas. La consulta de llaves pasa por `_pedir` (cuenta intentos y reintentos), con caché por versión: una por versión | ✅ |
| V. Reversibilidad y persistencia | El grafo es temporal y no es estado de partida. Caché de llaves con versión de cripta (lo de la Parte I no coincide y se vuelve a pedir). El log gana un campo opcional sin romper los anteriores; el formato binario no cambia | ✅ |
| VI. Medir antes de afirmar | Ninguna cifra afirmada: `benchResolubilidad` mide la referencia, las cadenas y la alternativa ingenua, y cuenta salidas examinadas; las cifras van a DECISIONES.md | ✅ |
| VII. La spec precede al código | spec.md confirmada (`33a4db8`, corrección `aea2b74`). FR-034 enmendado en un commit propio (`254747e`) antes de este ajuste del plan: frontera del recorrido de la fase 1, dependencias y ciclos de una sola pasada que continúa más allá de la frontera (research.md R4) | ✅ |
| Restricciones | Tipos y docstrings en lo nuevo; `_` con propiedades. Archivos en camelCase (`grafoVerificacion.py`, `verificadorResolubilidad.py`, `textoResolubilidad.py`, `modoVerificar.py`, `benchResolubilidad.py`); errores con `DatosInvalidos`/`ErrorCripta` | ✅ |
| Flujo y hecho | Cada FR con una prueba que lo cita; los 28 escenarios con marca H*.E*; DECISIONES.md con los siguientes D libres después de `git pull` de `main`; README (FR-037) y PROMPTS_LLM.md al día | ✅ |

**Resultado del gate (antes y después del diseño)**: pasa, sin notas
pendientes.

## Detalle de la fase 1 que fija el escenario 12

La marca `entra_por_puerta_salida` se pone al **examinar** una salida cerrada
que requiere llave_salida, con llave_salida ya obtenida y destino
sala_salida, aunque sala_salida ya estuviera alcanzada por otro camino. Se
examina en los dos momentos del recorrido: al sacar la sala de la cola y al
reexaminar las puertas pendientes cuando se obtiene llave_salida. Así,
H1.E12 (dos caminos, uno por la salida de llave_salida) da resoluble, y una
cripta que solo llega a sala_salida por caminos abiertos da no resoluble con
el motivo (b) (research.md R3).

## Flujo de inicio de partida

```text
menú "jugar" (nueva) ──► ControladorJuego.preparar_nueva(id)
                          ├─ servicio.iniciar_cripta(id)      (datos + esqueleto, ya existía)
                          └─ verificar_cripta(servicio)       (llaves + grafo + fases 1 y 2)
   RESOLUBLE ─────────────► iniciar_preparada(semilla, forzada=False) + aviso en bitácora
   NO_RESOLUBLE / NO_VERIFICADA
      sin --forzar ───────► vista.mostrar_resolubilidad(puede_continuar=False); "volver" → menú
      con --forzar ───────► vista.mostrar_resolubilidad(puede_continuar=True)
                             "aceptar_resolubilidad" → iniciar_preparada(semilla, forzada=True)
continuar guardada, --replay, replay en ventana ──► sin verificación (FR-021)
```

Si la partida no inicia, la sesión de red se reinicia al volver al menú, igual
que al salir de una partida (D65).

**Camino sin verificación**: `ControladorJuego.iniciar_nueva(id_cripta,
semilla)` se conserva con el mismo nombre y la misma firma y no verifica.
`iniciar_preparada` lo usa por dentro, y también las pruebas que arman una
partida directo. El bench y los dos replays crean la `Partida` sin pasar por
`ControladorJuego` y no cambian.

**Tecla V sin reporte**: en una partida cargada (`EstadoVista.resolubilidad`
es None), V manda el verbo de sesión `ver_resolubilidad` y la bitácora
muestra "Esta partida no tiene reporte de resolubilidad." Esa línea no va al
log ni gasta reloj. En el replay, V no hace nada (research.md R8).

## Paquetes de prueba y datos sin conexión

Detalle en research.md R12. En resumen:

- `pruebas/datos/terreno_cazador`: **no** se le agrega `llaves.json`. Ninguna
  de sus tres criptas es resoluble con FR-001, y cambiar su esqueleto
  alteraría las pruebas de la 001. `prueba_datos_costo` (inicia por el menú)
  arma el menú con `forzar=True` y manda `aceptar_resolubilidad`. Sin
  `llaves.json` el resultado es NO_VERIFICADA, que con `--forzar` también
  deja iniciar (FR-031). El error de caras distintas sigue apareciendo, al
  convertir el esqueleto o al iniciar la partida forzada, según dónde salte
  hoy. `prueba_persistencia_cazador` no pasa por la verificación.
- Paquetes temporales de `prueba_controlador` y `prueba_replay_menu`: se les
  agrega `llaves.json` y siguen el camino normal (su puerta cerrada lleva a la
  sala de salida). Si alguno no resultara resoluble, se usa `forzar=True`.
- `pruebas/datos/resolubilidad/` (nuevo): criptas sintéticas para los
  escenarios.
- **Tarea del equipo, fuera del agente**: regenerar `datos_offline/` con
  `python guardar_respuestas.py` (requiere red y el endpoint `/llaves`
  publicado). Hasta entonces, el juego sin conexión exige `--forzar`, la
  referencia del bench dice SIN DATOS y H5.E1 **salta** con el mensaje "SIN DATOS"
  (tasks.md T045); pasa a obligatorio en T061, cuando `datos_offline/` tenga llaves.

## Escenarios de aceptación hacia pruebas

Cada prueba marca el escenario con un comentario `# H<historia>.E<n>` y los
FR que ejerce (SC-001). Los 4 obligatorios del Apéndice B están marcados con
"(B)".

| Marca | Escenario | Prueba |
|---|---|---|
| H1.E1 (B) | llave_salida detrás de su propia puerta: ciclo | `prueba_resolubilidad_reporte` |
| H1.E2 (B) | llave suelta por un errante: sala inicial del enemigo | `prueba_resolubilidad_reglas` |
| H1.E3 (B) | varios órdenes: el mismo y el menor por id | `prueba_resolubilidad_reglas` |
| H1.E4 | cadena A, B, llave_salida | `prueba_resolubilidad_reglas` |
| H1.E5 | llave que no hace falta también va en el orden | `prueba_resolubilidad_reglas` |
| H1.E6 | puerta de frontera con llave sin ubicación | `prueba_resolubilidad_reporte` |
| H1.E7 | llave de enemigo en región inalcanzable | `prueba_resolubilidad_reporte` |
| H1.E8 | ciclo de dos llaves | `prueba_resolubilidad_reporte` |
| H1.E9 | cierre automático no bloquea | `prueba_resolubilidad_reglas` |
| H1.E10 | caras de puerta con estados distintos | `prueba_resolubilidad_reglas` |
| H1.E11 | no resoluble sin ciclo | `prueba_resolubilidad_reporte` |
| H1.E12 | dos caminos a sala_salida, uno por su puerta: resoluble | `prueba_resolubilidad_reglas` |
| H2.E1 (B) | no resoluble sin `--forzar`: no inicia | `prueba_resolubilidad_inicio` |
| H2.E2 | no resoluble con `--forzar`: inicia tras la pantalla | `prueba_resolubilidad_inicio` |
| H2.E3 | resoluble: aviso, V abre y cierra el reporte | `prueba_resolubilidad_inicio` y `prueba_vista_resolubilidad` |
| H2.E4 | `--replay` de una partida forzada | `prueba_resolubilidad_inicio` |
| H3.E1 | `--verificar` sin vista ni partida | `prueba_verificar` |
| H3.E2 | códigos de salida 0, 1 y 2 | `prueba_verificar` |
| H3.E3 | `--verificar --offline` igual que en línea | `prueba_verificar` |
| H4.E1 | consulta de llaves cuenta en el presupuesto | `prueba_datos_llaves` |
| H4.E2 | caché de la misma versión: sin solicitud | `prueba_datos_llaves` |
| H4.E3 | versión anterior: se pide de nuevo | `prueba_datos_llaves` |
| H4.E4 | en línea y sin conexión, iguales | `prueba_datos_llaves` |
| H4.E5 | respuesta mal formada: error explícito | `prueba_datos_llaves` |
| H4.E6 | presupuesto insuficiente: no se pudo verificar | `prueba_datos_llaves` |
| H5.E1 | referencia < 200 ms (salta con SIN DATOS hasta T061) | `prueba_rendimiento_resolubilidad` |
| H5.E2 | cadenas 100, 200, 400: mismo reporte que la ingenua | `prueba_rendimiento_resolubilidad` |
| H5.E3 | cocientes de salidas examinadas ≤ 2,5 y ≥ 3,5 | `prueba_rendimiento_resolubilidad` |

Además: `prueba_resolubilidad_oraculo` (research.md R13) compara el resultado
estructurado (tuplas, no el texto) con un oráculo en unas 200 criptas pequeñas
al azar con semilla fija.
Los casos borde de la spec van en `prueba_resolubilidad_reglas` y
`prueba_resolubilidad_reporte`, marcados como `# borde: <nombre>`.

## Posibles choques con las features de Pablo

| Punto | Riesgo | Cómo se evita |
|---|---|---|
| Último campo de `EstadoVista` | Las dos ramas agregan un campo al final con valor por omisión y chocan en el merge, o cambian el orden de los argumentos | `resolubilidad` va con nombre y valor None por omisión, y todo constructor usa argumentos con nombre. Al hacer merge se conservan los dos campos y ninguno queda por posición |
| Encabezado del log | Si otra feature también agrega un campo opcional por posición, "5 campos" significa cosas distintas | Las marcas son **palabras** (`FORZADA` con `NO_RESOLUBLE` o `NO_VERIFICADA`), no posiciones. El lector acepta, después de los 4 fijos, palabras conocidas en cualquier orden y rechaza las desconocidas. Si Pablo agrega otra, se suma a la lista de palabras conocidas (contracts/registro.md) |
| Teclas | V puede chocar con las de niebla, ir a o línea de tiempo | Antes de implementar la tecla se confirma con Pablo qué letras usa. `prueba_vista_resolubilidad` falla si dos acciones de la partida comparten tecla |
| Numeración de DECISIONES.md y PROMPTS_LLM.md | Las dos ramas toman el mismo D siguiente (D75...) o el mismo número de entrada | Las secciones se numeran al cerrar, después de `git pull` de `main`. Si al hacer merge se repite un número, se renumera la rama que entra segunda |
| `VistaJuego`, `fabricaAplicacion.py`, `benchTodo.py`, `ejecutar_pruebas.py`, README | Las dos ramas agregan métodos, banderas, benches, pruebas y filas en los mismos lugares | Son agregados al final de cada lista o tabla; se resuelven conservando ambos |
| `FORMATO_VERSION` del guardado | — | Esta feature no lo cambia |

## Project Structure

### Documentation (this feature)

```text
specs/003-resolubilidad/
├── spec.md
├── plan.md              # este archivo
├── research.md          # Fase 0
├── data-model.md        # Fase 1
├── quickstart.md        # Fase 1
├── contracts/           # Fase 1
│   ├── datos-llaves.md
│   ├── linea-de-comandos.md
│   ├── reporte.md
│   ├── vista.md
│   └── registro.md
├── checklists/requirements.md
└── tasks.md             # Fase 2 (/speckit-tasks; no lo crea este comando)
```

### Source Code (repository root)

```text
cripta/
├── modelo/
│   ├── puertos/
│   │   ├── dto.py                    # + UbicacionLlaveDTO
│   │   ├── fuenteDatos.py            # + llaves(id_cripta)
│   │   ├── almacenLocal.py           # + guardar_llaves / cargar_llaves
│   │   └── registroAcciones.py       # EncabezadoPartida + forzada
│   ├── datos/
│   │   └── servicioDatos.py          # + ubicacion_llaves() con caché por versión
│   └── resolubilidad/                # NUEVO
│       ├── grafoVerificacion.py      # NodoSala, AristaSalida, NodoLlave, construcción por fusión (R1)
│       ├── verificadorResolubilidad.py  # fase 1 (R2, R3) y fase 2 (R4), conteo de salidas
│       ├── resultadoResolubilidad.py # ResultadoResolubilidad y sus partes (data-model §3)
│       └── verificacion.py           # verificar_cripta(servicio): datos → resultado, errores → NO_VERIFICADA (R6)
├── adaptadores/
│   ├── convertidorJson.py            # + llaves_desde_json (validación FR-030)
│   ├── clienteHttp.py                # + GET /criptas/<id>/llaves
│   ├── fuenteOffline.py              # + criptas/<id>/llaves.json
│   ├── almacenLocalDisco.py          # + llaves/<id>.json con versión
│   └── registroArchivo.py            # encabezado de 4 o 5 campos
├── controlador/
│   ├── fabricaAplicacion.py          # + --verificar ID, --forzar
│   ├── modoVerificar.py              # NUEVO: imprime y devuelve 0, 1 o 2 (R10)
│   ├── textoResolubilidad.py         # NUEVO: formato canónico (contracts/reporte.md)
│   ├── controladorMenu.py            # pantalla de reporte, aceptar_resolubilidad, volver
│   ├── controladorJuego.py           # preparar_nueva / iniciar_preparada, aviso
│   ├── constructorEstadoVista.py     # EstadoVista.resolubilidad
│   └── bench/
│       ├── alternativasResolubilidad.py  # NUEVO: alternativa ingenua (R11)
│       ├── benchResolubilidad.py     # NUEVO
│       └── benchTodo.py              # + benchResolubilidad
└── vista/
    ├── estadoVista.py                # + ReporteResolubilidadVisible, EstadoVista.resolubilidad
    ├── vistaJuego.py                 # + mostrar_resolubilidad (no abstracto)
    ├── vistaArcade.py                # pantalla y panel
    ├── pantallaResolubilidad.py      # NUEVO: pantalla de reporte (ENTER/ESC)
    ├── pantallaJuego.py              # tecla V
    └── hudJuego.py                   # panel superpuesto del reporte

pruebas/
├── apoyo_resolubilidad.py            # criptas sintéticas y FuenteMemoria con llaves
├── oraculo_resolubilidad.py          # oráculo con las definiciones literales de la spec (R13)
├── datos/resolubilidad/              # paquete sin conexión con llaves.json
├── prueba_resolubilidad_oraculo.py   # ~200 criptas al azar con semilla fija contra el oráculo (R13)
├── prueba_resolubilidad_reglas.py    # FR-001 a FR-010 (H1)
├── prueba_resolubilidad_reporte.py   # FR-011 a FR-016, texto canónico (H1, SC-004)
├── prueba_resolubilidad_inicio.py    # FR-018 a FR-021 (H2)
├── prueba_verificar.py               # FR-022 a FR-024 (H3)
├── prueba_datos_llaves.py            # FR-025 a FR-031 (H4)
├── prueba_rendimiento_resolubilidad.py  # FR-032 a FR-035 (H5)
├── prueba_vista_resolubilidad.py     # FR-037: pantalla, V sin choque, fila de V en el README
└── prueba_sin_datos_concretos.py     # FR-036: ids y versiones de los paquetes ausentes del código

guardar_respuestas.py                 # + llaves.json
README.md                             # FR-037: tecla V, --verificar, --forzar
DECISIONES.md                         # secciones nuevas (siguientes D libres)
```

**Structure Decision**: se mantiene la estructura MVC existente. La lógica
nueva va en un paquete propio del modelo (`modelo/resolubilidad/`), porque no
depende de `Partida` ni de `Mundo`: solo de datos del puerto. Así se prueba sin
partida y lo reutilizan el juego, `--verificar` y el bench.

## Complexity Tracking

Sin violaciones de la constitución que justificar.
