# Feature Specification: Resolubilidad

**Feature Branch**: `003-resolubilidad`

**Created**: 2026-11-08

**Status**: Draft

**Input**: User description: "Resolubilidad: antes de iniciar una partida, el programa determina si la cripta puede ganarse y, si no, explica por qué. Usa el esqueleto de la cripta y la ubicación de las llaves. (Fuente: Cripta Parte II §3.5, §4.2, §4.3, §5.4, §6.1, §7.3 y Apéndice B.)" (descripción completa con reglas, contrato de datos, interfaz, rendimiento, 12 escenarios de aceptación y casos borde en el comando `/speckit-specify` del 2026-11-08, registrado en PROMPTS_LLM.md).

## Clarifications

### Session 2026-11-08

- Q: Si sala_salida también puede alcanzarse por un camino que no atraviesa ninguna puerta que requiera llave_salida, ¿qué debe decir la verificación? → A: Se aplica la definición literal del enunciado: la cripta es "no resoluble" y el reporte da el motivo "la sala de salida es alcanzable sin la puerta que requiere llave_salida"; la regla de victoria del juego no cambia (FR-001, FR-011). *Corregido tras la revisión de la spec (2026-11-08)*: la respuesta contradecía el enunciado ("llegar a sala_salida a través de una puerta que la requiere"; Parte I §2.12). La cripta es resoluble si EXISTE un camino que entra a sala_salida por una salida que requiere llave_salida, aunque sala_salida también sea alcanzable por otro camino; es no resoluble solo si llave_salida no es obtenible o si ninguna salida que la requiere da acceso a sala_salida desde la región alcanzable, incluido el caso en que sala_salida solo se alcanza sin esa puerta (FR-001, FR-011).
- Q: ¿Qué llaves debe incluir el orden de obtención cuando la cripta es resoluble? → A: Todas las llaves obtenibles, cada una después de las que hacen falta para alcanzarla, incluidas las que no se necesitan para ganar; llave_salida no tiene por qué ir última (FR-007, FR-008).
- Q: Cuando varias llaves ya pueden obtenerse al mismo tiempo, ¿qué regla decide cuál va antes en el orden? → A: Entre las llaves alcanzables con las ya ordenadas, va primero la de menor id (comparación de texto del identificador); el resultado es el orden lexicográficamente menor entre los válidos (FR-009).
- Q: En la ventana del juego, ¿cómo y cuándo se muestra el reporte de resolubilidad? → A: Resoluble: la partida inicia con un aviso corto y el reporte completo (con el orden) se abre a pedido con la tecla V, que no estaba asignada; no resoluble sin --forzar: pantalla con el reporte completo y vuelta al menú; no resoluble con --forzar: la misma pantalla y, al aceptar, la partida inicia, con el reporte disponible con V. La asignación de V se documenta en el README (FR-019, FR-020, FR-037).
- Q: Cuando hay un ciclo entre llaves no obtenibles, ¿qué ciclo concreto debe mostrar el reporte y en qué orden? → A: Un ciclo por grupo: se empieza en la llave de menor id del grupo y en cada paso se va a la dependencia de menor id dentro del grupo hasta volver a una llave ya visitada; el ciclo se muestra desde esa llave repetida, con la puerta que encierra cada llave (FR-015).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Saber si la cripta puede ganarse y por qué no (Priority: P1)

Antes de jugar, el jugador quiere saber si la cripta elegida tiene solución. El
programa recorre el esqueleto de la cripta con la ubicación de las llaves y
responde una de dos cosas: que la cripta es resoluble, junto con un orden en
el que pueden obtenerse las llaves, o que no lo es, con una explicación
concreta: qué llaves no se pueden obtener, qué puertas cerradas bloquean el
avance, dónde están las llaves que esas puertas piden y, si una llave está
encerrada detrás de puertas que solo ella abre, el ciclo que lo causa.

**Why this priority**: Es el núcleo de la capacidad. Sin este veredicto y su
explicación no hay nada que mostrar al iniciar la partida ni con la bandera de
solo verificación. Como el servicio publicará criptas no resolubles a
propósito, jugarlas sin aviso deja al jugador atascado sin saber por qué.

