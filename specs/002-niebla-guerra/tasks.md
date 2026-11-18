---
description: "Lista de tareas de Niebla de guerra e «ir a»"
---

# Tasks: Niebla de guerra e «ir a»

**Input**: Design documents from `specs/002-niebla-guerra/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: se piden de forma explícita (constitución, "Flujo y definición de hecho": cada FR tiene una prueba que lo cita; spec SC-001; enunciado §2.5). En cada fase las pruebas se escriben **antes** del código que las hace pasar y deben fallar primero. Cada prueba cita en su docstring y en el mensaje de cada `assert` el FR-xxx, SC-xxx o escenario (US*n* *m*, Apéndice B) que ejerce.

**Organization**: las tareas se agrupan por historia de usuario (US1 a US6 de spec.md), en orden de prioridad. Ninguna tarea queda sin requisito: cada una dice al final qué cubre.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (otro archivo y sin dependencias pendientes).
- **[Story]**: historia a la que pertenece (US1 a US6).
- **Depende de**: tareas que deben estar terminadas antes.

## Path Conventions

Proyecto único (plan.md, "Project Structure"): código en `cripta/`, pruebas en
`pruebas/` (cada una es un script `py -m pruebas.<nombre>` con `assert`, que se
registra en `PRUEBAS` de `pruebas/ejecutar_pruebas.py` en la misma tarea que la
crea), mediciones en `cripta/controlador/bench/`. Las pruebas pueden usar
estructuras de Python; el código de `cripta/` no puede usar dict, set, list,
heapq, bisect, collections ni bibliotecas de grafos (`prueba_reglas`).

---

## Phase 1: Setup (línea base y apoyo de pruebas)

**Purpose**: línea base verde, el fixture del formato anterior (antes de cambiar el formato) y las ayudas que usan las pruebas de todas las historias.

- [X] T001 Confirmar la línea base en la rama `002-niebla-guerra` antes de cambiar código: `git pull` de `main` si hay cambios, `py pruebas/ejecutar_pruebas.py` completa y en verde, y anotar el total (hoy 55) en esta tarea. Si falla algo, se investiga antes de seguir. Cubre: base de SC-001 (sin regresiones).
  **Hecho (15/11/2026):** `main` sin cambios nuevos; suite completa en verde, **55** pruebas, en 65 s.
- [X] T002 Con el código **actual** (`FORMATO_VERSION = 2`), antes de T041, agregar a `pruebas/generar_guardado_formato_anterior.py` un **modo propio** para el guardado de la versión 2 (por ejemplo, el argumento `--formato-2` o una función `generar_formato_2()`) que genere `pruebas/datos/niebla/guardado_formato_2.bin`: inicia una partida sin conexión sobre `datos_offline/` (cripta elegida por cantidad de salas, la más chica, sin ids en el código), da dos movimientos y la guarda con `PartidaBinaria.guardar`. Ese modo tiene **su propia comprobación** (`FORMATO_VERSION == 2`; si no, sale con un mensaje y no regenera el `.bin` confirmado). El camino de la versión 1 (`FORMATO_ANTERIOR = 1`, su comprobación y su fixture de `terreno_cazador`) **no se toca**. Confirmar en git el `.bin` y el script. Cubre: FR-013 (fixture de US5 escenario 4).
  **Hecho:** `py -m pruebas.generar_guardado_formato_anterior --formato-2` generó `pruebas/datos/niebla/guardado_formato_2.bin` (8047 bytes, la cripta de 20 salas, 2 movimientos, semilla 20261115); el modo de la versión 1 sigue negándose a correr con el formato 2.
- [X] T003 [P] Crear `pruebas/apoyo_niebla.py` sobre `pruebas/apoyo_terreno.py`:
  - constructores de criptas sintéticas con ids enteros, costos, puertas cerradas con llave, cierre automático, salidas de un solo sentido, enemigos dormidos, trampas y una antorcha en el inventario;
  - `partida_sobre(descripcion, semilla)` con Diario conectado, y `aplicar(partida, *acciones)`;
  - `huella_conocimiento(partida)`: tupla de `(id, conocimiento)` por sala y `(id, dirección, recordada)` por salida, ordenada por id, armada recorriendo el mundo desde la prueba;
  - `VistaRegistradora` y `RegistroEnMemoria` (implementa `RegistroAcciones` y guarda las líneas, comentarios incluidos) para las pruebas del Controlador;
  - `secuencias_sc003(semilla, cantidad)`: el generador de secuencias de 1 a 5 acciones (movimientos con y sin antorcha, abrir puertas, esperar cierres) que comparten T038 y T039.

  Cubre: soporte de las pruebas de FR-001 a FR-035, SC-002, SC-003 y SC-007.
- [X] T004 [P] Crear `pruebas/oraculo_ir_a.py`: Bellman-Ford **hacia adelante** desde la sala del jugador, sin heap, sin sellos y sin caché, sobre el subgrafo conocido (cara `u → v` usable si `u` y `v` están exploradas y la cara está recordada abierta), con costo 100 para salidas sin costo declarado y desempate por (costo total, id numérico de la vecina del primer paso, dirección N, S, E, O). Devuelve la dirección del primer paso o `None`. Con autopruebas: rutas de igual costo hacia 9 y 10 dan 9; una cara "no observada" no se usa. Cubre: base de SC-006 (FR-019, FR-020, FR-021).
- [X] T005 [P] [EQUIPO] Confirmar con Diego (autor de 001 y 003) que las teclas M (mapa conocido) e I (interrumpir el viaje) de esta feature y la H reservada para la feature 004 no chocan con las teclas de 001 y 003. Anotar la respuesta en esta tarea y en `contracts/vista.md`. El número de formato no se consulta: 002 y 004 son del mismo integrante, que fija `FORMATO_VERSION = 3` para 002 y 4 para 004 (`contracts/partida-binaria.md`). Cubre: FR-017.
  **Avance (15/11/2026):** Pablo revisó `cripta/vista`: M, I y H no se usan en ninguna pantalla (en la partida se usan A, C, G, L, O, P, Q, R, S, U y V; B, N y X en el menú). **Falta solo la confirmación de Diego** de que no planea usarlas; la implementación sigue sin esperar.
  **Hecha (17/11/2026, con Diego):** a pedido de Diego se revisaron las teclas en los controladores de las ramas del equipo: `git grep -n -E "key\.(M|I|H)\b" origin/main origin/003-resolubilidad origin/004-linea-tiempo -- cripta` solo encuentra M, I y H en 004-linea-tiempo (`cripta/vista/pantallaJuego.py` líneas 361, 365 y 368); main y 003-resolubilidad no las usan. Diego está de acuerdo: M, I y H no chocan con las teclas de 001 y 003.

**Checkpoint**: suite en verde con el total de T001; fixture de la versión 2 confirmado.

---

## Phase 2: Foundational (conocimiento como estado reversible)

**Purpose**: los campos del conocimiento, el registro de conocidas y su reversión por el Mutador, que usan todas las historias.

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase.

### Tests (escribir primero; deben fallar)

- [X] T006 Crear `pruebas/prueba_niebla_registro.py` (citando FR-011, FR-016, FR-033):
  - una `Sala` y una `Salida` nuevas tienen `conocimiento == DESCONOCIDA` (0) y `recordada == NO_OBSERVADA` (0);
  - `RegistroConocidas.agregar` agrega al final y `quitar_ultima(sala)` quita la última; `quitar_ultima` con otra sala lanza `ErrorCripta`;
  - `ordenadas_por_id()` con ids 10, 9, 2, 100 devuelve 2, 9, 10, 100 (comparación numérica) y no cambia el orden del registro;
  - con un `Diario` conectado, `mutador.conocida_agregar(registro, sala)` y `mutador.asignar(sala, "conocimiento", AVISTADA)` dentro de un intervalo, y `diario.deshacer`, dejan el registro vacío y la sala `DESCONOCIDA`.

  Registrar en `pruebas/ejecutar_pruebas.py`. Depende de: T001.

### Implementation

- [X] T007 [P] Crear `cripta/modelo/mundo/conocimiento.py` con las constantes `DESCONOCIDA = 0`, `AVISTADA = 1`, `EXPLORADA = 2`, `NO_OBSERVADA = 0`, `ABIERTA = 1`, `CERRADA = 2` y la clase `RegistroConocidas` sobre una `ListaDoble`: `agregar(sala)` O(1), `quitar_ultima(sala)` O(1) que verifica que la última sea `sala` (si no, `ErrorCripta`), `__iter__`, `__len__`, `ordenadas_por_id()` (copia a una `ListaEnlazada` de claves comparables por `sala.id` y usa `ordenamiento.mezcla`, O(k log k)) y `vaciar()`. Docstrings con la justificación de research R4. Cubre: FR-016, FR-033. Depende de: T006.
- [X] T008 [P] En `cripta/modelo/mundo/sala.py` agregar `conocimiento` (por omisión `DESCONOCIDA`) y en `cripta/modelo/mundo/salida.py` agregar `recordada` (por omisión `NO_OBSERVADA`), ambos atributos simples que el Diario puede restaurar con `setattr`. Documentar que `cerrada` sigue siendo el estado real (infraestructura, FR-015). Cubre: FR-001, FR-006, FR-007. Depende de: T006.
- [X] T009 En `cripta/modelo/mundo/mundo.py` agregar `conocidas`: en `__init__`, un `RegistroConocidas()` nuevo por instancia; como valor por omisión **de clase**, `None` (nunca un objeto mutable compartido entre instancias), para los `Mundo` que crea la carga con `__new__`, que reciben el suyo en T042 y `_sello_ruta` con `nuevo_sello_ruta()`, como `_sello_mapa` de 001. Cubre: FR-016, FR-033. Depende de: T007.
- [X] T010 En `cripta/modelo/nucleo/mutador.py` agregar el tipo `CONOCIDA_AGREGAR` y el método `conocida_agregar(registro, sala)`; en `cripta/modelo/nucleo/diario.py`, su inverso `objetivo.quitar_ultima(nuevo)`. Cubre: FR-011, FR-034. Depende de: T007. T006 pasa.

**Checkpoint**: `prueba_niebla_registro` en verde; la suite sigue en verde.

---

## Phase 3: User Story 1 - Ver solo lo que el jugador conoce (Priority: P1) 🎯 MVP

**Goal**: explorada/avistada/desconocida desde el instante 0, al entrar y al volver; la vista y el panel M muestran solo el conocimiento.

**Independent Test**: criptas sintéticas sin vista ni red; mover al jugador y comparar los estados y el DTO del mapa (spec US1).

### Tests for User Story 1 (escribir primero; deben fallar)

- [X] T011 [P] [US1] Crear `pruebas/prueba_niebla_conocimiento.py`:
  - US1 escenario 1 (FR-001, FR-002, FR-003, FR-016): en el instante 0 la inicial está explorada, sus destinos avistados, y ninguna otra sala tiene `conocimiento` distinto de `DESCONOCIDA`; el registro de conocidas tiene exactamente esas salas;
  - US1 escenario 2 (FR-001, FR-004): entrar a una avistada la explora y aviva sus destinos desconocidos;
  - US1 escenario 3 (FR-004): volver a una explorada no cambia ninguna sala ni agrega registros al Diario por conocimiento;
  - una cripta de dos salas conectadas en ambos sentidos no agrega dos veces la misma sala al registro (invariante de data-model.md).

  Registrar en `pruebas/ejecutar_pruebas.py`. Depende de: T003, T010.
- [X] T012 [P] [US1] Crear `pruebas/prueba_vista_mapa.py` (primera parte; T034 la amplía):
  - US1 escenario 4 (FR-002, FR-014, FR-015, SC-002): con salas desconocidas y avistadas cuyo nombre es una marca única (`"MARCA-<id>"`), y su contenido ya precargado, ningún texto del `EstadoVista` ni del `MapaConocidoVisible` contiene una marca de una sala no explorada; las avistadas aparecen con `nombre is None` y sin salidas;
  - US1 escenario 5 (FR-016, FR-017): el verbo `alternar_mapa` abre y cierra el panel, no cambia `reloj`, no llama a `registrar_accion` del `RegistroEnMemoria` y no agrega intervalos al Diario;
  - el mapa lista las salas por id numérico y las salidas en N, S, E, O (FR-016);
  - FR-017: en `PantallaJuego`, la tecla M solo encola `Comando("alternar_mapa")` y ninguna otra tecla de la partida lo encola.

  Registrar en `pruebas/ejecutar_pruebas.py`. Depende de: T003, T010.

### Implementation for User Story 1

- [X] T013 [US1] En `cripta/modelo/mundo/conocimiento.py` agregar `ConocimientoJugador(mundo, mutador)` con `iniciar(sala_inicial)` (explora la inicial y aviva sus destinos) y `entrar(sala)` (explora la sala si no lo estaba y aviva sus destinos desconocidos), usando `Salida.sala_destino` (sin `Mundo.sala(id)`), asignando por el Mutador **solo si el valor cambia** y llamando a `mutador.conocida_agregar` cuando una sala deja de ser `DESCONOCIDA`. Consultas `estado(sala)` y `recuerdo(salida)` O(1). Cubre: FR-001 a FR-004, FR-032. Depende de: T008, T009, T010.
- [X] T014 [US1] En `cripta/modelo/nucleo/partida.py`: crear `self.conocimiento` en `iniciar()` después de `mundo.enlazar()` y llamar a `iniciar(sala inicial)` con el Mutador en pausa (como hoy); en `_mover_jugador`, llamar a `self.conocimiento.entrar(destino)` inmediatamente después de asignar la sala del jugador y antes de trampas y enemigos (research R3). Cubre: FR-001, FR-003, FR-004, FR-010. Depende de: T013. T011 pasa.
- [X] T015 [P] [US1] En `cripta/vista/estadoVista.py` agregar los DTOs congelados `SalidaConocidaVisible(direccion, destino, costo, estado)` con estado `"abierta"`, `"cerrada"` o `"no observada"`, `SalaConocidaVisible(id, nombre, explorada, actual, salidas)` ("`nombre` (None si avistada)", salidas vacías si avistada) y `MapaConocidoVisible(salas, cantidad_exploradas, cantidad_avistadas)`, y `EstadoVista.mapa: Optional[MapaConocidoVisible] = None`. Cubre: FR-002, FR-014, FR-016. Depende de: T010.
- [X] T016 [US1] En `cripta/controlador/constructorEstadoVista.py` agregar `construir(..., mapa_abierto=False)`: si está abierto, arma `MapaConocidoVisible` desde `partida.mundo.conocidas.ordenadas_por_id()`, leyendo de cada sala solo lo que su `conocimiento` permite y de cada salida solo `recordada` y `costo`; nunca `cerrada` ni el contenido (FR-014, FR-015). Cubre: FR-002, FR-014, FR-015, FR-016. Depende de: T014, T015.
- [X] T017 [US1] En `cripta/controlador/controladorJuego.py` agregar el verbo de sesión `alternar_mapa` (estado `_mapa_abierto` del Controlador, no del Modelo; no va al log ni gasta reloj) y pasarlo al Constructor en `_mostrar_estado_actual`. Cubre: FR-016, FR-017. Depende de: T016.
- [X] T018 [US1] En `cripta/vista/pantallaJuego.py` asignar **M** a `Comando("alternar_mapa")`, y en `cripta/vista/hudJuego.py` dibujar el panel con el formato de `contracts/vista.md` (exploradas con salidas, costo y estado recordado; avistadas como `<id>  ?  (avistada)`), partiendo las filas con `partirLineas` y desplazándolo con RePág/AvPág como el panel de V (D80). Cubre: FR-016, FR-017. Depende de: T017. T012 pasa.

**Checkpoint**: US1 funciona sola: niebla y panel M sin «ir a».

---

## Phase 4: User Story 2 - Recordar el estado de las puertas (Priority: P1)

**Goal**: observar las caras al entrar y al cambiar con el jugador presente; el mapa recuerda la última observación.

**Independent Test**: puerta con cierre automático que se cierra con el jugador lejos (spec US2).

### Tests for User Story 2 (escribir primero; deben fallar)

- [X] T019 [P] [US2] Crear `pruebas/prueba_niebla_puertas.py`:
  - US2 escenario 1 (FR-005, FR-006): abrir con llave y un cierre automático con el jugador en una de las dos salas actualizan `recordada` de las dos caras;
  - US2 escenario 2 (FR-006): el cierre automático con el jugador lejos deja la cara recordada abierta;
  - US2 escenario 3 (FR-005, FR-006): al entrar a cualquiera de las dos salas, el recuerdo pasa a cerrada;
  - FR-005: estando en A se observan también las caras de un solo sentido que entran a A (`A.entrantes`);
  - FR-007: una salida de una sala explorada cuya puerta nunca se observó vale `NO_OBSERVADA`;
  - caso borde de caras con estados distintos (FR-005, FR-021): cada cara guarda su propio recuerdo;
  - FR-014 (sala actual): si se fuerza `cerrada` de una salida de la sala actual sin pasar por `cambiar_puerta` (de modo que difiera de `recordada`), `SalidaVisible.estado` del `EstadoVista` sigue al recuerdo y no al estado real;
  - revisión del AST de `cripta/`: `cerrada` solo se asigna en `Partida.cambiar_puerta`, en el constructor de `Salida`, en `Diario._revertir` (vía `setattr`) y en la carga de `partidaBinaria` (plan.md, "Riesgos").

  Registrar en `pruebas/ejecutar_pruebas.py`. Depende de: T003, T014.

### Implementation for User Story 2

- [X] T020 [US2] En `cripta/modelo/mundo/conocimiento.py` agregar `observar_cara(salida)` (copia `ABIERTA` o `CERRADA` según `cerrada`, por el Mutador, solo si cambia) y `observar_sala(sala)` (todas las caras de `sala.salidas` y de `sala.entrantes`), y llamarla desde `iniciar` y `entrar` (research R3). Cubre: FR-002, FR-005, FR-006. Depende de: T013.
- [X] T021 [US2] En `cripta/modelo/nucleo/partida.py` agregar `cambiar_puerta(salida, cerrada)`: asigna por el Mutador y, si `salida.origen` o `salida.sala_destino` es la sala del jugador (comparando `id` con `jugador.sala`), llama a `conocimiento.observar_cara(salida)`; `_abrir_puerta` la usa. En `cripta/modelo/reloj/eventos.py`, `EventoCierrePuerta.ejecutar` la usa en vez de `mutador.asignar(salida, "cerrada", True)`. Cubre: FR-005, FR-006. Depende de: T020. T019 pasa.
- [X] T022 [US2] En `cripta/controlador/constructorEstadoVista.py`, `_salida_visible` de la sala actual arma el estado desde `recordada` (igual al real porque la sala del jugador está observada) en vez de `cerrada` (contracts/vista.md, "Sala actual"). Ajustar `prueba_vista_costos` si compara con `cerrada`. Cubre: FR-014. Depende de: T021.

**Checkpoint**: US1 y US2 en verde; la suite completa sigue en verde.

---

## Phase 5: User Story 3 - Viajar con «ir a» a una sala explorada (Priority: P1)

**Goal**: orden validada, ruta de costo mínimo sobre el conocimiento, un paso por vuelta, motivos de detención, log con comentario.

**Independent Test**: criptas sintéticas sin vista ni red; secuencia de movimientos, tiempo, motivo y líneas del log (spec US3).

### Tests for User Story 3 (escribir primero; deben fallar)

- [X] T023 [P] [US3] Crear `pruebas/prueba_ir_a.py` (un caso por escenario, con su id en el nombre de la función):
  - **Apéndice B 1** / US3 escenario 1 (FR-018): «ir a» hacia una avistada, una desconocida y un id inexistente se rechaza con el mismo mensaje, sin mover, sin cambiar `reloj` y sin líneas en el registro;
  - **Apéndice B 2** / US3 escenario 2 (FR-005, FR-021, FR-024, FR-025): una cara recordada abierta y cerrada en realidad en la ruta; al llegar a su sala el recuerdo se actualiza y la ruta se recalcula: con otra ruta conocida sigue; sin otra, se detiene con "sin ruta conocida" y `reloj` no avanza después del último paso;
  - **Apéndice B 3** / US3 escenario 3 (FR-024, FR-025): la ruta entra a una sala con enemigos dormidos; se activan (P1 §2.4) y el viaje se detiene con "enemigos en la sala";
  - US3 escenarios 4 y 11 (FR-020, FR-030), **con un mismo armado**: dos rutas de igual costo cuyos primeros pasos van a las vecinas 9 y 10; el primer paso va a la 9 (menor id, comparado como número y no como texto) y la elección se repite igual en dos ejecuciones;
  - US3 escenario 5 (FR-019): una salida sin costo declarado cuenta 100 frente a otra de 30;
  - US3 escenario 6 (FR-018, FR-022): la única ruta pasa por una puerta recordada cerrada con la llave en el inventario: rechazo "sin ruta conocida" sin abrir nada;
  - US3 escenario 7 (FR-023): cada paso consume el mismo tiempo y procesa los mismos eventos que el `MOVER` a mano (se compara contra una partida gemela movida a mano);
  - US3 escenario 8 (FR-024, FR-025): trampa, veneno activo y ataque en el camino detienen con "daño recibido" (clarificación 2);
  - US3 escenario 9 (FR-024, FR-025): llegada;
  - casos borde (FR-018, FR-024): «ir a» a la sala actual; enemigo errante que llega sin dañar no detiene (clarificación 3); salida con llave_salida termina la partida con "partida terminada"; muerte durante el viaje;
  - **Controlador** (con `VistaRegistradora` y `RegistroEnMemoria`; escritas antes de T031 y en rojo):
    - FR-025: un viaje completo termina con el mensaje "Viaje detenido: llegada." y `EstadoVista.viaje` es `None` al final;
    - FR-028: `interrumpir` detiene el viaje con "interrumpido";
    - FR-028 (research R6): un comando que cambia la partida (una acción, `guardar`, `cargar` o `salir`) detiene el viaje con "interrumpido" y después se procesa; un comando de presentación (`alternar_mapa`, `inventario_siguiente`, `inventario_anterior`, `ordenar_inventario`) no lo detiene y el viaje sigue en la vuelta siguiente;
    - FR-023: `ControladorMenu` entrega `None` a la partida con un viaje en curso y el viaje avanza un paso por vuelta.

  Registrar en `pruebas/ejecutar_pruebas.py`. Depende de: T003, T021.
- [X] T024 [P] [US3] Crear `pruebas/prueba_ir_a_equivalencia.py` (SC-006; FR-019, FR-020, FR-021): ≥ 1000 pares con `random.Random` de semilla fija sobre criptas sintéticas con recuerdos al azar (abiertos, cerrados, no observados), salas exploradas y avistadas al azar y empates forzados; el primer paso de `BuscadorRuta` coincide con el de `pruebas/oraculo_ir_a.py` en todos. Además (SC-002, FR-015, FR-021; research R10), en esos mismos pares la búsqueda se corre **instrumentada**: la prueba reemplaza por envoltorios que anotan cada lectura los accesos que usa el buscador (`conocimiento` de cada sala que toca, `recordada` de cada cara que recorre) y hace que leer `cerrada` o llamar a `Mundo.sala` falle; comprueba que toda sala leída como transitable estaba `EXPLORADA` y toda cara recorrida estaba recordada `ABIERTA`. Registrar en `pruebas/ejecutar_pruebas.py`. Depende de: T004, T020.
- [X] T025 [P] [US3] Crear `pruebas/prueba_replay_ir_a.py`:
  - US3 escenario 10 (FR-026): una orden de tres pasos deja `# IR_A <id>` y luego tres `MOVER` en `partida.log` (con `RegistroArchivo` en una carpeta temporal); una orden rechazada no escribe nada;
  - FR-027: `RegistroArchivo.leer()` salta las líneas `#`; un log sin comentarios se lee igual que antes;
  - SC-007 (FR-027): 20 partidas con viajes, semillas fijas, reproducidas con el camino de `--replay` sin Vista, terminan con el mismo estado final y la misma `huella_conocimiento`.

  Registrar en `pruebas/ejecutar_pruebas.py`. Depende de: T003.

