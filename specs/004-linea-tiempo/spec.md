# Feature Specification: Línea de tiempo

**Feature Branch**: `004-linea-tiempo`

**Created**: 2026-11-17

**Status**: Draft

**Input**: User description: "Línea de tiempo de la Parte II de Cripta: §3.6 línea de tiempo, §5.5 línea de tiempo y puntos de control, §5.6 revisión del historial de retroceso, §6.1 límite de 50 ms por consulta, §6.3 mediciones con --bench y §7.3 interfaz mínima" (descripción completa con reglas del juego, 6 escenarios obligatorios del Apéndice B y requisitos de rendimiento en el comando `/speckit-specify` del 2026-11-17, registrado en PROMPTS_LLM.md).

## Clarifications

### Session 2026-11-17

- Q: Cuando `--replay partida.log --hasta t` reproduce un log con pergaminos, ¿el resumen muestra la historia tal como quedó con esos pergaminos aplicados, o el estado por el que pasa la reproducción al llegar a t antes de un pergamino posterior? → A: La historia tal como quedó: se aplican todos los pergaminos del log y se muestra el instante t de esa historia; coincide con «historia <t>» al final de la partida original (FR-014).
- Q: Si el jugador aprieta H mientras un viaje «ir a» está en curso, ¿el viaje se detiene para abrir la consulta? → A: Sí: H detiene el viaje con el motivo "interrumpido" y abre la consulta; es una excepción deliberada a la regla de la feature 002 de que las teclas de presentación no detienen un viaje (FR-017).
- Q: Un pergamino recogido durante acciones que otro pergamino revirtió sigue en el inventario (D50), pero su recogida ya no existe en la historia: ¿desde qué instante figura en el inventario al consultar la línea de tiempo? → A: Desde el reloj actual (el instante al que volvió el reloj); no figura en los instantes anteriores (FR-008).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar el estado de un instante pasado (Priority: P1)

En medio de una partida, el jugador quiere saber cómo estaba todo en un
momento anterior: en qué sala estaba, cuánta vida tenía, qué llevaba, qué
efectos tenía, qué enemigos había en su sala y qué parte del mapa conocía.
Pide «historia <t>» con un instante del reloj del juego, o «historia #k» con
el número de una de sus acciones, y ve un resumen de ese momento. La consulta
es solo de lectura: la partida sigue exactamente donde estaba.

**Why this priority**: Es la capacidad entera; sin la consulta no hay línea de
tiempo. Las demás historias la extienden (pergamino, reproducción, guardado,
ventana) o la miden.

**Independent Test**: En una cripta sintética, sin vista ni red, jugar una
secuencia fija de acciones, consultar varios instantes y números de acción, y
comparar cada resumen con el estado que se obtiene reproduciendo desde el principio solo las acciones que siguen existiendo en la historia (sin las revertidas por pergaminos) hasta ese instante. No sirve reproducir la partida tal como se jugó: con pergaminos el reloj vuelve atrás y las acciones nuevas reusan los mismos instantes, así que esa reproducción pasa por la rama revertida (FR-007, FR-014).

**Acceptance Scenarios**:

