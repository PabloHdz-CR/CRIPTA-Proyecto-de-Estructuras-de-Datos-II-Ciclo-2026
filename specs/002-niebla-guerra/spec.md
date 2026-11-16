# Feature Specification: Niebla de guerra e «ir a»

**Feature Branch**: `002-niebla-guerra`

**Created**: 2026-11-15

**Status**: Draft

**Input**: User description: "Niebla de guerra y viaje automático «ir a» de la Parte II de Cripta: §3.3 niebla de guerra, §3.4 «ir a», §5.3 el mapa conocido, §6.1 límite de 5 ms por paso, §6.3 mediciones con --bench y §7.3 interfaz mínima" (descripción completa con reglas del juego, 6 escenarios obligatorios del Apéndice B y requisitos de rendimiento en el comando `/speckit-specify` del 2026-11-15, registrado en PROMPTS_LLM.md).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver solo lo que el jugador conoce (Priority: P1)

El jugador ya no ve la cripta entera. Al empezar conoce solo la sala inicial y
sabe que existen las salas a las que llevan sus salidas. Cada sala en la que
entra queda explorada: conoce su nombre, sus salidas, el costo de cada salida y
el estado de sus puertas. Las salas a las que llevan esas salidas quedan
avistadas: sabe que existen, nada más. El resto de la cripta es desconocido.
Con un comando puede abrir el mapa conocido, que lista las salas exploradas con
sus salidas, costos y estado recordado de cada puerta, y las salas avistadas.

**Why this priority**: Es el núcleo de la capacidad: sin el conocimiento del
jugador no hay niebla, ni mapa conocido, ni rutas para «ir a». Las demás
historias leen o modifican ese conocimiento.

**Independent Test**: En una cripta sintética pequeña, sin vista ni red,
iniciar una partida, mover al jugador por un camino conocido y comprobar, sala
por sala, cuáles quedan exploradas, avistadas y desconocidas, y que el mapa
conocido y todo lo que recibe la vista contienen solo esa información.

**Acceptance Scenarios**:

1. **Given** una partida nueva, **When** se consulta el mapa conocido en el instante 0, **Then** la sala inicial figura explorada, con nombre, salidas, costo de cada salida y estado de sus puertas; los destinos de sus salidas figuran avistados, sin nombre ni salidas; ninguna otra sala aparece (FR-001, FR-002, FR-003, FR-016).
2. **Given** una sala avistada, **When** el jugador entra a ella, **Then** pasa a explorada, y los destinos de sus salidas que eran desconocidos pasan a avistados (FR-001, FR-004).
3. **Given** una sala explorada a la que el jugador vuelve, **When** entra otra vez, **Then** sigue explorada y no cambia ninguna otra sala por ese motivo (FR-004).
4. **Given** una partida en curso, **When** la vista dibuja la cripta o el jugador abre el mapa conocido, **Then** no aparece ningún dato de salas desconocidas ni el nombre, las salidas o el contenido de salas avistadas, aunque el programa ya los haya descargado (FR-002, FR-014, FR-015).
5. **Given** el mapa conocido abierto, **When** el jugador lo consulta, **Then** no se consume tiempo de juego ni se registra una acción en partida.log (FR-016, FR-017).

---

### User Story 2 - Recordar el estado de las puertas (Priority: P1)

El mapa recuerda cada puerta como estaba la última vez que el jugador la vio.
El jugador ve una puerta mientras está en cualquiera de las dos salas que
conecta. Si después la puerta cambia (por ejemplo, se cierra sola) y el jugador
ya no está allí, el mapa sigue mostrándola como la vio, hasta que vuelva a
verla.

**Why this priority**: Es la diferencia entre el mapa conocido y la cripta real,
y la base del escenario obligatorio de la puerta que se cerró sin que el
jugador lo supiera. «ir a» decide sus rutas con este recuerdo.

**Independent Test**: En una cripta sintética con una puerta de cierre
automático, abrirla, cruzarla, alejarse, dejar que se cierre y comprobar que el
mapa la sigue recordando abierta; volver a una de sus dos salas y comprobar que
el recuerdo se actualiza.

**Acceptance Scenarios**:

1. **Given** el jugador en una sala, **When** el estado de una de sus puertas cambia mientras sigue allí (la abre con una llave o se cierra sola), **Then** el mapa conocido refleja el estado nuevo (FR-005, FR-006).
2. **Given** una puerta que el mapa recuerda abierta y que se cerró sola cuando el jugador ya no estaba en ninguna de sus dos salas, **When** se consulta el mapa, **Then** la puerta sigue figurando abierta (FR-006).
3. **Given** esa misma puerta recordada abierta y en realidad cerrada, **When** el jugador entra a cualquiera de sus dos salas, **Then** el mapa pasa a recordarla cerrada (FR-005, FR-006).

---

### User Story 3 - Viajar con «ir a» a una sala explorada (Priority: P1)

El jugador escribe «ir a» y elige una sala explorada. El juego lo lleva hasta
ella paso a paso, con movimientos ordinarios, por la ruta más barata que
conoce: solo por salas exploradas y por puertas que el mapa recuerda abiertas.
Cada paso es una acción completa: consume tiempo y, entre un paso y el
siguiente, ocurren los eventos del juego. Antes de cada paso la ruta se vuelve
a calcular con lo que el jugador sabe en ese momento. El viaje se detiene al
llegar, al entrar a una sala con enemigos, al recibir daño o si ya no hay ruta
conocida, y la interfaz dice por qué se detuvo.

**Why this priority**: Es la acción nueva que pide el enunciado y la que más
escenarios obligatorios tiene. Depende de las historias 1 y 2.

**Independent Test**: En criptas sintéticas sin vista ni red, ordenar «ir a»
en situaciones preparadas (destino no explorado, ruta con empate, puerta
recordada abierta que está cerrada, sala con enemigos dormidos, trampa en el
camino) y comprobar la secuencia de movimientos, el tiempo consumido, el motivo
de detención y las líneas de partida.log.

**Acceptance Scenarios**:

1. **Given** una sala avistada o desconocida, **When** el jugador ordena «ir a» hacia ella, **Then** la orden se rechaza con un mensaje, el jugador no se mueve, no se consume tiempo y no se registra ningún movimiento (FR-018, FR-026; Apéndice B).
2. **Given** una puerta que el mapa recuerda abierta y que en realidad está cerrada, en la ruta elegida por «ir a», **When** el jugador llega a una de sus dos salas, **Then** el recuerdo se actualiza a cerrada y la ruta se recalcula antes del paso siguiente; si queda otra ruta conocida, el viaje sigue por ella; si no queda ninguna, el viaje se detiene con el motivo "sin ruta conocida" sin consumir tiempo adicional (FR-005, FR-021, FR-024, FR-025; Apéndice B).
3. **Given** una ruta de «ir a» que entra a una sala con enemigos dormidos, **When** el jugador entra a esa sala, **Then** los enemigos se activan según las reglas de activación de la primera parte (P1 §2.4) y el viaje se detiene con el motivo "enemigos en la sala" (FR-024, FR-025; Apéndice B).
4. **Given** dos rutas de igual costo total hacia el destino, **When** se ordena «ir a», **Then** el primer paso va hacia la sala vecina de menor id, y la elección es la misma en cada ejecución (FR-020, FR-030).
5. **Given** una salida sin costo declarado y otra con costo 30 en rutas alternativas, **When** se calcula la ruta, **Then** la salida sin costo declarado cuenta como 100 (FR-019).
6. **Given** una puerta que el mapa recuerda cerrada y cuya llave tiene el jugador, en la única ruta hacia el destino, **When** se ordena «ir a», **Then** «ir a» no abre la puerta: la orden se rechaza con el motivo "sin ruta conocida" sin consumir tiempo (FR-018, FR-022).
7. **Given** un viaje en curso con varios pasos, **When** termina cada paso, **Then** se consumió el tiempo de un movimiento ordinario por esa salida y se procesaron los eventos pendientes antes del paso siguiente, igual que si el jugador hubiera ordenado cada movimiento a mano (FR-023).
8. **Given** un viaje en el que una trampa, un veneno o un ataque le quita vida al jugador, **When** ocurre el daño, **Then** el viaje se detiene con el motivo "daño recibido" y no se da ningún paso más (FR-024, FR-025).
9. **Given** un viaje que llega a su destino, **When** se completa el último paso, **Then** el viaje termina con el motivo "llegada" (FR-024, FR-025).
10. **Given** una orden «ir a» de tres pasos, **When** se lee partida.log, **Then** contiene una línea de comentario con la orden «ir a» y su destino y, después, tres líneas de movimiento individuales; al reproducirlo con --replay se obtiene el mismo estado final (FR-026, FR-027).
11. **Given** dos rutas de igual costo total hacia el destino, una cuyo primer paso va a la sala vecina 9 y otra cuyo primer paso va a la vecina 10, **When** se ordena «ir a», **Then** el primer paso va a la sala 9, porque los ids de sala se comparan como números (FR-020).

