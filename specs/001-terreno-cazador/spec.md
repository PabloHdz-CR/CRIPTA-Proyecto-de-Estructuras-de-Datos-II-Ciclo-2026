# Feature Specification: Terreno y cazador

**Feature Branch**: `001-terreno-cazador`

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "Terreno y cazador: las salidas de una sala tienen costo de tránsito y aparece un nuevo enemigo, el cazador, que calcula la ruta más barata hacia el jugador." (descripción completa con reglas, contrato de datos, interfaz, rendimiento y escenarios de aceptación en el comando `/speckit-specify` del 2026-10-31, registrado en PROMPTS_LLM.md).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Atravesar salidas con costo de tránsito (Priority: P1)

El jugador recorre la cripta y nota que no todas las salidas tardan lo mismo: un
pasillo estrecho o un río subterráneo consume más tiempo que una puerta común.
El tiempo de cada movimiento de cualquier actor (jugador, errantes,
rastreadores y cazadores) depende del costo de la salida que atraviesa, y eso
cambia quién actúa primero en el reloj de eventos.

**Why this priority**: Es la base del resto: sin costos de salida no hay
"ruta más barata" que el cazador pueda calcular. Por sí sola ya cambia la
táctica del jugador (elegir caminos rápidos o lentos).

**Independent Test**: Cargar una cripta con salidas de costos distintos (y
alguna sin costo), mover al jugador y a un errante, y comprobar en el registro
de la partida que el intervalo de cada movimiento es
max(1, costo_salida × 100 // velocidad), sin que exista ningún cazador.

**Acceptance Scenarios**:

1. **Given** una salida sin costo declarado, **When** un actor de velocidad 100 la atraviesa, **Then** su próxima acción ocurre 100 unidades de tiempo después (la salida cuesta 100).
2. **Given** una salida de costo 300 y un jugador de velocidad 100, **When** el jugador la atraviesa, **Then** su próxima acción ocurre 300 unidades después.
3. **Given** una salida de costo 1 y un actor de velocidad muy alta (por ejemplo 1000), **When** la atraviesa, **Then** el intervalo hasta su próxima acción es 1 (nunca 0).
4. **Given** un actor que acaba de atravesar una salida de costo 400 con velocidad 100, **When** su velocidad cambia a 200 a mitad del tránsito, **Then** el tiempo restante se reescala con la regla de velocidad existente (restante × velocidad_anterior // velocidad_nueva, mínimo 1).
5. **Given** un errante y un rastreador, **When** deciden moverse, **Then** eligen la salida exactamente igual que antes de esta capacidad y solo cambia el tiempo que tarda su movimiento.
6. **Given** cualquier actor, **When** ataca, espera o realiza otra acción que no sea moverse, **Then** su costo es el mismo que antes de esta capacidad.

---

### User Story 2 - Ser perseguido por un cazador (Priority: P1)

El jugador se enfrenta a un nuevo enemigo, el cazador, que conoce el mapa
completo de la cripta y el estado de todas las puertas. Si el jugador está a su
alcance (costo total de la ruta menor o igual que su rango), el cazador avanza
paso a paso por la ruta más barata; si no lo alcanza o no hay camino abierto,
espera. Cerrar puertas a su paso o alejarse lo suficiente son formas de
escapar.

**Why this priority**: Es la novedad central de la capacidad y lo que el
jugador percibe como un enemigo distinto. Depende de la Historia 1 (costos).

**Independent Test**: Construir criptas pequeñas de prueba con costos y puertas
conocidas, colocar un cazador y al jugador, y comprobar turno a turno que cada
decisión del cazador coincide con la que daría un cálculo de ruta más barata
hecho desde cero en ese instante.

**Acceptance Scenarios**:

1. **Given** un cazador en la misma sala que el jugador vivo, **When** le toca actuar, **Then** ataca al jugador y no se mueve.
2. **Given** un cazador sin ninguna ruta de salidas abiertas hacia la sala del jugador, **When** le toca actuar, **Then** espera con costo 100.
3. **Given** un cazador de rango 500 cuya ruta más barata al jugador cuesta 600, **When** le toca actuar, **Then** espera con costo 100.
4. **Given** un cazador de rango 500 cuya ruta más barata cuesta exactamente 500, **When** le toca actuar, **Then** se mueve un paso por esa ruta.
5. **Given** dos rutas al jugador, una de 1 salida con costo 500 y otra de 3 salidas con costo total 300, **When** el cazador decide (con rango suficiente), **Then** sigue la de 3 salidas (menor costo), y el costo de su acción es el de la primera salida de esa ruta.
6. **Given** dos vecinas v1 (id menor) y v2 tales que costo(u, v) + dist(v, jugador) = d para ambas, **When** el cazador decide, **Then** se mueve hacia v1, la de menor id.
7. **Given** un cazador que en su turno anterior avanzó por una ruta, **When** una puerta de esa ruta se cierra antes de su siguiente turno, **Then** en ese turno decide exactamente como si calculara la ruta desde cero con las puertas actuales (puede desviarse por otra ruta o esperar).
8. **Given** un cazador cuya ruta pasa por salas cuyo contenido el jugador nunca descargó ni vio, **When** decide, **Then** la decisión es la misma que si esas salas estuvieran descargadas: solo dependen del esqueleto y del estado de las puertas.
9. **Given** una puerta cerrada en la única ruta, **When** el cazador decide, **Then** no la abre: la trata como intransitable.

---

### User Story 3 - Ver los costos y reconocer a los cazadores (Priority: P2)

Al estar en una sala, el jugador ve el costo de cada salida disponible y puede
distinguir a simple vista a los cazadores de los demás enemigos presentes.

**Why this priority**: Sin esta información el jugador no puede razonar sobre
rutas ni sobre el peligro, pero las reglas funcionan sin ella (pruebas y
reproducciones no usan la vista).

**Independent Test**: Abrir la vista en una sala con salidas de costos
distintos (incluida una sin costo declarado) y con un cazador y otro enemigo, y
comprobar que se muestran los costos (100 para la no declarada) y que el
cazador se distingue.

**Acceptance Scenarios**:

1. **Given** una sala con salidas de costo 100 (no declarado), 250 y 1, **When** el jugador la observa, **Then** la vista muestra 100, 250 y 1 junto a la salida correspondiente.
2. **Given** una sala con un cazador y un errante, **When** el jugador la observa, **Then** el cazador se identifica de forma distinta del errante.

---

### User Story 4 - Rendimiento con muchos cazadores (Priority: P2)

Una cripta grande con decenas de cazadores activos que persiguen al jugador
sigue respondiendo sin demora perceptible entre una decisión del jugador y la
siguiente.

**Why this priority**: El juego debe mantenerse jugable, y la constitución fija
el límite del ciclo de eventos; pero es posterior a tener reglas correctas.

**Independent Test**: Ejecutar el modo de medición sobre la cripta de
referencia con decenas de cazadores y medir el ciclo de eventos entre dos
decisiones del jugador; además, comparar el trabajo de un cazador de rango
pequeño en criptas de tamaños distintos.

**Acceptance Scenarios**:

1. **Given** la cripta de referencia con decenas de cazadores activos persiguiendo al jugador, **When** se resuelve un ciclo completo de eventos entre dos decisiones del jugador, **Then** toma menos de 20 ms medidos con el modo de medición.
2. **Given** un cazador de rango pequeño, **When** decide en criptas de tamaños muy distintos pero con la misma región a su alcance, **Then** el trabajo de su decisión es esencialmente el mismo (proporcional a la región dentro de su rango, no al total de salas).

---

### Edge Cases

- Salida sin costo declarado: vale 100.
- Costo declarado inválido (0, negativo, no entero): la cripta se rechaza con un error de datos claro; no se corrige en silencio.
- Las dos caras de una misma puerta declaran costos distintos (o una lo declara y la otra no): [NEEDS CLARIFICATION: ¿se rechaza la cripta como inconsistente, o cada cara usa su propio costo al atravesarla en su sentido?]
- Rango de cazador ausente, negativo o no entero en la ficha: la ficha se rechaza con error de datos.
- Rango 0: el cazador solo actúa si comparte sala con el jugador (ataca); en otro caso, como d ≥ 1 > 0, espera.
- Puertas direccionales: cada cara de una puerta tiene su propio estado abierto/cerrado; la ruta del cazador usa solo salidas abiertas en el sentido en que las recorre.
- El jugador cambia de sala, otra puerta se abre o se cierra, o muere otro actor entre dos turnos del cazador: el cazador decide de nuevo con el estado del instante.
- Varios cazadores en la misma sala con el mismo objetivo: cada uno decide de forma independiente y llega a la misma decisión si sus rangos lo permiten.
- Jugador muerto: el cazador no ataca (igual que los demás enemigos); la partida termina según las reglas existentes.
- Primera acción de un cazador al aparecer: mismo costo inicial que el resto de los enemigos.
- Cambio de velocidad cuando el próximo turno del actor no está agendado: se aplica la regla existente sin cambios.

## Requirements *(mandatory)*

### Functional Requirements

**Costo de las salidas**

- **FR-001**: Cada salida del esqueleto MUST poder declarar un costo de tránsito entero ≥ 1; si no lo declara, su costo MUST ser 100.
- **FR-002**: El costo de una salida MUST ser el mismo en ambos sentidos de la conexión que representa.
- **FR-003**: Un costo declarado que no sea un entero ≥ 1 MUST provocar un error de datos explícito que identifique la sala y la salida; nunca se sustituye en silencio.
- **FR-004**: El costo base de la acción de moverse a través de una salida MUST ser el costo de esa salida (en lugar del 100 fijo) para todos los actores que se mueven: jugador, errantes, rastreadores y cazadores.
- **FR-005**: El intervalo hasta la próxima acción tras un movimiento MUST ser max(1, costo_salida × 100 // velocidad).
- **FR-006**: El costo de atacar, esperar y las demás acciones que no son moverse MUST permanecer igual que antes de esta capacidad.
- **FR-007**: Errantes y rastreadores MUST elegir su acción exactamente con las mismas reglas de antes; solo cambia la duración de su movimiento.
- **FR-008**: Si la velocidad de un actor cambia mientras su próxima acción está pendiente tras atravesar una salida, el tiempo restante MUST reescalarse con la regla de velocidad existente, sin regla especial por costo de salida.

**El cazador**

- **FR-009**: El sistema MUST admitir un cuarto comportamiento de enemigo, "cazador", cuya ficha de catálogo incluye un campo rango (entero ≥ 0, en unidades de costo).
- **FR-010**: En su turno, si el cazador comparte sala con el jugador vivo, MUST atacarlo y no moverse.
- **FR-011**: Si no comparte sala, el cazador MUST considerar d = costo mínimo de llegar desde su sala hasta la sala actual del jugador, sumando el costo de cada salida recorrida y usando únicamente salidas abiertas en ese instante en el sentido del recorrido.
- **FR-012**: Si no existe ruta, o si d > rango, el cazador MUST esperar con costo 100.
- **FR-013**: Si existe ruta y d ≤ rango, el cazador MUST moverse un paso por una ruta de costo d; el costo de esa acción MUST ser el costo de la salida que atraviesa.
- **FR-014**: Sea u la sala del cazador; entre las vecinas v alcanzables por una salida abierta con costo(u, v) + dist(v, jugador) = d, el cazador MUST moverse a la de menor id, independientemente de cómo se calcule la ruta.
- **FR-015**: La decisión del cazador MUST depender solo del esqueleto (incluidos los costos), del estado actual de todas las puertas y de la sala actual del jugador; MUST NOT depender de la niebla de guerra del jugador ni de si el contenido de una sala ya fue descargado.
- **FR-016**: El cazador MUST NOT abrir puertas cerradas; una salida cerrada es intransitable para él.
- **FR-017**: La decisión del cazador en cada turno MUST ser idéntica a la que se obtendría calculando la ruta desde cero en ese instante; cualquier reutilización de cálculos previos solo es válida si nunca cambia esa decisión (y debe demostrarse con pruebas).
- **FR-018**: Las decisiones del cazador MUST ser deterministas: no usan azar y, con la misma cripta, semilla y acciones, se repiten exactamente.

**Contrato de datos, persistencia y reproducción**

- **FR-019**: El esqueleto de la cripta MUST aceptar el campo costo opcional en cada salida; esos costos son válidos mientras coincida la versión de la cripta.
- **FR-020**: El catálogo MUST aceptar fichas de enemigo con comportamiento "cazador" y campo rango; son válidas mientras coincida la versión global del catálogo.
- **FR-021**: Las fuentes en línea y sin conexión (modo --offline) MUST entregar los mismos costos y rangos para la misma versión de cripta y de catálogo.
- **FR-022**: Las partidas guardadas y el registro de la partida MUST permitir reanudar y reproducir (--replay) partidas con costos de salida y cazadores con resultado idéntico; los archivos de formato anterior siguen la política existente (incompatibilidad reportada o migración explícita).

**Interfaz**

- **FR-023**: La vista MUST mostrar el costo de cada salida de la sala actual (100 cuando no está declarado).
- **FR-024**: La vista MUST distinguir visualmente a los cazadores de los demás enemigos.

**Rendimiento**

- **FR-025**: Con decenas de cazadores activos persiguiendo al mismo objetivo en la cripta de referencia, resolver un ciclo completo de eventos entre dos decisiones del jugador MUST tomar menos de 20 ms, medido con --bench.
- **FR-026**: El trabajo de la decisión de un cazador con rango pequeño MUST crecer con la región que queda dentro de su rango y no con el tamaño total de la cripta, demostrado con mediciones en criptas de tamaños distintos.

### Key Entities *(include if feature involves data)*

- **Salida**: conexión desde una sala hacia una vecina en una dirección; tiene destino, estado abierto/cerrado, llave opcional y, ahora, costo de tránsito (entero ≥ 1, 100 por omisión).
- **Esqueleto de la cripta**: conjunto de salas y salidas con sus costos, ligado a una versión de cripta; es el mapa completo que conoce el cazador.
- **Ficha de enemigo cazador**: ficha del catálogo con comportamiento "cazador" y rango (entero en unidades de costo), ligada a la versión global del catálogo.
- **Cazador**: enemigo en juego con sala actual, velocidad y rango; decide atacar, esperar o avanzar un paso por la ruta más barata.
- **Distancia de costo d**: suma mínima de costos de salidas abiertas desde la sala del cazador hasta la sala del jugador, calculada en un instante dado.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Los 9 escenarios de aceptación de la descripción tienen una prueba automatizada que cita su requisito y pasa en el 100 % de las ejecuciones.
- **SC-002**: En al menos 1000 situaciones generadas al azar (con semilla fija) de criptas pequeñas con costos y puertas variadas, la decisión del cazador coincide en el 100 % de los casos con la de un cálculo independiente desde cero.
- **SC-003**: Con decenas de cazadores activos en la cripta de referencia, el ciclo de eventos entre dos decisiones del jugador se resuelve en menos de 20 ms en el equipo local.
- **SC-004**: Para un cazador de rango fijo, multiplicar por 10 el tamaño de la cripta sin cambiar la región a su alcance no multiplica de forma proporcional el trabajo de su decisión (medido con --bench).
- **SC-005**: Reproducir con --replay una partida con costos y cazadores produce exactamente la misma secuencia de acciones y estado final que la partida original.
- **SC-006**: Un jugador puede leer en la vista el costo de cada salida de su sala y reconocer a un cazador sin consultar ayuda externa.

## Assumptions

- La regla de reescalado por cambio de velocidad es la vigente (restante × velocidad_anterior // velocidad_nueva, mínimo 1) y no se modifica.
- Guardianes no se mueven, por lo que el costo de salida no les afecta.
- El costo de la primera acción de un enemigo al aparecer no cambia.
- "Sala actual del jugador" es la sala donde está registrado en el instante de la decisión del cazador; el jugador cambia de sala al ejecutar su movimiento.
- Un cazador con rango 0 solo ataca si comparte sala; no se mueve nunca.
- Las indicaciones de la vista que hoy traducen tiempo a "movimientos" (por ejemplo, la duración de la antorcha) siguen usando 100 como referencia aproximada.
- La verificación de resolubilidad de la cripta depende de qué salas son alcanzables, no de costos, por lo que no cambia.
- La cripta de referencia para las mediciones es la misma usada por los límites de rendimiento de la constitución.
- Los enemigos solo persiguen al jugador (no a otros enemigos).