**Independent Test**: Verificar criptas sintéticas pequeñas construidas para
cada caso (cadena de llaves, ciclo, llave suelta por un enemigo, llave
inexistente, cierre automático) y comparar el veredicto, el orden y el reporte
con el resultado esperado, sin vista ni red.

**Acceptance Scenarios**:

1. **Given** una cripta en la que llave_salida está detrás de la única puerta que ella misma abre, **When** se verifica, **Then** el resultado es "no resoluble" y el reporte señala el ciclo: llave_salida está detrás de la puerta que requiere llave_salida (FR-012, FR-013, FR-014; Apéndice B).
2. **Given** una llave que suelta un enemigo errante que inicia en una sala alcanzable, **When** se verifica, **Then** la llave se considera obtenible en la sala donde ese enemigo inicia, sin importar adónde se mueva el enemigo después (FR-004, FR-017; Apéndice B).
3. **Given** una cripta resoluble con varios órdenes válidos de obtención de llaves, **When** se verifica dos veces, **Then** las dos ejecuciones producen exactamente el mismo orden, que en cada posición elige la llave disponible de menor id (por ejemplo, con itm_llave_bronce e itm_llave_azul disponibles a la vez, va primero itm_llave_azul) (FR-009, FR-010; Apéndice B).
4. **Given** una cadena de llaves (la llave A abre la zona donde está la llave B y B abre la zona donde está llave_salida), **When** se verifica, **Then** la cripta es resoluble y el orden es A, B, llave_salida (FR-007, FR-008).
5. **Given** una cripta resoluble con una llave obtenible que no hace falta para ganar, **When** se verifica, **Then** esa llave también aparece en el orden, una sola vez, después de las llaves que hacen falta para alcanzarla (FR-007, FR-008).
6. **Given** una puerta de la frontera que requiere una llave que no aparece en la ubicación de llaves, **When** se verifica, **Then** esa llave se reporta como no obtenible y sin ubicación, y la puerta aparece en la frontera bloqueada con la llave que requiere (FR-011, FR-012, FR-013).
7. **Given** una llave que suelta un enemigo que inicia en una región inalcanzable, **When** se verifica, **Then** la llave se reporta como no obtenible, con la sala inicial del enemigo y el enemigo que la suelta como ubicación (FR-004, FR-011, FR-013).
8. **Given** dos llaves en las que cada una está detrás de la puerta que abre la otra, **When** se verifica, **Then** la cripta no es resoluble y el reporte señala ese ciclo concreto con las dos llaves y sus dos puertas, en el mismo orden en cada ejecución (FR-014, FR-015).
9. **Given** una puerta con cierre automático en el único camino hacia llave_salida y hacia la sala de salida, y la llave de esa puerta obtenible antes, **When** se verifica, **Then** la puerta no bloquea y la cripta es resoluble (FR-005).
10. **Given** una puerta cuyas dos caras tienen estados o llaves distintos (por ejemplo, abierta de A hacia B y cerrada con llave de B hacia A), **When** se verifica, **Then** cada cara se evalúa en el sentido en que se recorre: se puede pasar de A a B sin llave, pero volver de B a A exige la llave de esa cara (FR-006).
11. **Given** una cripta que no es resoluble por causas sin ciclo (por ejemplo, solo una llave faltante o una puerta cerrada sin llave), **When** se verifica, **Then** el reporte incluye las llaves no obtenibles, la frontera bloqueada y las ubicaciones, e indica que no hay ciclo (FR-011, FR-012, FR-013, FR-014).
12. **Given** una cripta en la que sala_salida es alcanzable por dos caminos, uno que entra por una salida que requiere llave_salida (obtenible) y otro que entra por una salida abierta, **When** se verifica, **Then** la cripta es resoluble (FR-001).

---

### User Story 2 - No empezar una partida imposible, salvo que se fuerce (Priority: P1)

Al elegir una cripta para jugar, el jugador ve el reporte de resolubilidad. Si
la cripta no puede ganarse, la partida no empieza y el reporte explica por qué.
Quien quiera jugarla de todos modos (por ejemplo, para explorar o probar) puede
iniciar el programa con la bandera de forzar, y entonces la partida comienza
igual, con el reporte visible.

**Why this priority**: Es la regla de inicio de partida que pide el enunciado y
lo que el jugador nota directamente. Depende del veredicto de la historia 1.