---

### User Story 4 - Antorcha: explorar las salas vecinas (Priority: P2)

Con la antorcha encendida, al entrar a una sala el jugador también explora
todas las salas vecinas, por cualquier salida, abierta o cerrada. De esas
vecinas conoce el nombre y las salidas, pero no su contenido, y no despierta a
sus enemigos ni activa sus trampas.

**Why this priority**: Modifica cómo crece el conocimiento, pero el juego con
niebla funciona sin ella. Tiene un escenario obligatorio propio.

**Independent Test**: En una cripta sintética, encender la antorcha, entrar a
una sala con vecinas (una de ellas con enemigos dormidos y una trampa, otra
detrás de una puerta cerrada) y comprobar qué salas quedan exploradas y
avistadas y que los enemigos y trampas de las vecinas siguen intactos.

**Acceptance Scenarios**:

1. **Given** la antorcha encendida, **When** el jugador entra a una sala, **Then** todas las salas vecinas, por salidas abiertas o cerradas, quedan exploradas con nombre y salidas, sin mostrar su contenido; sus enemigos no se activan y sus trampas no se disparan (FR-008, FR-009; Apéndice B).
2. **Given** la antorcha encendida, **When** las vecinas quedan exploradas, **Then** los destinos de sus salidas que eran desconocidos pasan a avistados (FR-004, FR-008).
3. **Given** la antorcha apagada, **When** el jugador entra a una sala, **Then** solo esa sala queda explorada (FR-004, FR-008).
4. **Given** una vecina explorada por la antorcha en la que el jugador nunca estuvo, **When** se consulta el mapa, **Then** sus salidas figuran con costo y, salvo la puerta que comparte con la sala del jugador, con estado "no observada", y «ir a» no las usa hasta observarlas (FR-007, FR-009, FR-021).

---

### User Story 5 - Deshacer, guardar y reproducir el conocimiento (Priority: P2)

El conocimiento del jugador es parte del estado del juego. El pergamino de
retroceso lo devuelve a como estaba antes de las acciones revertidas, la
partida guardada lo conserva y la reproducción de partida.log lo reconstruye
igual. Un viaje «ir a» es una serie de movimientos individuales: el pergamino
revierte solo el último.

**Why this priority**: Sin esto, deshacer o cargar una partida dejaría un mapa
que no corresponde a lo que el jugador vio. Es requisito de la constitución
(reversibilidad y persistencia versionada) y base de la línea de tiempo
(feature 004).

**Independent Test**: Con una cripta sintética, entrar a una sala con antorcha,
usar el pergamino y comparar el mapa conocido con el de antes de entrar; hacer
un viaje, usar el pergamino con el viaje en curso y comprobar que solo se revirtió el
último paso; guardar y cargar y comparar el mapa conocido; cargar un archivo de
un formato anterior.

**Acceptance Scenarios**:

1. **Given** el jugador entró con la antorcha encendida a una sala y eso exploró varias vecinas, **When** usa el pergamino de retroceso sobre esa entrada, **Then** la sala y todas las vecinas exploradas por ella vuelven a su estado anterior (explorada, avistada o desconocida), y los recuerdos de puertas vuelven a los de antes (FR-010, FR-011; Apéndice B).
2. **Given** un viaje «ir a» en curso que ya dio varios pasos, **When** el jugador usa el pergamino de retroceso sin haber interrumpido antes el viaje, **Then** el viaje se detiene al terminar el paso en curso, el pergamino revierte solo ese último paso (posición, tiempo y conocimiento de ese paso) y el viaje no continúa (FR-011, FR-024, FR-029; Apéndice B).
3. **Given** una partida con salas exploradas, avistadas y puertas recordadas con estados distintos del real, **When** se guarda y se carga, **Then** el mapa conocido cargado es idéntico al guardado, incluidos los recuerdos desactualizados (FR-012).
4. **Given** un archivo de partida de un formato anterior que no incluye el conocimiento del jugador (por ejemplo, de la primera parte), **When** se intenta cargar, **Then** se reporta incompatible con un mensaje que indica la versión del archivo y la esperada, o se migra de forma explícita y avisada; nunca se carga en silencio con un mapa inventado (FR-013).
5. **Given** un partida.log con viajes «ir a», **When** se reproduce con --replay, **Then** las líneas de comentario no se ejecutan como acciones y el conocimiento del jugador al final es idéntico al de la partida original (FR-027).

---

### User Story 6 - Consultas y rutas rápidas (Priority: P3)

Quien evalúa el proyecto quiere comprobar con mediciones que consultar el
estado de una sala o el recuerdo de una puerta es barato, que explorar cuesta
en proporción a las salas reveladas, que registrar e invertir cambios del mapa
es barato y que cada paso de «ir a» se calcula en menos de 5 ms con el mapa
conocido completo de la cripta de referencia.

**Why this priority**: Es un límite de la constitución y del enunciado, pero
solo tiene sentido con las reglas ya correctas.

**Independent Test**: Ejecutar --bench con la cripta de referencia totalmente
explorada y con criptas sintéticas de tamaños crecientes, y comparar los
tiempos con los límites.

**Acceptance Scenarios**:

1. **Given** la cripta de referencia con todas sus salas exploradas, **When** --bench mide el cálculo de un paso de «ir a» entre muchos pares de salas, **Then** cada paso tarda menos de 5 ms (FR-031).
2. **Given** mapas conocidos de tamaños crecientes, **When** --bench mide consultas de estado de sala y de puerta recordada y exploraciones con antorcha, **Then** la consulta no crece con el tamaño del mapa conocido y la exploración crece con la cantidad de salas reveladas, no con el tamaño del mapa (FR-032, FR-033).

---

### Edge Cases

- **«ir a» hacia la sala actual**: se rechaza con un mensaje ("ya estás en esa sala"), sin consumir tiempo ni registrar movimientos (FR-018).
- **«ir a» con un id que no existe en la cripta**: se rechaza igual que una sala desconocida, sin revelar si la sala existe (FR-018).
- **No hay ruta conocida desde el comienzo** (por ejemplo, todas las rutas pasan por puertas recordadas cerradas o no observadas): la orden se rechaza con "sin ruta conocida" y no se consume tiempo (FR-018, FR-021).
- **Una puerta recordada cerrada se abrió sin que el jugador lo supiera**: «ir a» no la usa hasta que el jugador vuelve a observarla (FR-006, FR-021).
- **El primer paso cae en dos salidas distintas hacia la misma vecina con el mismo costo**: se elige la salida en el orden N, S, E, O, como en el desempate de la feature 001 (FR-020).
- **La ruta pasa por la sala de salida con llave_salida**: al entrar, la partida termina por victoria y el viaje termina con ella (FR-024).
- **El jugador muere durante el viaje**: el viaje termina con la partida (FR-024).
- **Un veneno activo quita vida en cada paso**: el viaje se detiene en el primer paso en que el jugador pierde vida, aunque la sala no tenga enemigos (FR-024).
- **Un enemigo errante entra a la sala del jugador entre dos pasos**: si ataca y causa daño, el viaje se detiene por daño; su sola presencia no detiene el viaje (FR-024).
- **El jugador ordena «ir a» estando en una sala con enemigos**: la orden se acepta; el viaje solo se detiene si entra a otra sala con enemigos o recibe daño (FR-024).
- **Una puerta tiene caras con estados distintos**: el mapa recuerda cada cara por separado y «ir a» usa la cara en el sentido en que se recorre (FR-005, FR-021).
- **La antorcha se enciende estando ya en una sala**: no explora las vecinas hasta la próxima entrada a una sala (FR-008).
- **La antorcha se apaga en medio de un viaje**: a partir de ese paso las entradas exploran solo la sala a la que se entra (FR-008).
- **Una vecina explorada con la antorcha tiene enemigos dormidos o trampas**: siguen dormidos y sin dispararse; recién al entrar en ella se aplican las reglas normales, y si es un paso de «ir a», el viaje se detiene (FR-009, FR-024).
- **Pergamino que revierte la primera entrada a una sala**: la sala vuelve a avistada y los destinos que solo esa entrada había vuelto avistados vuelven a desconocidos (FR-010, FR-011).
- **Pergamino que revierte un movimiento a una sala ya explorada**: el conocimiento de salas no cambia, pero los recuerdos de puertas observadas en ese paso vuelven a los anteriores (FR-011).
- **Varios usos seguidos del pergamino después de un viaje**: cada uso revierte un paso individual más, según las reglas del pergamino de la primera parte; el viaje nunca se reanuda solo (FR-029).