### Implementation for User Story 3

- [X] T026 [P] [US3] En `cripta/modelo/mundo/sala.py` agregar los campos de búsqueda de «ir a» `_sello_ruta`, `_costo_ruta`, `_paso_ruta`, `_fijada_ruta` con un método `anotar_ruta(...)`, separados de los del mapa del cazador (research R5); no son estado reversible. Cubre: FR-031. Depende de: T009.
- [X] T027 [US3] Crear `cripta/modelo/mundo/buscadorRuta.py` con `EntradaRuta(costo, paso, sala)` ordenada por `(costo, paso, sala.id)` y `BuscadorRuta(mundo).primer_paso(origen, destino) -> Optional[Salida]`: Dijkstra hacia adelante con `HeapMinimo`, eliminación perezosa y sello nuevo por búsqueda; recorre una cara `u → v` solo si `u` y `v` están `EXPLORADA` y la cara está recordada `ABIERTA`; clave de primer paso `id_vecina * 4 + índice_dirección`; se detiene al fijar `destino`; nunca lee `cerrada`. Expone `salas_fijadas_ultima`. Cubre: FR-019, FR-020, FR-021, FR-022, FR-030, FR-031. Depende de: T026. T024 pasa.
- [X] T028 [P] [US3] En `cripta/modelo/nucleo/resultadoAccion.py` agregar `entro_con_enemigos` y `dano_recibido` (por omisión `False`). En `cripta/modelo/nucleo/partida.py`, limpiarlos al empezar `aplicar_accion`; en `_mover_jugador`, anotar `entro_con_enemigos` si la sala de destino tiene activos o dormidos **antes** de activarlos; en `danar`, anotar `dano_recibido` si el actor es el jugador; copiarlos al `ResultadoAccion`. No son estado del juego (no se guardan ni se revierten). Cubre: FR-024. Depende de: T014.
- [X] T029 [US3] Crear `cripta/modelo/nucleo/viajeIrA.py` con los motivos (`LLEGADA` "llegada", `ENEMIGOS` "enemigos en la sala", `DANO` "daño recibido", `SIN_RUTA` "sin ruta conocida", `FIN` "partida terminada", `PERGAMINO` "pergamino de retroceso", `INTERRUMPIDO` "interrumpido") y la clase `ViajeIrA(destino)` con `pasos`, `motivo` y `evaluar(resultado, partida)` según data-model.md. En `cripta/modelo/nucleo/partida.py` agregar `validar_ir_a(id_sala) -> Optional[str]` (mensajes de data-model.md, el mismo para inexistente y no explorada) y `primer_paso_ir_a(destino) -> Optional[Salida]` (usa `BuscadorRuta` desde la sala del jugador). Cubre: FR-018, FR-024, FR-025. Depende de: T027, T028.
- [X] T030 [P] [US3] En `cripta/modelo/puertos/registroAcciones.py` agregar `registrar_comentario(texto)` al puerto; en `cripta/adaptadores/registroArchivo.py` escribir `# ` + texto en modo anexado y hacer que `leer()` salte las líneas que empiezan con `#` (contracts/registro.md). Cubre: FR-026, FR-027. Depende de: T001. T025 (primeras dos viñetas) pasa.
- [X] T031 [US3] En `cripta/controlador/controladorJuego.py`:
  - verbo `ir_a <id>`: valida con `partida.validar_ir_a`; si rechaza, `mostrar_error` y nada más; si acepta, crea el `ViajeIrA`, escribe `IR_A <id>` con `registrar_comentario`, cierra el panel y da el primer paso;
  - `procesar(None)` con viaje en curso da **un** paso: `primer_paso_ir_a`; sin paso → motivo `SIN_RUTA` sin aplicar nada; con paso → `aplicar_accion(Mover(dir))`, `registrar_accion`, `evaluar`;
  - verbo `interrumpir` (motivo `INTERRUMPIDO`); con viaje en curso, solo los comandos que **cambian la partida** (las acciones que traduce `TraductorComandos`, `guardar`, `cargar` y `salir`) detienen el viaje con `INTERRUMPIDO` y luego se procesan; los de **presentación** (`alternar_mapa`, `inventario_siguiente`, `inventario_anterior`, `ordenar_inventario`, `ver_resolubilidad`) se procesan sin detenerlo (research R6; L es local de la Vista y no llega al Controlador);
  - al detenerse, `mostrar_mensajes("Viaje detenido: <motivo>.")`.

  Cubre: FR-018, FR-023 a FR-026, FR-028. Depende de: T029, T030.
