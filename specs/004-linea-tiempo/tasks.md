---

description: "Tareas de la feature 004: línea de tiempo"
---

# Tasks: Línea de tiempo

**Input**: Design documents from `specs/004-linea-tiempo/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md) (corregida en `67c1a83`), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: pedidos por la constitución ("cada FR tiene al menos una prueba") y por §2.5: en cada historia, las pruebas se escriben primero, fallan, y después se implementa. Cada prueba cita en su docstring o mensaje el FR, SC o escenario que cubre.

**Oráculo** (spec corregida en `67c1a83`, research R6): la referencia de las comparaciones es el **resumen capturado en vivo** en cada decisión del jugador de la partida real, quitando los de las acciones revertidas por pergaminos. No se compara con reproducir las acciones.

**Organización**: por historia de usuario, en orden de prioridad (US1, US2, US3 son P1; US4, US5 son P2; US6 es P3).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ir en paralelo (otro archivo, sin dependencias pendientes).
- **[Story]**: historia a la que pertenece (US1 a US6).
- Cada tarea dice el archivo, el requisito que cubre ("Cubre:") y de qué depende ("Depende de:").

---

## Phase 1: Setup

**Purpose**: línea base, fixture del formato anterior y apoyo de pruebas.

- [X] T001 Confirmar la línea base en la rama `004-linea-tiempo`: `py pruebas/ejecutar_pruebas.py` completa y en verde, anotando el total en esta tarea (se espera 67), y `py pruebas/prueba_reglas.py` limpia. Cubre: SC-001.
  **Hecho:** 67 pruebas en verde y prueba_reglas limpia (140 archivos) en la rama 004-linea-tiempo antes de cambiar código.
- [X] T002 Con el código **actual** (`FORMATO_VERSION = 3`), antes de T026, agregar a `pruebas/generar_guardado_formato_anterior.py` un modo propio `--formato-3` con su propia comprobación (`FORMATO_VERSION == 3`), sin tocar los modos de las versiones 1 y 2, que genere `pruebas/datos/linea/guardado_formato_3.bin` desde una partida sin conexión con algunas acciones. Correrlo y versionar el archivo. Cubre: FR-010 (Apéndice B 6).
  **Hecho:** pruebas/datos/linea/guardado_formato_3.bin (8287 bytes, 20 salas, 2 movimientos, semilla 20261117), generado con el modo --formato-3 y el código del formato 3.
- [X] T003 [P] Crear `pruebas/apoyo_linea.py` sobre `pruebas/apoyo_niebla.py`:
  - `partida_con_linea(descripcion, k, semilla)`: Partida sintética con `LineaTiempo` conectada (cuando exista, T012).
  - `OraculoVivo`: se engancha a la Partida real y captura en cada decisión del jugador la **huella del resumen** (reloj, número de acción, sala, vida, vida_max, ataque, defensa, velocidad, inventario como (id_objeto, id_ficha, equipado) en orden, efectos con tiempo restante, enemigos de la sala con vida, huella del mapa conocido de la 002); al usar un pergamino quita las capturas de las acciones revertidas y vuelve a capturar el estado actual. También captura la huella después de cada **instante de evento distinto** (enganchado al bucle de eventos de la partida real, solo en pruebas), para comparar instantes entre dos decisiones (FR-001, SC-002; análisis F2); las capturas de instantes revertidos se quitan igual.
  - `huella(resumen)`: la misma huella desde un `ResumenInstante`, para comparar.
  - `secuencia_al_azar(partida, azar, n, con_pergaminos, con_viajes)`: acciones deterministas por semilla (movimientos, esperas, recoger, viajes «ir a», pergaminos).
  - `partida_referencia_inmortal(semilla)`: la cripta de más salas de `datos_offline/` con el jugador sin daño letal (solo para medir), elegida por cantidad de salas sin ids en el código.
  Cubre: FR-001, SC-002, SC-004, SC-005, SC-006.

**Checkpoint**: línea base en verde y fixture del formato 3 versionado.

---

## Phase 2: Foundational (bloquea todas las historias)

**Purpose**: estructura propia, copia del estado, límite del bucle de eventos, servicio sin red y el esqueleto de la línea.

- [X] T004 [P] Crear `pruebas/prueba_arreglo_arbol.py` (escrita primero, debe fallar): `obtener(i)` para i de 1 a n, `agregar_al_final`, `quitar_ultimo`, `len`, error con índice fuera de rango; 10 000 operaciones al azar con semilla contra una lista de referencia; altura O(log n). Cubre: FR-023.
- [X] T005 Crear `cripta/modelo/estructuras/arregloArbol.py` con `ArregloArbol`: árbol binario completo de nodos; la posición i se alcanza bajando por los bits de i (como el montículo de D23); `obtener`, `agregar_al_final` y `quitar_ultimo` en O(log n), `__len__` O(1), `__iter__` en orden. Sin list, dict ni set. Cubre: FR-023. Depende de: T004. T004 pasa.
- [X] T006 [P] Crear `cripta/modelo/puertos/copiadorEstado.py` con el puerto `CopiadorEstado` (`tomar(partida) -> bytes`, `restaurar(datos, servicio) -> Partida`) con docstrings. Cubre: FR-020, FR-021.
- [X] T007 En `cripta/adaptadores/partidaBinaria.py`: separar `guardar` en `a_bytes(partida) -> bytes` + escritura del archivo y `cargar` en lectura del archivo + `desde_bytes(datos, servicio) -> Partida`, sin cambiar el formato todavía; una clase `CopiadorBinario(CopiadorEstado)` que los usa. `prueba_6_3`, `prueba_persistencia_niebla` y `prueba_persistencia_cazador` siguen pasando. Cubre: FR-020, FR-021. Depende de: T006.
- [X] T008 [P] Crear `pruebas/prueba_limite_eventos.py` (escrita primero, debe fallar): con `aplicar_accion(accion, limite=t)` sobre una partida sintética, no se ejecuta ningún evento con tiempo > t y sí todos los de tiempo ≤ t, incluidos varios en el mismo instante (FR-004); sin límite, el resultado es idéntico al de hoy (misma huella y mismo log en 200 acciones al azar). Cubre: FR-001, FR-004.
- [X] T009 En `cripta/modelo/nucleo/partida.py`: parámetro opcional `limite` en `aplicar_accion` y `_procesar_eventos` (con límite, el bucle se detiene antes del primer evento con tiempo > límite). La partida real nunca lo pasa. Cubre: FR-001, FR-004. Depende de: T008. T008 pasa.
- [X] T010 [P] Crear `pruebas/prueba_servicio_solo_lectura.py` (escrita primero, debe fallar): con una fuente falsa que cuenta solicitudes, `ServicioSoloLectura` devuelve contenidos registrados, `precargar` no hace nada, `resolver_fichas` usa memoria y disco, y una ficha o contenido ausente da `ErrorCripta` con mensaje claro; la fuente recibe 0 solicitudes. Cubre: FR-012.
- [X] T011 Crear `cripta/modelo/datos/servicioSoloLectura.py` (`ServicioSoloLectura`) y agregar `resolver_fichas_sin_red(ids)` en `cripta/modelo/datos/servicioDatos.py` (memoria y disco, D33; nunca la red). Cubre: FR-012. Depende de: T010. T010 pasa.
- [X] T012 Crear `cripta/modelo/nucleo/lineaTiempo.py` con `LineaTiempo(k, copiador)` (K entero ≥ 1), `Bloque`, `EntradaAccion` y `AjustePergamino` según data-model.md: `antes_de_accion` (punto de control al empezar cada bloque de K acciones), `registrar_accion` (acción + instante de decisión, O(1)), `registrar_contenido` (primera vez por sala) y `acciones`. Bloques en `ArregloArbol`, entradas en `ListaDoble`, contenidos en `ListaEnlazada`. En `partida.py`: atributo `linea` (None por omisión) y llamadas desde `aplicar_accion` (antes y después de una acción aceptada) y `_asegurar_contenido`. Todas las pruebas existentes siguen pasando. Cubre: FR-020. Depende de: T005, T007, T009.

**Checkpoint**: la línea registra la historia de una partida; todavía no se consulta.

---

## Phase 3: User Story 1 - Consultar el estado de un instante pasado (Priority: P1) 🎯 MVP

**Goal**: «historia <t>» e «historia #k» reconstruyen el estado sobre una copia, sin tocar la partida.

**Independent Test**: partidas sintéticas sin pergaminos; cada consulta coincide con la huella del oráculo en vivo, y la partida queda idéntica.

### Tests for User Story 1 ⚠️ (escritas primero, deben fallar)

- [X] T013 [P] [US1] Crear `pruebas/prueba_linea_consulta.py`, un caso por escenario de US1:
  - escenario 1 (FR-003, FR-012; **Apéndice B 1**): t > reloj actual se rechaza con el reloj en el mensaje y nada cambia;
  - escenario 2 (FR-001, FR-004; **Apéndice B 3**): varios eventos en el mismo instante t → estado después de todos;
  - escenario 3 (FR-011, FR-012; **Apéndice B 4**): la consulta no consume tiempo, no escribe en partida.log y el siguiente pergamino revierte lo mismo que sin la consulta;
  - escenario 4 (FR-001): t de una decisión → estado justo antes de ella;
  - escenario 5 (FR-002, FR-003): #k con 1 ≤ k ≤ n, k = n + 1 (estado actual), y rechazos con k = 0, k > n + 1 y texto;
  - escenario 6 (FR-002): cada paso de «ir a» cuenta como una acción; rechazos, consultas y pergamino no;
  - escenario 7 (FR-005, FR-006): el resumen trae todos los campos y el mapa conocido de ese instante (incluido un recuerdo de puerta que después cambió);
  - escenario 8 (FR-001, FR-002): «historia 0» y «#1» dan el estado inicial;
  - caso borde: t entre dos decisiones (FR-001).
  Compara con `OraculoVivo` (T003). Cubre: FR-001 a FR-006, FR-011, FR-012.
- [X] T014 [P] [US1] En `pruebas/prueba_linea_consulta.py`, caso SC-002 sin pergaminos: 300 consultas a instantes y números de acción elegidos con semilla sobre partidas sintéticas de 500 acciones con viajes «ir a», todas iguales a la huella del oráculo en vivo, y resultado independiente de K (FR-026: mismas consultas con K = 1, 25 y 100). Cubre: SC-002, FR-026.

### Implementation for User Story 1

- [X] T015 [US1] En `cripta/modelo/nucleo/lineaTiempo.py`: `reconstruir_accion(k, servicio_real)` (bloque ⌊(k−1)/K⌋ con `ArregloArbol.obtener`, restaurar el punto de control con `ServicioSoloLectura`, aplicar completas las acciones anteriores a k) y `reconstruir_instante(t, servicio_real)` (búsqueda binaria por `tiempo_inicio`; aplicar completas las acciones cuya siguiente decisión es ≤ t y la última con `limite=t`, R3). La copia no tiene diario, vista ni registro. Nunca aplica más de K acciones (FR-021). Cubre: FR-001 a FR-004, FR-021, FR-023. Depende de: T011, T012.
- [X] T016 [P] [US1] Agregar `ResumenInstante` (DTO inmutable, campos de data-model.md) en `cripta/vista/estadoVista.py` y crear `cripta/controlador/constructorResumen.py`: arma el resumen desde una Partida (con el mapa conocido de la 002 vía el mismo constructor del panel M) y su texto según contracts/cli.md. Cubre: FR-005, FR-006. Depende de: T012.
  **Hecho:** ResumenInstante lleva el EstadoVista de la copia (campo estado) en vez de repetir sus campos uno por uno: así el resumen y el dibujo del juego salen del mismo constructor. Se anota en contracts/ en T038.
- [X] T017 [US1] En `cripta/controlador/controladorJuego.py`: crear la `LineaTiempo(K, CopiadorBinario)` y conectarla a la partida al empezar; verbo de sesión `historia` (no consume tiempo, no va al log, no detiene viajes): interpretar `"<t>"` o `"#<k>"`, validar (FR-003, con el motivo en `mostrar_error`), reconstruir y mandar el `ResumenInstante` en `EstadoVista.historia` (solo mientras la consulta está abierta). Cubre: FR-002, FR-003, FR-011, FR-012. Depende de: T015, T016. T013 y T014 pasan.
  **Hecho:** El copiador entra por el constructor de ControladorJuego (copiador_estado, k_linea), así el Controlador no importa adaptadores (D48); apoyo_niebla.controlador_sobre pasa CopiadorBinario. Un instante posterior al reloj actual se rechaza aunque sea el de la decisión pendiente: esa se consulta con #(n+1).

**Checkpoint**: US1 en verde: MVP de la línea de tiempo (consulta sin pergaminos).

---

## Phase 4: User Story 2 - La línea de tiempo respeta el pergamino (Priority: P1)

**Goal**: lo revertido deja de existir; el pergamino gastado y la regla D50 aparecen desde el reloj actual.

**Independent Test**: secuencias con pergaminos (también dentro de viajes y con pergaminos recogidos en el tramo revertido) comparadas con el oráculo en vivo.

### Tests for User Story 2 ⚠️

- [X] T018 [P] [US2] Crear `pruebas/prueba_linea_pergamino.py`, un caso por escenario de US2:
  - escenario 1 (FR-007; **Apéndice B 2**): después del pergamino ninguna consulta muestra efectos de lo revertido;
  - escenario 2 (FR-002, FR-007): revertir y hacer otras acciones; la numeración #k sigue la historia que quedó, sin huecos;
  - escenario 3 (FR-008): el pergamino gastado figura en instantes anteriores al reloj actual y no desde el reloj actual;
  - escenario 4 (FR-003, FR-007): instantes mayores que R' se rechazan;
  - escenario 5 (FR-008, D50): un pergamino recogido en el tramo revertido no figura antes de R' y sí desde R';
  - casos borde: pergamino que revierte un paso de «ir a»; pergamino soltado en el tramo revertido que queda en el suelo; pergamino que soltó un enemigo muerto en el tramo revertido.
  Compara con `OraculoVivo`. Cubre: FR-002, FR-003, FR-007, FR-008.
- [X] T019 [P] [US2] En `pruebas/prueba_linea_pergamino.py`, caso SC-002 completo: 1000 consultas elegidas con semilla sobre partidas sintéticas de al menos 500 acciones con pergaminos y viajes, todas iguales al oráculo en vivo; y el recorte del pergamino toca un número constante de entradas sin importar el largo de la historia (contador instrumentado, FR-023); y el caso **SC-004** (análisis G1): 1000 secuencias con semilla ejecutadas con y sin consultas intercaladas, comparando reloj, huella del estado, partida.log y lo que revierte el siguiente pergamino. Se mantienen las 1000 consultas de SC-002 y las 1000 secuencias de SC-004; si la prueba pasa de 120 s, se le da un tope propio más alto en `pruebas/ejecutar_pruebas.py` en vez de reducir el número (análisis G3). Cubre: SC-002, SC-004, FR-011, FR-023.
  **Hecho:** SC-002 (1000 consultas sobre dos partidas de 500 acciones con pergaminos y viajes) y SC-004 (1000 secuencias con y sin consultas) pasan; el recorte toca 2 entradas con 100 y con 1000 acciones.

### Implementation for User Story 2

- [X] T020 [US2] En `cripta/modelo/nucleo/lineaTiempo.py`: `al_usar_pergamino(partida)`: quitar la última `EntradaAccion` del último bloque (O(1)); si el bloque se quedó sin su primera acción, quitar el bloque (`quitar_ultimo`, O(log n)); agregar un `AjustePergamino` con el instante actual, el inventario de la partida real (id_objeto, id_ficha, equipado, en orden) y los pergaminos en el suelo de cada sala (id_sala, id_objeto, id_ficha). En `partida.py`, `_usar_pergamino` lo llama después de gastar el pergamino. Cubre: FR-007, FR-008, FR-023. Depende de: T015.
- [X] T021 [US2] En `cripta/modelo/nucleo/partida.py`: `aplicar_ajuste_pergamino(ajuste)` (solo para copias): deja el inventario y los pergaminos del suelo de la copia iguales al ajuste, moviendo objetos por `id_objeto` o creándolos desde su ficha con el mismo id; y la reconstrucción de T015 aplica los ajustes al llegar a ellos. Cubre: FR-008. Depende de: T020. T018 y T019 pasan.
  **Hecho:** Hallazgo al implementar (research R6, no cambia la spec): el Diario de la primera parte no revierte el generador aleatorio, la secuencia de la agenda ni el próximo id de objeto, así que el ajuste del pergamino también guarda esos tres valores y la copia los restaura; sin ellos, lo que viene después del pergamino sorteaba distinto. La huella de las pruebas compara los enemigos y el suelo como conjuntos: deshacer los reinserta al final de su lista y ese orden no es estado del juego.

**Checkpoint**: US1 y US2 en verde.

---

## Phase 5: User Story 3 - Consultar sin interacción con --replay … --hasta (Priority: P1)

**Goal**: el mismo resumen por texto, sin ventana.

**Independent Test**: partidas grabadas reproducidas con `--hasta`, comparadas con «historia» al final de la partida original y con el oráculo en vivo.

### Tests for User Story 3 ⚠️

- [X] T022 [P] [US3] Crear `pruebas/prueba_replay_hasta.py`:
  - escenario 1 (FR-013; **Apéndice B 5**): t mayor que el final → estado final y "La partida terminó antes, en el instante F.";
  - escenario 2 (FR-013, FR-014): t ≤ final → el mismo texto que «historia <t>» al final de la partida original, sin abrir la ventana;
  - escenario 3 (FR-007, FR-014): log con pergaminos → la historia tal como quedó;
  - escenario 4 (FR-015): `--hasta` sin `--replay` y t inválido → mensaje de uso y código 2;
  - escenario 5 (FR-016): versión no disponible → el mismo mensaje y código 1 que `--replay`;
  - `--checkpoint-cada` con 0, negativo o texto → error y código 2 antes de empezar (FR-022);
  - SC-006: 20 partidas grabadas con semilla, 10 instantes cada una, `--hasta` igual a «historia».
  Cubre: FR-013 a FR-016, FR-022, SC-006.

### Implementation for User Story 3

- [X] T023 [US3] En `cripta/controlador/fabricaAplicacion.py`: leer `--hasta t` (solo con `--replay`; t entero ≥ 0) y `--checkpoint-cada K` (entero ≥ 1, por omisión 25), con los mensajes y códigos de contracts/cli.md; pasar K a `ControladorJuego` y a `ModoReplay`. Actualizar el docstring de opciones. Cubre: FR-015, FR-022. Depende de: T017.
- [X] T024 [US3] En `cripta/controlador/modoReplay.py`: conectar una `LineaTiempo(K)` a la partida reproducida; con `--hasta`, al terminar el log reconstruir t (o el estado final con el aviso si t es mayor que el reloj final) e imprimir el texto de `ConstructorResumen` con `Reporte`; la comprobación de versiones queda igual. Cubre: FR-013, FR-014, FR-016. Depende de: T021, T023. T022 pasa.

**Checkpoint**: las tres historias P1 en verde.

---

## Phase 6: User Story 4 - Guardar y cargar conserva la línea (Priority: P2)

**Goal**: formato 4 con la línea completa; la versión 3 o anterior se rechaza.

**Independent Test**: guardar y cargar en puntos elegidos con semilla y comparar todas las consultas; cargar el fixture del formato 3.

### Tests for User Story 4 ⚠️

- [ ] T025 [P] [US4] Crear `pruebas/prueba_persistencia_linea.py`:
  - escenario 1 (FR-009): guardar y cargar una partida con pergaminos y viajes; todas las consultas de instantes y números de acción iguales a antes;
  - escenario 2 (FR-010; **Apéndice B 6**): `pruebas/datos/linea/guardado_formato_3.bin` (T002) se reporta incompatible con "se esperaba 4 y se encontró 3" y no se carga;
  - escenario 3 (FR-009): seguir jugando después de cargar; la historia es continua (instantes antes y después de la carga);
  - SC-005: las 1000 secuencias de T019 con un guardar y cargar en un punto elegido con semilla; ninguna consulta cambia;
  - `cargar_sala` (§4.10 de la primera parte) sigue funcionando con el formato 4 y lee solo el encabezado, el índice y su sala: con una línea grande (cientos de puntos de control), la cantidad de bytes que lee (archivo instrumentado) es la misma que sin línea (análisis F1);
  - caso borde (análisis G4): usar el pergamino justo después de cargar (el historial del pergamino no se guarda, primera parte) y consultar instantes anteriores a la carga: siguen dando lo mismo.
  Cubre: FR-009, FR-010, SC-005.

### Implementation for User Story 4

- [ ] T026 [US4] En `cripta/adaptadores/partidaBinaria.py`: `FORMATO_VERSION = 4`, la bandera `con_linea` y la sección de la línea según contracts/partida-binaria.md (K, acciones, contenidos iniciales, bloques con su punto de control y sus entradas "A"/"P"), escrita **antes** del índice de salas para que el índice siga siendo lo último del archivo y `cargar_sala` lea solo el índice y su sala (análisis F1); las acciones se leen con `_accion_desde_texto` de `registroArchivo.py` (expuesto como función pública); los puntos de control van con `con_linea` en falso y sin la sección de la línea, y `desde_bytes` los distingue de un guardado por esa bandera (análisis F3); la carga reconstruye la `LineaTiempo`. Actualizar el docstring del formato. Cubre: FR-009, FR-010. Depende de: T002, T021.
- [ ] T027 [US4] En `cripta/controlador/controladorJuego.py` y donde se carga una partida: conectar la línea cargada a la partida; en `pruebas/prueba_persistencia_niebla.py` y `pruebas/prueba_persistencia_cazador.py`, aceptar la versión actual (≥ 3 y ≥ 2) en vez de un número fijo. Cubre: FR-009. Depende de: T026. T025 pasa.

**Checkpoint**: US4 en verde.

---

## Phase 7: User Story 5 - Consultar desde la ventana con la tecla H (Priority: P2)

**Goal**: H abre la consulta, Enter la hace, ESC vuelve.

**Independent Test**: ventana real oculta y controlador real; teclas y comandos encolados, vaciando la cola antes de cada tecla (patrón de prueba_vista_10).

### Tests for User Story 5 ⚠️

- [ ] T028 [P] [US5] Crear `pruebas/prueba_vista_historia.py` (vaciar la cola antes de cada tecla):
  - escenario 1 (FR-017, FR-018): H, "120", Enter → `Comando("historia", ("120",))` y el panel muestra el resumen; ESC vuelve y el reloj no cambió;
  - escenario 2 (FR-017): "#3" y Enter;
  - escenario 3 (FR-003, FR-017): valor inválido → el motivo y la consulta sigue abierta;
  - escenario 4 (FR-018): con la consulta abierta, letras y flechas no encolan acciones ni abren selecciones;
  - con un viaje en curso, H encola `interrumpir` antes de abrir (FR-017, aclaración);
  - con el panel del mapa abierto, H lo cierra antes (como FR-037 de la 002);
  - H no existe en el replay en la ventana (FR-017).
  Cubre: FR-003, FR-017, FR-018.

### Implementation for User Story 5

- [ ] T029 [US5] En `cripta/vista/pantallaJuego.py`: tecla H y modo **historia** según contracts/vista.md (dígitos, `#`, Retroceso, Enter encola `historia`, ESC cierra; las demás teclas no hacen nada; con viaje en curso encola `interrumpir` primero; con el mapa abierto lo cierra antes). Cubre: FR-017, FR-018. Depende de: T017.
- [ ] T030 [US5] En `cripta/vista/hudJuego.py`: panel del resumen (`EstadoVista.historia`) sobre el mapa con `partirLineas` y desplazamiento (↑/↓, RePág/AvPág), la línea de entrada mientras se escribe, y la fila "H Historia" en el panel de Controles sin encimarse (la prueba `caso_controles_sin_encimarse` sigue pasando). Cubre: FR-017. Depende de: T029. T028 pasa.

