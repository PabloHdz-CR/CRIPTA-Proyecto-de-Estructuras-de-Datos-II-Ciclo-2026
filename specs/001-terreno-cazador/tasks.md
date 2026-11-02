---
description: "Lista de tareas de Terreno y cazador"
---

# Tasks: Terreno y cazador

**Input**: Design documents from `specs/001-terreno-cazador/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: se piden de forma explícita (constitución, "Flujo y definición de hecho": cada FR tiene una prueba que lo cita; spec SC-001). En cada fase, las pruebas se escriben **antes** del código que las hace pasar, y deben fallar primero.

**Organization**: las tareas se agrupan por historia de usuario (US1 a US4 de spec.md). La persistencia (FR-022) es transversal y tiene su propia fase. La tarea que cierra la feature es la última de todas.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (otro archivo y sin dependencias pendientes).
- **[Story]**: historia a la que pertenece (US1, US2, US3, US4).
- Cada tarea cita los FR-xxx que cubre y la ruta exacta del archivo.

## Path Conventions

Proyecto único (plan.md, "Project Structure"): código en `cripta/`, pruebas en
`pruebas/` (cada una es un script `py -m pruebas.<nombre>` con `assert`),
mediciones en `cripta/controlador/bench/`. Comandos con `py` y el entorno
`.venv` activado (quickstart.md). Las pruebas de `pruebas/` pueden usar
estructuras de Python; el código de `cripta/` no puede usar dict, set, list,
heapq ni sorted (`prueba_reglas`).

---

## Phase 1: Setup (infraestructura compartida de pruebas)

**Purpose**: dejar una línea base verde y los datos y ayudas que usan las pruebas de todas las historias. T001 a T003 van **antes de cambiar cualquier código** de `cripta/`.

- [X] T001 Confirmar la línea base en esta rama, antes de cambiar código, con `.venv` activado:
  - En `PRUEBAS` de `pruebas/ejecutar_pruebas.py`, revisar las pruebas comentadas que no usan la red. La única es `prueba_falso_1_6`, que **queda fuera**: no es una prueba, sino el módulo que define `ServidorFalso` (no tiene asserts y, corrido solo, sale con 0 sin verificar nada). Lo ejercita `prueba_falso_1_9`, que ya está en la suite. Se deja comentada, con un comentario que lo explica.
  - Las `prueba_real_1_6` y `prueba_real_1_9` siguen comentadas, con su comentario actual, porque llaman al API real y gastan `presupuesto_solicitudes` (principio IV). El README ya indica que se corren aparte.
  - Si una prueba descomentada falla, se corrige o se documenta por qué queda fuera, en el mismo commit.
  - Ejecutar `py pruebas/ejecutar_pruebas.py` hasta que corra **completa y en verde**, y anotar el total de pruebas como línea base: **37**.
  - En `README.md:27`, corregir "Corre las 36 pruebas" al total de la línea base (37).

  Cubre: protege FR-006 y FR-007 (sin regresiones) y es la base de SC-001.
- [X] T002 Ampliar `pruebas/prueba_reglas.py` para que haga cumplir todo el principio I sobre `cripta/`, antes de escribir código nuevo. Debe detectar:
  - Conjuntos: literales `{a, b}`, comprensiones de conjunto y las llamadas `set()` y `frozenset()`. Solo la llamada a la función cuenta: un método llamado `.set()` (por ejemplo `threading.Event.set()` en `cripta/modelo/datos/fuenteAsincrona.py`) no es un conjunto y no se marca.
  - Módulos: `heapq` y `bisect` (ya se detectan), **cualquier** import de `collections` (no solo `deque`: también `OrderedDict`, `defaultdict` y `Counter`), y `networkx` y otras bibliotecas de grafos (`igraph`, `rustworkx`, `graph_tool`, `scipy.sparse.csgraph`).
  - Los conjuntos y los módulos nuevos no tienen la excepción de `ARCHIVOS_CON_EXCEPCION`: ningún archivo los necesita para hablar con requests o json.
  - Autopruebas en `CASOS`: un caso que debe marcarse por cada forma nueva (`{1, 2}`, `{a for a in b}`, `set(x)`, `frozenset(x)`, `import collections`, `from collections import Counter`, `import networkx`, `from scipy.sparse import csgraph`) y uno que no (`evento.set()`).
  - Actualizar el docstring del módulo con las reglas nuevas.
  - `py pruebas/prueba_reglas.py` sigue en verde sobre el código actual de `cripta/`. Si marca algo, se corrige en el mismo commit o se documenta por qué queda.

  No cubre ningún FR: hace cumplir el principio I de la constitución, que es el control que usan T041, T042 y T058.
- [X] T003 Con el código **actual**, antes de T049, generar el fixture `pruebas/datos/terreno_cazador/guardado_formato_anterior.bin`: un archivo de partida guardada con el formato vigente (`FORMATO_VERSION = 1`).
  - Hacerlo con un script reproducible, `pruebas/generar_guardado_formato_anterior.py`, que inicia una partida sin conexión sobre `datos_offline/` y la guarda con `PartidaBinaria.guardar`.
  - La cripta se elige en el script por cantidad de salas (la más chica). No usa `terreno-a`, porque el código actual no reconoce el comportamiento "cazador".
  - Confirmar en git el `.bin` y el script. T047(b) usa este fixture.

  Cubre FR-022.
- [X] T004 Crear el paquete sin conexión de prueba en `pruebas/datos/terreno_cazador/`, con la misma estructura que `datos_offline/`: `criptas.json`, `criptas/<id>/general.json`, `version.json`, `esqueleto/pagina_1.json`, `contenido/<sala>.json` y `catalogo/<ficha>.json`. Copiar el formato de `datos_offline/criptas/cripta-01` y `datos_offline/catalogo`. Contenido:
  - (a) Cripta `terreno-a`, con salidas de costo 1, 50, 250 y 300; salidas sin `costo` (valen 100); una puerta con `cierre_automatico`; una salida de un solo sentido; un enemigo cazador (`comportamiento: "cazador"`, `rango: 400`) y uno errante.
  - (b) Cripta `terreno-caras-distintas`, donde A→B declara `costo: 300` y B→A declara `costo: 200`.
  - (c) Cripta `terreno-sin-rango`, con una ficha de cazador sin `rango`.

  Los ids viven solo en los datos de prueba, nunca en `cripta/` (principio IV). Cubre FR-001, FR-009, FR-019, FR-020 y FR-027.
- [X] T005 [P] Crear `pruebas/apoyo_terreno.py` con ayudas compartidas:
  - Construir mundos sintéticos: pasillo, malla de n×n, rutas "menos salas pero más caras" y criptas pequeñas al azar con `random.Random(semilla)`.
  - Construir una `Partida` mínima sobre una fuente falsa.
  - `VistaRegistradora`, que guarda cada llamada a `mostrar_error`, `mostrar_estado` y `mostrar_fin` para que las pruebas las revisen.

  Lo usan las pruebas de FR-004 a FR-028.
- [X] T006 [P] Crear `pruebas/oraculo_rutas.py`, el oráculo **independiente** de R9. Solo lee `Sala.salidas`, `Salida.destino`, `Salida.cerrada` y `Salida.costo`, y no importa nada de `mapaDistancias.py`.
  - Si el cazador comparte sala con el jugador vivo → `Atacar`.
  - Si no, para **cada vecina abierta `v`** de la sala `u` del cazador, corre un Bellman-Ford **hacia adelante desde `v`** hasta la sala del jugador, sin cota, sin caché y sin sellos, y obtiene `dist(v, jugador)`.
  - Con eso calcula `d = min(costo(u, v) + dist(v, jugador))`. Si no hay ninguna o `d > rango`, la acción es `Esperar` (costo 100). Si no, es `Mover(dir)` hacia la `v` de menor id entre las que alcanzan `d`, con el costo de esa salida. Si dos o más salidas abiertas de `u` llevan a esa misma `v` y alcanzan `d`, usa la primera en el orden N, S, E, O (FR-014).

  Es la fórmula literal de FR-014, calculada desde las vecinas y no desde el jugador. Cubre FR-011 a FR-014 y FR-017.

---

## Phase 2: Foundational (prerrequisitos que bloquean todo)

**Purpose**: tipos mínimos para que las pruebas puedan importarse. No agregan comportamiento.

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase.

- [X] T007 [P] Agregar `class DatosInvalidos(ErrorCripta)` en `cripta/modelo/puertos/errores.py`, con docstring: datos de la cripta o del catálogo inconsistentes entre sí o fuera de rango; el mensaje identifica salas, dirección y valores. Cubre FR-027 y FR-003.
- [X] T008 [P] Agregar a `cripta/modelo/puertos/dto.py`:
  - `SalidaDTO.costo: int = None`, que significa "None = no declarado. Si viene, entero ≥ 1 (sin bool)".
  - `FichaEnemigoDTO.rango: int = None`, que significa "Obligatorio si el comportamiento es cazador: entero ≥ 0, sin bool. Se ignora en los demás comportamientos".

  Los dos van al final y con valor por omisión, para no romper las pruebas existentes que construyen DTOs a mano. Cubre FR-001, FR-009, FR-019 y FR-020.
- [X] T009 [P] Crear `cripta/modelo/mundo/registroPuertas.py`:
  - `class RegistroPuertas` con `_version: int = 0`, la propiedad `version` y `avisar_cambio()`, que incrementa la versión.
  - Docstring que explique por qué no es estado reversible: deshacer la incrementa en lugar de restaurarla.

  Cubre FR-017 (research R2).

**Checkpoint**: los módulos nuevos se importan y `py pruebas/ejecutar_pruebas.py` sigue en verde, **37/37** (la línea base de T001).

---

## Phase 3: User Story 1 - Atravesar salidas con costo de tránsito (Priority: P1) 🎯 MVP

**Goal**: moverse cuesta el costo de la salida para todos los actores (100 si no se declara). La cripta se rechaza si las dos caras de una puerta declaran costos distintos.

**Independent Test**: con `terreno-a` y sin cazadores, el intervalo de cada movimiento del jugador y de un errante es `max(1, costo_salida × 100 // velocidad)` (quickstart.md §1).

### Tests for User Story 1 (escribir primero; deben fallar)

- [X] T010 [P] [US1] Crear `pruebas/prueba_costo_salidas.py`, con docstring que cite FR-001, FR-002, FR-004 a FR-008 y FR-028, y un caso por escenario con su marca:
  - **H1.E1**: sin costo declarado, velocidad 100 → +100.
  - **H1.E2**: costo 300, velocidad 100 → +300.
  - **H1.E3**: costo 1, velocidad 1000 → +1.
  - **H1.E4**: costo 400 y la velocidad cambia de 100 a 200 a mitad del intervalo → `restante × 100 // 200`, mínimo 1.
  - **H1.E5**: errante y rastreador eligen la misma salida que antes; la secuencia del Random propio no cambia.
  - **H1.E6**: atacar, esperar, abrir, recoger, soltar, usar y equipar cuestan lo mismo que hoy.

  Además:
  - Una puerta cruzada en los dos sentidos cuesta lo mismo (FR-002).
  - Durante el intervalo, el actor ya está en la sala de destino y puede ser atacado ahí (FR-028).
- [X] T011 [P] [US1] Crear `pruebas/prueba_datos_costo.py`, con docstring que cite FR-001, FR-003, FR-019 y FR-027:
  - **H1.E7**: caras con costos distintos (300 y 200) → `DatosInvalidos`; el mensaje nombra las dos salas y los dos costos.
  - **H1.E8**: solo A→B declara 300 → cuesta 300 en ambos sentidos.
  - Costo inválido (`0`, `-5`, `2.5`, `"100"`, `true`) → error de datos que nombra sala y dirección.
  - Contraparte inexistente (salida de un solo sentido) → vale el costo declarado.
  - `enlazar()` es idempotente: dos llamadas seguidas dejan las mismas entrantes en cada sala (misma cantidad, sin duplicados), los mismos costos y una sola versión de registro por salida (FR-002).
  - **Error en el Controlador**: `ControladorMenu` con `VistaRegistradora` (T005) sobre `pruebas/datos/terreno_cazador` inicia `terreno-caras-distintas`. Debe capturar `DatosInvalidos`, llamar una sola vez a `mostrar_error` con un texto que contenga "No se pudo iniciar la cripta", ambas salas y ambos costos, y dejar `_juego` en None (la partida no empieza).
- [X] T012 [P] [US1] Crear `pruebas/prueba_fuentes_costos.py`, con docstring que cite FR-019 y FR-021. Las mismas páginas de esqueleto de `terreno-a`, servidas por `ClienteHttp` contra `ServidorFalso` (de `pruebas/prueba_falso_1_6.py`, como en `prueba_falso_1_9`) y por `FuenteOffline` sobre `pruebas/datos/terreno_cazador`, deben dar el mismo `SalidaDTO.costo` en cada salida y el mismo costo efectivo después de `Mundo.enlazar()`.

### Implementation for User Story 1

- [X] T013 [US1] En `cripta/adaptadores/convertidorJson.py`, hacer que `_salida_desde_json` lea `costo` (recibe también el id de la sala para el mensaje). Regla: "entero ≥ 1; se rechazan bool, 0, negativos, decimales y texto". Si no se cumple, lanza un error de datos de la jerarquía `ErrorCripta` que nombra la sala y la dirección. Si falta el campo o viene `null`, queda `None` (no declarado; aclaración de FR-003). Cubre FR-001, FR-003 y FR-019.
- [X] T014 [US1] En `cripta/modelo/mundo/salida.py`:
  - Nuevo parámetro `costo=None`, guardado como `_costo_declarado`.
  - Propiedad `costo`: el costo efectivo si ya se enlazó; si no, el declarado, o 100.
  - Propiedad `cerrada` sobre `_cerrada`; su *setter* llama a `_registro.avisar_cambio()` si `_registro` no es None.
  - En `__init__`, `self._registro = None` se asigna **antes** que `self.cerrada`, porque esa asignación ya pasa por el *setter*. Si no, crear una `Salida` (en `partidaBinaria` o en las pruebas que la construyen a mano) falla con `AttributeError`.
  - Propiedades `origen` y `sala_destino`.
  - Docstrings y anotaciones de tipo.
  - `transitable()` sigue siendo `not cerrada`. Mutador, Diario y partidaBinaria siguen escribiendo `salida.cerrada` sin cambios.

  Cubre FR-001, FR-002 y FR-017.
- [X] T015 [US1] En `cripta/modelo/mundo/sala.py`, agregar `_entrantes` (ListaEnlazada de Salida) y la propiedad `entrantes`. Cubre FR-011 (research R4).
- [X] T016 [US1] En `cripta/modelo/mundo/mundo.py`:
  - `_construir_salidas` pasa `dto.costo`.
  - Nuevo atributo `registro_puertas` (un `RegistroPuertas` por Mundo).
  - Nuevo método `enlazar()`. Para cada salida: resuelve `origen` y `sala_destino`; la agrega a `entrantes` de su destino; busca la contraparte (la salida de la sala destino en la dirección opuesta, N↔S y E↔O, que conduce de vuelta); resuelve el costo efectivo con la tabla de `contracts/datos-entrada.md`; y conecta `_registro`.
  - **Idempotente**: antes de llenar, vacía `entrantes` de todas las salas. Llamarlo dos veces deja las mismas entrantes (sin duplicados), los mismos costos efectivos y el mismo registro conectado.
  - Si las dos caras declaran costos distintos, lanza `DatosInvalidos` con el mensaje del contrato ("Las caras de la puerta entre la sala A (DIR, costo k₁) y la sala B (DIR', costo k₂) declaran costos distintos").
  - Docstring con el costo: O(salas²), una sola vez.

  Cubre FR-002 y FR-027.
- [X] T017 [US1] En `cripta/modelo/nucleo/partida.py`:
  - `iniciar()` llama a `self.mundo.enlazar()` justo después de `agregar_esqueleto`.
  - Nuevo `costo_de(actor, accion) -> int`: si es `Mover` y existe la salida en esa dirección de la sala **actual** del actor, su `costo`; si no, `accion.costo_base`.
  - `aplicar_accion` calcula el costo **antes** de `_ejecutar_accion_jugador` y lo usa en `programar_accion`.
  - `cambiar_velocidad` no cambia.

  Cubre FR-004, FR-005, FR-006, FR-008 y FR-028.
- [X] T018 [US1] En `cripta/modelo/reloj/eventos.py`, `EventoAccionActor.ejecutar` calcula `costo = partida.costo_de(actor, accion)` **antes** de `partida.ejecutar_accion_enemigo` y reprograma con ese costo. Cubre FR-004 y FR-007.
- [X] T019 [US1] Confirmar que `cripta/controlador/controladorMenu.py` no necesita cambios: `_empezar_partida` ya captura `ErrorCripta` y llama a `mostrar_error`. Hacer que T011 pase. Si no pasa, ajustar solo el mensaje, sin capturar `DatosInvalidos` aparte. Cubre FR-027.
- [X] T020 [US1] Ejecutar `py -m pruebas.prueba_costo_salidas`, `py -m pruebas.prueba_datos_costo`, `py -m pruebas.prueba_fuentes_costos`, `py -m pruebas.prueba_reglas` y la suite completa con `py pruebas/ejecutar_pruebas.py`: todo en verde y sin regresiones, porque las criptas sin `costo` se comportan igual que antes. Cubre FR-006 y FR-007.

**Checkpoint**: US1 completa y demostrable sola (MVP).

---

## Phase 4: User Story 2 - Ser perseguido por un cazador (Priority: P1)

**Goal**: el cazador ataca si comparte sala con el jugador; si no, avanza un paso por la ruta de costo mínimo cuando `d ≤ rango`, y si no puede, espera con costo 100.

**Independent Test**: con criptas pequeñas de `apoyo_terreno`, cada decisión del cazador coincide turno a turno con el oráculo desde cero (T006).

### Tests for User Story 2 (escribir primero; deben fallar)

- [X] T021 [P] [US2] Crear `pruebas/prueba_cazador.py`, con docstring que cite FR-010 a FR-016, y un caso por escenario con su marca:
  - **H2.E1**: comparte sala → `Atacar` y no se mueve.
  - **H2.E2**: sin ruta abierta → `Esperar`, costo 100.
  - **H2.E3**: rango 500 y d = 600 → `Esperar`, costo 100.
  - **H2.E4**: rango 500 y d = 500 → se mueve.
  - **H2.E5**: ruta de 1 salida que cuesta 500 contra ruta de 3 salidas que suman 300 → sigue la de 3, y el costo de la acción es el de su primera salida.
  - **H2.E6**: empate entre v1 y v2 → va a la de menor id.
  - **H2.E7**: una puerta de la ruta se cierra entre dos turnos → decide como desde cero (se desvía o espera).
  - **H2.E8**: salas con `contenido_cargado = False` → la misma decisión que con contenido.
  - **H2.E9**: la única ruta tiene una puerta cerrada → no la abre (espera).

  Además:
  - Rango 0 → solo ataca o espera.
  - Dos salidas abiertas de la sala del cazador llevan a la misma vecina con el mismo costo y ambas alcanzan `d` → usa la primera en el orden N, S, E, O (FR-014).
  - Casos borde de spec.md, con la marca **BORDE** en el nombre o el docstring:
    - **BORDE** jugador muerto: el cazador no lo ataca (FR-010).
    - **BORDE** varios cazadores en la misma sala con el mismo objetivo: cada uno decide por su cuenta y, con rangos que lo permiten, todos toman la misma decisión (FR-014, FR-018).
    - **BORDE** primer costo del cazador al aparecer: su primera acción se agenda con el mismo costo inicial que la de los demás enemigos (FR-009).
- [X] T022 [P] [US2] Crear `pruebas/prueba_cazador_equivalencia.py`, con docstring que cite FR-017, FR-018 y SC-002:
  - Al menos **1000 situaciones** al azar con `random.Random(semilla fija)`: criptas de 4 a 12 salas, costos al azar en {1, 50, 100, 250, 300}, puertas cerradas al azar, salidas de un solo sentido y rangos entre 0 y la suma de todos los costos.
  - El generador también crea, con una frecuencia fija, salas con dos salidas hacia la misma vecina y con el mismo costo, para ejercitar el desempate N, S, E, O de FR-014. Cazador y oráculo siguen la misma regla: id de la vecina y, después, orden N, S, E, O.
  - En cada situación se encadenan varios turnos con cambios entre ellos: el jugador se mueve, una puerta se abre o se cierra (por el Mutador) y se deshace una acción (con el Diario).
  - En cada turno se exige que la acción y el costo del cazador sean **idénticos** a los del oráculo Bellman-Ford independiente de `pruebas/oraculo_rutas.py` (T006).
  - Una segunda pasada con la misma semilla debe dar exactamente la misma secuencia (FR-018).
  - Al fallar, reporta la semilla y la situación.
- [X] T023 [P] [US2] Ampliar `pruebas/prueba_datos_costo.py` con los casos del rango:
  - Ficha de cazador sin `rango`, con `-1`, `true` o `2.5` → error de datos que nombra la ficha.
  - `rango: 0` es válido.
  - En un errante, `rango` se ignora.
  - `terreno-sin-rango` no puede iniciarse y el Controlador lo informa con `mostrar_error`.

  Cubre FR-009 y FR-020.
- [X] T024 [P] [US2] Ampliar `pruebas/prueba_fuentes_costos.py`: la ficha de cazador servida por `ServidorFalso` y por `FuenteOffline` da el mismo `rango`, y la caché local de fichas (`AlmacenLocalDisco`) lo guarda y lo devuelve igual. Cubre FR-020 y FR-021.

### Implementation for User Story 2

- [X] T025 [US2] En `cripta/adaptadores/convertidorJson.py`, leer `rango` en las fichas de clase enemigo. Si el comportamiento empieza por "cazad" (en minúsculas), exige "entero ≥ 0, sin bool" y, si falta o no lo cumple, lanza un error de datos que nombra la ficha. En otros comportamientos lo ignora. Cubre FR-009 y FR-020.
- [X] T026 [P] [US2] En `cripta/adaptadores/almacenLocalDisco.py`, hacer que `_ficha_a_dict` escriba `rango` y `_dict_a_ficha` lo lea con `.get("rango")`. Cubre FR-020.
- [X] T027 [US2] En `cripta/modelo/mundo/sala.py`, agregar `_sello_mapa: int = 0` y `_distancia_mapa: int = 0` para la búsqueda sin diccionarios (research R5). Cubre FR-011.
- [X] T028 [US2] Crear `cripta/modelo/mundo/mapaDistancias.py`:
  - Clase interna `EntradaMapa(distancia, sala)` con `__lt__` por `(distancia, sala.id)`.
  - `class MapaDistancias` con `_sello`, `_id_objetivo`, `_version_puertas`, `_cota`, `_salas_examinadas` y `_calculos`.
  - La regla de la cota vive **aislada** en el método `_cota_nueva(cota_minima) -> int`, pensado para que las subclases lo sobrescriban. La versión base es la política **P1**: `max(cota_anterior si el objetivo y la versión no cambiaron, cota_minima)`.
  - `asegurar(sala_objetivo, cota_minima)` decide si hay que recalcular. Si hay que hacerlo, pide la cota a `_cota_nueva` y hace un Dijkstra hacia atrás por `entrantes` abiertas con `HeapMinimo` y eliminación perezosa, sin pasar de la cota.
  - `distancia(sala)`: devuelve None si el sello no coincide **o** si la distancia guardada es mayor que `_cota`.
  - Docstrings con la prueba de corrección de R3.
  - Sin dict, set, list ni heapq.

  Cubre FR-011, FR-015 y FR-017.
- [X] T029 [US2] En `cripta/modelo/actores/comportamientos.py`:
  - `class Cazador(Comportamiento)` con `NOMBRE = "cazador"` y `_rango`.
  - `decidir_sin_jugador`:
    1. `partida.mapa_distancias.asegurar(sala del jugador, rango)`.
    2. Recorre las salidas abiertas en orden N, S, E, O y se queda con la de menor `costo + distancia(v)`; en un empate, la de menor `v.id`. Solo reemplaza a la candidata si la nueva es **estrictamente** mejor por `(t, v.id)`, así que, si dos salidas llevan a la misma `v` con el mismo `t`, queda la primera en el orden N, S, E, O (FR-014).
    3. Devuelve `Esperar()` si no hay candidata o si `t > rango`; si no, `Mover(dir)`.
  - `crear_comportamiento(nombre, rango=None)` reconoce el prefijo "cazad" y lanza un error de datos si el rango es None.

  Cubre FR-009, FR-010, FR-012, FR-013, FR-014 y FR-016.
- [X] T030 [US2] En `cripta/modelo/nucleo/fabricaEntidades.py`, llamar a `crear_comportamiento(ficha.comportamiento, ficha.rango)`. Cubre FR-009.
- [X] T031 [US2] En `cripta/modelo/nucleo/partida.py`, crear `self.mapa_distancias = MapaDistancias(self.mundo)` en `iniciar()` después de `enlazar()`, con su propiedad y docstring. No es estado reversible: es caché derivada (principio V). Cubre FR-011, FR-015 y FR-018.
- [X] T032 [US2] Ejecutar T021 a T024 y `prueba_reglas` hasta tenerlos en verde, más la suite completa sin regresiones. Cubre FR-009 a FR-018, FR-020 y FR-021.

**Checkpoint**: US1 y US2 funcionan juntas; el cazador persigue en `terreno-a`.

---

## Phase 5: User Story 3 - Ver los costos y reconocer a los cazadores (Priority: P2)

**Goal**: la vista muestra el costo de cada salida de la sala actual y distingue a los cazadores.

**Independent Test**: los DTOs que arma el Controlador para una sala de `terreno-a` traen los costos (100 en la no declarada) y `es_cazador` correcto.

### Tests for User Story 3 (escribir primero; deben fallar)

- [X] T033 [P] [US3] Crear `pruebas/prueba_vista_costos.py`, con docstring que cite FR-023 y FR-024:
  - **H3.E1**: una sala con salidas de costo 100 (no declarado), 250 y 1 → `SalidaVisible.costo` vale 100, 250 y 1, y `None` donde no hay salida.
  - **H3.E2**: un cazador y un errante → `ActorVisible.es_cazador` vale True y False.
  - Además, un DTO construido sin los campos nuevos sigue siendo válido (valores por omisión).

### Implementation for User Story 3

- [X] T034 [US3] En `cripta/vista/estadoVista.py`, agregar `SalidaVisible.costo: int = None` ("costo efectivo (100 si no se declaró); None si estado == SALIDA_SIN_SALIDA") y `ActorVisible.es_cazador: bool = False`, según `contracts/vista.md`. Cubre FR-023 y FR-024.
- [X] T035 [US3] En `cripta/controlador/constructorEstadoVista.py`, llenar `costo` desde `salida.costo` y `es_cazador` según si el comportamiento del enemigo es `Cazador`. Cubre FR-023 y FR-024.
- [X] T036 [P] [US3] En `cripta/vista/dibujoSala.py`, dibujar el costo junto a cada salida existente de la sala actual, abierta o cerrada. Cubre FR-023.
- [X] T037 [P] [US3] En `cripta/vista/hudJuego.py` (y `dibujoSala.py` si dibuja enemigos), marcar al cazador con un marcador o un prefijo en la etiqueta además del color: "la distinción no depende solo del color". Cubre FR-024.
- [X] T038 [US3] Ejecutar T033 y las pruebas `prueba_vista_*` existentes en verde, y hacer la revisión manual de quickstart.md §3 con `py main.py --offline=pruebas/datos/terreno_cazador`. Cubre FR-023, FR-024 y SC-006.

**Checkpoint**: US3 visible en la ventana.

---

## Phase 6: User Story 4 - Rendimiento con muchos cazadores (Priority: P2)

**Goal**: el ciclo de eventos baja de 20 ms con 20, 50 y 100 cazadores, y el trabajo no crece con el tamaño de la cripta.

**Independent Test**: `py -m cripta.controlador.bench.benchCazador --rapido`, más las verificaciones automáticas T039 y T040.

### Tests for User Story 4 (escribir primero; deben fallar)

- [X] T039 [P] [US4] Crear `pruebas/prueba_conteo_cazador.py`, con docstring que cite FR-026 y SC-004, y la marca **H4.E2**. Con conteos deterministas, sin medir tiempo, sobre una cripta base y otra 10 veces más grande con la misma región alcanzable:
  - (a) Cada decisión examina solo las salidas de la sala del cazador y sus destinos.
  - (b) Cada cálculo del mapa examina como máximo las salas a costo ≤ R de la sala del jugador, más sus vecinas inmediatas.
  - (c) Los dos conteos son idénticos en ambas criptas.
- [X] T040 [P] [US4] Crear `pruebas/prueba_rendimiento_cazador.py`, con docstring que cite FR-025 y SC-003, y la marca **H4.E1**. Importa los escenarios de `benchCazador` en versión rápida y falla si el **mínimo** de las repeticiones de un ciclo llega a 20 ms en:
  - 20, 50 y 100 cazadores en la cripta de referencia y en la malla de 1024 salas.
  - 100 cazadores con rangos distintos.

  Al fallar reporta la cifra medida.

### Implementation for User Story 4

- [X] T041 [US4] Crear `cripta/controlador/bench/alternativasCazador.py`, siguiendo el patrón de `alternativasAgenda.py`:
  - `MapaDistanciasP2(MapaDistancias)`: sobrescribe **solo** `_cota_nueva` con duplicar, `max(rango, 2 × anterior)`.
  - `MapaDistanciasP3(MapaDistancias)`: sobrescribe **solo** `_cota_nueva` con duplicar con tope, `min(max(rango, 2 × anterior), R_activos)`. Recibe R_activos.
  - `BusquedaPorCazador`: un Dijkstra **hacia adelante propio** desde la sala de cada cazador, acotado por su rango, con `HeapMinimo` y su propio sello de búsqueda. Es la alternativa descartada de R1 y **no reutiliza** `MapaDistancias`, para que la comparación mida otro algoritmo y no comparta errores.

  **Nota**: este código vive en `cripta/`, así que `prueba_reglas` lo revisa: nada de list, dict, sorted ni heapq; se usan `ListaEnlazada` y `HeapMinimo`. Cubre FR-025 y FR-026.
- [X] T042 [US4] Crear `cripta/controlador/bench/benchCazador.py`, con `ejecutar(reporte, rapido)` y estos escenarios:
  1. Ciclo completo con 20, 50 y 100 cazadores, en la cripta de referencia y en la malla de 1024 salas. La cripta de referencia es la de más salas que lista `FuenteOffline` sobre `datos_offline/`; se elige por cantidad de salas, sin ids en el código, y recibe costos sintéticos con semilla fija.
  2. **Bench de la cota**: 100 cazadores con **rangos distintos**, activados en orden creciente, decreciente y al azar (semilla fija). Para **P1, P2 y P3** reporta recálculos por ciclo, salas examinadas y tiempo del ciclo, con PASA/FALLA contra 20 ms.
  3. Conteos de salas examinadas en una cripta base y en otra 10 veces más grande.
  4. Comparación del mapa compartido contra `BusquedaPorCazador`, con las mismas decisiones.
  5. Costo de `Mundo.enlazar()`.

  Usa `Medidor` y `Reporte`, y la evidencia principal son las cifras de salas examinadas.

  **Nota**: este código vive en `cripta/`, así que `prueba_reglas` lo revisa: nada de list, dict, sorted ni heapq (las criptas sintéticas y los resultados van en `ListaEnlazada` o tuplas). Cubre FR-025 y FR-026.
- [X] T043 [US4] En `cripta/controlador/bench/benchCazador.py`, agregar un bloque `if __name__ == "__main__":` que acepte `--rapido`, para que funcione `py -m cripta.controlador.bench.benchCazador [--rapido]`. Además, registrar `benchCazador.ejecutar(reporte, rapido)` en `cripta/controlador/bench/benchTodo.py` (import y llamada en `ejecutar_todo`). Cubre FR-025.
- [X] T044 [US4] Ejecutar el bench completo y **decidir la política de cota** con el criterio de plan.md ("la más simple que deje el ciclo con 100 cazadores de rangos distintos por debajo de 20 ms en la cripta de referencia y en la malla de 1024 salas"). Guardar las cifras para DECISIONES.md (T055). Cubre FR-025 y FR-026.
- [X] T045 [US4] **CONDICIONAL**, solo si en T044 gana P2 o P3:
  1. Enmendar primero FR-026(b), y SC-004 si hace falta, en `specs/001-terreno-cazador/spec.md`, en un **commit propio** que solo toque la spec (principio VII). Para P2, la cota pasa a "≤ 2R"; para P3, R es "el mayor rango de los cazadores activos que consultan en el ciclo".
  2. **Después**, en otro commit, mover la política ganadora a `cripta/modelo/mundo/mapaDistancias.py`. Si es P3, `cripta/modelo/nucleo/partida.py` debe proveer R_activos.
  3. Volver a ejecutar T022, T039 y T040.

  Si gana P1, escribir "no aplica" en esta tarea y en DECISIONES.md. Cubre FR-026.
- [X] T046 [US4] Ejecutar T039 y T040 en verde, junto con la suite completa. Cubre FR-025, FR-026, SC-003 y SC-004.

**Checkpoint**: US4 medida y verificada.

---

## Phase 7: Persistencia y reproducción (transversal: FR-022, SC-005)

**Purpose**: guardar, cargar y reproducir partidas con costos y cazadores.

### Tests (escribir primero; deben fallar)

- [X] T047 [P] Crear `pruebas/prueba_persistencia_cazador.py`, con docstring que cite FR-022, FR-027 y SC-005:
  - (a) Guardar y cargar `terreno-a` en el formato nuevo: los costos se conservan, `enlazar()` corre al cargar, y la decisión del cazador después de cargar es igual a la de antes de guardar.
  - (b) Cargar el fixture `pruebas/datos/terreno_cazador/guardado_formato_anterior.bin` (T003) → `VersionIncompatible`, sin migrar ni modificar el archivo.
  - (c) `--replay` de un log de `terreno-a` → mismas acciones y mismo estado final.
  - (d) **modoReplay con caras distintas**: un log de `terreno-caras-distintas` **escrito a mano** por la prueba en una carpeta temporal, con el encabezado mínimo del formato de `cripta/adaptadores/registroArchivo.py` (`PREFIJO_ENCABEZADO` seguido de id de cripta, versión de la cripta, versión del catálogo y semilla) y sin acciones, reproducido con `py main.py --offline=pruebas/datos/terreno_cazador --replay <log>` en un subproceso, sale con **código 1** e imprime el mensaje de `DatosInvalidos`.

### Implementation

- [X] T048 **Acordado el 01/11/2026: `FORMATO_VERSION = 2`, provisional según el orden de merge a `main`** (registrado en `contracts/partida-binaria.md`). Texto original: **PENDIENTE DE COORDINAR con Pablo**: acordar el número nuevo de `FORMATO_VERSION` con las otras features que cambian el formato de guardado, **sin fijar un número de antemano** (plan.md, "Formato de guardado"). Registrar el acuerdo en `specs/001-terreno-cazador/contracts/partida-binaria.md`, donde se reemplaza `VERSION_NUEVA`. Bloquea T049. Cubre FR-022.
- [X] T049 En `cripta/adaptadores/partidaBinaria.py`:
  - `_escribir_sala` escribe el **costo efectivo** de cada salida y `_leer_sala` lo lee.
  - `FORMATO_VERSION` toma el número acordado en T048.
  - `cargar()` llama a `mundo.enlazar()` y la Partida vuelve a crear `MapaDistancias`.
  - `cargar_sala()` lee el costo pero no enlaza.
  - Actualizar el docstring del formato.

  Cubre FR-022.
- [X] T050 Verificar con T047(d) que `cripta/controlador/modoReplay.py` ya reporta el error y que `fabricaAplicacion` sale con 1: hoy `ejecutar()` envuelve `iniciar_cripta` y `partida.iniciar` en `except ErrorCripta` y llama a `_fallar`. **Si no lo hace**, agregar la captura en `ModoReplay.ejecutar`, con su prueba en `pruebas/prueba_persistencia_cazador.py`. Cubre FR-027.
- [X] T051 Ampliar `pruebas/prueba_cazador_equivalencia.py` (T022) para que también guarde y cargue entre turnos, y compruebe que la decisión sigue igual a la del oráculo. Cubre FR-017 y FR-022.
- [X] T052 Ejecutar T047 y T051 en verde. Cubre FR-022 y SC-005.

---

## Phase 8: Polish, documentación y cierre

- [ ] T053 Registrar las **9 pruebas nuevas** en `PRUEBAS` de `pruebas/ejecutar_pruebas.py`, con un comentario de los FR de cada una: `prueba_costo_salidas`, `prueba_datos_costo`, `prueba_fuentes_costos`, `prueba_cazador`, `prueba_cazador_equivalencia`, `prueba_conteo_cazador`, `prueba_rendimiento_cazador`, `prueba_persistencia_cazador` y `prueba_vista_costos`. Cubre FR-001 a FR-028 y SC-001.
- [ ] T054 [P] En `README.md`:
  - Agregar una nota: los archivos de guardado del formato anterior se reportan incompatibles (`VersionIncompatible`) y no se migran; hay que empezar una partida nueva.
  - Mencionar el costo de las salidas y el cazador.
  - En `README.md:27`, cambiar el conteo de pruebas de 37 (lo deja T001) a **46**: las 37 de la línea base más las 9 nuevas de T053. Confirmar que `py pruebas/ejecutar_pruebas.py` imprime "Todas las pruebas pasaron (46)" (46/46) antes de escribirlo.

  Cubre FR-022.
- [ ] T055 [P] En `DECISIONES.md`, **antes de numerar**, hacer `git pull` de `main` (otras features pueden haber agregado decisiones) y usar el **siguiente número D libre**, sin suponer D71. Agregar la sección del problema resuelto, con enlaces a `specs/001-terreno-cazador/spec.md` y `specs/001-terreno-cazador/plan.md`:
  - Mapa compartido frente a búsqueda por cazador, con las cifras de T044.
  - Invalidación por el *setter* de `cerrada`.
  - Política de cota elegida y resultado de T045.
  - Referencias directas y salidas entrantes.
  - Formato de guardado con el número acordado.

  Cubre FR-017, FR-025 y FR-026.
- [ ] T056 [P] Registro en `PROMPTS_LLM.md`: **cada commit de fase incluye** la entrada de los prompts usados en esa fase (constitución, "Flujo y definición de hecho"), con el siguiente número libre de `## Entrada N` tal como está en el archivo en ese momento. Esta tarea verifica al final que ningún commit de fase quedó sin su entrada y que la numeración es continua. No cubre ningún FR: es un requisito de proceso de la constitución, no del producto.
- [ ] T057 Comprobar la tabla de escenarios (SC-001): buscar en `pruebas/` las 21 marcas `H<historia>.E<escenario>` de la sección "Escenarios de aceptación → pruebas" y confirmar que cada una aparece en la prueba asignada. Cubre SC-001.
- [ ] T058 Validación completa con `.venv` activado:
  - `py pruebas/ejecutar_pruebas.py`: todas pasan, **46/46**.
  - `py pruebas/prueba_reglas.py` (ampliada en T002): sin dict, set, list, heapq, bisect ni sorted en `cripta/`.
  - `py main.py --bench --rapido`.
  - quickstart.md §3 y §4.

  Cubre FR-001 a FR-028.
- [ ] T059 **Cerrar la feature** (última tarea). Comprobar:
  - Todas las tareas anteriores marcadas, y T045 y T048 resueltas (o T045 con "no aplica").
  - Cada FR-001 a FR-028 citado por al menos una prueba en verde.
  - DECISIONES.md y PROMPTS_LLM.md al día.
  - Sin datos de criptas concretas en `cripta/`.
  - Commits separados donde la constitución lo exige.

  Después, hacer push de `001-terreno-cazador` y abrir el PR hacia `main`.

---

## Escenarios de aceptación → pruebas (SC-001)

Cada escenario tiene una verificación automatizada que lleva su marca en el nombre o el docstring del caso de prueba.

| Marca | Escenario (spec.md) | Prueba | Tarea | FR |
|---|---|---|---|---|
| H1.E1 | Salida sin costo, velocidad 100 → +100 | `prueba_costo_salidas` | T010 | FR-001, FR-005 |
| H1.E2 | Costo 300, velocidad 100 → +300 | `prueba_costo_salidas` | T010 | FR-004, FR-005 |
| H1.E3 | Costo 1, velocidad muy alta → intervalo 1 | `prueba_costo_salidas` | T010 | FR-005 |
| H1.E4 | Cambio de velocidad a mitad del tránsito → reescalado | `prueba_costo_salidas` | T010 | FR-008 |
| H1.E5 | Errante y rastreador eligen igual | `prueba_costo_salidas` | T010 | FR-007 |
| H1.E6 | Otras acciones cuestan lo mismo | `prueba_costo_salidas` | T010 | FR-006 |
| H1.E7 | Caras con costos distintos → la cripta se rechaza | `prueba_datos_costo` | T011 | FR-027 |
| H1.E8 | Una sola cara declara 300 → 300 en ambos sentidos | `prueba_datos_costo` | T011 | FR-027, FR-002 |
| H2.E1 | Comparte sala → ataca y no se mueve | `prueba_cazador` | T021 | FR-010 |
| H2.E2 | Sin ruta abierta → espera, costo 100 | `prueba_cazador` | T021 | FR-012 |
| H2.E3 | d > rango → espera, costo 100 | `prueba_cazador` | T021 | FR-012 |
| H2.E4 | d = rango → se mueve | `prueba_cazador` | T021 | FR-013 |
| H2.E5 | Ruta con más salas pero más barata | `prueba_cazador` | T021 | FR-011, FR-013 |
| H2.E6 | Empate → vecina de menor id | `prueba_cazador` | T021 | FR-014 |
| H2.E7 | Puerta que se cierra entre turnos → decide desde cero | `prueba_cazador` | T021 | FR-017 |
| H2.E8 | Salas sin descargar → misma decisión | `prueba_cazador` | T021 | FR-015 |
| H2.E9 | Puerta cerrada → no la abre | `prueba_cazador` | T021 | FR-016 |
| H3.E1 | La vista muestra 100, 250 y 1 | `prueba_vista_costos` | T033 | FR-023 |
| H3.E2 | Cazador distinguible del errante | `prueba_vista_costos` | T033 | FR-024 |
| H4.E1 | Ciclo < 20 ms con 20, 50 y 100 cazadores | `prueba_rendimiento_cazador` | T040 | FR-025 |
| H4.E2 | Conteos iguales en criptas de tamaños distintos | `prueba_conteo_cazador` | T039 | FR-026 |

## Cobertura de requisitos

| FR | Pruebas | Implementación |
|---|---|---|
| FR-001 | T010, T011 | T008, T013, T014 |
| FR-002 | T010, T011 (incluye `enlazar()` idempotente) | T014, T016 |
| FR-003 | T011 | T007, T013 |
| FR-004, FR-005 | T010 | T017, T018 |
| FR-006 | T001 (línea base), T010, T020 | T017 |
| FR-007 | T001 (línea base), T010, T020 | T018 |
| FR-008 | T010 | T017 (sin cambio en `cambiar_velocidad`) |
| FR-009 | T021, T023 | T008, T025, T029, T030 |
| FR-010, FR-012, FR-013, FR-014, FR-016 | T021, T022 | T029 |
| FR-011, FR-015 | T021, T022 | T015, T027, T028, T031 |
| FR-017 | T021, T022, T051 | T009, T014, T028 |
| FR-018 | T022 | T029, T031 |
| FR-019 | T011, T012 | T008, T013 |
| FR-020 | T023, T024 | T008, T025, T026 |
| FR-021 | T012, T024 | T013, T025 |
| FR-022 | T003 (fixture), T047, T051 | T048, T049 |
| FR-023, FR-024 | T033 | T034 a T037 |
| FR-025 | T040 | T041 a T044 |
| FR-026 | T039 | T028, T041 a T045 |
| FR-027 | T011, T047 | T007, T016, T019, T050 |
| FR-028 | T010 | T017 |

Fuera de los FR: T002 hace cumplir el principio I de la constitución (`prueba_reglas`), y T056 es el registro de proceso en `PROMPTS_LLM.md`. Los casos **BORDE** de T021 cubren casos borde de spec.md y no cuentan en los 21 escenarios de SC-001.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 va primero (línea base verde). T002 amplía `prueba_reglas` antes de escribir código nuevo en `cripta/`. T003 va antes de cualquier cambio en `cripta/` y, sobre todo, antes de T049 (el fixture debe salir del formato actual). Después siguen T004 a T006.
- **Setup (Phase 1)** → **Foundational (Phase 2)** → historias.
- **US1 (Phase 3)**: depende de la Phase 2. Es el MVP.
- **US2 (Phase 4)**: depende de US1, porque usa `Salida.costo`, `entrantes`, `enlazar()` y `costo_de()`.
- **US3 (Phase 5)**: depende de US1 para el costo de las salidas y de US2 para `es_cazador`. Puede ir en paralelo con US4.
- **US4 (Phase 6)**: depende de US2 (`MapaDistancias`).
- **Persistencia (Phase 7)**: depende de US1, de US2 y del fixture T003. T049 está **bloqueada por T048** (coordinación con Pablo). T047, T050 y T051 pueden avanzar antes, con `VERSION_NUEVA` todavía sin número.
- **Polish (Phase 8)**: depende de todo lo anterior. **T059 va última.**

### Within Each Phase

- Pruebas primero, y deben fallar; después, modelo, adaptadores, Controlador y Vista.
- T045 (condicional) espera a T044. Dentro de T045, el commit de la spec va **antes** del commit de código.

### Parallel Opportunities

- Setup: T001 → T002 → T003 → T004; después, T005 ∥ T006.
- Foundational: T007 ∥ T008 ∥ T009.
- US1: las pruebas T010 ∥ T011 ∥ T012.
- US2: las pruebas T021 ∥ T022 ∥ T023 ∥ T024; T026 ∥ T027.
- US3: T036 ∥ T037, después de T034 y T035. US3 completa ∥ US4 completa.
- US4: T039 ∥ T040.
- Polish: T054 ∥ T055 ∥ T056.

---

## Parallel Example: User Story 1

```text
# Escribir las tres pruebas de US1 a la vez (fallan hasta T013 a T018):
T010 pruebas/prueba_costo_salidas.py
T011 pruebas/prueba_datos_costo.py
T012 pruebas/prueba_fuentes_costos.py
```

## Parallel Example: User Story 2

```text
T021 pruebas/prueba_cazador.py
T022 pruebas/prueba_cazador_equivalencia.py
T023 pruebas/prueba_datos_costo.py (casos de rango)
T024 pruebas/prueba_fuentes_costos.py (rango)
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 y Phase 2.
2. Phase 3 (US1): costos de las salidas y rechazo de las caras con costos distintos.
3. **Detenerse y validar** con T020; se puede demostrar sin cazador.

### Incremental Delivery

1. US1 (costos).
2. US2 (cazador correcto y equivalente al oráculo).
3. US3 (vista) en paralelo con US4 (medición y política de cota).
4. Persistencia, en cuanto haya acuerdo con Pablo sobre `FORMATO_VERSION`.
5. Polish y cierre (T059).

### Notes

- Cada tarea, una vez hecha, se marca `[x]` en este archivo.
- Cada commit de fase incluye su entrada en `PROMPTS_LLM.md` (T056); no se deja todo para el final.
- Los commits siguen la constitución: las correcciones de la spec van en commits propios y antes del código (T045).
- Si una prueba de equivalencia falla, se reporta la semilla y se corrige el código, nunca el oráculo.
