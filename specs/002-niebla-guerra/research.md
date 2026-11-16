# Research: Niebla de guerra e «ir a»

**Feature**: `002-niebla-guerra` | **Fecha**: 2026-11-15 | **Plan**: [plan.md](plan.md)

Este documento resuelve las incógnitas técnicas del plan y evalúa la
orientación del equipo (puntos 1 a 8 del prompt de `/speckit-plan`). Cada
decisión trae su justificación y las alternativas descartadas.

Las cifras son **mediciones previas al plan**, hechas en el equipo local
(Python 3.14.5 con `py`) con las estructuras del proyecto (`HeapMinimo`,
`ListaEnlazada`, `ListaDoble`, `ordenamiento.mezcla`) sobre la cripta de
referencia de `datos_offline/` (la de más salas, 300, elegida en ejecución
como en `benchCazador`) y la malla de 32 × 32 = 1024 salas de la feature 001,
ambas con los costos sintéticos de `benchCazador`. El script de medición no
forma parte del proyecto. La evidencia definitiva sale de `--bench`
(R11) y va a DECISIONES.md (principio VI).

---

## R1. Dónde vive el conocimiento del jugador

**Decisión**: como **campos de los objetos que ya existen**, tal como propuso
el equipo:

- `Sala.conocimiento`: `DESCONOCIDA` (0), `AVISTADA` (1) o `EXPLORADA` (2).
- `Salida.recordada`: `NO_OBSERVADA` (0), `ABIERTA` (1) o `CERRADA` (2). Cada
  cara de puerta es una `Salida` distinta (así viene el esqueleto), así que
  FR-005 y el caso borde de caras con estados distintos salen solos.

Consultar el estado de una sala o el recuerdo de una cara es leer un campo
del objeto que ya se tiene: O(1) y sin dict ni set (principio I). Ni la
vista, ni la antorcha, ni «ir a» buscan salas por id: llegan a ellas por
referencia (`Salida.sala_destino`, `Salida.origen`, `Sala.entrantes`, todas
del enlace de la feature 001, research R4 de 001). `Mundo.sala(id)`, que es
O(salas) (D32), se usa solo una vez por orden «ir a» para resolver el destino
elegido (R6), nunca por paso ni por consulta.

**Mediciones** (tiempo de una consulta según la cantidad de salas conocidas):

| Conocidas | Campo del objeto | Búsqueda lineal por id |
|---:|---:|---:|
| 25 | 0,017 µs | 0,38 µs |
| 100 | 0,018 µs | 1,25 µs |
| 300 | 0,018 µs | 3,09 µs |
| 1200 | 0,020 µs | 10,92 µs |

El campo no crece con el mapa conocido (FR-032, SC-005); la búsqueda lineal
crece en proporción y, como «ir a» consulta cada sala y cada cara que toca
la búsqueda, multiplicaría el costo de cada paso por cientos.

**Alternativas descartadas**:

- *Lista de salas exploradas con búsqueda lineal*: O(conocidas) por consulta
  (tabla). Contradice FR-032 y SC-005.
- *Índice propio por id (tabla hash o arreglo propio indexado por id)*: O(1),
  pero D32 descartó para todo el proyecto una tabla de búsqueda propia como
  sustituto de dict, y no hace falta: todas las consultas parten de una
  referencia. Además los ids no son necesariamente consecutivos.
- *Un objeto "mapa conocido" separado con sus propias salas*: duplica el
  esqueleto (nombre y salidas ya están en `Sala`) y obliga a mantener dos
  grafos sincronizados. El conocimiento es un estado por sala y por cara, no
  otro grafo.

**Qué es infraestructura y qué no (FR-015)**: el esqueleto completo, la
precarga, el contenido cargado y el estado real de las puertas siguen en los
mismos objetos. La separación la garantizan los lectores: el Constructor de
la vista y el buscador de «ir a» leen solo `conocimiento` y `recordada`
(más nombre, salidas y costo de las salas cuyo `conocimiento` lo permite).
Lo verifican pruebas que comparan el DTO con el conocimiento (SC-002).

---

## R2. Cómo cambia el conocimiento y cómo se revierte

**Decisión**: todo cambio pasa por el **Mutador** (orientación 2 del equipo):