1. **Given** una partida en curso con reloj R, **When** el jugador consulta «historia <t>» con t mayor que R, **Then** la consulta se rechaza con un mensaje que indica el reloj actual, y nada de la partida cambia (FR-003, FR-012; Apéndice B).
2. **Given** varios eventos que ocurrieron en el mismo instante t (por ejemplo, el turno de dos enemigos y un efecto que vence), **When** se consulta «historia <t>», **Then** el resumen muestra el estado después de todos ellos (FR-001, FR-004; Apéndice B).
3. **Given** una partida en curso, **When** el jugador consulta «historia <t>» o «historia #k», **Then** no se consume tiempo del juego, no se escribe nada en partida.log y el historial del pergamino queda exactamente igual: el siguiente uso del pergamino revierte lo mismo que habría revertido sin la consulta (FR-011, FR-012; Apéndice B).
4. **Given** un instante t en el que el jugador tenía que decidir su próxima acción, **When** se consulta «historia <t>», **Then** el resumen muestra el estado justo antes de esa decisión, no después (FR-001).
5. **Given** una partida en la que el jugador hizo n acciones, **When** consulta «historia #k» con 1 ≤ k ≤ n, **Then** ve el estado justo antes de su acción número k; con k = n + 1 ve el estado actual; con k = 0, k > n + 1 o un valor que no es número entero, la consulta se rechaza con un mensaje (FR-002, FR-003).
6. **Given** una partida con un viaje «ir a» de tres pasos, **When** se consulta «historia #k» para cada paso, **Then** cada paso cuenta como una acción distinta, y las acciones rechazadas, las consultas y el uso del pergamino no cuentan (FR-002).
7. **Given** cualquier instante consultado, **When** se muestra el resumen, **Then** incluye al menos: reloj, sala del jugador (id y nombre), vida actual y máxima, ataque, defensa y velocidad, inventario con lo equipado, efectos activos, enemigos de esa sala con su vida, y el mapa conocido de ese momento con el mismo formato que el panel del mapa de la feature 002 (FR-005, FR-006).
8. **Given** el instante 0, **When** se consulta «historia 0» o «historia #1», **Then** se ve el estado inicial de la partida: la sala inicial, la vida completa y el mapa conocido inicial (FR-001, FR-002).

---

### User Story 2 - La línea de tiempo respeta el pergamino (Priority: P1)

Después de usar el pergamino de retroceso, la historia de la partida es la que
quedó: las acciones revertidas ya no existen y no deben aparecer al consultar
el pasado. El pergamino sigue limitado a 5 acciones y es independiente de la
línea de tiempo.

**Why this priority**: Es la regla que distingue a la línea de tiempo de un
simple registro de todo lo que pasó, y tiene un escenario obligatorio propio.

**Independent Test**: Jugar varias acciones, usar el pergamino para revertir
dos, jugar otras distintas y consultar instantes y números de acción antes,
durante y después del tramo revertido.

**Acceptance Scenarios**:

1. **Given** el jugador hizo acciones que después revirtió con un pergamino, **When** consulta la historia de cualquier instante, **Then** no aparece ningún efecto de las acciones revertidas: se ve la historia tal como quedó (FR-007; Apéndice B).
2. **Given** el jugador revirtió dos acciones y después hizo otras dos distintas, **When** consulta «historia #k» con los números de las acciones nuevas, **Then** ve el estado antes de las acciones nuevas (la numeración sigue la historia que quedó, sin huecos) (FR-002, FR-007).
3. **Given** el jugador usó el pergamino, **When** consulta un instante anterior al reloj actual, **Then** el pergamino gastado sigue figurando en el inventario de ese instante, porque se gastó al usarlo, en el reloj actual (FR-008).
4. **Given** el jugador usó el pergamino y el reloj volvió a R', **When** consulta un instante mayor que R' (aunque antes del pergamino el reloj lo hubiera alcanzado), **Then** la consulta se rechaza por ser posterior al reloj actual (FR-003, FR-007).
5. **Given** el jugador recogió un pergamino durante acciones que después revirtió con otro pergamino, y el reloj volvió a R', **When** consulta instantes menores que R' y el instante R', **Then** ese pergamino no figura en el inventario de los instantes menores que R' y sí figura desde R' (FR-008).

---

### User Story 3 - Consultar sin interacción con --replay … --hasta (Priority: P1)

Quien revisa el proyecto, o el propio jugador después de una partida, quiere
ver el estado de un instante sin abrir el juego: reproduce un partida.log
hasta un instante y obtiene el mismo resumen por la salida de texto.

**Why this priority**: Es la forma obligatoria de consultar sin interacción y
la que se usa en la revisión para repetir escenarios.

**Independent Test**: Grabar una partida con pergaminos y viajes «ir a»,
reproducirla con --replay … --hasta t para varios t y comparar cada resumen
con el que da «historia <t>» al final de la partida original y con el estado
que se obtiene reproduciendo desde el principio solo las acciones que siguen
existiendo (sin las revertidas), no la partida tal como se jugó (FR-014).