- [X] T032 [US3] En `cripta/controlador/controladorMenu.py`, `procesar` entrega `None` a la partida cuando `self._juego` tiene un viaje en curso (hoy los descarta antes). Cubre: FR-023. Depende de: T031. T023 y T025 pasan.
- [X] T033 [P] [US3] En `cripta/vista/estadoVista.py` agregar `ViajeVisible(destino_id, destino_nombre, pasos)` y `EstadoVista.viaje: Optional[ViajeVisible] = None`; en `cripta/controlador/constructorEstadoVista.py`, armarlo desde el viaje en curso. Cubre: FR-025. Depende de: T031.
- [X] T034 [US3] Prueba de la Vista, escrita antes de T035 y en rojo: ampliar `pruebas/prueba_vista_mapa.py` con (FR-035)
  - con el panel M abierto, ↑/↓ mueven el cursor solo entre las salas exploradas y saltan las avistadas;
  - con el panel abierto, las flechas no encolan `mover`;
  - Enter encola `Comando("ir_a", (id,))` con el id de la sala bajo el cursor; sobre la sala actual o sobre una sin ruta, el Controlador responde con el rechazo de FR-018.

  Las pruebas del Controlador (mensaje de detención, `interrumpir`, comandos que detienen o no el viaje, `None` hacia la partida) están en T023. Depende de: T012, T032.
