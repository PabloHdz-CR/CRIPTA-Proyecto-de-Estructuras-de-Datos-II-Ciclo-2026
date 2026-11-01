# Research: Terreno y cazador

**Feature**: `001-terreno-cazador` | **Fecha**: 2026-10-31 | **Plan**: [plan.md](plan.md)

Este documento resuelve las incógnitas técnicas del plan. Cada decisión trae su
justificación y las alternativas descartadas. Las cifras de la sección R1 son
mediciones previas al plan, hechas en el equipo local (Python 3.12.10) con el
`HeapMinimo` del proyecto, sobre mallas sintéticas con costos al azar entre
1, 50, 100 y 300. Son una estimación para elegir el diseño. La evidencia
definitiva sale de `--bench` (sección R12) y se documenta en DECISIONES.md
(principio VI).

---

## R1. Cómo calcula el cazador la ruta más barata

**Decisión**: hay un **mapa de distancias hacia el jugador**, compartido por
todos los cazadores. Se calcula con una búsqueda de costo mínimo (Dijkstra)
**hacia atrás**: parte de la sala del jugador, recorre las salidas abiertas en
sentido contrario y se detiene en una cota de costo. Cada cazador decide
leyendo el mapa solo en las salidas de su propia sala:
`d = min(costo(u, v) + dist(v))` entre sus salidas abiertas `u → v`. Desempata
por menor id de `v` y mueve si `d ≤ rango`.

**Justificación**:

- Es literalmente la fórmula de desempate de la spec (FR-014):
  `costo(u, v) + dist(v, jugador) = d`, con la vecina de menor id. No hace
  falta propagar el "primer paso" de una búsqueda hacia adelante.
- Todos los cazadores persiguen **el mismo objetivo** y el jugador no cambia de
  sala dentro de un ciclo de eventos: solo se mueve en su propia acción. Una
  sola búsqueda sirve para todos los turnos de cazadores del ciclo.
- Mediciones previas (100 cazadores, una decisión cada uno):

| Salas | Rango | Búsqueda por cazador desde cero | Mapa compartido + 100 consultas | ¿Misma decisión? |
|------:|------:|--------------------------------:|--------------------------------:|:----------------:|
|    49 | total |                        12,48 ms |                         0,41 ms | sí (100/100) |
|    49 |   300 |                         8,24 ms |                         0,25 ms | sí |
|   289 | total |                        52,63 ms |                         2,37 ms | sí |
|   289 |   300 |                        18,00 ms |                         0,23 ms | sí |
|  1024 | total |                       496,76 ms |                         9,83 ms | sí |
|  1024 |   300 |                        28,52 ms |                         0,30 ms | sí |

  La búsqueda por cazador ya come 12,5 ms de los 20 ms en una cripta de 49
  salas con rango total, y falla FR-025 desde unos cientos de salas. El mapa
  compartido se mantiene muy por debajo del límite incluso con 1024 salas.

**Alternativas descartadas**:

- *Dijkstra hacia adelante desde cada cazador, acotado por su rango*. Es
  correcto y cumple FR-026 tal como está redactado hoy, pero no cumple FR-025
  con rangos grandes (tabla).
- *BFS por número de salas*. No sirve: la spec exige costo mínimo, y el
  escenario "menos salas pero más caro" lo descarta.
- *A\**. No hay heurística admisible: el esqueleto no trae coordenadas.
- *Bellman-Ford*. Es O(salas × salidas) por consulta, sin ventaja con costos
  positivos.
- *Guardar la ruta previa del cazador y seguirla*. Exige detectar qué cambio
  invalida qué ruta. Es más frágil que invalidar el mapa entero, y FR-017 no
  admite errores.

**Consecuencia para la spec**: FR-026 y SC-004 cuentan "las salas que examina
la decisión de un cazador" a partir de **la sala del cazador**. Con el mapa
compartido, la decisión examina solo las salidas de su sala. El cálculo del
mapa examina las salas a costo ≤ cota **alrededor del jugador**. El espíritu
del requisito original se cumple: nada crece con el tamaño total de la cripta.
La redacción aclarada no se cumplía, así que la spec se enmendó antes de
programar, en el commit `d944688` (ver plan.md, "Enmienda de la spec").

---

## R2. Cuándo deja de valer el mapa (equivalencia con calcular desde cero, FR-017)

