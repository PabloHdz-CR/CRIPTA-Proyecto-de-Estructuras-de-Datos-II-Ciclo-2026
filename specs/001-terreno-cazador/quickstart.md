# Quickstart: validar Terreno y cazador

**Feature**: `001-terreno-cazador` | **Plan**: [plan.md](plan.md)

Todo se ejecuta desde la raíz del repositorio (la carpeta que contiene `cripta/`
y `pruebas/`), con Python 3.11 o superior y las dependencias de
`requirements.txt` (`py -m pip install -r requirements.txt`). Los comandos usan
el lanzador `py`, igual que el README, **con el entorno virtual del proyecto
activado** (`.venv\Scripts\activate`; es el intérprete que usa PyCharm). Con el
entorno activo, `py` usa ese intérprete. Sin él, `py` toma el Python del
sistema, que puede no tener `requests` ni `arcade`, y entonces fallan las
pruebas que importan el Controlador o la Vista.

## 1. Pruebas automatizadas

```bash
py pruebas/ejecutar_pruebas.py
```

Resultado esperado: todas pasan, incluidas `prueba_reglas` (sin dict, list,
heapq ni sorted en `cripta/`) y las pruebas nuevas de esta capacidad:

| Prueba | Qué demuestra | Requisitos |
|---|---|---|
| `prueba_costo_salidas` | costo por omisión 100; intervalo `max(1, costo*100//velocidad)`; velocidad 1000 y costo 1 dan 1; reescalado al cambiar la velocidad; atacar y esperar no cambian; errante y rastreador eligen igual que antes; el actor ya está en la sala de destino durante el intervalo | FR-001, FR-002, FR-004 a FR-008, FR-028 |
| `prueba_datos_costo` | costo inválido; caras con costos distintos; una sola cara declarada; ficha de cazador sin rango. Con una cripta de caras distintas, el Controlador captura `DatosInvalidos` al iniciarla, llama a `mostrar_error` (con una vista de prueba que registra las llamadas) y la partida no empieza | FR-003, FR-009, FR-019, FR-020, FR-027 |
| `prueba_fuentes_costos` | el mismo esqueleto y el mismo catálogo servidos por la fuente en línea (servidor HTTP simulado, como `prueba_falso_1_9`) y por la fuente sin conexión producen costos y rangos idénticos | FR-021 |
| `prueba_cazador` | los 9 escenarios de la Historia 2: ataca, espera sin ruta, espera fuera de rango, rango justo, ruta más barata con más salas, desempate por menor id, puerta que se cierra, salas sin descargar, no abre puertas | FR-010 a FR-016 |
| `prueba_cazador_equivalencia` | ≥ 1000 situaciones al azar (semilla fija) con turnos encadenados: puertas que cambian, el jugador que se mueve, deshacer. La decisión coincide siempre con el oráculo desde cero | FR-017, FR-018, SC-002 |
| `prueba_conteo_cazador` | conteos de salas examinadas, deterministas y sin medir tiempo: (a) cada decisión examina solo las salidas de la sala del cazador y sus destinos; (b) cada cálculo de distancias examina como máximo las salas a costo ≤ R de la sala del jugador más sus vecinas; (c) los dos conteos son idénticos en una cripta base y en otra 10 veces más grande con la misma región alcanzable | FR-026, SC-004 |
| `prueba_rendimiento_cazador` | verificación automática: ejecuta el escenario del bench (versión rápida) con 20, 50 y 100 cazadores y con 100 cazadores de rangos distintos, y falla si el mínimo de las repeticiones de un ciclo llega a 20 ms. Al fallar reporta la cifra medida | FR-025, SC-003 |
| `prueba_persistencia_cazador` | guardar y cargar con costos y cazadores en el formato nuevo (número de `FORMATO_VERSION` pendiente de coordinar, ver plan.md); un archivo del formato anterior se reporta incompatible; replay idéntico | FR-022, SC-005 |
| `prueba_vista_costos` | `SalidaVisible.costo` y `ActorVisible.es_cazador` llegan bien armados a la vista | FR-023, FR-024 |

Cada prueba cita en su docstring los FR que ejerce y los escenarios de
aceptación que cubre (definición de hecho de la constitución).

### Escenarios de aceptación → pruebas (SC-001)

Los 21 escenarios del spec tienen una verificación automatizada. Cada caso de
prueba lleva en su nombre o docstring la marca `H<historia>.E<escenario>`.

| Historia | Escenarios | Prueba |
|---|---|---|
| 1. Costo de tránsito | E1 a E6 | `prueba_costo_salidas` |
| 1. Costo de tránsito | E7 y E8 (caras distintas, una sola cara declarada) | `prueba_datos_costo` |
| 2. Cazador | E1 a E9 | `prueba_cazador` |
| 3. Vista | E1 y E2 | `prueba_vista_costos` |
| 4. Rendimiento | E1 (ciclo < 20 ms con 20, 50 y 100) | `prueba_rendimiento_cazador` |
| 4. Rendimiento | E2 (conteos iguales en criptas de tamaños distintos) | `prueba_conteo_cazador` |

## 2. Mediciones

```bash
py -m cripta.controlador.bench.benchCazador --rapido   # versión corta
py -m cripta.controlador.bench.benchCazador            # completa
py main.py --bench                                     # todas las mediciones
```

Resultado esperado:

- **Ciclo de eventos**: con 20, 50 y 100 cazadores, el mínimo es < 20 ms en
  la cripta de referencia y en la malla de 1024 salas (FR-025, SC-003).
- **Rangos distintos**: 100 cazadores con rangos distintos, activados en orden
  creciente, decreciente y al azar (semilla fija). Por cada política de cota
  (P1 `max(anterior, rango)`, P2 duplicar, P3 duplicar con tope; ver
  plan.md, "Política de cota del mapa") reporta los recálculos del mapa por
  ciclo, las salas examinadas y el tiempo del ciclo. La política elegida y
  sus cifras van a DECISIONES.md.
- **Salas examinadas**: idénticas en la cripta base y en la 10 veces más
  grande, y dentro de las cotas de FR-026 (FR-026, SC-004).
- **Comparación**: mapa compartido frente a búsqueda por cazador desde cero,
  con las mismas decisiones. Va a DECISIONES.md.

El bench informa las cifras; las pruebas `prueba_rendimiento_cazador` y
`prueba_conteo_cazador` convierten los mismos criterios en verificaciones que
pasan o fallan dentro de `py pruebas/ejecutar_pruebas.py`.

## 3. Prueba manual (Vista)

1. Usar el paquete sin conexión de prueba con costos y cazadores (lo crea la
   tarea de datos de prueba en `pruebas/datos/terreno_cazador/`, con la
   misma estructura que `datos_offline/`).
2. `py main.py --offline=pruebas/datos/terreno_cazador` y entrar a esa
   cripta.
3. Comprobar:
   - Cada salida de la sala actual muestra su costo, y 100 si no se declaró
     (SC-006).
   - El cazador se reconoce frente a otros enemigos sin depender solo del
     color.
   - Al cruzar una salida de costo alto, los enemigos actúan más veces antes
     de tu siguiente turno.
   - Al cerrar el paso (si una puerta se cierra sola), el cazador se desvía o
     se queda esperando.

## 4. Reproducción

```bash
py main.py --replay partidas/<archivo>.log
```

Una partida jugada en el paso 3 se reproduce sin interacción, con las mismas
acciones y el mismo estado final (SC-005).