**Checkpoint**: US5 en verde.

---

## Phase 8: User Story 6 - Memoria acotada y consultas rápidas (Priority: P3)

**Goal**: evidencia con `--bench` de memoria, tiempo de consulta, K por defecto, búsqueda del bloque y §5.6.

**Independent Test**: `py main.py --bench --rapido` muestra las tablas de `benchLineaTiempo` y la de `benchHistorial` con la carga nueva.

### Tests for User Story 6 ⚠️

- [ ] T031 [P] [US6] Crear `pruebas/prueba_rendimiento_linea.py`:
  - escenario 1 (FR-019, SC-003): partida de 5000 acciones sobre la cripta de referencia (`partida_referencia_inmortal`, T003) con el K por defecto; la consulta peor (mínimo de varias repeticiones) < 50 ms en instantes repartidos, con la cifra en el mensaje;
  - FR-021: ninguna consulta aplica más de K acciones (contador instrumentado);
  - escenario 2 (FR-020, SC-007): con `tracemalloc`, en una partida de 500 acciones, la memoria de la línea con K = 25 es menos de la mitad que con K = 1, y crece con las acciones (no con acciones por tamaño del estado); K = 1 con 5000 acciones queda solo para el bench (análisis G2);
  - escenario 3 (FR-023): el recorte del pergamino cuesta lo mismo con 100 y con 5000 acciones (contador).
  Cubre: FR-019 a FR-021, FR-023, SC-003, SC-007.
  **Nota (análisis I1):** estas pruebas miden código de historias anteriores, así que pueden pasar apenas se escriben; confirman el diseño en vez de guiarlo, como T047 de la feature 002.