## Requirements *(mandatory)*

### Functional Requirements

**Conocimiento del jugador**

- **FR-001**: Para el jugador, cada sala MUST estar en uno de tres estados: explorada (entró al menos una vez, o la exploró la antorcha según FR-008), avistada (no explorada, pero destino de alguna salida de una sala explorada) o desconocida (ninguno de los anteriores). La sala inicial MUST estar explorada desde el instante 0.
- **FR-002**: De una sala explorada, el jugador MUST conocer su nombre, sus salidas (dirección y sala de destino), el costo de cada salida y el estado recordado de cada puerta (FR-006); de una sala avistada, solo que existe y su id; de una sala desconocida, nada.
- **FR-003**: Al iniciar una partida, las salas de destino de las salidas de la sala inicial MUST quedar avistadas y todas las demás desconocidas.
- **FR-004**: Al entrar el jugador a una sala, esa sala MUST quedar explorada y los destinos de sus salidas que eran desconocidos MUST quedar avistados. Ninguna otra sala MUST cambiar de estado por esa entrada, salvo por la antorcha (FR-008).

**Memoria de puertas**

- **FR-005**: El jugador MUST observar una puerta mientras está en cualquiera de las dos salas que conecta: al entrar a la sala, al inicio de la partida para la sala inicial y cada vez que la puerta cambia de estado mientras él sigue allí. Observar una puerta MUST registrar el estado actual de cada una de sus caras.
- **FR-006**: El mapa conocido MUST recordar, para cada cara de puerta, el estado de su última observación, aunque la puerta haya cambiado después sin que el jugador la observara.
- **FR-007**: Una salida de una sala explorada cuya puerta nunca fue observada MUST figurar con estado "no observada".

**Antorcha**

- **FR-008**: Con la antorcha encendida en el momento de entrar a una sala, además de esa sala MUST quedar exploradas todas sus vecinas, por cualquier salida abierta o cerrada, y los destinos desconocidos de las salidas de esas vecinas MUST quedar avistados. Encender la antorcha MUST NOT explorar nada hasta la siguiente entrada a una sala.
- **FR-009**: Explorar una sala con la antorcha MUST revelar solo su nombre, sus salidas y el costo de cada salida; MUST NOT revelar su contenido (objetos, enemigos, trampas), MUST NOT activar sus enemigos ni disparar sus trampas y MUST NOT contar como observación de sus puertas, salvo la que comparte con la sala del jugador.

**Conocimiento como estado del juego**

- **FR-010**: El conocimiento del jugador (estado de cada sala y recuerdo de cada cara de puerta) MUST ser parte del estado del juego y MUST cambiar solo por acciones del jugador o por eventos que el jugador observa.
- **FR-011**: El pergamino de retroceso MUST devolver el conocimiento del jugador exactamente al que tenía antes de las acciones revertidas: estados de salas (incluidas las exploradas o avistadas por la antorcha) y recuerdos de puertas. Para hacerlo MUST registrarse solo lo necesario para invertir cada cambio, sin copias completas del mapa (constitución, principio V).
- **FR-012**: Guardar una partida MUST conservar el conocimiento completo del jugador, y cargarla MUST restaurarlo idéntico, incluidos los recuerdos de puertas que ya no coinciden con su estado real.
- **FR-013**: El archivo de partida MUST cambiar de versión de formato. Un archivo de una versión anterior que no incluye el conocimiento del jugador MUST reportarse incompatible, indicando la versión encontrada y la esperada, o migrarse de forma explícita, con un aviso al jugador que diga qué conocimiento se reconstruyó; MUST NOT cargarse en silencio.
- **FR-034**: El conocimiento del jugador en cada instante MUST poder consultarse a partir de los cambios registrados, para que la línea de tiempo (feature 004) pueda mostrar el mapa conocido de un instante pasado.