**Independent Test**: Con una cripta no resoluble de los datos sin conexión,
pedir una partida nueva sin la bandera de forzar y comprobar que no se crea
partida (ni registro de partida) y que se muestra el reporte; repetir con la
bandera de forzar y comprobar que la partida comienza.

**Acceptance Scenarios**:

1. **Given** una cripta no resoluble y el programa iniciado sin --forzar, **When** el jugador pide una partida nueva en ella, **Then** la partida no inicia, no se crea registro de partida, se muestra la pantalla con el reporte de resolubilidad y, al cerrarla, se vuelve al menú (FR-018, FR-019; Apéndice B).
2. **Given** una cripta no resoluble y el programa iniciado con --forzar, **When** el jugador pide una partida nueva en ella, **Then** primero se muestra la pantalla con el reporte completo y, al aceptarla, la partida inicia; durante la partida, la tecla V vuelve a abrir el reporte (FR-018, FR-020).
3. **Given** una cripta resoluble, **When** el jugador pide una partida nueva en ella, con o sin --forzar, **Then** la partida inicia con un aviso corto de que la cripta es resoluble, sin mostrar el orden, y al pulsar V se abre el reporte completo con el orden de obtención de llaves; al pulsar V otra vez se cierra (FR-018, FR-019, FR-037).
4. **Given** una partida iniciada con --forzar sobre una cripta no resoluble, **When** se reproduce su registro con --replay, **Then** la reproducción no se bloquea por la resolubilidad y termina igual que la partida original (FR-021).

---

### User Story 3 - Verificar una cripta desde la terminal (Priority: P2)

Quien prepara o revisa criptas quiere comprobar una sin jugarla. Con la bandera
de solo verificación y el identificador de la cripta, el programa descarga (o
lee sin conexión) lo necesario, imprime el reporte en la terminal y termina, sin
abrir la ventana del juego ni iniciar partida.

**Why this priority**: Es la forma de revisar en lote las criptas publicadas,
incluidas las no resolubles, y la vía de evaluación sin interfaz. Se apoya en la
historia 1 pero no en la 2.

**Independent Test**: Ejecutar el programa con --verificar sobre una cripta
resoluble y otra no resoluble, con --offline, y comprobar el texto del reporte,
el código de salida y que no se abrió ninguna ventana ni se creó partida.

**Acceptance Scenarios**:

1. **Given** el programa ejecutado con --verificar y una cripta, **When** termina, **Then** el reporte se imprimió en la terminal, no se instanció la vista y no se inició ninguna partida (FR-022, FR-023).
2. **Given** --verificar sobre una cripta resoluble, **When** termina, **Then** el código de salida indica "resoluble"; sobre una no resoluble, indica "no resoluble"; si los datos no pudieron obtenerse o son inválidos, indica un error de datos distinto de los dos anteriores (FR-024).
3. **Given** --verificar junto con --offline, **When** se verifica una cripta presente en los datos sin conexión, **Then** el reporte es idéntico al obtenido en línea para la misma versión de cripta (FR-022, FR-029).

---

### User Story 4 - Obtener la ubicación de las llaves dentro del presupuesto (Priority: P2)

Para verificar, el programa necesita saber dónde está cada llave: en el suelo
de una sala o en lo que suelta un enemigo. Esa información se pide al servicio
una sola vez por versión de cripta, cuenta dentro del presupuesto de
solicitudes, se guarda junto con los demás datos de la cripta y se vuelve a
pedir solo si la versión cambia. Las fuentes en línea y sin conexión entregan la
misma información.

**Why this priority**: Sin la ubicación de las llaves no hay verificación, pero
la consulta es un contrato de datos acotado que puede probarse con datos
sintéticos antes de existir el servicio.

**Independent Test**: Con una fuente simulada, verificar dos veces la misma
cripta y contar las solicitudes: la ubicación de llaves se pide una vez y cuenta
en el presupuesto; cambiar la versión de la cripta y comprobar que se vuelve a
pedir; comparar lo entregado por la fuente en línea y la sin conexión.

**Acceptance Scenarios**:

1. **Given** una cripta cuya ubicación de llaves no está guardada, **When** se verifica, **Then** se hace una consulta de ubicación de llaves y esa solicitud (y cada reintento) cuenta en el presupuesto de solicitudes (FR-025, FR-026).
2. **Given** una ubicación de llaves guardada para la versión actual de la cripta, **When** se verifica otra vez, **Then** no se hace una solicitud nueva (FR-027).
3. **Given** una ubicación de llaves guardada para una versión anterior de la cripta (por ejemplo, de la primera parte), **When** se verifica, **Then** lo guardado se invalida por la validación de versión existente y se pide de nuevo (FR-027, FR-028).
4. **Given** la misma versión de cripta, **When** se obtiene la ubicación de llaves por la fuente en línea y por la fuente sin conexión, **Then** ambas entregan las mismas llaves en las mismas ubicaciones (FR-029).
5. **Given** una respuesta de ubicación de llaves mal formada (falta id o sala, o la sala no existe en el esqueleto), **When** se verifica, **Then** se produce un error de datos explícito que identifica la entrada inválida; nunca se ignora en silencio (FR-030).
6. **Given** que el presupuesto de solicitudes no alcanza para la consulta de llaves, **When** se intenta verificar, **Then** no se excede el presupuesto y se informa que la verificación no pudo hacerse (FR-026, FR-031).

---

### User Story 5 - Verificación rápida y que escala (Priority: P3)

Quien evalúa el proyecto quiere comprobar con mediciones que la verificación es
rápida en la cripta publicada más grande y que su costo crece de forma
aproximadamente lineal con el tamaño de la cripta, y no con el producto de
salas por llaves como la alternativa ingenua de repetir el recorrido completo
cada vez que se obtiene una llave.

**Why this priority**: Es un requisito de rendimiento de la constitución y del
enunciado, pero solo tiene sentido una vez que el veredicto es correcto.

**Independent Test**: Ejecutar --bench, que mide la verificación en la cripta
más grande disponible y en criptas sintéticas con muchas llaves encadenadas, y
compararla con la alternativa ingenua.

**Acceptance Scenarios**:

1. **Given** la cripta publicada más grande disponible, **When** se mide la verificación con --bench sin red ni renderizado, **Then** toma menos de 200 ms (FR-032).
2. **Given** criptas sintéticas con cadenas de 100, 200 y 400 llaves, **When** --bench mide la verificación y la alternativa ingenua, **Then** se reportan tiempos y conteo de salidas examinadas de ambas, y el resultado (veredicto, orden y reporte) es idéntico entre ellas (FR-033, FR-034, FR-035).
3. **Given** las mismas criptas sintéticas, **When** se duplica la cantidad de llaves encadenadas, **Then** las salidas examinadas por la verificación crecen en proporción al tamaño de la cripta y no se multiplican por la cantidad de llaves (FR-033).

---

### Edge Cases

- **Una llave abre varias puertas**: al obtenerla quedan transitables todas las salidas que la requieren, desde cualquier sala alcanzable y en cualquier momento posterior (FR-002, FR-003).
- **Una llave está en la sala inicial**: es obtenible desde el comienzo y puede aparecer primera en el orden (FR-007).
- **Una puerta cerrada sin llave asociada**: nunca puede abrirse; si limita la región alcanzable, aparece en la frontera bloqueada marcada "sin llave" (FR-002, FR-012).
- **Una puerta que requiere una llave que no existe en la ubicación de llaves**: la llave se reporta como no obtenible "sin ubicación" y la puerta, si limita la región alcanzable, en la frontera bloqueada (FR-011, FR-012, FR-013).
- **Una cripta con varios ciclos de dependencia**: se reporta exactamente un ciclo por cada grupo de llaves no obtenibles que dependen entre sí, construido con la regla de menor id de FR-015; los grupos aparecen ordenados por su menor id y el texto del reporte es idéntico en cada ejecución (FR-014, FR-015).
- **Dentro de un grupo hay varios ciclos posibles** (por ejemplo, las llaves k_a, k_b y k_c, donde k_a depende de k_b y de k_c, k_b de k_a y k_c de k_a): se muestra solo el que da la regla de FR-015 (k_a → k_b → k_a) (FR-015).
- **La misma llave aparece en varias ubicaciones**: es obtenible si al menos una de ellas es alcanzable; si no lo es, el reporte lista todas sus ubicaciones (FR-013, FR-016).
- **llave_salida es obtenible pero ninguna puerta que la requiere conduce a la sala de salida desde la región alcanzable**: la cripta no es resoluble y el reporte lo indica (FR-001, FR-011).
- **sala_salida es alcanzable por dos caminos, uno por una salida que requiere llave_salida y otro sin ella**: la cripta es resoluble, porque existe el camino por la salida que requiere llave_salida (FR-001).
- **sala_salida solo es alcanzable sin atravesar ninguna salida que requiera llave_salida**: la cripta es no resoluble con el motivo (b) de FR-011, y el reporte indica que sala_salida solo se alcanza sin esa salida, aunque el juego permita ganarla. La regla de victoria del juego no cambia (FR-001, FR-011).
- **Una puerta cerrada cuya sala de destino ya es alcanzable por otro camino**: no forma parte de la frontera bloqueada (FR-012).
- **La ubicación de llaves está vacía**: llave_salida no puede obtenerse, la cripta no es resoluble y el reporte la lista como no obtenible "sin ubicación" (FR-001, FR-011, FR-013).
- **Las páginas del esqueleto o las entradas de la ubicación de llaves llegan en otro orden**: el veredicto, el orden y el reporte no cambian (FR-010).

