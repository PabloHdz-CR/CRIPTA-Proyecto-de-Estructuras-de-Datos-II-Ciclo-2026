# Implementation Plan: Terreno y cazador

**Branch**: `001-terreno-cazador` | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-terreno-cazador/spec.md`

## Summary

Cada salida del esqueleto puede traer un costo de tránsito (100 por omisión,
el mismo en ambos sentidos). Moverse cuesta el costo de la salida para todos
los actores, y el resto de las reglas de tiempo no cambia. Se agrega el
**cazador**, un enemigo que avanza un paso por la ruta de costo mínimo hacia
el jugador si esa ruta no supera su rango.

Enfoque técnico (ver [research.md](research.md)): un **mapa de distancias
hacia el jugador** compartido. Se calcula con Dijkstra hacia atrás, acotado
por costo, con el `HeapMinimo` propio y eliminación perezosa. Se invalida por
(sala del jugador, versión de puertas, cota). Cada cazador decide en
O(salidas de su sala) aplicando la fórmula de desempate de la spec. La
versión de puertas avanza en el *setter* de `Salida.cerrada`, así que deshacer
y cargar también invalidan el mapa. Las salidas guardan referencias directas a
sus salas y cada sala lista sus salidas entrantes, así la búsqueda nunca busca
salas por id. Mediciones previas: 100 cazadores en 0,3 a 9,8 ms, contra 8 a
497 ms calculando por cazador, con decisiones idénticas.

## Technical Context

**Language/Version**: Python 3.11+ (equipo local: 3.12.10)

**Primary Dependencies**: `arcade` (solo la Vista), `requests` (solo el
adaptador HTTP). Las estructuras son propias: `HeapMinimo`, `ListaEnlazada`,
`ListaDoble`. Están prohibidos heapq, dict y set como índice, list de Python y
cualquier biblioteca de grafos.

**Storage**: archivos propios. Partida binaria (`FORMATO_VERSION` 1 → 2),
`partida.log` de solo anexado (sin cambios), caché JSON de fichas por versión
del catálogo (agrega `rango`).

**Testing**: scripts `pruebas/prueba_*.py` ejecutados por
`python -m pruebas.ejecutar_pruebas`, uno por proceso. Incluye
`prueba_reglas`, que verifica las reglas de la constitución leyendo el AST.

**Target Platform**: escritorio, en el equipo local de la defensa (Windows 11).

**Project Type**: juego de escritorio MVC con puertos y adaptadores, y modos
`--offline`, `--replay` y `--bench`.

**Performance Goals**: ciclo de eventos entre dos decisiones del jugador menor
a 20 ms con 20, 50 y 100 cazadores (FR-025). Las salas examinadas no crecen
con el tamaño de la cripta (FR-026).

**Constraints**: determinismo (sin azar en el cazador y con orden fijo N, S,
E, O); la decisión es idéntica a la que daría un cálculo desde cero (FR-017);
sin datos de criptas concretas en el código; presupuesto de red intacto (la
capacidad no hace solicitudes nuevas).

**Scale/Scope**: criptas de decenas a pocos cientos de salas (las de
`datos_offline` tienen 6, 20, 40 y 50), hasta 4 salidas por sala y hasta 100
cazadores activos. Estrés medido con 1024 salas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento del plan | Estado |
|---|---|---|
| I. Estructuras propias | Mapa con `HeapMinimo` propio; estado de búsqueda en campos de la sala con sello (sin dict ni set); entrantes en `ListaEnlazada`; el oráculo de las pruebas también usa estructuras propias. Sin heapq, sorted ni bibliotecas de grafos | ✅ |
| II. Determinismo | El cazador no usa azar; recorre las salidas en orden fijo, desempata por menor id y el heap ordena por (distancia, id). No se agregan sorteos al Random propio, así que las secuencias del errante no cambian | ✅ |
| III. MVC y puertos | Costos y cazador viven en el Modelo; el convertidor (adaptador) valida tipos; el Controlador arma `SalidaVisible.costo` y `ActorVisible.es_cazador`; la Vista solo recibe DTOs. `--bench` y `--replay` no instancian la Vista | ✅ |
| IV. Sin datos concretos y presupuesto | La cripta de referencia del bench se elige en ejecución por cantidad de salas; ningún id en el código. No hay solicitudes HTTP nuevas | ✅ |
| V. Reversibilidad y persistencia | El mapa es caché derivada, no estado reversible: se invalida, nunca se restaura. Formato de guardado v2 y v1 reportado incompatible. El log y el replay no cambian | ✅ |
| VI. Medir antes de afirmar | Mediciones previas en research.md R1; el bench nuevo (R12) da la evidencia definitiva; la reutilización del mapa se justifica en R2/R3 y se demuestra con la prueba de equivalencia (R9) | ✅ |
| VII. La spec precede al código | spec.md está confirmada en git. La enmienda de FR-026 y SC-004 que exige el diseño ya se aplicó en un commit propio (`d944688`), antes del plan | ✅ |
| Restricciones | Anotaciones de tipo, docstrings y `_` con propiedades en el código nuevo; nombres camelCase en archivos (`mapaDistancias.py`, `registroPuertas.py`, `benchCazador.py`); excepción propia `DatosInvalidos(ErrorCripta)` | ✅ |
| Flujo y hecho | Cada FR tiene una prueba que lo cita (quickstart.md); se agregan secciones D71 en adelante a DECISIONES.md; PROMPTS_LLM.md queda registrado | ✅ |

**Resultado del gate (antes y después del diseño)**: pasa. La enmienda de
FR-026/SC-004 ya está confirmada en la spec.

### Enmienda de la spec (FR-026, SC-004), aplicada en `d944688`

La redacción aclarada cuenta las salas que examina "la decisión de un cazador"
**alrededor de su sala**. Con el mapa compartido (R1), la decisión examina solo
las salidas de su sala, y el cálculo del mapa examina la región **alrededor
del jugador** con cota igual al mayor rango pedido. Se respeta la intención
original ("no proporcional al tamaño de la cripta, sino a la región dentro de
su rango"), pero no la letra. Redacción aplicada:

> **FR-026**: El trabajo de las decisiones de los cazadores MUST NOT crecer con
> el tamaño total de la cripta: (a) cada decisión examina solo las salidas de
> la sala del cazador y sus salas destino; (b) los cálculos de distancia que
> esas decisiones necesitan examinan como máximo las salas a costo ≤ R de la
> sala del jugador más sus vecinas inmediatas, donde R es el mayor rango de
> los cazadores que lo consultaron; (c) ambos conteos son idénticos en criptas
> de tamaños distintos con la misma región alcanzable. Se demuestra contando
> salas examinadas, no midiendo tiempo.
>
> **SC-004**: Multiplicar por 10 el tamaño de la cripta sin cambiar la región
> alcanzable deja exactamente iguales los conteos de salas examinadas por
> decisión y por cálculo de distancias, y ambos respetan las cotas de FR-026
> (medido con --bench).

La alternativa que cumple la letra actual (Dijkstra por cazador) no cumple
FR-025 con rangos grandes (research.md R1). Por eso se corrigió la spec y no
el diseño.

## Project Structure

### Documentation (this feature)

```text
specs/001-terreno-cazador/
├── spec.md
├── plan.md              # este archivo
├── research.md          # Fase 0
├── data-model.md        # Fase 1
├── quickstart.md        # Fase 1
├── contracts/           # Fase 1
│   ├── datos-entrada.md
│   ├── vista.md
│   └── partida-binaria-v2.md
├── checklists/requirements.md
└── tasks.md             # Fase 2 (/speckit-tasks; no lo crea este comando)
```

### Source Code (repository root)

```text
cripta/
├── modelo/
│   ├── puertos/
│   │   ├── dto.py                  # SalidaDTO.costo, FichaEnemigoDTO.rango
│   │   └── errores.py              # + DatosInvalidos
│   ├── mundo/
│   │   ├── salida.py               # costo, propiedad cerrada con aviso, origen/sala_destino
│   │   ├── sala.py                 # entrantes, sello y distancia del mapa
│   │   ├── mundo.py                # registro_puertas, enlazar(), validación de caras
│   │   ├── registroPuertas.py      # NUEVO: versión de las puertas
│   │   └── mapaDistancias.py       # NUEVO: Dijkstra hacia atrás acotado + consulta
│   ├── actores/
│   │   └── comportamientos.py      # + Cazador; crear_comportamiento con rango
│   ├── nucleo/
│   │   ├── partida.py              # costo_de(); usa el mapa; enlaza al iniciar
│   │   └── fabricaEntidades.py     # pasa el rango al crear el comportamiento
│   └── reloj/
│       └── eventos.py              # EventoAccionActor usa costo_de()
├── adaptadores/
│   ├── convertidorJson.py          # lee y valida costo y rango
│   ├── almacenLocalDisco.py        # persiste rango en la caché de fichas
│   └── partidaBinaria.py           # formato v2: costo por salida; enlazar al cargar
├── controlador/
│   ├── constructorEstadoVista.py   # SalidaVisible.costo, ActorVisible.es_cazador
│   └── bench/
│       ├── benchCazador.py         # NUEVO: ciclo con 20/50/100, conteos, comparación
│       └── benchTodo.py            # registra benchCazador
└── vista/
    ├── estadoVista.py              # campos nuevos de los DTOs
    ├── dibujoSala.py               # costo junto a cada salida; marca del cazador
    └── hudJuego.py                 # etiqueta distinguible del cazador