### Implementation for User Story 6

- [ ] T032 [P] [US6] Crear `cripta/controlador/bench/alternativasLineaTiempo.py` (solo para medir): búsqueda lineal del bloque en una `ListaEnlazada` y reconstrucción sin puntos de control (re-simular desde el instante 0, con un tope de tiempo en el bench). Cubre: FR-023, FR-024.
- [ ] T033 [US6] Crear `cripta/controlador/bench/benchLineaTiempo.py` con `ejecutar(reporte, rapido)`, determinista por semilla, sobre la cripta de referencia y 5000 acciones (menos en `--rapido`): (1) memoria y tiempo de consulta (peor y mediana) con K = 10, 25 y 50 y sin puntos de control; (2) adelante contra atrás: tomar y restaurar una copia y deshacer K acciones con el Diario, junto a la reconstrucción hacia adelante medida; (3) búsqueda del bloque, arreglo por árbol contra lineal, con 10² a 10⁵ bloques; (4) recorte del pergamino según el largo de la historia; (5) tamaño y tiempo de guardar y cargar el formato 4. Cubre: FR-019 a FR-024, SC-003, SC-007. Depende de: T026, T032.
- [ ] T034 [US6] En `cripta/controlador/bench/benchHistorial.py`: tabla nueva que repite las mediciones de la primera parte con la carga nueva (cazadores, viajes «ir a» y la línea conectada) y las compara con las anteriores, con el veredicto "sigue siendo adecuado" o "se cambió" (§5.6). Cubre: FR-025.
- [ ] T035 [US6] Registrar `benchLineaTiempo` en `cripta/controlador/bench/benchTodo.py` y actualizar el total de tablas en `pruebas/prueba_4_4.py`; además, `prueba_4_4` comprueba que `benchHistorial` trae la tabla con la carga nueva y su veredicto ("sigue siendo adecuado" o "se cambió"), citando FR-025 (análisis C1); correr `py main.py --bench --rapido`. Cubre: FR-024, FR-025. Depende de: T033, T034. T031 pasa.