**Acceptance Scenarios**:

1. **Given** un partida.log de una partida que terminó en el reloj F, **When** se ejecuta --replay partida.log --hasta t con t mayor que F, **Then** se imprime el estado final y un aviso de que la partida terminó antes, en el instante F (FR-013; Apéndice B).
2. **Given** un partida.log y un instante t menor o igual que el final, **When** se ejecuta --replay partida.log --hasta t, **Then** se imprime el mismo resumen que mostraría «historia <t>» en la partida original al terminar, sin abrir la ventana (FR-013, FR-014).
3. **Given** un partida.log con pergaminos que revirtieron acciones, **When** se reproduce --hasta t con t dentro del tramo que quedó, **Then** el resumen corresponde a la historia tal como quedó, no a las acciones revertidas (FR-007, FR-014).
4. **Given** --hasta sin --replay, o un valor de t que no es un entero mayor o igual que 0, **When** se arranca el programa, **Then** termina con un mensaje de error que explica el uso, sin abrir la ventana (FR-015).
5. **Given** un partida.log cuya versión de cripta o de catálogo ya no está disponible, **When** se ejecuta con --hasta, **Then** se informa que no puede garantizarse una reproducción fiel, igual que --replay sin --hasta (FR-016).

---

### User Story 4 - Guardar y cargar conserva la línea de tiempo (Priority: P2)

El jugador guarda, sale y vuelve a cargar la partida; todas las consultas de
instantes anteriores dan lo mismo que antes de guardar.

**Why this priority**: Es un requisito del enunciado y de la constitución
(persistencia versionada), pero la capacidad se puede usar sin guardar.

**Independent Test**: Jugar, consultar varios instantes, guardar, cargar,
repetir las consultas y comparar; cargar un archivo de un formato anterior.

**Acceptance Scenarios**:

1. **Given** una partida con historia (incluidos pergaminos y viajes), **When** se guarda y se carga, **Then** «historia <t>» e «historia #k» dan el mismo resumen que antes de guardar para todos los instantes y números de acción (FR-009).
2. **Given** un archivo de partida de un formato anterior (de la primera parte o de la feature 002), **When** se intenta cargar, **Then** se reporta incompatible con un mensaje que indica la versión encontrada y la esperada, y no se carga (FR-010; Apéndice B).
3. **Given** una partida cargada, **When** el jugador sigue jugando y consulta instantes de antes y de después de la carga, **Then** la línea de tiempo es continua: no hay saltos ni estados perdidos en el punto de la carga (FR-009).

---

### User Story 5 - Consultar desde la ventana con la tecla H (Priority: P2)

En la ventana del juego, el jugador aprieta H, escribe un instante o un número
de acción con #, confirma con Enter y ve el resumen; con ESC vuelve a la
partida.

**Why this priority**: Es la interfaz mínima pedida (§7.3), pero la lógica de
la consulta se prueba sin ventana.

**Independent Test**: Con la ventana real y una partida corta, abrir la
consulta, escribir un instante válido, uno inválido y un #k, y comprobar el
resumen, el mensaje de error y que la partida no cambió.

**Acceptance Scenarios**:

1. **Given** una partida en curso en la ventana, **When** el jugador aprieta H, escribe «120» y Enter, **Then** se muestra el resumen del instante 120; con ESC vuelve a la partida sin que el reloj haya avanzado (FR-017, FR-018).
2. **Given** la consulta abierta, **When** el jugador escribe «#3» y Enter, **Then** se muestra el estado justo antes de su acción número 3 (FR-017).
3. **Given** la consulta abierta, **When** el jugador escribe un valor inválido (texto, negativo o un instante posterior al reloj actual) y Enter, **Then** se muestra el motivo del rechazo y la consulta sigue abierta para corregirlo (FR-003, FR-017).
4. **Given** la consulta abierta, **When** el jugador escribe, **Then** las letras y flechas no mueven al jugador ni disparan otras acciones (FR-018).

