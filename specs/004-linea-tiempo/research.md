# Research: Línea de tiempo (004)

Mediciones previas con scripts fuera del proyecto (Python 3.14.5, Windows 11),
sobre la cripta de referencia (la de más salas de `datos_offline/`, 300 salas),
partida con semilla 123, jugador sin daño letal (truco solo de medición para
llegar a 5000 acciones), 70 % movimientos y 30 % esperas al azar con
`random.Random(7)`. Las cifras definitivas salen de `benchLineaTiempo` (R10).

| Medición previa | Valor |
|---|---|
| Una acción del jugador con sus eventos (12 enemigos activos) | mediana 1,17 ms; p99 2,12 ms |
| Punto de control (estado completo escrito por `PartidaBinaria`) | 57 KB; tomarlo 2,4 ms |
| Restaurar un punto de control | 12,9 a 13,6 ms |
| Restaurar + re-simular K acciones | K=10: 12,3 ms · K=25: 24,0 ms · K=50: 42,5 ms · K=100: 88,1 ms |
| Deshacer K acciones con el Diario (en la partida real) | K=10: 0,31 ms · K=25: 0,81 ms · K=50: 2,60 ms (unos 70 cambios por acción) |
| Re-simular la partida entera (sin puntos de control) | unas 5000 × 1,2 ms ≈ 6 s |

## R1. Qué es un punto de control

**Decisión**: los bytes que produce el mismo escritor de `PartidaBinaria`, en
memoria. Se separa `guardar(partida, ruta)` en `a_bytes(partida) -> bytes` y la
escritura del archivo, y `cargar(ruta, servicio)` en la lectura del archivo y
`desde_bytes(datos, servicio) -> Partida`. El punto de control incluye todo lo
que ya guarda el formato: salas, actores, efectos, la agenda con sus
secuencias, el estado de `random.Random` y el conocimiento del jugador de la
feature 002.

