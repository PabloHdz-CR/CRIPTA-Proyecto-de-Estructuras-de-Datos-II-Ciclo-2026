# Research: Resolubilidad

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Fecha**: 2026-11-08

Cada sección da la decisión, la justificación y las alternativas descartadas.
Las cifras de rendimiento que se citan como **objetivo** se confirman con
`--bench` en la implementación (principio VI); este documento no afirma
tiempos medidos.

Notación: S = salas, E = salidas (caras de puerta), K = llaves distintas
(las que aparecen en la ubicación de llaves, en alguna salida o como
llave_salida), L = entradas de la ubicación de llaves.

---

## R1. Grafo de verificación sin dict: nodos propios enlazados por ordenamiento

**Decisión**: la verificación construye su propio grafo, separado del `Mundo`
de la partida. Un `NodoSala` por sala del esqueleto y un `NodoLlave` por id
de llave distinto. Las referencias (salida → nodo destino, salida → nodo de
su llave, ubicación → nodo sala y nodo llave) se resuelven **ordenando** con
`ordenamiento.mezcla` (merge sort propio, estable, O(n log n)) y
**fusionando** dos secuencias ordenadas en una pasada, nunca buscando por id.

- Nodos de sala ordenados por id; pares (id_destino, salida) ordenados por id
  de destino; una pasada de fusión asigna a cada salida su `NodoSala`.
- Ids de llave de tres orígenes (salidas cerradas con llave, ubicaciones y
  llave_salida) ordenados como texto y deduplicados en la misma pasada: un
  `NodoLlave` por id.
- Cada `NodoLlave` lista sus ubicaciones (ordenadas por sala y enemigo) y sus
  puertas (las salidas cerradas que lo requieren).
- Una ubicación cuya sala no existe en el esqueleto o una salida cuyo destino
  no existe se detectan en la fusión (queda sin pareja) y lanzan
  `DatosInvalidos` con la entrada concreta (FR-030).

Costo de la construcción: O((S + E + L) log(S + E + L)). Es la única parte
no lineal y es un factor log sobre el tamaño, no sobre las llaves (FR-033:
"aproximadamente lineal").

**Justificación**: el principio I prohíbe dict y set como índice. Buscar cada
destino recorriendo el esqueleto (`EsqueletoCripta.buscar`, O(S)) costaría
O(E · S): D73 midió `enlazar()` del Mundo con búsqueda lineal en 64,79 ms
sobre 1024 salas, un tercio del presupuesto de 200 ms solo en armar el grafo.
Ordenar y fusionar evita el cuadrático sin estructuras prohibidas, y además
deja todo en un orden canónico que no depende del orden de llegada de las
páginas ni de las entradas de llaves (FR-010, SC-004).

**Alternativas descartadas**:
- Reutilizar `Mundo` + `Mundo.enlazar()`: exige crear salas del modelo de
  juego (con contenido pendiente) solo para verificar y arrastra el costo
  O(E · S) de D73.
- Tabla hash propia: es un dict hecho a mano; el equipo decidió no usar tablas
  de búsqueda (D32) y no está entre los TDA permitidos.
- Árbol binario de búsqueda propio: tampoco está entre los TDA permitidos y
  no mejora O(n log n).

---

## R2. Orden de obtención: recorrido con llaves pendientes y heap mínimo

**Decisión**: un solo recorrido en anchura desde la sala inicial que nunca
vuelve a empezar (fase 1).

1. Se marca la sala inicial como alcanzada y se encola.
2. Al sacar una sala se examinan sus salidas en orden N, S, E, O:
   - abierta, o cerrada cuya llave ya está **obtenida** → se alcanza el
     destino si no estaba alcanzado. Si además es una salida que requiere
     llave_salida con destino sala_salida, se pone la marca
     `entra_por_puerta_salida` (R3), **aunque sala_salida ya estuviera
     alcanzada por otro camino**;
   - cerrada con llave no obtenida → la salida se anexa a las **puertas
     pendientes** de su `NodoLlave`;
   - cerrada sin llave → se anexa a la lista de bloqueadas sin llave.
3. Al alcanzar una sala, cada llave ubicada en ella que todavía no esté
   disponible entra a un `HeapMinimo` propio de llaves **disponibles**,
   comparadas por id (texto).