## Requirements *(mandatory)*

### Functional Requirements

**Reglas de la verificación**

- **FR-001**: Una cripta MUST considerarse resoluble si y solo si, partiendo de la sala inicial y bajo los supuestos de FR-002 a FR-006, el jugador puede obtener llave_salida y existe un camino que entra a sala_salida por una salida que requiere llave_salida. Que sala_salida también sea alcanzable por otro camino, sin esa salida, MUST NOT cambiar el veredicto.
- **FR-002**: La verificación MUST considerar transitable toda salida abierta y toda salida cerrada cuya llave ya fue obtenida; una salida cerrada sin llave asociada MUST considerarse intransitable siempre.
- **FR-003**: Las llaves MUST NOT consumirse: una llave obtenida sigue sirviendo para todas las salidas que la requieren durante el resto de la verificación.
- **FR-004**: Todo enemigo MUST considerarse derrotable. Una llave que suelta un enemigo MUST considerarse obtenible en la sala donde ese enemigo inicia, aunque sea errante o se mueva después.
- **FR-005**: Las trampas y los cierres automáticos MUST NOT bloquear: una puerta que se cierra sola se considera transitable siempre que su llave haya sido obtenida, igual que cualquier otra puerta cerrada.
- **FR-006**: Cada cara de una puerta MUST evaluarse por separado, con su propio estado y su propia llave, en el sentido en que se recorre.
- **FR-007**: Si la cripta es resoluble, el resultado MUST incluir un orden de obtención de todas las llaves obtenibles en el que cada llave aparece después de las llaves necesarias para alcanzarla: para cada posición, la ubicación de esa llave es alcanzable desde la sala inicial usando solo las llaves de las posiciones anteriores.
- **FR-008**: El orden de FR-007 MUST incluir llave_salida y cada llave obtenible exactamente una vez, aunque aparezca en varias ubicaciones o no haga falta para ganar; llave_salida MUST NOT forzarse a la última posición.
- **FR-009**: Si hay varios órdenes válidos, la verificación MUST entregar el lexicográficamente menor: en cada posición va, entre las llaves aún no ordenadas cuya ubicación es alcanzable usando solo las llaves de las posiciones anteriores, la de menor id, comparando los identificadores como texto, carácter por carácter.
- **FR-010**: El veredicto, el orden y el reporte MUST depender solo del contenido del esqueleto y de la ubicación de llaves (incluidos los identificadores de salas, puertas y llaves), nunca del orden de llegada de las respuestas, de la hora del sistema ni del azar.

**Reporte de no resolubilidad**