**Checkpoint**: todas las historias en verde.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [ ] T036 [P] Actualizar `README.md`: tecla **H** (consultar la línea de tiempo), `--replay partida.log --hasta t`, `--checkpoint-cada K` (25 por omisión), formato de guardado 4 (los guardados anteriores se rechazan) y el total de pruebas. Cubre: FR-010, FR-013, FR-018, FR-022.
- [ ] T037 Agregar al Documento de Decisiones (`DECISIONES.md`) las secciones nuevas de la línea de tiempo con el siguiente número D libre (estructura de P1 §8): puntos de control con `PartidaBinaria` en memoria; reconstrucción hacia adelante (con la evidencia de adelante contra atrás); K por defecto con la tabla de los tres valores y sin puntos de control; arreglo por árbol contra búsqueda lineal; servicio de solo lectura; ajuste del pergamino; formato 4; y §5.6 con el antes y el después del historial del pergamino. Cada sección enlaza a `specs/004-linea-tiempo/spec.md` y `plan.md` y dice si la decisión final coincide con el plan y qué medición la cambió (§7.1). Usar las cifras de `benchLineaTiempo`, no las previas. Cubre: FR-024, FR-025.
- [ ] T038 Poner al día `specs/004-linea-tiempo/contracts/` (cli.md, vista.md, partida-binaria.md) con lo que quedó en el código, en un commit propio. Cubre: FR-013 a FR-018, FR-009.
- [ ] T039 [P] Correr `py pruebas/prueba_reglas.py` y `py pruebas/prueba_sin_datos_concretos.py` (si existe) sobre `cripta/`: sin dict, set, list, heapq, bisect, collections, pickle ni deepcopy, y sin datos de criptas concretas. Cubre: FR-026 (constitución I, II y IV).
- [ ] T040 Registrar las pruebas nuevas en `pruebas/ejecutar_pruebas.py` (con un tope de tiempo propio más alto para las que lo necesiten, como las de SC-002 y SC-004, sin reducir su número; análisis G3) y correr la suite completa tres veces seguidas, todas en verde, anotando el total. Cubre: SC-001.
- [ ] T041 Validación a mano según `quickstart.md` §2 y §3 a 1024×720 (H, `#k`, valor inválido, pergamino, H durante un viaje, guardar y cargar), anotando el resultado en esta tarea. Cubre: FR-017, FR-018, SC-001.