**Vista y mapa conocido**

- **FR-014**: Todo lo que la vista muestra sobre la cripta (mapa, salas, salidas, puertas) MUST salir solo del conocimiento del jugador; MUST NOT mostrar datos de salas desconocidas ni nombre, salidas o contenido de salas avistadas.
- **FR-015**: El esqueleto completo de la cripta y la precarga de salas MUST seguir disponibles para el programa como infraestructura (verificación de resolubilidad, enemigos, movimientos), pero MUST NOT llegar a la vista ni a «ir a».
- **FR-016**: La interfaz MUST ofrecer un comando para ver el mapa conocido, que liste las salas exploradas (id y nombre) con cada salida (dirección, sala de destino, costo y estado recordado: abierta, cerrada o no observada) y las salas avistadas (solo su id). Las salas MUST listarse ordenadas por id y las salidas en el orden N, S, E, O.
- **FR-017**: Ver el mapa conocido MUST NOT consumir tiempo de juego ni registrarse como acción en partida.log, y su tecla MUST NOT estar asignada a otra acción en la partida (incluida V, de la feature 003); su uso MUST documentarse en la tabla de teclas del README.

**«ir a»: orden y ruta**

- **FR-018**: La orden «ir a <sala>» MUST aceptarse solo si la sala está explorada, no es la sala actual y existe una ruta conocida según FR-021. Si no, MUST rechazarse con un mensaje que diga el motivo (sala no explorada, ya estás en esa sala o sin ruta conocida), sin mover al jugador, sin consumir tiempo y sin registrar movimientos. El mensaje para una sala desconocida o inexistente MUST ser el mismo.
- **FR-019**: El costo de una ruta MUST ser la suma de los costos de sus salidas; una salida sin costo declarado MUST valer 100.
- **FR-020**: La ruta MUST minimizar el costo total. Entre rutas de igual costo MUST elegirse la que da el primer paso hacia la sala vecina de menor id (los ids de sala son enteros y se comparan como números, igual que el cazador de la feature 001, FR-014 de 001); si hay varias salidas hacia esa vecina con el mismo costo mínimo, la primera en el orden N, S, E, O.
- **FR-021**: La ruta MUST usar solo salas exploradas y salidas cuya cara, en el sentido en que se recorre, el mapa recuerda abierta. MUST NOT usar salidas recordadas cerradas o no observadas, ni información que no esté en el conocimiento del jugador.
- **FR-022**: «ir a» MUST NOT abrir puertas, aunque el jugador tenga la llave.

**«ir a»: ejecución**