4. Cuando la cola se vacía, se extrae del heap la llave disponible de menor id,
   se agrega al orden, se marca obtenida y sus puertas pendientes se
   reexaminan: sus destinos no alcanzados se alcanzan y se encolan, y una
   pendiente que requiere llave_salida con destino sala_salida pone la marca
   `entra_por_puerta_salida`, aunque sala_salida ya estuviera alcanzada. Se
   vuelve al paso 2.
5. Termina cuando la cola y el heap están vacíos.

Cada salida se examina como máximo dos veces (al sacar su sala y, si quedó
pendiente, al obtenerse su llave); cada sala se encola una vez; cada llave
entra al heap una vez. Costo: O(S + E + L + K log K).

**Justificación**:
- Es el orden **lexicográficamente menor** que exige FR-009: obtener una llave
  solo agranda la región (FR-003, las llaves no se consumen), así que la
  elección codiciosa "la disponible de menor id" nunca impide una elección
  posterior. Por eso el orden codicioso coincide con el menor válido.
- La región se expande hasta agotarse **antes** de elegir la próxima llave,
  así que el heap contiene exactamente las llaves alcanzables con las ya
  ordenadas (FR-007). Elegir antes de agotar la cola daría un orden válido
  pero no siempre el menor.
- Se cumple FR-033: nunca se repite el recorrido completo al obtener una
  llave; solo se reexaminan sus puertas pendientes.

**Ubicación mostrada en el orden**: para cada llave del orden se muestra su
primera ubicación (por sala y enemigo) que ya estaba alcanzada al elegirla.
Cuesta O(ubicaciones de esa llave) y no cambia el orden.

**Alternativas descartadas**:
- Repetir el recorrido completo por cada llave obtenida: es la **alternativa
  ingenua** de FR-035, O(K · (S + E)). Queda en el bench como comparación.
- Ordenar por orden de descubrimiento (recorrido N, S, E, O): se descartó en
  la aclaración 3, porque depende de cómo se defina el recorrido.

---

## R3. Veredicto, motivo y frontera bloqueada: del mismo recorrido

**Decisión**:
- **Salida que requiere llave_salida**: una salida **cerrada** cuya llave es
  llave_salida. Una salida abierta que declara llave no "requiere" nada
  (FR-002: se atraviesa sin llave).
- **Ganable**: la marca `entra_por_puerta_salida` se pone al **examinar**
  una salida cerrada que requiere llave_salida, con llave_salida ya obtenida
  y destino sala_salida, desde una sala alcanzada. Se examina en los dos
  momentos de R2: al sacar la sala de la cola y al reexaminar las puertas
  pendientes cuando se obtiene llave_salida. La marca **no** depende de que
  sala_salida esté o no alcanzada: si ya se llegó por un camino abierto, la
  salida se examina igual y la marca se pone. Esto es lo que hace resoluble el
  escenario 12 de la historia 1 (dos caminos, uno por la salida que requiere
  llave_salida; H1.E12, FR-001). Sin esta regla, el recorrido ignoraría la
  salida por "destino ya alcanzado" y daría no resoluble.
  **Resoluble** ⇔ llave_salida obtenida y `entra_por_puerta_salida`
  (FR-001). Llegar a sala_salida por otro camino marca
  `sala_salida_alcanzada`, pero no cambia el veredicto.
- **Motivo** (FR-011): (a) si llave_salida no está obtenida; (b) en otro caso.
  En el caso (b), `sala_salida_alcanzada` indica que solo se llega sin esa
  salida.
- **Frontera** (FR-012): al final de la fase 1, las puertas pendientes de las
  llaves no obtenidas y las bloqueadas sin llave cuyo destino **no** quedó
  alcanzado. Ya están en memoria, así que se filtran en una pasada sin otro
  recorrido (FR-034). Una puerta cerrada cuyo destino se alcanzó por otro
  camino no es frontera (caso borde).
- **Llaves no obtenibles** (FR-011, FR-013): los `NodoLlave` no obtenidos,
  ordenados por id (ya lo están por R1), con todas sus ubicaciones o
  "sin ubicación" (FR-016).

---

## R4. Dependencias y ciclos: componentes fuertes del grafo de bloqueo

FR-014 define: K depende de Y si alguna salida cerrada que requiere Y conduce
hasta la ubicación de K sin atravesar otra salida intransitable con las
llaves obtenibles.