---

## Escenarios → pruebas (28, SC-001)

| Escenario | Prueba | Tarea |
|---|---|---|
| US1 1 (**Apéndice B 1**) | `prueba_linea_consulta` | T013 |
| US1 2 (**Apéndice B 3**) | `prueba_linea_consulta` | T013 |
| US1 3 (**Apéndice B 4**) | `prueba_linea_consulta` | T013 |
| US1 4 a 8 | `prueba_linea_consulta` | T013 |
| US2 1 (**Apéndice B 2**) | `prueba_linea_pergamino` | T018 |
| US2 2 a 5 | `prueba_linea_pergamino` | T018 |
| US3 1 (**Apéndice B 5**) | `prueba_replay_hasta` | T022 |
| US3 2 a 5 | `prueba_replay_hasta` | T022 |
| US4 1 y 3 | `prueba_persistencia_linea` | T025 |
| US4 2 (**Apéndice B 6**) | `prueba_persistencia_linea` | T025 |
| US5 1 a 4 | `prueba_vista_historia` | T028 |
| US6 1 a 3 | `prueba_rendimiento_linea` | T031 |

## Cobertura de requisitos

| Requisito | Prueba | Implementación |
|---|---|---|
| FR-001, FR-004 | T008, T013 | T009, T015 |
| FR-002, FR-003 | T013, T018, T028 | T015, T017 |
| FR-005, FR-006 | T013 | T016 |
| FR-007, FR-008 | T018, T019 | T020, T021 |
| FR-009, FR-010 | T025 | T002, T026, T027 |
| FR-011, FR-012 | T010, T013 | T011, T017 |
| FR-013 a FR-016 | T022 | T023, T024 |
| FR-017, FR-018 | T028 | T029, T030 |
| FR-019 a FR-021 | T031 | T012, T015, T033 |
| FR-022 | T022 | T023 |
| FR-023 | T004, T019, T031 | T005, T015, T020, T032 |
| FR-024 | T031 | T033, T035, T037 |
| FR-025 | T035 (`prueba_4_4`) | T034, T037 |
| FR-026 | T014, T039 | T015 |
| SC-001 | T040 | todas |
| SC-002 | T014, T019 | T003, T015, T021 |
| SC-003, SC-007 | T031 | T033 |
| SC-004 | T019 | T015, T017 |
| SC-005 | T025 | T026 |
| SC-006 | T022 | T024 |