- **FR-023**: Cada paso del viaje MUST ser un movimiento ordinario del jugador por una sola salida, con el mismo costo de tiempo, los mismos efectos y los mismos eventos que ese movimiento ordenado a mano; entre un paso y el siguiente MUST procesarse los eventos del juego.
- **FR-024**: Antes de cada paso, con las observaciones de la sala actual ya registradas (FR-005), la ruta MUST recalcularse desde cero con el conocimiento vigente. El viaje MUST detenerse, sin dar más pasos, en el primero de estos casos: (a) el jugador llegó al destino; (b) el jugador entró a una sala con enemigos activos o dormidos (los dormidos se activan según P1 §2.4); (c) el jugador recibió daño de cualquier fuente durante el último paso o los eventos que lo siguieron; (d) ya no hay ruta conocida al destino, en cuyo caso no se consume tiempo adicional; (e) la partida terminó (victoria o muerte); (f) el jugador usó el pergamino de retroceso durante el viaje (FR-029); (g) el jugador interrumpió el viaje (FR-028).
- **FR-025**: Al detenerse el viaje, la interfaz MUST mostrar el motivo de la detención: "llegada", "enemigos en la sala", "daño recibido", "sin ruta conocida", "partida terminada", "pergamino de retroceso" o "interrumpido" (§7.3).
- **FR-026**: En partida.log, cada paso de «ir a» MUST registrarse como un movimiento individual, igual que un movimiento hecho a mano, y la orden «ir a» MUST registrarse además como una línea de comentario con el destino, antes del primer paso. Una orden rechazada MUST NOT registrar movimientos.
- **FR-027**: --replay MUST ignorar las líneas de comentario de partida.log al ejecutar acciones y MUST reproducir los viajes a partir de sus movimientos individuales, con el mismo estado final, incluido el conocimiento del jugador.
- **FR-028**: Como opción adicional, el jugador MUST poder interrumpir un viaje sin usar el pergamino; el paso en curso termina y no se da ninguno más.
- **FR-029**: Si el jugador usa el pergamino de retroceso mientras un viaje está en curso, el viaje MUST detenerse al terminar el paso en curso y el pergamino MUST revertir solo ese último paso, con su tiempo y sus cambios de conocimiento; el viaje MUST NOT continuar. No hace falta interrumpir el viaje antes. Usar el pergamino después de un viaje ya detenido MUST revertir igualmente solo el último movimiento individual.
- **FR-030**: El resultado de una orden «ir a» (ruta elegida, pasos dados y motivo de detención) MUST depender solo del estado del juego y de la semilla, nunca de la hora del sistema ni del orden de llegada de respuestas (constitución, principio II).

**Rendimiento**

- **FR-031**: Calcular cada paso de «ir a» MUST tardar menos de 5 ms con el mapa conocido completo de la cripta de referencia, medido con --bench en el equipo local (§6.1, §6.3).
- **FR-032**: Consultar el estado de una sala para el jugador y el estado recordado de una puerta MUST tener un costo que no crece con la cantidad de salas del mapa conocido.
- **FR-033**: Explorar (por entrada o por antorcha) MUST costar en proporción a la cantidad de salas y salidas reveladas, no al tamaño del mapa conocido; registrar e invertir un cambio del conocimiento MUST costar en proporción al tamaño de ese cambio.

### Key Entities *(include if feature involves data)*

- **Conocimiento del jugador**: lo que el jugador sabe de la cripta en un instante. Para cada sala, su estado (explorada, avistada, desconocida); para cada cara de puerta de una sala explorada, su estado recordado (abierta, cerrada, no observada). Es parte del estado del juego.
- **Observación de puerta**: el registro del estado real de las caras de una puerta en un instante en que el jugador está en una de sus dos salas; reemplaza al recuerdo anterior.
- **Cambio de conocimiento**: lo que una acción o un evento cambió en el conocimiento (salas que cambiaron de estado y recuerdos de puertas que cambiaron, con su valor anterior). Es lo mínimo para invertirlo con el pergamino y para la línea de tiempo.
- **Mapa conocido**: la vista de consulta del conocimiento: salas exploradas con sus salidas, costos y estados recordados, y salas avistadas.
- **Orden «ir a»**: un destino elegido por el jugador; produce una serie de movimientos individuales y termina con un motivo de detención.
- **Motivo de detención**: llegada, enemigos en la sala, daño recibido, sin ruta conocida, partida terminada, pergamino de retroceso o interrumpido.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Los 30 escenarios de aceptación de esta especificación (5 + 3 + 11 + 4 + 5 + 2), incluidos los 6 obligatorios del Apéndice B, tienen al menos una prueba automatizada o un partida.log que los ejerce y todas pasan.
- **SC-002**: En el 100 % de las partidas de prueba, ningún dato que recibe la vista ni ningún paso de «ir a» proviene de una sala desconocida, del nombre o salidas de una sala avistada, o de una puerta en un estado distinto del recordado.
- **SC-003**: Para 1000 secuencias de acciones aleatorias con semilla fija sobre criptas sintéticas, aplicar las acciones y luego revertirlas con el pergamino devuelve el conocimiento del jugador idéntico al inicial; y guardar y cargar en cualquier punto devuelve un conocimiento idéntico.
- **SC-004**: Con el mapa conocido completo de la cripta de referencia, el cálculo de cada paso de «ir a» tarda menos de 5 ms en todos los pares de salas medidos con --bench.
- **SC-005**: Al multiplicar por 4 el tamaño del mapa conocido, el tiempo medio de una consulta de estado de sala o de puerta recordada no crece más de 1,5 veces, y el de una exploración con antorcha que revela la misma cantidad de salas tampoco.
- **SC-006**: La ruta de cada paso de «ir a» coincide en el 100 % de los casos con la de una búsqueda de referencia que calcula desde cero el camino de menor costo con la misma regla de desempate, en al menos 1000 pares de salas de criptas sintéticas.
- **SC-007**: Reproducir con --replay 20 partidas con viajes «ir a» da el mismo estado final y el mismo conocimiento del jugador que la partida original en todas.