- [X] T035 [US3] En `cripta/vista/pantallaJuego.py`, con el panel M abierto: ↑/↓ mueven un cursor que salta las avistadas, Enter encola `Comando("ir_a", (id,))`, y las flechas no mueven al jugador; **I** encola `Comando("interrumpir")`. En `cripta/vista/hudJuego.py`, la línea "Viajando a <id> <nombre> — paso <n> (I para detener)" y la marca del cursor en el panel. Cubre: FR-028, FR-035. Depende de: T018, T033, T034. T034 pasa.
- [X] T055 [US3] FR-036 (enmienda de la spec `5d32f60`, agregada durante la implementación): pausa de presentación de `PAUSA_PASO_VIAJE` (0,15 s al principio; 0,5 s desde T057) de tiempo real entre pasos de «ir a» en la ventana. La decide `ControladorJuego` con un `reloj_real` inyectado (el mismo `time.perf_counter` que `ControladorMenu` ya le pasa al replay); sin reloj (pruebas sin vista, `--replay`, `--bench`) no hay pausa. El Modelo y el reloj del juego no cambian. Pruebas primero en `pruebas/prueba_ir_a.py` (`caso_fr036_pausa_entre_pasos`, `caso_fr036_pausa_no_cambia_el_juego`; US3 escenario 12). Cubre: FR-036. Depende de: T031, T032.
- [X] T057 [US3] FR-036 (enmienda de la spec `c470bae`, por la prueba en la ventana): `PAUSA_PASO_VIAJE` pasa de 0,15 a 0,5 s porque con 0,15 s no alcanzaba el tiempo para apretar I o P a mitad de un viaje. `prueba_ir_a` (caso_fr036_pausa_entre_pasos) ajustada: sin paso a 0,4 s y con paso a 0,51 s; contracts/vista.md y D85 al día. Cubre: FR-036. Depende de: T055.
- [X] T056 [US3] FR-037 (enmienda de la spec `751bc3b`, por la prueba en la ventana): con el panel del mapa abierto, R, A, U, Q y S abrían su selección encima del mapa y quedaban dos cursores. Ahora `PantallaJuego._entrar_modo_objetivo` encola `alternar_mapa` y deja la selección pendiente en `VistaArcade.pedir_objetivo`; la `PantallaJuego` siguiente, que llega sin mapa, la abre en `on_show_view`. Prueba primero en `pruebas/prueba_vista_mapa.py` (`caso_us1_e6_seleccion_cierra_el_mapa`, US1 escenario 6, con S, U y Q, el Controlador real y ESC). Cubre: FR-037. Depende de: T018, T035.
- [X] T058 [US3] FR-035 (enmienda de la spec `dc54119`, por la prueba en la ventana): con el panel del mapa abierto y más filas de las que caben, la flecha movía el cursor pero la vista no lo seguía y la sala elegida quedaba fuera de la vista. Ahora `PantallaJuego._seguir_cursor_mapa`, después de cada flecha, desplaza el panel lo justo para que la fila del cursor (`HudJuego.fila_cursor_mapa`, la que empieza con `>`) quede visible, al bajar, al subir y al saltar avistadas; cambia el mismo desplazamiento de `VistaArcade` que usan RePág/AvPág, que siguen igual. Prueba primero en `pruebas/prueba_vista_mapa.py` (`caso_t058_la_vista_sigue_al_cursor`: 31 exploradas en un pasillo de 40, bajar hasta la última y subir hasta la primera con la fila del cursor siempre visible, y RePág/AvPág como antes); falló antes del arreglo (paso 8: cursor en la fila 23 con 0 a 21 visibles). Cubre: FR-035. Depende de: T034.