---

## Dependencies & Execution Order

- **Setup (T001 a T003)**: sin dependencias; T002 antes de T026.
- **Foundational (T004 a T012)**: T005 tras T004; T007 tras T006; T009 tras T008; T011 tras T010; T012 tras T005, T007 y T009. Bloquea todas las historias.
- **US1 (T013 a T017)**: tras la fase 2. Es el MVP.
- **US2 (T018 a T021)**: tras US1 (usa la reconstrucción).
- **US3 (T022 a T024)**: tras US2 (el log trae pergaminos).
- **US4 (T025 a T027)**: tras US2; puede ir en paralelo con US3.
- **US5 (T028 a T030)**: tras US1 (T017); puede ir en paralelo con US2 a US4.
- **US6 (T031 a T035)**: tras US4 (mide guardar y cargar el formato 4).
- **Polish (T036 a T041)**: al final.

## Parallel Opportunities

- Fase 1: T002 y T003.
- Fase 2: T004, T006, T008 y T010 (cuatro archivos distintos).
- En cada historia, las pruebas [P] se escriben juntas antes de implementar.
- US5 en paralelo con US2, US3 y US4 (archivos de la Vista distintos).
- T032 en paralelo con las pruebas de US6.

## Implementation Strategy

1. **MVP**: fases 1 y 2 y US1: consultas sin pergaminos, ya con el oráculo en vivo.
2. US2 y US3: el resto de lo P1 (pergamino y `--hasta`), con 4 de los 6 escenarios del Apéndice B listos tras US1 y US3.
3. US4 y US5: guardado y ventana.
4. US6: mediciones y K por defecto confirmado con `benchLineaTiempo`.
5. Polish: README, DECISIONES.md, contratos, reglas, suite y validación a mano.

Un commit por fase o historia, con el nombre de la historia y las tareas.