**Decisión**: la fase 2 continúa el mismo recorrido más allá de la frontera,
sobre las salas **no alcanzadas** (las alcanzadas no participan: desde ellas
no se llega a ninguna ubicación no obtenible sin pasar por una puerta
bloqueada). Usa el **grafo de bloqueo**:

- nodos: salas no alcanzadas y llaves no obtenidas;
- sala → sala: salida transitable con las llaves obtenibles (abierta, o
  cerrada con llave obtenida) entre salas no alcanzadas;
- sala → llave K: K está ubicada en esa sala;
- llave Y → sala d: una salida cerrada que requiere Y llega a d, desde
  cualquier sala.

K depende de Y ⇔ hay un camino Y → (salas)* → K sin otra llave en medio. Una
cadena de dependencias K → Y₁ → … → K es un ciclo del grafo de bloqueo que
pasa por nodos de llave. Por eso:

1. **Grupos (FR-015)** = componentes fuertemente conexas del grafo de bloqueo
   que contienen al menos una llave y más de un nodo. Se calculan con una sola
   pasada de Tarjan **iterativo** (pila propia `Pila`, índices y enlaces en
   campos de los nodos con sello, sin recursión ni dict). O(S + E + L + K).
2. **Dependencia mínima dentro del grupo**: todo camino Y → … → K entre llaves
   de un mismo grupo queda dentro del grupo. Se hace un **relleno por orden
   de prioridad**: las puertas que requieren una llave de un grupo y llegan a
   una sala del mismo grupo se ordenan por (id de Y, sala de origen, dirección
   N, S, E, O) con `mezcla`. Cada una inunda, por salidas transitables dentro
   del grupo, las salas todavía sin etiqueta, y les pone la etiqueta
   (Y, puerta). Cada sala queda con la **menor** puerta que la alcanza: si una
   puerta anterior ya la etiquetó, todo lo que se alcanza desde ella ya tiene
   una etiqueta igual o menor. Cada sala se etiqueta una vez. O(S + E log E).
3. **Dependencia de K** = la menor etiqueta entre las salas de sus
   ubicaciones dentro del grupo. Da a la vez la llave Y de menor id de la que
   depende K y la puerta que muestra FR-015 (menor sala de origen y luego
   N, S, E, O).
4. **Ciclo (FR-015)**: desde la llave de menor id del grupo se sigue la
   dependencia mínima hasta repetir una llave; el ciclo se muestra desde esa
   llave repetida. Hay un solo sucesor por llave, así que el paseo cuesta
   O(llaves del grupo). Los grupos se listan por su menor id.

Ninguna pasada se repite por llave: la fase 2 es una pasada de Tarjan y una
de relleno sobre la parte no alcanzada. Sumadas a la fase 1, cada salida se
examina un número constante de veces. Así se cumplen FR-033 y FR-034. El bench
cuenta las salidas examinadas para demostrarlo (SC-003).

**FR-034** (enmendado en `254747e`): la frontera sale del recorrido de la
fase 1, y las dependencias y los ciclos, de una sola pasada para todas las
llaves que continúa más allá de la frontera. Es exactamente la fase 2.

**Alternativas descartadas**:
- Una búsqueda por llave no obtenible (hacia atrás desde su ubicación):
  O(K · (S + E)), que es justo lo que FR-034 prohíbe.
- Una sola dependencia por llave (la primera puerta que la alcanza en una
  búsqueda multifuente): es lineal pero no es la relación de FR-014 y
  cambiaría los ciclos de FR-015.
- Enumerar todos los ciclos elementales: exponencial, y FR-015 pide uno por
  grupo.

---

## R5. Consulta de llaves: nuevo método del puerto, síncrono, con caché por versión

**Decisión**:
- `FuenteDatos.llaves(id_cripta)` → `ListaEnlazada` de `UbicacionLlaveDTO`.
  `ClienteHttp` hace `GET /criptas/<id>/llaves` por `_pedir`, así que cuenta
  cada intento y reintento en el `ContadorSolicitudes` y respeta el
  presupuesto (FR-026). `FuenteOffline` lee `criptas/<id>/llaves.json`.
  Ambas convierten con la misma `convertidorJson.llaves_desde_json`
  (FR-029).
- Es una consulta **síncrona** (como los datos generales): una sola solicitud
  por versión, que hace falta antes de decidir si la partida inicia.