- **FR-011**: Si la cripta no es resoluble, el reporte MUST listar las llaves que no pueden obtenerse, incluidas las que requiere alguna puerta pero no aparecen en la ubicación de llaves, e indicar el motivo del fracaso, que MUST ser uno de estos dos: (a) llave_salida no es obtenible; (b) llave_salida es obtenible, pero ninguna salida que la requiere da acceso a sala_salida desde la región alcanzable. En el caso (b), si sala_salida es alcanzable solo por caminos que no atraviesan esa salida, el reporte MUST indicarlo.
- **FR-012**: El reporte MUST listar las puertas de la frontera bloqueada: las salidas cerradas que parten de una sala alcanzable hacia una sala no alcanzable, identificadas por sala de origen, dirección y sala de destino, con la llave que requiere cada una o la marca "sin llave".
- **FR-013**: Para cada llave de FR-011 y de FR-012, el reporte MUST indicar dónde se encuentra: la sala, y el enemigo que la suelta si corresponde; o "sin ubicación" si no aparece en la ubicación de llaves.
- **FR-014**: Una llave K depende de una llave Y si alguna salida cerrada que requiere Y conduce hasta la ubicación de K sin atravesar ninguna otra salida intransitable con las llaves obtenibles. Si una llave no obtenible depende de sí misma, directamente o mediante una cadena de dependencias entre llaves no obtenibles, el reporte MUST señalar el ciclo concreto como la secuencia de llaves y de las puertas que las encierran; si no hay ciclo, MUST indicar que no lo hay.
- **FR-015**: Un grupo de dependencia es un conjunto máximo de llaves no obtenibles en el que cada una depende, directamente o por cadena, de todas las demás (una llave sola que depende de sí misma también forma grupo). Para cada grupo, el reporte MUST señalar exactamente un ciclo, construido así: se empieza en la llave de menor id del grupo; en cada paso se pasa a la llave de menor id, dentro del grupo, de la que depende la llave actual; al llegar a una llave ya visitada, el ciclo es la secuencia desde esa llave hasta volver a ella. Para cada paso K → Y, la puerta mostrada es, entre las salidas cerradas que requieren Y y conducen a la ubicación de K (FR-014), la de menor sala de origen y, a igual sala, la primera en el orden N, S, E, O. Los grupos MUST listarse por el menor id de cada grupo y los ids se comparan como texto, carácter por carácter.
- **FR-016**: Si una misma llave aparece en varias ubicaciones, MUST considerarse obtenible en cuanto cualquiera de ellas sea alcanzable; si ninguna lo es, el reporte MUST listar todas.
- **FR-017**: La verificación MUST usar solo el esqueleto, los datos generales de la cripta (sala inicial, sala de salida, llave de salida) y la ubicación de llaves; MUST NOT necesitar descargar el contenido de las salas ni el catálogo.

**Inicio de partida**

- **FR-018**: Antes de iniciar una partida nueva, el programa MUST verificar la resolubilidad de la cripta elegida.
- **FR-019**: El reporte de resolubilidad MUST poder verse al iniciar una partida. Si la cripta es resoluble, la partida MUST iniciar con un aviso corto de que la cripta es resoluble, sin mostrar el orden de llaves; el reporte completo MUST abrirse y cerrarse a pedido con la tecla V durante la partida. Si la cripta no es resoluble y no se usó --forzar, la partida MUST NOT iniciar (no se crea partida ni registro de partida): se muestra una pantalla con el reporte completo y, al cerrarla, se vuelve al menú.
- **FR-020**: Con la bandera --forzar, una cripta no resoluble MUST mostrar primero la misma pantalla con el reporte completo y, cuando el jugador la acepta, iniciar la partida igual, con el reporte disponible con la tecla V; el registro de la partida MUST anotar que la cripta no era resoluble y que se forzó el inicio.
- **FR-037**: La tecla V MUST NOT estar asignada a ninguna otra acción en la partida, y su uso MUST documentarse en la tabla de teclas de la partida del README.
- **FR-021**: --replay MUST reproducir una partida sin bloquearla por resolubilidad, incluida una partida forzada; cargar una partida guardada MUST NOT volver a exigir la verificación.

**Solo verificación**

- **FR-022**: La bandera --verificar <cripta> MUST ejecutar únicamente la verificación de esa cripta e imprimir el reporte en la terminal; MUST funcionar también con --offline.
- **FR-023**: --verificar MUST NOT instanciar la vista ni iniciar una partida, ni crear registro de partida ni puntaje.
- **FR-024**: --verificar MUST terminar con un código de salida que distinga tres casos: resoluble (0), no resoluble (1) y error de datos o de red que impidió verificar (2).

**Contrato de datos**