**Decisión**: el mapa guarda una **clave de validez**: (id de la sala del
jugador, versión de las puertas, cota). Se reutiliza solo si la sala del
jugador y la versión coinciden y la cota del mapa es ≥ al rango del cazador
que consulta. En cualquier otro caso se recalcula desde cero.

La **versión de las puertas** es un contador que avanza cada vez que cambia el
estado abierto/cerrado de **cualquier** salida. Se incrementa dentro del
*setter* de la propiedad `cerrada` de la salida, no en el Mutador.

**Justificación**:

- Las distancias del mapa dependen solo de la sala objetivo, del esqueleto
  (fijo durante la partida, costos incluidos) y del estado de las puertas. Si
  nada de eso cambió, el mapa es idéntico al que daría un cálculo nuevo, y la
  decisión también.
- Deshacer (Diario) revierte con `setattr(objeto, "cerrada", anterior)`, y la
  carga de una partida guardada construye salidas sin pasar por el Mutador. Un
  contador en el Mutador no vería esos cambios. Con el *setter* de la
  propiedad, todo camino que escriba `cerrada` invalida el mapa, también los
  que se agreguen en el futuro.
- Es conservador: deshacer también *incrementa* la versión, aunque el estado
  vuelva a uno anterior. Invalidar de más solo cuesta recalcular, nunca cambia
  la decisión.
- La muerte de otros actores, los efectos y los objetos no entran en la clave
  porque no afectan las distancias (los enemigos no bloquean salas). La spec
  dice que "pueden" cambiar la respuesta. Con estas reglas no la cambian, y la
  prueba de equivalencia (R9) lo comprueba igual.

**Alternativas descartadas**: un contador en `Mutador.asignar` (no ve deshacer
ni la carga); recalcular en cada turno de cazador (correcto, pero es la
columna lenta de R1); comparar el estado de todas las puertas en cada consulta
(O(salidas totales), contradice FR-026).

---

## R3. Cota del mapa

**Decisión**: las salas a costo mayor que la cota quedan "sin distancia"
(infinito). La regla para elegir la cota nueva al recalcular **se decide con el
bench** (plan.md, "Política de cota del mapa"). Hay tres candidatas:

- **P1** (punto de partida): `max(cota_anterior, rango_del_cazador)`.
- **P2**: duplicar, `max(rango, 2 × cota_anterior)`.
- **P3**: duplicar con tope, `min(max(rango, 2 × cota_anterior), R_activos)`,
  donde R_activos es el mayor rango entre los cazadores activos.

P1 puede recalcular una vez por cada rango distinto dentro de un ciclo; P2 y P3,
O(log₂(R_max / R_min)) veces. P2 explora hasta casi el doble de R y exigiría
enmendar FR-026(b) antes de adoptarla (principio VII).

**Justificación (corrección, vale para las tres políticas)**: las tres
garantizan que, después de `asegurar`, la cota es ≥ al rango del cazador que
consulta. Si un cazador de rango `r ≤ cota` puede moverse,
existe `u → v` con `costo + dist(v) ≤ r`. Entonces `dist(v) < r ≤ cota` y `v`
está en el mapa con su distancia exacta. Una `v` fuera del mapa tiene
`dist(v) > cota ≥ r`, así que nunca forma parte de una ruta admisible. Leer
"infinito" para ella da la misma decisión que el cálculo completo.

**Alternativas descartadas**:

- *Cota fija = mayor rango entre todas las fichas de cazador cargadas en la
  caché del catálogo*. Se distingue de P3 en el **conjunto** del que sale el
  máximo, no en la idea de usar un máximo como tope. Las fichas cargadas
  incluyen cazadores dormidos en salas lejanas, muertos o que todavía no
  aparecieron. Entonces el mapa se calcularía siempre con el mayor rango
  posible, aunque ningún cazador activo lo necesite, y explorar más de lo que
  pide algún cazador que consulta excede FR-026(b). Esa cota además cambia
  cuando se descarga contenido nuevo, que es justo de lo que la decisión no
  debe depender (FR-015). P3, en cambio, usa R_activos (el mayor rango entre
  los cazadores **activos**, los únicos que deciden), y solo como **tope** del
  crecimiento al duplicar: la cota parte del rango que se pide y nunca pasa de
  lo que algún cazador activo puede consultar.
- *Sin cota*: recorre toda la cripta aunque todos los rangos sean pequeños, y
  el trabajo crece con el tamaño de la cripta (contradice FR-026).

---

## R4. Referencias directas entre salas y salidas entrantes