- `ServicioDatos.ubicacion_llaves()` resuelve en cascada: memoria, luego disco
  (`AlmacenLocal.cargar_llaves(id_cripta, version_cripta)`, None si la versión
  no coincide) y por último red, que guarda en disco con
  `guardar_llaves(...)`. Dos verificaciones de la misma versión hacen como
  máximo una solicitud (FR-027, SC-007).
- Validación en el convertidor: la raíz es un objeto con `llaves` (lista);
  cada entrada trae `id` (texto no vacío), `sala` (entero, sin bool) y
  opcionalmente `enemigo` (texto). Cualquier otra cosa lanza `DatosInvalidos`
  con el índice y el campo (FR-030). La existencia de la sala se valida en el
  grafo (R1), porque el convertidor no conoce el esqueleto.

**Justificación**: sigue el patrón de D15 (fichas por versión de catálogo) con
la versión de cripta. Un dato de la primera parte nunca coincide con una
versión nueva y se trata como no encontrado (FR-028); no hay datos viejos de
llaves que borrar.

**Alternativas descartadas**:
- Pedirla por la fuente asíncrona: no hay nada que hacer en paralelo, porque
  la verificación espera la respuesta.
- Guardarla dentro del archivo de partida: la verificación ocurre antes de que
  exista una partida, y cargar una guardada no verifica (FR-021).

---

## R6. Tres resultados y "no se pudo verificar"

**Decisión**: la función del modelo `verificar_cripta(servicio)` captura
`ErrorCripta` (red, presupuesto agotado, datos inválidos o ausentes) al pedir
llaves o al armar el grafo, y devuelve un resultado `NO_VERIFICADA` con el
mensaje. Nunca lo convierte en "no resoluble" (FR-031). Si la fuente sin
conexión no tiene `llaves.json`, el error sale de `FuenteOffline._leer` y
termina en `NO_VERIFICADA`; nunca se supone una lista vacía (FR-029).

---

## R7. Formato del reporte: un texto canónico compartido por terminal y ventana

**Decisión**: el modelo entrega un `ResultadoResolubilidad` (datos puros). El
Controlador lo convierte en líneas de texto con un solo formateador
(`textoResolubilidad`), con el formato exacto de
[contracts/reporte.md](contracts/reporte.md). `--verificar` imprime esas
líneas y la Vista recibe las mismas dentro de un DTO inmutable. Así, el
"idéntico carácter por carácter" de SC-004 se prueba sobre un solo texto.

---

## R8. Inicio de partida, `--forzar` y la tecla V

**Decisión**:
- `ControladorJuego` se divide en `preparar_nueva(id_cripta)`, que descarga
  datos, esqueleto y llaves, verifica y devuelve el resultado, e
  `iniciar_preparada(semilla, forzada)`, que crea la `Partida` y el log.
- `ControladorMenu._empezar_partida` decide:
  - resoluble: inicia y agrega a la bitácora el aviso "La cripta es
    resoluble. V muestra el reporte.";
  - no resoluble o no verificada **sin** `--forzar`: muestra la pantalla de
    reporte, no crea partida ni log y reinicia la sesión al volver
    (FR-019);
  - con `--forzar`: misma pantalla y, con el comando `aceptar_resolubilidad`,
    inicia con `forzada=True` (FR-020).
- La partida cargada y los dos replays no llaman a `preparar_nueva`
  (FR-021).
- **Camino sin verificación**: `ControladorJuego.iniciar_nueva(id_cripta,
  semilla)` se conserva con el mismo nombre y la misma firma, y **no**
  verifica. Lo usan las pruebas que arman una partida directo, y lo usa
  `iniciar_preparada` por dentro. El bench y los replays no pasan por
  `ControladorJuego` (crean la `Partida` directo) y no cambian.
- La tecla V alterna en la Vista un panel con las líneas del reporte, como L
  con la bitácora: estado local de la Vista, sin comando ni acción del
  jugador, así que no va al log ni gasta reloj. Las líneas llegan en
  `EstadoVista.resolubilidad`.
- **V sin reporte**: en una partida cargada, `resolubilidad` es None (FR-021:
  cargar no verifica). V manda entonces el verbo de sesión
  `ver_resolubilidad` y `ControladorJuego` escribe en la bitácora "Esta
  partida no tiene reporte de resolubilidad." con `Partida.avisar`. Es
  presentación: no va al log, no gasta reloj y no se revierte (como el resto
  de `avisar`). En el replay, V no hace nada.
  Contrato en [contracts/vista.md](contracts/vista.md).