- Estado de sala y recuerdo de cara: `mutador.asignar(sala, "conocimiento",
  nuevo)` y `mutador.asignar(salida, "recordada", nuevo)`. El Diario ya
  revierte `ATRIBUTO` con `setattr`, sin código nuevo.
- Alta en el registro de conocidas (R4): un tipo nuevo del Mutador,
  `CONOCIDA_AGREGAR`, cuyo inverso en el Diario es quitar la última.
- **Solo se registra lo que cambia**: antes de asignar se compara con el valor
  actual. Entrar a una sala ya explorada con las puertas como se recordaban
  no registra nada. Una entrada con antorcha registra solo las salas que
  cambiaron de estado y las caras cuyo recuerdo cambió, así que su costo y el
  de invertirla son proporcionales a lo revelado (§5.3, FR-033).

**Justificación**:

- Es el mecanismo único de reversión del proyecto (principio V: solo se
  registra lo necesario para invertir, sin copias). El pergamino (FR-011,
  FR-029) y la reversión de una entrada con antorcha (US5 escenario 1) salen
  del Diario existente: el intervalo de un paso contiene el movimiento y sus
  cambios de conocimiento, y deshacer lo revierte todo junto.
- La línea de tiempo (feature 004, FR-034) necesita ver cada cambio de estado
  con su valor anterior. Si el conocimiento cambia solo por el Mutador, el
  observador que conecte 004 lo recibe sin que esta feature sepa nada de 004.
- La carga inicial (`Partida.iniciar`) corre con el Mutador en pausa, igual
  que hoy: el conocimiento del instante 0 es el punto de partida, no un cambio
  reversible.

**Alternativas descartadas**: guardar una copia del conocimiento por acción
(prohibido por el principio V y O(salas) por acción); un Diario propio de la
niebla (dos mecanismos de reversión que deben coincidir en orden).

---

## R3. Observación de puertas

**Decisión**: "observar una puerta" es copiar el estado real de **cada cara**
de esa puerta a su `recordada`. Estando en la sala A, el jugador observa:

- las caras que salen de A (`A.salidas`), y
- las caras que entran a A (`A.entrantes`, del enlace de 001): la contraparte
  B→A de cada puerta y también las de un solo sentido que llegan a A.

Son a lo sumo 4 + (entrantes de A) caras, O(grado de A). Se observa:

1. al iniciar la partida, la sala inicial;
2. al entrar a una sala (en `Partida._mover_jugador`, inmediatamente después
   de cambiar la sala del jugador y antes de trampas y enemigos);
3. cuando una cara cambia de estado mientras el jugador está en una de sus dos
   salas. Hoy `cerrada` se escribe en dos lugares del Modelo
   (`Partida._abrir_puerta` y `EventoCierrePuerta.ejecutar`). Ambos pasan a
   llamar a un único `Partida.cambiar_puerta(salida, cerrada)`, que asigna por
   el Mutador y, si `salida.origen` o `salida.sala_destino` es la sala del
   jugador, observa esa cara. O(1).