**Decisión**: después de construir el mundo, un único paso de **enlace** guarda
en cada salida una referencia directa a su sala de origen y a su sala de
destino. En cada sala guarda una lista de **salidas entrantes** (ListaEnlazada
propia). La búsqueda hacia atrás recorre esas listas y nunca busca salas por
id.

**Justificación**: `Mundo.sala(id)` es una búsqueda lineal (decisión D32: sin
tabla hash). Llamarla por cada vecina haría que cada paso de la búsqueda
costara O(salas), y el mapa dependería del tamaño de la cripta (FR-026). El
enlace cuesta O(salas²) **una sola vez** al cargar la cripta (o la partida
guardada). Con decenas o pocos cientos de salas eso es despreciable, y se
medirá en el bench.

**Alternativas**: tabla de búsqueda propia por id (D32 la descartó para todo el
proyecto); ordenar las salas por id y buscar por bisección (cambia Mundo más
de lo necesario, y la búsqueda seguiría siendo O(log n) por vecina en vez de
O(1)).

---

## R5. Estado de la búsqueda sin diccionarios

**Decisión**: cada sala tiene dos campos internos para la búsqueda: un
**sello** (número de la última búsqueda que la tocó) y su distancia. Una sala
"tiene distancia" solo si su sello coincide con el del mapa vigente. Empezar
una búsqueda nueva es incrementar el sello: O(1), sin limpiar nada.

**Justificación**: la constitución (principio I) prohíbe dict y set como
índice. El sello hace que el costo de cada búsqueda sea proporcional a las
salas que toca, no al total. Hay un solo jugador, así que hay un solo mapa
vigente.

---

## R6. Cola de prioridad

**Decisión**: el `HeapMinimo` del proyecto con **eliminación perezosa**. Se
inserta una entrada nueva cada vez que mejora la distancia de una sala, y al
extraer se descartan las entradas viejas cuya distancia ya no coincide con la
de la sala. Las entradas son objetos pequeños que se comparan por
(distancia, id de sala), un orden total y determinista.

**Justificación**: heapq está prohibido (principio I). El heap propio ya está
probado (prueba_2_2) y medido. La eliminación perezosa evita implementar
"disminuir clave" en un heap enlazado.

---

## R7. Costo del movimiento

**Decisión**: el costo de una acción se calcula **antes** de ejecutarla, con
la sala de origen del actor. Para `Mover`, es el costo de la salida en esa
dirección. Para el resto de las acciones, su `COSTO_BASE` actual. El
intervalo se sigue calculando con `calcular_intervalo(costo, velocidad)` y el
cambio de velocidad con `reescalar_restante`, sin tocar esas reglas.

**Justificación**: después de moverse, el actor ya está en la sala de destino
(FR-028), y la salida que cruzó pertenece a la sala de origen. Calcular antes
evita reconstruir de dónde venía. Hoy el jugador (`aplicar_accion`) y los
enemigos (`EventoAccionActor`) leen `accion.costo_base`. Los dos pasan a usar
un único punto que calcula el costo.

**Caso imposible documentado**: un enemigo solo elige salidas abiertas y
ejecuta en el mismo instante en que decide, así que no puede "moverse" por una
salida cerrada. Si ocurriera, se cobra el costo de esa salida igual (el turno
se consume, como hoy).

---

## R8. Costos de las dos caras de una puerta (FR-002, FR-027)

**Decisión**: la **contraparte** de la salida `A —dir→ B` es la salida de `B`
en la **dirección opuesta** (N↔S, E↔O), si existe y conduce a `A`. Reglas del
costo efectivo, que se resuelven en el paso de enlace (R4):

| Cara A→B | Contraparte B→A | Costo efectivo de ambas |
|---|---|---|
| sin costo | sin costo | 100 |
| k | sin costo | k |
| sin costo | k | k |
| k | k | k |
| k₁ | k₂ ≠ k₁ | **error de datos**: la cripta se rechaza y el mensaje nombra ambas salas y ambos costos |
| k | (no existe: salida de un solo sentido) | k |

El tipo del valor (entero ≥ 1; se rechazan bool, 0, negativos y no enteros) se
valida al convertir el JSON (FR-003). El error usa la jerarquía propia: una
subclase nueva `DatosInvalidos(ErrorCripta)`.