---

### User Story 6 - Memoria acotada y consultas rápidas en partidas largas (Priority: P3)

Quien evalúa el proyecto quiere comprobar con mediciones que la consulta es
rápida aunque la partida sea larga, que la memoria no crece como «una copia
del estado por acción» y que el valor por defecto de K está justificado.

**Why this priority**: Es el núcleo del problema de estructuras de datos
(§5.5), pero solo tiene sentido con las reglas ya correctas.

**Independent Test**: Ejecutar --bench con partidas sintéticas de 5000 o más
acciones del jugador para al menos tres valores de K y sin puntos de control,
y comparar memoria y tiempo de consulta con los límites.

**Acceptance Scenarios**:

1. **Given** una partida de al menos 5000 acciones del jugador con el K por defecto, **When** --bench mide consultas a instantes repartidos en toda la partida, **Then** cada consulta tarda menos de 50 ms (FR-019).
2. **Given** partidas largas medidas con al menos tres valores de K y sin puntos de control, **When** --bench reporta memoria y tiempo de consulta, **Then** la memoria crece con los cambios ocurridos más un punto de control cada K acciones, y la tabla permite justificar el K por defecto (FR-020, FR-021, FR-024).
3. **Given** una partida larga, **When** el jugador usa el pergamino, **Then** el recorte de la línea de tiempo cuesta en proporción a lo revertido, no al largo de la historia (FR-023).

---

### Edge Cases