## Assumptions

- **Fuente de las reglas**: Cripta Parte II §3.3 (niebla de guerra), §3.4 («ir a»), §5.3 (el mapa conocido como problema de estructuras de datos), §6.1 (límite de 5 ms por paso de «ir a»), §6.3 (mediciones con --bench), §7.3 (interfaz mínima: ver el mapa conocido, ejecutar «ir a» y ver por qué se detuvo) y Apéndice B (6 escenarios obligatorios), y las reglas de la primera parte para movimiento, antorcha, pergamino y activación de enemigos (P1 §2.4).
- **Salidas de vecinas exploradas con la antorcha**: como el jugador no está en la vecina, sus puertas (salvo la que comparte con la sala actual) no se observan y figuran "no observada"; «ir a» no las usa hasta que el jugador entre a esa vecina o a la sala del otro lado. Es la lectura literal de "observa una puerta cuando está en cualquiera de las dos salas"; es candidata a confirmarse en /speckit-clarify.
- **Identificación de salas avistadas**: el mapa conocido muestra el id de una sala avistada (lo que dice la salida que lleva a ella) pero no su nombre. El destino de «ir a» se indica por el id de una sala explorada, tal como aparece en el mapa conocido.
- **Daño durante el viaje**: "recibir daño" incluye cualquier pérdida de vida (ataque, trampa, veneno), en el paso o en los eventos que lo siguen. Un veneno activo detiene el viaje en el primer paso con pérdida de vida.
- **Enemigos y viaje**: detiene el viaje entrar a una sala con enemigos activos o dormidos; un enemigo que llega a la sala del jugador entre pasos solo lo detiene si le causa daño. Se puede ordenar «ir a» desde una sala con enemigos.
- **Pergamino e interrupción**: en el escenario obligatorio "un pergamino durante un viaje", el jugador usa el pergamino con el viaje en curso, sin interrumpirlo antes: el viaje se detiene al terminar el paso en curso y el pergamino revierte ese paso (FR-029); el pergamino nunca se aplica en medio de un paso. La interrupción manual sin pergamino (FR-028) es una opción adicional.
- **Archivo de la primera parte**: la opción por defecto es reportarlo incompatible (FR-013), porque no puede reconstruirse fielmente lo que el jugador vio. Si el plan elige migrar, la migración debe avisar qué reconstruyó y no inventar recuerdos de puertas. Lo mismo vale para el formato actual de la feature 001, que tampoco tiene el conocimiento del jugador.
- **Línea de tiempo**: esta capacidad solo deja el conocimiento registrado de forma reversible y consultable por instante (FR-034); la vista de línea de tiempo es la feature 004.
- **Costos de salida**: los da la feature 001 (terreno), incluida la regla de que un costo nulo equivale a no declarado; aquí sin costo declarado vale 100 (FR-019).
- **Teclas**: las letras en uso en la partida son A, B, C, G, L, N, O, P, Q, R, S, U, V y X; el plan elige las del mapa conocido y de «ir a» sin repetirlas y las coordina con la feature 004.
- **Cripta de referencia**: la publicada más grande entre las disponibles al medir (hoy cripta-06), sin escribir su id ni su tamaño en el código (constitución, principio IV).
- **Orden de comparación de ids**: los ids de sala son enteros y se comparan como números (9 va antes que 10), igual que el cazador de la feature 001 (FR-014 de 001). La comparación como texto, carácter por carácter, es solo para los ids de llaves de la feature 003.