**Checkpoint**: US1, US2 y US3 en verde: MVP de la Parte II para esta feature (niebla + «ir a»).

---

## Phase 6: User Story 4 - Antorcha: explorar las salas vecinas (Priority: P2)

**Goal**: con la antorcha encendida al entrar, las vecinas quedan exploradas sin contenido, sin activar nada y con caras "no observada".

**Independent Test**: sala con vecinas con enemigos dormidos, trampa y puerta cerrada (spec US4).

### Tests for User Story 4 (escribir primero; deben fallar)

- [X] T036 [P] [US4] Crear `pruebas/prueba_niebla_antorcha.py`:
  - **Apéndice B 4** / US4 escenario 1 (FR-008, FR-009): con la antorcha encendida, entrar explora todas las vecinas por salidas abiertas y cerradas; sus enemigos siguen dormidos, sus trampas armadas y su contenido no llega al DTO;
  - US4 escenario 2 (FR-004, FR-008): los destinos desconocidos de las vecinas pasan a avistados;
  - US4 escenario 3 (FR-008): con la antorcha apagada solo se explora la sala;
  - US4 escenario 4 (FR-007, FR-009, FR-021; clarificación 1): las caras de una vecina explorada por la antorcha valen `NO_OBSERVADA` salvo las de la puerta compartida, y «ir a» no las usa;
  - casos borde (FR-008): encender la antorcha dentro de una sala no explora nada hasta la próxima entrada; si se apaga durante un viaje, los pasos siguientes exploran solo la sala.

  Registrar en `pruebas/ejecutar_pruebas.py`. Depende de: T003, T031.

### Implementation for User Story 4

- [X] T037 [US4] En `cripta/modelo/mundo/conocimiento.py`, `entrar(sala, antorcha)`: con `antorcha=True`, cada destino de `sala.salidas` (abierta o cerrada) pasa a `EXPLORADA` y sus destinos desconocidos a `AVISTADA`, sin observar sus caras ni tocar su contenido; registra solo lo que cambia. En `cripta/modelo/nucleo/partida.py`, `_mover_jugador` pasa `self.jugador.antorcha_encendida`. Cubre: FR-008, FR-009, FR-033. Depende de: T020. T036 pasa.

**Checkpoint**: US4 en verde sin romper US1 a US3.

---

## Phase 7: User Story 5 - Deshacer, guardar y reproducir el conocimiento (Priority: P2)