- **Consulta del instante actual** («historia <R>» con R el reloj actual, o «historia #(n+1)»): muestra el estado actual, el mismo que se ve en pantalla (FR-001, FR-002).
- **Instante entre dos decisiones del jugador**: muestra el estado después de los eventos con tiempo menor o igual que t, aunque el jugador no haya decidido en ese instante (FR-001).
- **Partida terminada (victoria o derrota)**: en la ventana, H existe solo durante la partida; después de terminar, el estado de cualquier instante se consulta con --replay … --hasta sobre el log archivado (FR-013, FR-017).
- **Viaje «ir a» en curso**: apretar H detiene el viaje (motivo "interrumpido") y abre la consulta. Es una excepción deliberada a la regla de la feature 002 de que las teclas de presentación (M, Tab, O, L, V) no detienen un viaje: no se puede escribir un instante mientras el jugador camina (FR-017).
- **Pergamino que revierte un viaje**: los pasos revertidos dejan de existir en la línea de tiempo, como cualquier otra acción (FR-007).
- **Pergamino justo después de cargar**: el historial del pergamino no se guarda (decisión de la primera parte), pero la línea de tiempo sí; consultar instantes anteriores a la carga sigue funcionando (FR-009).
- **Instante anterior a cualquier acción** (0 ≤ t antes de la primera decisión): muestra el estado inicial más los eventos que ya ocurrieron (FR-001).
- **K = 1**: puede haber un punto de control por acción; la consulta es inmediata y la memoria es la mayor. **K mayor que la cantidad de acciones**: no hay más punto de control que el inicial y las consultas cuestan más, sin pasar nunca el límite de K acciones por consulta (FR-020, FR-021).
- **--checkpoint-cada con 0, negativo o texto**: el programa termina con un mensaje de error antes de empezar (FR-022).
- **Mapa conocido en el pasado**: el resumen muestra lo que el jugador conocía en ese instante, incluidos los recuerdos de puertas que después cambiaron (FR-006).

## Requirements *(mandatory)*

### Functional Requirements

**Qué se consulta**

- **FR-001**: El estado en el instante t MUST ser el estado después de ejecutar todos los eventos con tiempo menor o igual que t; si a t le corresponde una decisión del jugador, MUST ser el estado justo antes de tomarla. t MUST ser un entero mayor o igual que 0 en unidades del reloj del juego.
- **FR-002**: «historia #k» MUST mostrar el estado justo antes de la acción número k del jugador, contando desde 1 solo las acciones que siguen existiendo en la historia (no las revertidas). Cada paso de «ir a» MUST contar como una acción; las acciones rechazadas, las consultas y el uso del pergamino MUST NOT contar. Con n acciones hechas, k = n + 1 MUST mostrar el estado actual.
- **FR-003**: Una consulta MUST rechazarse, con un mensaje que diga el motivo, si t es mayor que el reloj actual, si k es menor que 1 o mayor que n + 1, o si el valor no es un entero válido.
- **FR-004**: Cuando varios eventos ocurren en el mismo instante t, «historia <t>» MUST mostrar el estado después de todos ellos, en el orden de desempate de la primera parte.
- **FR-005**: El resumen de un instante MUST incluir como mínimo: reloj, sala del jugador (id y nombre), vida actual y máxima, ataque, defensa y velocidad, inventario (con lo equipado), efectos activos con su tiempo restante, enemigos de esa sala con su vida, y el mapa conocido de ese instante.
- **FR-006**: El mapa conocido del resumen MUST ser el conocimiento del jugador en ese instante (feature 002): salas exploradas con sus salidas, costos y estados recordados, y salas avistadas, con el mismo formato que el panel del mapa. MUST NOT mostrar información que el jugador no tenía en ese instante.

**Pergamino**

- **FR-007**: Las acciones revertidas con un pergamino, con todos sus efectos y eventos, MUST dejar de existir en la línea de tiempo; la línea MUST describir la historia tal como quedó. El pergamino MUST seguir limitado a 5 acciones y MUST NOT depender de la línea de tiempo.
- **FR-008**: El pergamino gastado MUST figurar en el inventario de los instantes anteriores al reloj actual y dejar de figurar desde el reloj actual, porque se gasta al usarlo y el uso no consume tiempo. Un pergamino recogido durante las acciones revertidas, que sigue en el inventario por la regla de la primera parte (D50), MUST figurar desde el reloj actual y MUST NOT figurar en los instantes anteriores, porque su recogida ya no existe en la historia.

**Persistencia**

- **FR-009**: Guardar una partida MUST conservar la línea de tiempo completa, y cargarla MUST restaurarla de modo que toda consulta dé el mismo resumen que antes de guardar, y que la historia sea continua al seguir jugando.
- **FR-010**: El archivo de partida MUST cambiar de versión de formato. Un archivo de una versión anterior (de la primera parte o de la feature 002) MUST reportarse incompatible, indicando la versión encontrada y la esperada, y MUST NOT cargarse en silencio.

**Consulta sin modificar la partida**

- **FR-011**: Una consulta MUST NOT modificar ningún estado del juego: ni el reloj, ni el azar, ni la agenda, ni el conocimiento del jugador, ni el historial del pergamino. Después de cualquier consulta, la partida MUST continuar exactamente igual que sin ella.
- **FR-012**: Una consulta MUST NOT consumir tiempo virtual, MUST NOT registrarse en partida.log y MUST NOT hacer solicitudes de red ni gastar presupuesto.

**Sin interacción**

- **FR-013**: `--replay partida.log --hasta t` MUST reproducir la partida sin abrir la ventana e imprimir el resumen del instante t (FR-005). Si t es mayor que el reloj en que terminó la partida, MUST imprimir el estado final e indicar que la partida terminó antes, en qué instante.
- **FR-014**: El resumen de `--replay … --hasta t` MUST ser idéntico al que mostraría «historia <t>» al final de la partida original: la historia tal como quedó, con los pergaminos aplicados.
- **FR-015**: `--hasta` sin `--replay`, o con un valor que no es un entero mayor o igual que 0, MUST terminar con un mensaje de uso y código de error, sin abrir la ventana.
- **FR-016**: Si la versión de la cripta o del catálogo del log ya no está disponible, `--replay … --hasta` MUST informarlo igual que `--replay` y MUST NOT imprimir un resumen de datos distintos.

**Ventana**

- **FR-017**: En la ventana, la tecla H MUST abrir la consulta: el jugador escribe un instante (por ejemplo «120») o un número de acción con # (por ejemplo «#3»), confirma con Enter y ve el resumen; un valor inválido MUST mostrar el motivo sin cerrar la consulta; ESC MUST volver a la partida. Con un viaje «ir a» en curso, H MUST detener el viaje (motivo "interrumpido") antes de abrir la consulta: es una excepción deliberada a la regla de la feature 002 (las teclas de presentación M, Tab, O, L y V no detienen un viaje), porque no se puede escribir un instante mientras el jugador camina. H MUST existir solo durante la partida, no en el replay en la ventana ni en otras pantallas.
- **FR-018**: Con la consulta abierta, las teclas MUST ir solo a la consulta: MUST NOT mover al jugador, abrir otras selecciones ni disparar acciones. La tecla H y su uso MUST documentarse en la tabla de teclas del README.

**Memoria y rendimiento**

- **FR-019**: Una consulta «historia» MUST tardar menos de 50 ms en una partida de al menos 5000 acciones del jugador con el K por defecto, medido con --bench en el equipo local (§6.1, §6.3).
- **FR-020**: Se MAY guardar copias completas del estado (puntos de control), pero no más de una cada K acciones del jugador. Fuera de los puntos de control MUST guardarse solo lo necesario para reconstruir los cambios. La memoria total MUST crecer con la cantidad de cambios ocurridos más un punto de control cada K acciones, nunca con acciones por tamaño del estado.
- **FR-021**: Una consulta MUST NOT requerir aplicar o deshacer cambios de más de K acciones del jugador. Reconstruir un instante MUST dar exactamente el estado que tuvo la partida, incluido todo lo que depende del azar.
- **FR-022**: K MUST configurarse con `--checkpoint-cada K` (entero mayor o igual que 1); sin la opción, MUST usarse un valor por defecto justificado con mediciones. Un valor inválido MUST terminar con un mensaje de error antes de empezar.
- **FR-023**: Ubicar el punto de control más cercano a un instante pedido MUST tener un costo que no crece linealmente con la cantidad de puntos de control. Al usar un pergamino, recortar la línea de tiempo MUST costar en proporción a lo revertido, sin recorrer toda la historia.
- **FR-024**: --bench MUST medir memoria y tiempo de consulta para al menos tres valores de K y para la alternativa sin puntos de control (§5.5, §6.3), y MUST incluir la evidencia de la decisión entre reconstruir hacia adelante o hacia atrás (§5.5).
- **FR-025**: --bench MUST repetir las mediciones del historial del pergamino de la primera parte con la carga nueva (línea de tiempo, viajes y cazadores), y el resultado MUST documentarse como "sigue siendo adecuado" o "se cambió", con el antes y el después (§5.6).
- **FR-026**: El resultado de una consulta MUST depender solo de la historia de la partida, nunca de la hora del sistema, del valor de K ni del orden de llegada de respuestas (constitución, principio II).

### Key Entities *(include if feature involves data)*

- **Línea de tiempo**: la historia de la partida tal como quedó, desde el instante 0 hasta el reloj actual, consultable en cualquier instante; excluye lo revertido con pergaminos.
- **Instante**: un valor del reloj del juego (entero ≥ 0) o un número de acción del jugador (#k); define qué estado se consulta.
- **Resumen de un instante**: lo que se muestra de una consulta (FR-005), igual en la ventana y en --replay … --hasta.
- **Punto de control**: una copia completa del estado en un instante, permitida como mucho una cada K acciones del jugador.
- **Cambio registrado**: lo mínimo que hace falta para reconstruir lo que una acción o un evento cambió, entre puntos de control.
- **K**: la cantidad de acciones del jugador entre puntos de control; configurable con --checkpoint-cada.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Los 28 escenarios de aceptación de esta especificación (8 + 5 + 5 + 3 + 4 + 3), incluidos los 6 obligatorios del Apéndice B, tienen al menos una prueba automatizada o un partida.log que los ejerce y todas pasan.
- **SC-002**: En 1000 consultas a instantes y números de acción elegidos con semilla fija, sobre partidas sintéticas de al menos 500 acciones con pergaminos y viajes «ir a», el resumen coincide en el 100 % de los casos con el estado que se obtiene reproduciendo desde el principio solo las acciones que siguen existiendo en la historia (sin las revertidas por pergaminos) hasta ese instante. No sirve reproducir la partida tal como se jugó: con pergaminos el reloj vuelve atrás y las acciones nuevas reusan los mismos instantes, así que esa reproducción pasa por la rama revertida.
- **SC-003**: En una partida de al menos 5000 acciones del jugador con el K por defecto, todas las consultas medidas por --bench tardan menos de 50 ms.
- **SC-004**: En 1000 secuencias aleatorias de acciones con consultas intercaladas, la partida resultante (reloj, estado, partida.log y lo que revierte el siguiente pergamino) es idéntica a la misma secuencia sin consultas.
- **SC-005**: Guardar y cargar en un punto elegido con semilla, en cada una de esas secuencias, no cambia el resumen de ningún instante consultado.
- **SC-006**: Para 20 partidas grabadas, `--replay … --hasta t` da el mismo resumen que «historia <t>» al final de la partida original, para al menos 10 instantes de cada una.
- **SC-007**: La tabla de --bench muestra, para al menos tres valores de K y sin puntos de control, la memoria y el tiempo de consulta; con el K por defecto, la memoria es menos de la mitad que con un punto de control por acción (K = 1) y la consulta cumple SC-003.

## Assumptions

- **Fuente de las reglas**: Cripta Parte II §3.6 (línea de tiempo), §5.5 (línea de tiempo y puntos de control), §5.6 (revisión del historial de retroceso), §6.1 (límite de 50 ms con 5000 acciones), §6.3 (mediciones con --bench), §7.3 (interfaz mínima: consultar la línea de tiempo con historia <t> e historia #k) y Apéndice B (6 escenarios obligatorios); de la primera parte, el reloj, la agenda con su desempate, el pergamino (5 acciones, no consume tiempo ni cuenta como acción) y el guardado.
- **El pergamino en la línea**: usar el pergamino no cuenta como acción ni consume tiempo (primera parte); el reloj vuelve al instante de antes de lo revertido y el pergamino se gasta en ese instante, así que figura en el inventario de los instantes anteriores (FR-008).
- **--replay … --hasta y los pergaminos**: el resumen corresponde a la historia tal como quedó al final del log (FR-014), no al estado que la reproducción tuvo de paso antes de aplicar un pergamino posterior. Así coincide con «historia <t>» en la partida original (confirmado en Clarifications).
- **H durante un viaje «ir a»**: en la feature 002 se decidió que las teclas de presentación (M, Tab, O, L, V) no detienen un viaje; H lo detiene como la interrupción manual (motivo "interrumpido"), como excepción deliberada, porque no se puede escribir un instante mientras el jugador camina (FR-017; confirmado en Clarifications).
- **Pergamino recogido dentro de un tramo revertido**: por la regla de la primera parte (D50), un pergamino que el jugador recogió durante las acciones revertidas sigue en su inventario, pero su recogida ya no existe en la historia que quedó. Supuesto por omisión: figura en el inventario desde el reloj actual (el instante al que volvió el reloj), igual que el pergamino gastado de FR-008, y no figura en los instantes anteriores (FR-008; confirmado en Clarifications).
- **Formato de guardado**: la feature 002 usa la versión 3; esta, la 4. Un archivo de la versión 3 o anterior se reporta incompatible, sin migrar, igual que decidió la 002.
- **Partida terminada**: en la ventana, la consulta existe durante la partida; después de terminar, se consulta con --replay … --hasta sobre el log archivado.
- **Mapa conocido**: lo da la feature 002 (conocimiento del jugador, reversible); esta feature solo lo muestra en el instante consultado.
- **Teclas**: H estaba reservada por la feature 002 para esta consulta; no la usa ninguna otra pantalla de la partida.
- **Partida de 5000 acciones**: las mediciones usan partidas sintéticas deterministas por semilla (§6.3), porque las criptas publicadas no llegan a 5000 acciones jugando a mano.