- **FR-025**: La ubicación de las llaves MUST obtenerse con la consulta de llaves de la cripta (`GET /criptas/<id>/llaves`), cuya respuesta es una lista de entradas con id de llave y sala, y opcionalmente el enemigo que la suelta; cuando hay enemigo, la llave está en lo que suelta esa instancia y la sala es donde el enemigo inicia.
- **FR-026**: La consulta de llaves, y cada uno de sus reintentos, MUST contar dentro de presupuesto_solicitudes; el presupuesto MUST NOT excederse.
- **FR-027**: La ubicación de llaves MUST guardarse junto con los demás datos de la cripta y reutilizarse mientras coincida la versión de la cripta; con otra versión MUST pedirse de nuevo.
- **FR-028**: Los datos guardados por la primera parte MUST invalidarse por la validación de versión existente, nunca borrando archivos a mano ni cargándolos en silencio contra una versión distinta.
- **FR-029**: Las fuentes en línea y sin conexión MUST entregar la misma ubicación de llaves para la misma versión de cripta; si la fuente sin conexión no tiene la ubicación de llaves de esa versión, MUST reportarlo como datos no disponibles y nunca suponer que la cripta no tiene llaves.
- **FR-030**: Una entrada de la ubicación de llaves sin id o sin sala, con una sala que no existe en el esqueleto o con campos de tipo inválido MUST provocar un error de datos explícito que identifique la entrada; nunca se descarta en silencio.
- **FR-031**: Si la verificación no puede hacerse por falta de datos, presupuesto o red, el programa MUST informarlo como "no se pudo verificar", distinto de "no resoluble"; sin --forzar la partida MUST NOT iniciar, y con --forzar MUST iniciar.

**Rendimiento y medición**

- **FR-032**: La verificación MUST tomar menos de 200 ms en la cripta publicada más grande disponible (la de más salas entre las disponibles al medir), sin red ni renderizado, medido con --bench.
- **FR-033**: El costo total de la verificación MUST crecer aproximadamente de forma lineal con la cantidad de salas, salidas y llaves: MUST NOT repetirse el recorrido completo de la cripta cada vez que se obtiene una llave. --bench MUST reportar la cantidad de salidas examinadas, que no se multiplica por la cantidad de llaves.
- **FR-034**: La frontera bloqueada y las dependencias entre llaves MUST obtenerse del mismo recorrido que decide la resolubilidad, sin recorridos adicionales por cada llave.
- **FR-035**: --bench MUST medir también la alternativa ingenua (repetir el recorrido por cada llave obtenida) sobre criptas sintéticas con muchas llaves encadenadas, comprobar que ambas dan el mismo resultado y reportar tiempos y salidas examinadas de las dos.

**Datos de criptas concretas**

- **FR-036**: Ningún identificador, cantidad de salas, cantidad de llaves, versión ni resultado de una cripta concreta MUST aparecer en el código; las criptas de prueba son sintéticas o se leen de los datos sin conexión.

### Key Entities *(include if feature involves data)*

- **Ubicación de llave**: una entrada que dice dónde puede obtenerse una llave: id de la llave, sala y, opcionalmente, el enemigo que la suelta (y que inicia en esa sala). Pertenece a una versión de cripta.
- **Región alcanzable**: las salas a las que el jugador puede llegar desde la sala inicial con las llaves obtenibles, bajo los supuestos de la verificación.
- **Puerta de la frontera**: una cara de puerta cerrada que sale de la región alcanzable hacia una sala fuera de ella, con su sala de origen, dirección, sala de destino y la llave que requiere (o ninguna).
- **Dependencia entre llaves**: la relación "K está detrás de una puerta que requiere Y" entre llaves no obtenibles; un ciclo en ella explica una llave encerrada por puertas que solo ella abre.
- **Reporte de resolubilidad**: el veredicto (resoluble, no resoluble o no se pudo verificar) y, según el caso, el orden de obtención de llaves o las llaves no obtenibles, la frontera bloqueada, las ubicaciones, los ciclos y el motivo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Los 28 escenarios de aceptación de esta especificación (12 de la historia 1, 4 de la 2, 3 de la 3, 6 de la 4 y 3 de la 5), de los cuales 4 son los obligatorios del Apéndice B, y sus casos borde tienen una prueba automatizada que pasa; cada prueba cita los FR que ejerce.
- **SC-002**: La verificación de la cripta publicada más grande disponible toma menos de 200 ms en el equipo local, medido con --bench, sin red ni renderizado.
- **SC-003**: En criptas sintéticas con 100, 200 y 400 llaves encadenadas, al duplicar la cantidad de llaves (de 100 a 200 y de 200 a 400), el cociente de salidas examinadas es ≤ 2,5 en la verificación y ≥ 3,5 en la alternativa ingenua; ambas dan el mismo veredicto, orden y reporte en todos los casos.
- **SC-004**: Dos verificaciones de la misma cripta, incluso con las páginas del esqueleto y las entradas de llaves en otro orden, producen reportes idénticos carácter por carácter.
- **SC-005**: Ninguna partida nueva comienza en una cripta no resoluble sin --forzar; con --forzar comienza en el 100 % de los casos.
- **SC-006**: --verificar nunca abre la ventana del juego ni crea partidas, registros ni puntajes, y su código de salida distingue resoluble, no resoluble y error.
- **SC-007**: Verificar dos veces la misma versión de una cripta hace como máximo una consulta de ubicación de llaves, y el total de solicitudes nunca supera presupuesto_solicitudes.