**Alternativas descartadas**: un verbo de sesión "ver_resolubilidad"
procesado por el Controlador. Funciona, pero agrega un viaje de ida y vuelta
para algo que es solo mostrar u ocultar datos que la Vista ya tiene (mismo
criterio que la tecla L con la bitácora).

---

## R9. Anotación de partida forzada en el log

**Decisión**: `EncabezadoPartida` gana `forzada: bool = False`.
`RegistroArchivo` agrega la **palabra** `FORZADA` después de los 4 campos fijos
del encabezado solo si es True. Al leer, acepta después de los 4 fijos
cualquier cantidad de palabras **conocidas**, en cualquier orden, y rechaza
las desconocidas. Así, si otra feature agrega su propia palabra, no hay
choque por posición (plan.md, "Posibles choques"). Los logs anteriores se
siguen leyendo igual y `--replay` ignora la marca (FR-021). El archivo binario
de partida no cambia (no hay versión nueva de formato).

**Alternativa descartada**: una línea extra después del encabezado. El lector
la tomaría por una acción y rompería los logs existentes al reproducir.

---

**Ajuste tras /speckit-analyze (I2)**: FR-020 pide anotar "que la cripta no
era resoluble y que se forzó", así que `FORZADA` va siempre con una palabra de
veredicto: `FORZADA NO_RESOLUBLE` o `FORZADA NO_VERIFICADA`. Se agrega
`EncabezadoPartida.veredicto_forzado`. Las reglas de lectura están en
[contracts/registro.md](contracts/registro.md).

---

## R10. `--verificar <cripta>`

**Decisión**: `FabricaAplicacion` lee `--verificar ID` y `--forzar`. Con
`--verificar`, arma el servicio (en línea o `--offline`), ejecuta `ModoVerificar`
y sale con el código del contrato
([contracts/linea-de-comandos.md](contracts/linea-de-comandos.md)): 0, 1 o 2.
No importa `vistaArcade`, no crea `Partida`, log ni puntaje (FR-023), igual que
`--replay` y `--bench` (principio III).

---

## R11. Bench: verificación, alternativa ingenua y criptas sintéticas

**Decisión**: `benchResolubilidad`, registrado en `benchTodo`.
- **Cripta de referencia**: la de más salas que lista `FuenteOffline` sobre
  `datos_offline/`, elegida en ejecución (sin ids, FR-036), igual que
  `benchCazador`. Solo cuenta el tiempo de construir el grafo y verificar, sin
  red ni renderizado. Se reporta PASA/FALLA contra 200 ms (FR-032). Si esa
  cripta no tiene `llaves.json`, la fila dice **SIN DATOS** y el resultado no
  es PASA: no se mide con una ubicación de llaves inventada ni vacía. La
  prueba de la suite que la usa (H5.E1) **salta** imprimiendo "SIN DATOS"
  mientras `datos_offline/` no tenga llaves, y pasa a obligatoria (falla sin
  datos) en la tarea final T061.
- **Cadenas sintéticas** de 100, 200 y 400 llaves: la llave i abre la puerta
  hacia la zona de la llave i+1. Hay una variante resoluble y otra con la
  última puerta en ciclo, para medir también la fase 2. Para cada una se mide
  el tiempo y las salidas examinadas de la verificación y de la alternativa
  ingenua. SC-003 mide **salidas examinadas**, no tiempo: el PASA/FALLA se
  decide con los cocientes de salidas examinadas 200/100 y 400/200 contra
  ≤ 2,5 (verificación) y ≥ 3,5 (ingenua). El tiempo se reporta como
  información (y el de la referencia, contra 200 ms, para FR-032). Además se
  compara que el texto del reporte sea idéntico (FR-035). Las salidas
  examinadas son un contador determinista, así que el cociente no depende del
  equipo ni del ruido de la medición.
- La alternativa ingenua vive en `controlador/bench/alternativasResolubilidad.py`
  y repite la fase 1 desde cero por cada llave obtenida. Reutiliza la fase 2 y
  el formateador, así que solo difiere en cómo obtiene el orden.

---

## R12. Paquetes sin conexión