**Alternativas**: emparejar por "cualquier salida de B que conduzca a A"
(ambiguo si hay dos pasajes paralelos); validar en el convertidor JSON (el
convertidor ve una sala a la vez, no las dos caras).

---

## R9. Prueba de equivalencia (FR-017, SC-002)

**Decisión**: la prueba compara el cazador real con un **oráculo**
independiente que vive solo en la carpeta de pruebas: Bellman-Ford
hacia adelante desde la sala del cazador, sin cota, sin caché y sin sellos,
con ListaEnlazada. Se generan al menos 1000 situaciones con `random.Random`
de semilla fija: criptas pequeñas con costos al azar, puertas cerradas al
azar y algunas de un solo sentido. Además se encadenan turnos con cambios
entre ellos: el jugador se mueve, una puerta se abre o se cierra, se deshace
una acción. En cada turno se exige la misma acción (atacar, esperar o mover
en cierta dirección) y el mismo costo.

**Justificación**: un oráculo con otro algoritmo y otra dirección de búsqueda
no comparte errores con la implementación. Los turnos encadenados ejercitan la
invalidación del mapa (R2), que es donde puede fallar la equivalencia.

---

## R10. Persistencia

**Decisión**:

- **Partida guardada**: hoy guarda cada salida (destino, cerrada, llave,
  cierre automático). Se agrega el **costo efectivo**, lo que exige un número
  nuevo de `FORMATO_VERSION`. Ese número **queda pendiente de coordinar** con
  las otras features que cambian el formato (plan.md, "Formato de guardado").
  Un archivo con una versión distinta de la vigente se reporta incompatible con
  el error que ya existe (`VersionIncompatible`), sin migrarlo. Tras cargar, se
  ejecuta el mismo paso de enlace (R4).
- **Caché local de fichas** (`almacenLocalDisco`): se escribe y se lee `rango`.
  Una ficha con comportamiento cazador sin `rango` válido es un error de datos.
- **partida.log y --replay**: no cambian. Las acciones se registran como hoy
  (`MOVER N`). Los costos salen del esqueleto de la misma versión de la
  cripta, y si la versión no está disponible, aplica la regla existente del
  principio V.
- **Esqueleto**: no se guarda en disco local; se descarga entero al iniciar
  (`ServicioDatos.iniciar_cripta`). El campo `costo` solo se agrega al
  convertidor y al DTO.

**Alternativa descartada**: migrar archivos del formato anterior suponiendo costo 100.
Sería cargar en silencio datos que quizá no coinciden con la cripta, y el
principio V lo prohíbe.

---

## R11. Interfaz

**Decisión**: `SalidaVisible` gana el campo `costo` (entero, ya resuelto; 100
si no se declaró). `ActorVisible` gana `es_cazador` (bool). La vista dibuja
el costo junto a cada salida existente de la sala actual y usa un marcador o
color propio del cazador. El Controlador arma estos DTOs; la Vista no conoce
el Modelo (principio III).

---

## R12. Medición (`--bench`)

**Decisión**: un módulo nuevo de bench para el cazador, registrado en
`benchTodo`, que mide:

1. **Ciclo completo de eventos** entre dos decisiones del jugador, con 20, 50 y
   100 cazadores activos y cotas grandes. Se mide en (a) la **cripta de
   referencia** y (b) una malla sintética de 1024 salas como prueba de
   estrés. La cripta de referencia es la de más salas entre las que lista la
   fuente sin conexión. Se elige en tiempo de ejecución por cantidad de
   salas, sin escribir ningún id en el código (principio IV), y se le asignan
   costos sintéticos con semilla fija. Criterio: mínimo < 20 ms en los tres
   casos.
2. **Salas examinadas**, como cifra principal porque no depende de la
   máquina: por decisión de cazador y por cálculo de mapa, en una cripta
   base y en otra 10 veces más grande con la misma región alcanzable.
   Criterio: conteos idénticos y dentro de la cota de FR-026 (enmendado).
3. **Comparación con la alternativa descartada** (búsqueda por cazador desde
   cero), para dejar la evidencia de R1 en DECISIONES.md.
4. **Costo del enlace** (R4) al cargar la cripta.
5. **Rangos distintos y política de cota** (R3): 100 cazadores con rangos
   distintos, activados en orden creciente, decreciente y al azar con semilla
   fija. Para P1, P2 y P3 reporta los recálculos del mapa por ciclo, las salas
   examinadas y el tiempo del ciclo. Se elige la política más simple que quede
   por debajo de 20 ms.