Con esto, la sala del jugador tiene siempre sus caras observadas: el recuerdo
coincide con el estado real. Por eso FR-024 ("antes de cada paso, con las
observaciones de la sala actual ya registradas") se cumple sin observar de
nuevo antes de cada paso, y el escenario obligatorio de la puerta recordada
abierta que está cerrada se resuelve al entrar a la sala vecina de esa puerta.

**Por qué no en el setter de `cerrada`**: el setter también lo dispara el
Diario al deshacer (`setattr`) y la carga. Si observara ahí, deshacer
escribiría recuerdos que el Diario también restaura y el orden de las dos
reversiones decidiría el resultado. Al hacerlo en `cambiar_puerta`, solo los
cambios del juego observan; deshacer restaura `cerrada` y `recordada` cada uno
con su propio registro.

**Antorcha** (FR-009, clarificación 1): explorar una vecina con la antorcha no
observa sus puertas. La única puerta compartida con la sala del jugador ya
quedó observada por el punto 2. Las demás caras de la vecina quedan
`NO_OBSERVADA` y «ir a» no las usa (FR-021).

---

## R4. Salas exploradas y avistadas en orden de id para el panel

**Orientación del equipo**: una colección propia **ordenada** que crece al
explorar (inserción ordenada en `ListaEnlazada`), revertible con el Mutador.

**Decisión**: se cambia la orientación. Se mantiene un **registro de salas
conocidas en orden de descubrimiento** (`ListaDoble` propia): cada sala que
pasa de desconocida a avistada o explorada se agrega **al final** (O(1)), y el
inverso en el Diario la **quita del final** (O(1)). El orden por id se obtiene
**al armar el panel**, copiando el registro y ordenándolo con el
`ordenamiento.mezcla` propio (O(k log k), k = conocidas), solo cuando el panel
del mapa está abierto.

**Justificación**:

- La inserción ordenada recorre el registro hasta su lugar: O(k) por sala
  revelada. Eso hace que explorar dependa del tamaño del mapa conocido, que es
  justo lo que prohíben §5.3, FR-033 y SC-005 (tabla: ×28 de 25 a 1200
  conocidas).
- El Diario revierte siempre en orden inverso al de los cambios (pila de
  intervalos, pila de registros), así que la sala que hay que quitar es
  siempre la última agregada: quitar del final es exacto y O(1).
- El panel se abre a pedido. Ordenar 300 conocidas cuesta 0,33 ms; ni
  siquiera las 1200 de la malla llegan a 2 ms, y no está en el camino de cada
  paso de «ir a» ni de cada entrada.

**Mediciones** (registrar 4 salas reveladas, que es lo que revela una antorcha
en una sala con 4 salidas, según el tamaño del mapa conocido):

| Conocidas | Inserción ordenada | Agregar al final | Ordenar al abrir el panel |
|---:|---:|---:|---:|
| 25 | 2,58 µs | 1,01 µs | 0,02 ms |
| 100 | 5,00 µs | 0,88 µs | 0,09 ms |
| 300 | 18,58 µs | 0,91 µs | 0,33 ms |
| 1200 | 71,44 µs | 0,88 µs | 1,80 ms |

**Alternativas descartadas**: inserción ordenada (la del equipo, por FR-033);
recorrer todo el mundo al abrir el panel filtrando por `conocimiento`
(O(salas) en vez de O(k), y FR-016/§5.3 piden no recorrer la cripta); un
árbol de búsqueda propio (O(log k) por inserción, pero más código que probar
para un orden que solo se necesita al abrir el panel).

**Carga**: el Diario no se guarda (una partida cargada empieza con el Diario
vacío, D64 y `ControladorJuego._cargar_desde_guardado`), así que el orden de
descubrimiento no importa después de cargar. El registro se reconstruye con
una pasada O(salas) sobre el mundo cargado, una vez por carga, como ya hace
`Partida.reconstruir_tras_cargar` con los cazadores.

---

## R5. Ruta de «ir a»

**Decisión**: un **buscador propio, separado del mapa de distancias del
cazador**: Dijkstra **hacia adelante** desde la sala del jugador sobre el
subgrafo conocido, con el `HeapMinimo` propio, eliminación perezosa y estado
de búsqueda en campos de la sala con sello (como R5 y R6 de 001). Se detiene
en cuanto fija la sala destino.

- **Subgrafo conocido** (FR-021): una cara `u → v` se recorre si
  `u.conocimiento == EXPLORADA`, `u_salida.recordada == ABIERTA` y
  `v.conocimiento == EXPLORADA`. El costo es `Salida.costo` (100 si no se
  declaró, FR-019). Nunca se lee `cerrada` (estado real).
- **Desempate** (FR-020): la etiqueta de cada sala es el par
  (costo acumulado, clave del primer paso), con clave del primer paso =
  `id de la vecina × 4 + índice de la dirección` (N=0, S=1, E=2, O=3). Se
  compara en orden lexicográfico. La clave se hereda sin cambios al extender
  una ruta, así que el orden lexicográfico es compatible con Dijkstra: entre
  rutas de igual costo gana la de primer paso hacia la vecina de menor id
  (comparación de enteros, clarificación de FR-020) y, hacia la misma vecina,
  la primera salida en N, S, E, O.
- **Sin reutilizar**: la ruta se calcula desde cero antes de cada paso
  (FR-024). No hay caché que invalidar (principio VI).

**Mediciones** (un paso de «ir a» con el mapa conocido completo; mínimo de 5
repeticiones por par, 300 pares al azar con semilla fija):

| Cripta | Recuerdos | A: adelante con parada | B: atrás completo + fórmula del cazador | ¿Mismo primer paso? |
|---|---|---:|---:|:--:|
| referencia (300 salas) | estado real | media 0,10 ms, peor 0,14 ms | media 0,10 ms, peor 0,13 ms | 299/299 |
| referencia (300 salas) | todas abiertas | media 0,32 ms, peor 0,65 ms | media 0,57 ms, peor 0,65 ms | 299/299 |
| malla (1024 salas) | todas abiertas | media 1,94 ms, peor 3,99 ms | media 3,62 ms, peor 7,47 ms | 300/300 |

Ambos cumplen < 5 ms en la cripta de referencia (FR-031, SC-004) con un
margen de casi 8 veces en el peor caso. En la malla de estrés solo A queda por
debajo de 5 ms: la parada temprana fija en promedio 541 de 1024 salas, B las
fija todas.

**¿Compartir implementación con el cazador? (§5.3)**: **no**, se separan.

- Grafo distinto: el cazador recorre el esqueleto real (`cerrada`); «ir a»,
  el conocimiento (`conocimiento`, `recordada`). Compartir obliga a
  parametrizar `MapaDistancias` con un predicado de transitabilidad.
- Objetivo y sentido distintos: el mapa del cazador es hacia la sala del
  jugador, compartido por todos los cazadores, con cota (D72) y clave de
  validez (R2 de 001). «ir a» es un solo origen y un solo destino por paso, sin
  cota y sin caché; reutilizar el mapa hacia atrás obliga a calcularlo completo
  (columna B), que en la malla falla los 5 ms.
- Riesgo: `MapaDistancias` ya está medido y probado contra su oráculo
  (`prueba_cazador_equivalencia`). Cambiarlo para servir a «ir a» arriesga
  FR-017 de 001 sin ganar nada medible.
- Lo que sí se comparte es el **patrón**: `HeapMinimo` con eliminación
  perezosa, sellos en campos de la sala y entradas con orden total
  determinista. Los campos de búsqueda de «ir a» son **propios**
  (`_sello_ruta`, `_costo_ruta`, `_paso_ruta`, `_fijada_ruta`) y su sello vive
  en el Mundo junto al del mapa, para que una búsqueda de «ir a» nunca
  invalide ni ensucie el mapa del cazador.

**Alternativas descartadas**: B (sentido inverso, reutiliza el patrón del
cazador, pero no cumple en la malla y no puede parar antes); BFS por cantidad
de salas (FR-019 exige costo mínimo); A\* (sin coordenadas, no hay heurística
admisible, igual que en 001); guardar la ruta del paso anterior y seguirla
(FR-024 exige recalcular; reutilizar exigiría probar que no cambia la
decisión, principio VI, y la memoria de puertas cambia entre pasos).

**Equivalencia** (SC-006): un oráculo en la carpeta de pruebas, Bellman-Ford
hacia adelante sobre el subgrafo conocido con las mismas reglas de desempate
(como `oraculo_rutas.py` de 001), compara el primer paso en ≥ 1000 pares de
criptas sintéticas con puertas recordadas al azar (abiertas, cerradas, no
observadas) y empates forzados (costos iguales, vecinas 9 y 10).

---

## R6. Ejecución del viaje

**Decisión** (orientación 5 del equipo, con precisiones):

- **Modelo**: `ViajeIrA` (estado del viaje) y `BuscadorRuta` (R5) en el
  Modelo. El Modelo valida la orden (FR-018: destino explorado, no es la sala
  actual, hay ruta) y elige cada paso como un `Mover(dirección)` ordinario.
  Cada paso se aplica con `Partida.aplicar_accion`, así consume tiempo,
  dispara trampas, activa enemigos, procesa eventos y abre su propio
  intervalo del Diario igual que un movimiento a mano (FR-023, FR-029).
- **Controlador**: `ControladorJuego` guarda el viaje en curso y da **un paso
  por vuelta del bucle externo** (`fabricaAplicacion`, D44), con la vista
  refrescada entre pasos. `ControladorMenu.procesar` hoy descarta los `None`
  antes de llegar a la partida; pasa a entregarle también los `None` cuando
  hay un viaje en curso.
- **Detección de motivos** (FR-024), sin recorrer nada:
  - *llegada*: la sala del jugador es el destino;
  - *enemigos en la sala*: `Partida._mover_jugador` anota, antes de activar,
    si la sala de destino tenía enemigos activos o dormidos;
  - *daño recibido*: `Partida.danar` anota si el dañado fue el jugador (ataque,
    trampa o veneno, también en los eventos que siguen al paso,
    clarificaciones 2 y 3);
  - *partida terminada*: `Partida.terminada()`;
  - *sin ruta conocida*: el buscador no encuentra ruta antes del paso
    siguiente; no se aplica ninguna acción, así que no se consume tiempo.

  Las dos anotaciones son **transitorias**, como `Partida._mensajes`: se
  limpian al empezar cada `aplicar_accion` y viajan en `ResultadoAccion`
  (`entro_con_enemigos`, `dano_recibido`). No son estado del juego, no se
  guardan ni se revierten.
- **Pergamino e interrupción** (FR-028, FR-029): los comandos llegan de a uno
  por vuelta del bucle, y cada paso es atómico dentro de una vuelta, así que
  cuando llega un comando el paso en curso ya terminó. Con un viaje en curso:
  - `pergamino`: el viaje se detiene con el motivo "pergamino de retroceso" y
    luego se aplica `UsarPergamino` como siempre, que deshace el intervalo más
    reciente, es decir, solo el último paso;
  - `interrumpir` (tecla **I**): el viaje se detiene con el motivo
    "interrumpido";
  - cualquier otro comando: el viaje se detiene ("interrumpido") y el comando
    se procesa normalmente. Así ninguna tecla compite con un viaje en curso.
- **Destino**: el comando `ir_a <id>` lo resuelve con `Mundo.sala(id)` una
  sola vez; una sala inexistente da el mismo rechazo que una desconocida
  (FR-018). El viaje guarda la referencia a la sala destino.

**Alternativas descartadas**: ejecutar el viaje completo dentro de un solo
`procesar` (la vista no se refresca entre pasos y no hay punto donde detectar
el pergamino, FR-029); una acción compuesta `IrA` en el Modelo con un solo
intervalo del Diario (el pergamino revertiría el viaje entero, contra FR-029 y
el Apéndice B); detectar daño comparando la vida antes y después (una
curación en el mismo paso lo ocultaría).

---

## R7. Registro y reproducción

**Decisión**: el puerto `RegistroAcciones` gana `registrar_comentario(texto)`.
`RegistroArchivo` escribe la línea `# IR_A <id>` (prefijo `# `) antes del
primer paso, y cada paso queda como la línea `MOVER <dir>` de siempre
(FR-026). `RegistroArchivo.leer()` ignora toda línea que empiece con `#`
(FR-027), así que `--replay` reproduce los movimientos individuales y llega al
mismo estado, con el mismo conocimiento, porque el conocimiento es función de
las acciones. Los logs anteriores no tienen comentarios y se leen igual. Una
orden rechazada no escribe nada (FR-018, FR-026).

**Alternativa descartada**: registrar `IR_A <id>` como acción y reproducir el
viaje (la reproducción dependería de recalcular rutas y de los motivos de
detención; con los movimientos individuales el replay es literal).

---

## R8. Vista y teclas

**Decisión** (orientación 6 del equipo):

- **M** abre y cierra el panel del mapa conocido (verbo de sesión
  `alternar_mapa`: no consume tiempo ni va al log, FR-017). El Controlador
  arma el DTO `MapaConocidoVisible` solo mientras el panel está abierto, así
  el costo de ordenar (R4) no se paga en cada turno.
- Con el panel abierto, flecha arriba/abajo mueven el cursor entre las salas
  **exploradas** (las avistadas se muestran pero el cursor las salta,
  FR-035), RePág/AvPág desplazan como el panel de V, y **Enter** envía
  `ir_a <id>` y cierra el panel. Mientras está abierto, las flechas no
  mueven al jugador (como el panel de V, D80).
- **I** interrumpe un viaje en curso (FR-028). Fuera de un viaje no hace nada.
- **H** queda reservada para la feature 004 (historia); esta feature no la
  asigna.
- El motivo de detención llega como mensaje (`mostrar_mensajes`) y queda en
  la bitácora (FR-025); mientras el viaje sigue, el HUD muestra "Viajando a
  <nombre> (I para detener)" desde `ViajeVisible`.
- La sala actual sigue dibujándose como hoy; el estado de sus salidas se lee
  de `recordada` (que coincide con el real, R3) para que todo lo dibujado
  salga del conocimiento (FR-014).

Letras ocupadas hoy en la partida: A, C, G, L, O, P, Q, R, S, U, V (más B, N
y X en el menú). M e I estaban libres; H queda reservada. Se actualiza la
tabla de teclas del README.

---

## R9. Guardado

**Decisión** (orientación 7): `FORMATO_VERSION` pasa de 2 a **3**. Cada sala
agrega un `uentero32` con `conocimiento` y cada salida uno con `recordada` (el codificador binario no tiene enteros de un byte y no hace falta agregarlos). No se
guarda el registro de conocidas: se reconstruye al cargar (R4). Un archivo de
versión 1 o 2 lanza `VersionIncompatible("formato de archivo de partida", 3,
version_leida)`, cuyo mensaje ya dice la versión encontrada y la esperada
(FR-013, clarificación 4). `cargar_sala` (carga parcial por índice) lee los
mismos campos nuevos. El número 3 se coordina con la feature 004, que también
cambiará el formato: la que llegue segunda a `main` toma el 4.

---

## R10. Comprobaciones de SC-003 y SC-002

- **SC-003** (revertir devuelve el conocimiento): el Diario guarda como mucho
  5 intervalos (`TAMANO_HISTORIAL`). La prueba genera 1000 secuencias con
  semilla fija de 1 a 5 acciones (movimientos con y sin antorcha, abrir
  puertas, esperar cierres automáticos), toma una huella del conocimiento
  (lista de `(id, conocimiento)` y `(id, dirección, recordada)` armada por la
  prueba), aplica, revierte con pergaminos y compara. En cada punto también
  guarda y carga y compara la huella.
- **SC-002** (nada desconocido llega a la vista ni a «ir a»): la prueba arma
  partidas sintéticas con salas desconocidas cuyo nombre es una marca única y
  revisa que ninguna marca aparezca en `EstadoVista` ni en el mapa; para
  «ir a», instrumenta el buscador para registrar cada sala y cara que lee y
  comprueba que todas eran exploradas y abiertas según el recuerdo.

---

## R11. Mediciones para `--bench`

**Decisión**: un módulo `benchNiebla` registrado en `benchTodo` mide, con la
cripta de referencia (elegida en ejecución, principio IV) y la malla de 1024
salas:

1. **Un paso de «ir a»** con el mapa conocido completo (estado real y todas
   abiertas), peor caso y media sobre pares al azar con semilla fija. Criterio:
   peor < 5 ms en la cripta de referencia (FR-031, SC-004). Alternativa
   descartada medida al lado: búsqueda hacia atrás completa + fórmula del
   cazador (R5).
2. **Consultas** de estado de sala y de cara recordada con mapas conocidos de
   25, 100, 300 y 1200 salas. Criterio: al multiplicar por 4 el mapa, la media
   no crece más de 1,5 veces (SC-005). Alternativa: búsqueda lineal por id (R1).
3. **Exploración con antorcha** que revela 4 salas con mapas conocidos de los
   mismos tamaños. Criterio: mismo de SC-005. Alternativa: inserción ordenada
   (R4).
4. **Registrar e invertir** el cambio de una entrada con antorcha (registros
   del Diario y tiempo de deshacer) según las salas reveladas: crece con lo
   revelado, no con el mapa (FR-033).
5. **Armar el panel** (copiar y ordenar las conocidas) con 300 y 1200 conocidas,
   como dato informativo.

La prueba automática `prueba_rendimiento_ir_a` toma el mínimo de varias
repeticiones (como `Medidor`) y verifica solo el criterio de FR-031 en la
cripta de referencia; la malla queda como estrés informativo, igual que en 001.