## Assumptions

- **Definición de "resoluble"** (confirmada en Clarifications y corregida tras la revisión): basta con que exista un camino que entra a sala_salida por una salida que requiere llave_salida, con llave_salida obtenible; otros caminos hacia sala_salida no cambian el veredicto. La regla de victoria del juego (entrar a sala_salida por cualquier camino) queda fuera del alcance y no cambia; el único caso en que difiere de la verificación (sala_salida alcanzable solo sin esa salida) se explica en el reporte (FR-001, FR-011).
- **Contenido del orden** (confirmado en Clarifications): el orden de FR-007 incluye todas las llaves obtenibles, no solo las necesarias para ganar; entre llaves disponibles a la vez va primero la de menor id (FR-009, confirmado en Clarifications).
- **Dependencias con varias entradas**: si la ubicación de una llave puede alcanzarse por puertas que requieren llaves distintas, la llave depende de cada una de ellas (FR-014); un ciclo se reporta solo entre llaves no obtenibles, de modo que siempre explica un bloqueo real.
- **Códigos de salida de --verificar**: 0 resoluble, 1 no resoluble, 2 error de datos o de red (FR-024). Es una decisión propia de esta capacidad: en --replay el 1 significa fallo, mientras que en --verificar significa un veredicto válido (no resoluble); los errores van con el 2. Cada modo documenta sus propios códigos.
- **Fallo al verificar**: si no puede verificarse (datos ausentes, presupuesto agotado, red), se trata como un tercer resultado y no como "no resoluble" (FR-031).
- **Paquetes sin conexión**: los paquetes sin conexión (datos_offline y el paquete de pruebas) deben incluir la ubicación de llaves de cada cripta. Sin ella, FR-029 la reporta como datos no disponibles y FR-031 trata la verificación como "no se pudo verificar", así que jugar sin conexión exige --forzar.
- **Interfaz del reporte** (confirmada en Clarifications): el orden de llaves de una cripta resoluble no se muestra por defecto porque revela la solución; queda a pedido con V. V se eligió porque no estaba asignada en el menú, la partida ni el replay (letras en uso: A, B, C, G, L, N, O, P, Q, R, S, U, X). Se coordina con el otro integrante del grupo para que no choque con las teclas de niebla, ir a y línea de tiempo de sus capacidades.
- **Alcance de la verificación**: solo partidas nuevas; cargar una partida guardada o reproducir un registro no vuelve a verificar ni se bloquea (FR-021).
- **Validez de la ubicación de llaves**: el programa confía en que la sala indicada para un enemigo es su sala inicial y no cruza esa información con el contenido de las salas, que la verificación no descarga (FR-017).
- **Esqueleto completo**: la verificación usa el esqueleto completo, que el programa ya descarga al preparar una partida; no añade solicitudes de esqueleto propias.
- **Cripta de referencia**: la cripta publicada más grande se identifica al medir, entre las disponibles, sin escribir su id ni su tamaño en el código (FR-036).
- **Costos de salida**: la verificación depende de qué salas son alcanzables, no de los costos de tránsito de la feature 001, que no influyen en el veredicto.