pruebas/
├── prueba_costo_salidas.py         # NUEVO
├── prueba_datos_costo.py           # NUEVO
├── prueba_cazador.py               # NUEVO
├── prueba_cazador_equivalencia.py  # NUEVO (con oráculo Bellman-Ford propio)
├── prueba_persistencia_cazador.py  # NUEVO
├── prueba_vista_costos.py          # NUEVO
├── ejecutar_pruebas.py             # registra las nuevas
└── datos/terreno_cazador/          # NUEVO: paquete sin conexión de prueba
```

**Structure Decision**: es un solo proyecto con la estructura MVC que ya
existe. No se crean capas ni paquetes nuevos: dos módulos en `modelo/mundo/`,
un bench y las pruebas. El grafo de búsqueda vive en `mundo/` porque depende
solo de salas, salidas y puertas, no de actores.

## Riesgos y cómo se cubren

| Riesgo | Mitigación |
|---|---|
| Un camino que cambia `cerrada` sin invalidar el mapa | La invalidación vive en el *setter* de la propiedad: cualquier escritura la dispara. La prueba de equivalencia encadena deshacer, cerrar y cargar |
| Equivalencia rota por la cota | Prueba formal en R3 y casos con rangos variados en el oráculo |
| Costo del enlace O(salas²) al cargar | Se mide en el bench; con pocos cientos de salas son menos de 10⁵ comparaciones, una sola vez |
| Pruebas existentes que construyen `Salida`, `Sala` o DTOs a mano | Los parámetros nuevos tienen valores por omisión; sin enlace, `costo` devuelve el declarado o 100 |
| Archivos guardados v1 de los usuarios | Se reportan incompatibles con el mensaje que ya existe (principio V); se documenta en el README |
| Intervalo de enemigos: el costo se calcula después de moverse | `costo_de()` se evalúa antes de ejecutar la acción, en ambos caminos (jugador y enemigo) |

## Complexity Tracking

No hay violaciones de la constitución que justificar.