**Goal**: el pergamino revierte el conocimiento (también con un viaje en curso), el guardado lo conserva y un formato anterior se rechaza.

**Independent Test**: entrada con antorcha + pergamino; viaje + pergamino; guardar y cargar; cargar el fixture de la versión 2 (spec US5).

### Tests for User Story 5 (escribir primero; deben fallar)

- [X] T038 [P] [US5] Crear `pruebas/prueba_niebla_retroceso.py`:
  - **Apéndice B 5** / US5 escenario 1 (FR-010, FR-011): una entrada con antorcha que explora varias vecinas y el pergamino: `huella_conocimiento` vuelve a la de antes de entrar y el registro de conocidas también;
  - **Apéndice B 6** / US5 escenario 2 (FR-011, FR-024, FR-029): con un viaje en curso, el comando `pergamino` detiene el viaje al terminar el paso en curso con el motivo "pergamino de retroceso", revierte solo ese paso (sala, `reloj` y conocimiento del paso) y no hay más pasos con `procesar(None)`;
  - casos borde (FR-011): revertir la primera entrada a una sala la devuelve a avistada y sus destinos nuevos a desconocidos; revertir un movimiento a una sala ya explorada restaura solo los recuerdos de puertas; varios pergaminos seguidos revierten de a un paso;
  - SC-003 (FR-011): 1000 secuencias de 1 a 5 acciones con semilla fija (movimientos con y sin antorcha, abrir puertas, esperar cierres): aplicar y revertir con pergaminos devuelve la huella inicial;
  - FR-034: con un Diario conectado, cada cambio de `conocimiento`, `recordada` o del registro durante una acción queda registrado (se cuenta comparando la huella antes y después con los registros del intervalo);
  - FR-010 (la parte de "solo"): un cierre automático con el jugador lejos no cambia la huella del conocimiento ni agrega registros de conocimiento al intervalo, y revertir ese intervalo con el pergamino tampoco la cambia.

  Registrar en `pruebas/ejecutar_pruebas.py`. Depende de: T003, T031, T037.
- [X] T039 [P] [US5] Crear `pruebas/prueba_persistencia_niebla.py`:
  - US5 escenario 3 (FR-012): una partida con exploradas, avistadas y recuerdos desactualizados se guarda y se carga con `huella_conocimiento` idéntica, registro de conocidas con las mismas salas y `cargar_sala` con los mismos campos;
  - SC-003 (FR-012), segunda mitad: las **mismas 1000 secuencias** de T038 (misma semilla y mismo generador, compartido en `pruebas/apoyo_niebla.py`); en cada una se guarda y se carga en **un punto elegido con la semilla** (entre 0 y la cantidad de acciones de la secuencia) y la `huella_conocimiento` cargada es idéntica a la guardada;
  - **US5 escenario 4** (FR-013; clarificación 4): cargar `pruebas/datos/niebla/guardado_formato_2.bin` lanza `VersionIncompatible` con "se esperaba 3 y se encontró 2" y no crea partida; el Controlador lo muestra con `mostrar_error`;
  - un valor fuera de rango en `conocimiento` o `recordada` lanza `ErrorCripta`.

  Registrar en `pruebas/ejecutar_pruebas.py`. Depende de: T002, T003, T037.

### Implementation for User Story 5

- [X] T040 [US5] En `cripta/controlador/controladorJuego.py`, con un viaje en curso el comando `pergamino` detiene el viaje con el motivo `PERGAMINO` (no `INTERRUMPIDO`) y luego aplica `UsarPergamino` como siempre, que deshace solo el intervalo del último paso (research R6). Cubre: FR-029. Depende de: T031. T038 (escenario Apéndice B 6) pasa.
- [X] T041 [US5] En `cripta/adaptadores/partidaBinaria.py`: `FORMATO_VERSION = 3`; escribir `uentero32` con `conocimiento` por sala y `uentero32` con `recordada` por salida; leerlos en la carga completa y en `cargar_sala`, con `ErrorCripta` si están fuera de rango; actualizar el docstring del formato (contracts/partida-binaria.md). Depende de: T002 (el fixture ya existe), T008. Cubre: FR-012, FR-013.
- [X] T042 [US5] En `cripta/modelo/nucleo/partida.py`, `reconstruir_tras_cargar()` asigna a `mundo.conocidas` un `RegistroConocidas()` **nuevo** (no vacía uno existente, que podría ser de otro `Mundo`) y lo reconstruye con una pasada O(salas) agregando las salas con `conocimiento != DESCONOCIDA` (sin pasar por el Mutador), y crea `self.conocimiento`. Cubre: FR-012, FR-016. Depende de: T041. T039 pasa.
  **Avance (US1):** la parte del modelo se adelantó en US1 porque sin ella una partida cargada no tenía `conocimiento` y fallaban `prueba_controlador`, `prueba_replay_menu`, `prueba_cazador_equivalencia` y `prueba_persistencia_cazador`. Con T041 el conocimiento se guarda y se lee; T042 queda completa.

**Checkpoint**: US5 en verde; el pergamino, el guardado y el replay respetan el conocimiento.

---

## Phase 8: User Story 6 - Consultas y rutas rápidas (Priority: P3)

**Goal**: evidencia medida de FR-031 a FR-033 con la alternativa descartada de cada decisión.

**Independent Test**: `--bench` con la cripta de referencia explorada y mapas de tamaños crecientes (spec US6).

### Tests for User Story 6 (escribir primero; deben fallar)

- [X] T043 [P] [US6] Crear `pruebas/prueba_rendimiento_ir_a.py` (FR-031, SC-004; US6 escenario 1): con la cripta de referencia de `datos_offline/` (la de más salas, elegida en ejecución) totalmente explorada y con recuerdos iguales al estado real, el peor paso de `BuscadorRuta.primer_paso` sobre ≥ 200 pares con semilla fija, tomando el mínimo de 5 repeticiones por par, es < 5 ms; al fallar, el mensaje dice la cifra medida. Registrar en `pruebas/ejecutar_pruebas.py`. Depende de: T027.
- [X] T044 [P] [US6] Crear `pruebas/prueba_conteo_niebla.py` (FR-032, FR-033, SC-005; US6 escenario 2), con conteos y no tiempos:
  - consultar `estado` y `recuerdo` no busca ni recorre nada: con mapas de 25 y 1200 conocidas, la prueba reemplaza `Mundo.sala` y el iterador de `RegistroConocidas` (`__iter__`) por versiones que lanzan `AssertionError` si se llaman, y después consulta `estado` de cada sala y `recuerdo` de cada salida sin que fallen;
  - una entrada con antorcha que revela 4 salas registra la misma cantidad de entradas en el Diario con mapas conocidos de 25, 100, 300 y 1200 salas;
  - deshacer esa entrada procesa exactamente esos registros.

  Registrar en `pruebas/ejecutar_pruebas.py`. Depende de: T037.

### Implementation for User Story 6