**Por qué**: es la única forma de copiar el estado completo que ya existe y
está probada (prueba_6_3, prueba_persistencia_niebla); cubre el azar sin
código nuevo (§3.6: "si re-simulan, el punto de control debe incluir el estado
del generador"). Tomarlo cuesta 2,4 ms y ocupa 57 KB con 300 salas.

**Alternativas**: (a) `copy.deepcopy` o `pickle`: prohibidos por el equipo como
sustituto de la estructura y copian también referencias que no son estado
(servicio, vista). (b) Un formato propio más compacto (solo lo que cambia): es
el camino de R2 (b) y (c), con el problema de las referencias.

## R2. Reconstruir un instante: adelante, cambios registrados o atrás

**Decisión**: (a) **re-simular hacia adelante** sobre una copia: restaurar el
punto de control más cercano anterior al instante y volver a aplicar, con el
mismo código de `Partida`, las acciones de la historia que quedó, deteniéndose
en el instante pedido (R3). La copia usa un servicio de solo lectura (R5), no
tiene diario, vista ni registro, y se descarta al terminar.

**Por qué**: reutiliza `Partida.aplicar_accion` y el bucle de eventos tal cual,
así el estado reconstruido es exacto por el principio II (determinismo) y no
hay que mantener una segunda implementación de cada regla. Con K = 25 la
consulta peor cuesta unos 24 ms (13 ms de restaurar + 25 acciones), la mitad
del límite de 50 ms (§6.1). Es la opción con menos código nuevo.

**Alternativas medidas o estimadas**:

- (b) **Aplicar cambios registrados con su instante** (rehacer hacia adelante
  con los valores "nuevo" del Mutador): aplicar es rápido, pero los registros
  apuntan a objetos de la partida real; aplicarlos a una copia exige traducir
  cada registro a los objetos de la copia por claves naturales (como hace
  `PartidaBinaria` con los eventos), para todos los tipos del Mutador. Mucho
  código nuevo y una segunda fuente de verdad de las reglas. Memoria: unos 70
  registros por acción (medido), del orden de 7 KB por acción, contra unos
  2,3 KB por acción de (a) con K = 25.
- (c) **Deshacer hacia atrás desde el estado actual**: invertir es muy barato
  (0,03 ms por acción con el Diario), pero no se puede invertir sobre la
  partida real sin modificarla (FR-011); habría que copiar el estado actual en
  cada consulta (2,4 + 13 ms) y traducir los registros a la copia, con el mismo
  problema de (b), más las excepciones del pergamino (D50) al invertir. Además
  exige guardar todos los cambios de la partida, no solo los 5 del pergamino.
- **Sin puntos de control** (re-simular desde el instante 0): unos 6 s en una
  partida de 5000 acciones; no cumple 50 ms. Se mide en el bench como la
  alternativa pedida (§5.5, §6.3).

## R3. Detenerse en "todos los eventos con tiempo ≤ t"

**Decisión**: cada acción de la historia guarda su **instante de decisión**
(el `tiempo` del turno del jugador que la tomó). Para reconstruir t:

1. Se aplican completas las acciones cuya siguiente decisión es ≤ t: el bucle
   de eventos ya se detiene cuando el turno del jugador es el siguiente, así que
   el estado queda "justo antes de la decisión" (FR-001), y los eventos con el
   mismo tiempo y secuencia menor ya ocurrieron (FR-004).
2. La última acción con decisión ≤ t se aplica con un **límite**: el bucle de
   eventos de la copia se detiene antes del primer evento con tiempo > t. Se
   agrega un parámetro opcional `limite` a `aplicar_accion` y a
   `_procesar_eventos`; sin él, todo sigue igual (la partida real nunca lo usa).
3. Si t es menor que la primera decisión del bloque, se usa el bloque anterior.

**«historia #k»**: estado del punto de control del bloque de k más las
acciones anteriores a k del bloque, completas.

**Alternativas**: reconstruir solo en instantes de decisión (más simple, pero no
cumple FR-001 para t entre dos decisiones); un evento "marca" en la agenda de la
copia en el instante t (cambia secuencias y desempates, contra FR-004).

## R4. Ubicar el bloque de un instante

**Decisión**: la línea es una sucesión de **bloques**; cada bloque tiene un
punto de control y hasta K acciones. Los bloques se guardan en un
**arreglo por árbol** propio: árbol binario completo de nodos, con acceso a la
posición i en O(log n) bajando por los bits de i (la misma técnica que el
montículo de nodos de D23), agregar y quitar al final en O(log n).

- «historia #k»: bloque ⌊(k−1)/K⌋, acceso directo O(log n).
- «historia <t>»: búsqueda binaria por el instante de decisión del primer paso
  de cada bloque (crecientes en la historia que quedó): O(log² n) con n
  bloques.

**Por qué**: FR-023 pide un costo que no crezca linealmente con los puntos de
control; con 5000 acciones y K = 25 hay 200 bloques, y la diferencia es de
microsegundos frente a los 13 ms de restaurar, pero en partidas mucho más
largas (o K pequeño) la búsqueda lineal crece sin tope. Se mide contra la
búsqueda lineal en una `ListaEnlazada` con 10² a 10⁵ bloques.

**Alternativas**: búsqueda lineal (O(n), medida); árbol binario de búsqueda por
instante (los bloques llegan ordenados, así que sin balanceo se degenera en
lista); tupla que se copia al agregar (acceso O(1) pero agregar O(n) y es usar
la tupla como lista, contra el espíritu del principio I).

## R5. La copia no toca la red ni el presupuesto

**Decisión**: la copia usa un `ServicioSoloLectura` que implementa lo que
`Partida` le pide al servicio:

- `asegurar_contenido(id)`: devuelve el contenido inicial de la sala que la
  **línea de tiempo registró** cuando la partida real lo cargó por primera vez
  (registro "contenidos iniciales", persistido con la línea, R7). Al re-simular
  solo se entra a salas en las que la partida real ya entró, así que el
  contenido siempre está.
- `precargar(id)`: no hace nada.
- Fichas del catálogo: memoria y disco (`CacheFichas` y `AlmacenLocalDisco`,
  D33) con un método nuevo `resolver_fichas_sin_red`; si una ficha no está, la
  consulta falla con un mensaje claro y **nunca** usa la red (FR-012).

**Por qué**: después de cargar una partida en otro proceso, el servicio real no
tiene en memoria el contenido de salas visitadas antes del guardado;
re-simular desde un punto de control viejo pediría ese contenido a la red. El
registro de contenidos iniciales lo evita y ocupa poco (un DTO por sala
visitada).

**Alternativa**: guardar en cada punto de control el contenido de todas las
salas (ya está en los bytes para las salas cargadas, pero no para las que se
cargan después del punto de control y antes del instante pedido).

## R6. El pergamino en la línea de tiempo

**Decisión**:

1. **Recorte**: el pergamino revierte la última acción del jugador (primera
   parte). La línea quita esa acción del último bloque (O(1)); si el bloque
   queda sin su acción inicial (su punto de control era el estado antes de una
   acción que ya no existe), se quita el bloque entero (O(log n)). Cuesta en
   proporción a lo revertido, sin recorrer la historia (FR-023).
2. **Ajuste del pergamino**: lo que el pergamino cambia fuera de la reversión
   (el pergamino gastado y los pergaminos que la regla D50 deja donde el jugador
   los movió) se registra como una **entrada de ajuste** en la historia, en el
   instante al que volvió el reloj: la secuencia de objetos del inventario (id
   de objeto, id de ficha, equipado) y los pergaminos que quedaron en el suelo
   de cada sala. Al re-simular, al llegar al ajuste, la copia mueve o crea esos
   objetos para que su inventario y sus pergaminos en el suelo coincidan. Así se
   cumplen FR-008 y la aclaración del pergamino recogido en un tramo revertido.

**Por qué**: re-simular solo las acciones que quedaron no reproduce esos
cambios, porque no son acciones (el pergamino no cuenta como acción). Tomar un
punto de control en el momento del pergamino sería más simple, pero podría
dejar dos puntos de control a menos de K acciones (contra §3.6).

**Hallazgo para la spec**: SC-002 y las pruebas independientes de US1 y US3
toman como referencia "reproducir desde el principio solo las acciones que
siguen existiendo". Esa referencia **no** reproduce los ajustes del pergamino,
así que con FR-008 daría inventarios distintos de los correctos. La referencia
correcta es el estado que la partida real tuvo en ese instante de la historia
que quedó (por ejemplo, el resumen capturado en vivo en cada decisión, quitando
los de las acciones revertidas), o reproducir las acciones que quedan
aplicando los ajustes del pergamino. **Se corrige primero la spec, en su propio
commit, antes de `/speckit-tasks`** (principio VII).

## R7. Persistencia: formato 4

**Decisión**: `FORMATO_VERSION = 4`. Después de lo que escribe el formato 3 se
agrega la sección de la línea: K; los contenidos iniciales registrados (sala y
su DTO de contenido); y los bloques, cada uno con su punto de control (longitud
y bytes), el número de su primera acción y sus entradas (acción como
`Accion.texto()` con su instante de decisión, o ajuste del pergamino). Las
acciones se leen con el mismo intérprete de texto que `RegistroArchivo`. Un
archivo de la versión 3 o anterior se reporta incompatible (FR-010), igual que
decidió la 002.

**Límite**: el archivo crece con los puntos de control: con 5000 acciones y
K = 25, unos 200 × 57 KB ≈ 11 MB. Se mide el tiempo de guardar y cargar.

**Alternativa**: no guardar los puntos de control y reconstruirlos al cargar
re-simulando desde el inicio (archivo chico, pero cargar tardaría segundos).

## R8. Sin interacción: `--replay … --hasta t` y `--checkpoint-cada K`

**Decisión**: `ModoReplay` ya reproduce el log con la misma `Partida`; se le
conecta la misma línea de tiempo que en la partida en vivo (las acciones y los
pergaminos del log la alimentan igual). Al terminar el log se consulta t; si t
es mayor que el reloj final, se imprime el estado final con el aviso de que la
partida terminó antes (FR-013). Así el resultado es por construcción el mismo
que «historia <t>» al final de la partida (FR-014). El resumen se arma una
sola vez (`ResumenInstante`, DTO inmutable) y se usa igual en la ventana y en
el texto. `main.py` acepta `--hasta t` (solo con `--replay`) y
`--checkpoint-cada K` (entero ≥ 1), validados antes de empezar (FR-015,
FR-022).

## R9. Ventana: tecla H

**Decisión**: en `PantallaJuego`, H abre un modo de entrada de texto (como el
nombre del jugador en el menú, D57): dígitos, `#`, retroceso; Enter manda
`Comando("historia", (texto,))`; ESC cierra. Si hay un viaje en curso
(`EstadoVista.viaje`), H primero encola `interrumpir` (FR-017, aclaración). El
Controlador interpreta el texto (t o #k), valida (FR-003), consulta la línea y
manda el `ResumenInstante` en el `EstadoVista`; el HUD lo muestra como panel
sobre el mapa, con `partirLineas` y desplazamiento, igual que el mapa conocido.
`historia` es un verbo de sesión: no consume tiempo ni va al log.

## R10. Mediciones para `--bench` (`benchLineaTiempo`) y §5.6

1. Memoria (bytes de la línea, con `tracemalloc`) y tiempo de consulta (peor y
   mediana, en instantes repartidos) con K = 10, 25 y 50, y la alternativa sin
   puntos de control, en una partida determinista de 5000 acciones sobre la
   cripta de referencia (jugador sin daño letal, sorteos con semilla).
2. Adelante contra atrás: costo de tomar y restaurar una copia y de deshacer K
   acciones con el Diario (estimación de (c)), junto a (a) medido.
3. Ubicar el bloque: arreglo por árbol contra búsqueda lineal con 10² a 10⁵
   bloques.
4. Recorte con el pergamino según el largo de la historia (debe ser constante).
5. §5.6: se repite `benchHistorial` con la carga nueva (cazadores, viajes y la
   línea conectada) y se compara con las cifras de la primera parte.

**K por defecto**: 25, porque la consulta peor queda alrededor de 24 ms (margen
de 2× sobre 50 ms) con una memoria de unos 2,3 KB por acción; K = 50 queda a
42,5 ms (sin margen ante la variación de la máquina) y K = 10 duplica la
memoria sin ganar mucho tiempo, porque restaurar (13 ms) domina. La decisión
final se confirma con el bench.