**Decisión**:
- `guardar_respuestas.py` agrega `criptas/<id>/llaves.json` para cada cripta.
- **Regenerar `datos_offline/`** con las versiones de la segunda parte es una
  tarea explícita. Requiere red y que el servicio publique `/llaves`, así que
  la corre el equipo, no el agente. Hasta entonces, jugar sin conexión exige
  `--forzar`, la referencia del bench dice SIN DATOS y H5.E1 salta.
- Un paquete nuevo `pruebas/datos/resolubilidad/` trae criptas sintéticas con
  `llaves.json` para los escenarios de aceptación.

**Paquetes y pruebas existentes** (revisados en el código):

| Paquete o prueba | Inicia por | Llaves | Qué se hace |
|---|---|---|---|
| `pruebas/datos/terreno_cazador` (terreno-a, terreno-caras-distintas, terreno-sin-rango) en `prueba_datos_costo` | menú "jugar" | no tiene | **No** se le agrega `llaves.json`. Ninguna de sus criptas es resoluble con FR-001: terreno-a tiene la única puerta de llave_salida hacia la sala 5 y la salida es la 7, y las otras dos no tienen puertas cerradas. Agregar llaves no las vuelve resolubles, y cambiar el esqueleto alteraría las pruebas de la 001. `prueba_datos_costo` arma el menú con `forzar=True` y manda `aceptar_resolubilidad` después de cada "jugar"; el error de caras distintas aparece entonces al iniciar la partida forzada |
| `pruebas/datos/terreno_cazador` en `prueba_persistencia_cazador` | `servicio_terreno()` + partida directa y `--replay` | no tiene | Sin cambios: no pasa por la verificación (FR-021) |
| paquete temporal de `prueba_controlador` | menú "jugar" | no tiene | Se agrega `llaves.json` al paquete que la prueba escribe, con la llave en una sala alcanzable. Su puerta cerrada hacia la sala de salida la vuelve resoluble, así que la prueba sigue el camino normal sin `--forzar`. Se comprueba al implementar; si no resultara resoluble, se usa `forzar=True` como en `prueba_datos_costo` |
| paquete temporal de `prueba_replay_menu` | menú "jugar" | no tiene | Igual que `prueba_controlador` |
| `prueba_vista_*` | solo arman comandos | — | Sin cambios |
| `datos_offline/` | juego real, bench, `generar_guardado_formato_anterior.py` | no tiene (Parte I) | Regenerar (tarea del equipo); el bench de la 001 y el generador no verifican |

---

## R13. Prueba de oráculo

**Decisión**: `prueba_resolubilidad_oraculo` compara la verificación con un
**oráculo** independiente en unas 200 criptas pequeñas (de 3 a 12 salas, de 0
a 5 llaves) generadas con `random.Random(semilla)` y semillas fijas. Las
criptas incluyen puertas de una sola cara, puertas sin llave, llaves
repetidas y suelta por enemigos, y llaves inexistentes.

El oráculo vive en `pruebas/oraculo_resolubilidad.py`, que puede usar
estructuras de Python porque está fuera de `cripta/`:
- **orden**: en cada paso, recorre desde cero con las llaves ya ordenadas y
  elige la disponible de menor id (la definición literal de FR-007 y FR-009);
- **veredicto y motivo**: la definición literal de FR-001 y FR-011;
- **dependencias**: una búsqueda por cada puerta bloqueada (FR-014, sin
  optimizar);
- **grupos**: clausura transitiva de la relación;
- **ciclos**: la regla de FR-015 aplicada sobre esa relación.

Se compara el **resultado estructurado** (veredicto, motivo, orden, no
obtenibles, frontera y ciclos, convertidos a tuplas de Python), no el texto.
Así el oráculo no depende del formateador del programa ni de sus clases, y
una diferencia del formateador no se esconde detrás de un formateador
compartido. El texto exacto lo cubre `prueba_resolubilidad_reporte`
(contracts/reporte.md). Una discrepancia imprime la semilla, la cripta y el
primer campo distinto para reproducirla. (Ajuste tras /speckit-analyze, U1.)

**Justificación**: la fase 2 (Tarjan y relleno por prioridad, R4) es la parte
más fácil de equivocar. La alternativa ingenua del bench reutiliza la fase 2,
así que no la comprueba. El oráculo sí, porque implementa las definiciones de
la spec directamente. Es el mismo patrón que `oraculo_rutas.py` en la 001.