- [X] T045 [P] [US6] Crear `cripta/controlador/bench/alternativasNiebla.py` (solo para medir, con estructuras propias): `RutaHaciaAtras` (Dijkstra completo desde el destino por entrantes conocidas + fórmula del cazador, research R5), `ConsultaLineal` (busca la sala por id en el registro, R1) y `RegistroOrdenado` (inserción ordenada en `ListaEnlazada`, la orientación inicial del equipo, R4). Cubre: FR-031, FR-032, FR-033 (alternativas descartadas). Depende de: T027, T037.
- [X] T046 [US6] Crear `cripta/controlador/bench/benchNiebla.py` con `ejecutar(reporte, rapido)` y las cinco mediciones de research R11: (1) paso de «ir a» en la cripta de referencia y la malla de 1024 salas, recuerdos reales y todos abiertos, frente a `RutaHaciaAtras`, con criterio peor < 5 ms en la referencia; (2) consultas con 25, 100, 300 y 1200 conocidas frente a `ConsultaLineal`, criterio crecimiento ≤ 1,5 al multiplicar por 4; (3) exploración con antorcha que revela 4 salas frente a `RegistroOrdenado`, mismo criterio; (4) registros del Diario y tiempo de deshacer según las salas reveladas; (5) armar el panel con 300 y 1200 conocidas. La cripta de referencia se elige en ejecución por cantidad de salas (principio IV). Cubre: FR-031, FR-032, FR-033, SC-004, SC-005. Depende de: T045.
- [X] T047 [US6] Registrar `benchNiebla` en `cripta/controlador/bench/benchTodo.py` (después de `benchResolubilidad`); si `prueba_4_4` cuenta las tablas del bench, actualizar su total. Correr `py main.py --bench --rapido` y `py -m cripta.controlador.bench.benchNiebla`, y copiar las cifras a esta tarea para T049. Cubre: FR-031, SC-004, SC-005. Depende de: T046.
  **Cifras (`py -m cripta.controlador.bench.benchNiebla`, 15/11/2026, Python 3.14.5, equipo local):**
  - Paso de «ir a», peor/media (salas fijadas): referencia de 300 salas con recuerdos reales 0,140/0,102 ms (66) frente a 0,128/0,104 ms hacia atrás (75); referencia con todas abiertas 0,674/0,319 ms (148) frente a 0,651/0,590 ms (300); malla de 1024 salas 4,547/1,997 ms (522) frente a 5,677/3,746 ms (1024). Mismo primer paso en 299/299 pares en las tres. FR-031: PASA.
  - Consulta por campo: 0,060, 0,063, 0,068 y 0,087 µs con 25, 100, 300 y 1200 conocidas (crecimiento ×4: 1,05 y 1,28, PASA); búsqueda lineal: 0,47, 1,30, 3,42 y 12,95 µs.
  - Entrada con antorcha (4 reveladas), µs por entrada: 6,22, 6,09, 6,13 y 6,20 (crecimiento ×4: 0,98 y 1,01, PASA); inserción ordenada (incluye quitar las 4 después): 4,81, 15,50, 47,66 y 180,18.
  - Registros del Diario por entrada con antorcha: 4, 8, 12 y 16 con 1 a 4 salas reveladas; deshacer 1,6 a 3,8 µs.
  - Panel del mapa: 0,337 ms con 300 conocidas y 1,623 ms con 1200.
  - Nota de proceso: T043 y T044 pasaron al escribirlas, porque miden código hecho en T013, T027 y T037; no guiaron implementación nueva. `prueba_4_4` cuenta 5 tablas más.

**Checkpoint**: US6 en verde; cifras medidas disponibles para DECISIONES.md.

---

## Phase 9: Polish, documentación y cierre

- [X] T048 [P] Actualizar `README.md`: tabla de teclas de la partida con **M** (mapa conocido), **I** (interrumpir el viaje) y **H** reservada para la línea de tiempo (004); con el panel abierto, ↑/↓, RePág/AvPág y Enter; nota de que los guardados anteriores (formato 1 y 2) se reportan incompatibles con el formato **3**; comando de `benchNiebla`; total de pruebas nuevo. Cubre: FR-013, FR-017, FR-035.
  **Hecho:** tabla de teclas con M, I y H reservada; sección «Niebla de guerra e «ir a»»; formato 3; comando de benchNiebla; 67 pruebas.
- [X] T049 Agregar a `DECISIONES.md` (§7.1), después de `git pull` de `main` y con el siguiente número D libre (hoy D81), la sección "Niebla de guerra e «ir a»" enlazada a `specs/002-niebla-guerra/spec.md` y `specs/002-niebla-guerra/plan.md`, con una decisión por problema y su complejidad: conocimiento en campos (R1), cambios por el Mutador (R2), observación (R3), registro de conocidas (R4), buscador separado del cazador (R5), viaje por vuelta (R6), comentario del log (R7), teclas (R8) y formato 3 (R9). Debe decir **dónde cambió respecto de la orientación inicial del equipo** (el punto 3: inserción ordenada → registro en orden de descubrimiento + mezcla al abrir el panel) y **qué medición lo motivó** (18,6 µs frente a 0,9 µs con 300 conocidas en las mediciones previas, y la cifra definitiva de T047), y por qué no se comparte el buscador con el cazador (peor paso en la malla, cifras de T047). Cubre: FR-031, FR-032, FR-033 (evidencia, principio VI).
  **Hecho:** D81 a D88 y una fila nueva en el índice de DECISIONES.md, enlazadas a spec.md y plan.md; D83 explica el cambio del punto 3 con 18,6 frente a 0,9 µs (plan) y 180,18 frente a 6,20 µs con 1200 conocidas (T047).
- [X] T050 [P] Revisar que `contracts/partida-binaria.md`, `contracts/registro.md` y `contracts/vista.md` coinciden con lo implementado (versión 3, textos de mensajes, teclas confirmadas en T005); si algo cambió, corregir primero el contrato en un commit propio (principio VII). Cubre: FR-013, FR-016, FR-026.
  **Hecho:** partida-binaria.md y registro.md coinciden; vista.md se corrigió en su propio commit (`0f4e25f`): formato real del panel, línea de viaje, pausa de FR-036, motivo del pergamino y panel de Controles.
- [X] T051 Correr `py pruebas/prueba_reglas.py` sobre `cripta/`: sin dict, set, list, heapq, bisect, collections ni bibliotecas de grafos en el código nuevo; sin ids de criptas concretas (`prueba_sin_datos_concretos`). Cubre: FR-031, FR-032, FR-033 (principio I y IV aplicados a las estructuras de esta feature).
  **Hecho:** `prueba_reglas` en verde (140 archivos) y `prueba_sin_datos_concretos` en verde.
- [X] T052 Correr `py pruebas/ejecutar_pruebas.py` completa: todas en verde, con el total de T001 más las 12 pruebas nuevas de esta feature (`prueba_niebla_registro`, `prueba_niebla_conocimiento`, `prueba_vista_mapa`, `prueba_niebla_puertas`, `prueba_ir_a`, `prueba_ir_a_equivalencia`, `prueba_replay_ir_a`, `prueba_niebla_antorcha`, `prueba_niebla_retroceso`, `prueba_persistencia_niebla`, `prueba_rendimiento_ir_a`, `prueba_conteo_niebla`). Anotar el total en esta tarea y en el README. Cubre: SC-001.
  **Hecho:** 67 de 67 (55 de la línea base + 12 de esta feature), anotado en el README.
- [X] T053 Validación a mano con `py main.py --offline` según `quickstart.md` §3 (pasos 1 a 8) y §4, a 1024×720, anotando el resultado de cada paso en esta tarea. Cubre: FR-016, FR-025, FR-028, FR-029, FR-035; SC-001.
  **Hecha (2026-11-17, Pablo en la ventana):** mapa conocido, «ir a», detención por enemigos y puertas recordadas; la antorcha explora las vecinas con sus puertas "no observada" salvo la compartida; P durante un viaje retrocede un solo paso con "pergamino de retroceso" y el viaje no sigue; guardar y cargar conserva el mapa con los estados recordados; con el mapa abierto, S lo cierra antes de "Soltar". Todo funciona.
- [X] T054 Registrar en `PROMPTS_LLM.md` cada prompt usado durante la implementación de esta feature (constitución, "Flujo y definición de hecho"). Cubre: SC-001 (definición de hecho).
  **Hecho:** entradas 156 a 165 de PROMPTS_LLM.md.

---

## Escenarios de aceptación → pruebas (SC-001)

| Escenario | Prueba | Tarea |
|---|---|---|
| US1 1–3 | `prueba_niebla_conocimiento` | T011 |
| US1 4–5 | `prueba_vista_mapa` | T012 |
| US1 6 | `prueba_vista_mapa` | T056 |
| US2 1–3 | `prueba_niebla_puertas` | T019 |
| US3 1 (**Apéndice B 1**), 2 (**Apéndice B 2**), 3 (**Apéndice B 3**), 4 y 11 (mismo armado), 5–9 | `prueba_ir_a` | T023 |
| US3 12 | `prueba_ir_a` | T055, T057 |
| US3 10 | `prueba_replay_ir_a` | T025 |
| US4 1 (**Apéndice B 4**), 2–4 | `prueba_niebla_antorcha` | T036 |
| US5 1 (**Apéndice B 5**), 2 (**Apéndice B 6**) | `prueba_niebla_retroceso` | T038 |
| US5 3–4 | `prueba_persistencia_niebla` | T039 |
| US5 5 | `prueba_replay_ir_a` | T025 |
| US6 1 | `prueba_rendimiento_ir_a` | T043 |
| US6 2 | `prueba_conteo_niebla` | T044 |

32 escenarios (6 + 3 + 12 + 4 + 5 + 2), los 6 del Apéndice B marcados.

## Cobertura de requisitos

| Requisito | Pruebas | Implementación |
|---|---|---|
| FR-001 a FR-004 | T011 | T013, T014 |
| FR-005 a FR-007 | T019 | T020, T021 |
| FR-008, FR-009 | T036 | T037 |
| FR-010, FR-011 | T006, T038 | T010, T014, T021 |
| FR-012 | T039 | T041, T042 |
| FR-013 | T039 | T002, T041 |
| FR-014, FR-015 | T012, T019, T024 | T016, T022 |
| FR-016, FR-017 | T012 | T017, T018 |
| FR-018 | T023, T034 | T029, T031 |
| FR-019 a FR-022 | T023, T024 | T027 |
| FR-023 | T023 | T031, T032 |
| FR-024, FR-025 | T023 | T028, T029, T031, T033 |
| FR-026, FR-027 | T025 | T030, T031 |
| FR-028 | T023 | T031, T035 |
| FR-029 | T038 | T040 |
| FR-030 | T023, T024 | T027 |
| FR-031 | T043 | T026, T027, T046 |
| FR-032, FR-033 | T044 | T007, T013, T037, T046 |
| FR-034 | T038 | T010 |
| FR-035 | T034 | T035 |
| FR-036 | T055, T057 | T055, T057 |
| FR-037 | T056 | T056 |
| SC-001 | T052 | — |
| SC-002 | T012, T024 | T016, T027 |
| SC-003 | T038, T039 | T010, T037 |
| SC-004 | T043 | T046, T047 |
| SC-005 | T044 | T046, T047 |
| SC-006 | T024 | T027 |
| SC-007 | T025 | T030 |

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias. T002 debe terminar antes de T041 (el fixture se genera con la versión 2).
- **Foundational (Phase 2)**: depende de T001; bloquea todas las historias.
- **US1 (Phase 3)**: depende de la Fase 2.
- **US2 (Phase 4)**: depende de US1 (T013, T014).
- **US3 (Phase 5)**: depende de US2 (la ruta usa los recuerdos).
- **US4 (Phase 6)**: depende de US2 (T020) y, para su caso borde de viaje, de T031.
- **US5 (Phase 7)**: depende de US3 (viaje) y US4 (antorcha en el escenario 1).
- **US6 (Phase 8)**: depende de T027 y T037; puede ir en paralelo con US5.
- **Polish (Phase 9)**: después de todas las historias; T051 y T052 son las últimas pruebas.

### Within Each Phase

Pruebas primero y en rojo; luego modelo → servicios del modelo → Controlador → Vista; checkpoint con la suite completa en verde antes de pasar de fase. Una confirmación en git por tarea o grupo coherente de tareas.

### Parallel Opportunities

- Fase 1: T003, T004 y T005 en paralelo (T002 primero si se puede).
- Fase 2: T007 y T008 en paralelo.
- US1: T011 y T012 en paralelo; T015 en paralelo con T013–T014.
- US3: T023, T024 y T025 en paralelo; T026, T028 y T030 en paralelo; T033 en paralelo con T035 una vez hecho T031.
- US5: T038 y T039 en paralelo.
- US6: T043, T044 y T045 en paralelo; US6 entera en paralelo con US5.
- Polish: T048 y T050 en paralelo.

## Parallel Example: User Story 3

```text
# Pruebas (en rojo) a la vez:
T023 pruebas/prueba_ir_a.py
T024 pruebas/prueba_ir_a_equivalencia.py
T025 pruebas/prueba_replay_ir_a.py

# Piezas independientes del modelo y del adaptador:
T026 cripta/modelo/mundo/sala.py (campos de búsqueda)
T028 cripta/modelo/nucleo/resultadoAccion.py + anotaciones en partida.py
T030 cripta/modelo/puertos/registroAcciones.py + cripta/adaptadores/registroArchivo.py
```

## Parallel Example: User Story 6

```text
T043 pruebas/prueba_rendimiento_ir_a.py
T044 pruebas/prueba_conteo_niebla.py
T045 cripta/controlador/bench/alternativasNiebla.py
```

## Implementation Strategy

### MVP First (User Story 1)

Fases 1 y 2, luego US1: la niebla y el panel M ya son demostrables solos. Validar con T011 y T012 antes de seguir.

### Incremental Delivery

1. US1 → niebla y mapa conocido.
2. US2 → memoria de puertas (sin ella «ir a» no tiene datos fiables).
3. US3 → «ir a»: con US1 a US3 se cubren los escenarios obligatorios 1 a 3 del Apéndice B.
4. US4 → antorcha (Apéndice B 4).
5. US5 → pergamino, guardado y replay (Apéndice B 5 y 6, formato 3).
6. US6 → bench y evidencia para DECISIONES.md.
7. Polish → README, DECISIONES.md, contratos, `prueba_reglas` y suite completa.

### Notes

- Cada prueba nueva se registra en `PRUEBAS` de `pruebas/ejecutar_pruebas.py` en la misma tarea que la crea.
- Si una tarea muestra que la spec o un contrato estaba mal, se corrige primero el documento en un commit propio y después el código (principio VII).
- Las tareas [EQUIPO] requieren respuesta del otro integrante antes de cerrar la fase.
