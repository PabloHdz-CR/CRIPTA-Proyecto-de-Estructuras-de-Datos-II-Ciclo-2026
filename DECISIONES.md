Diego

D1. Espera de red: puerto síncrono y FuenteAsincrona con hilo y cola propia

(Alimenta la sección de §4.2 y el rubro de cliente y presupuesto.)

Problema: al entrar a una sala su contenido debe estar en memoria. Cada solicitud tarda unos 400 ms, así que pedirlo justo al moverse congelaría el juego en cada puerta. Además, la latencia real no puede cambiar la partida ni mover el reloj virtual.
Alternativas:
(a) Todo síncrono y bajo demanda: se descarta porque cada puerta costaría 400 ms.
(b) Hilos dentro de cada adaptador: se descarta porque duplica la concurrencia en HTTP y offline.
(c) Tickets en el puerto: se descarta porque mezcla el contrato de datos con la concurrencia.
Decisión: el puerto FuenteDatos es síncrono. Un decorador FuenteAsincrona recibe solicitudes en una Cola FIFO propia y las atiende con un único hilo. Las respuestas se incorporan en el orden de solicitud.
Complejidad: encolar y desencolar son O(1). Esperar un resultado bloquea solo el hilo del juego. Un único hilo serializa las solicitudes, lo que además respeta el límite de frecuencia (429).
Evidencia por medir:
Tiempo hasta tener disponible el contenido, con y sin precarga, simulando 400 ms de latencia.
Cantidad de esperas bloqueantes por partida.
Medir directamente la alternativa (a).
Límites: si el servidor permitiera solicitudes en paralelo, un solo hilo desperdiciaría esa capacidad. Una precarga demasiado agresiva gasta presupuesto.
D2. Contador de solicitudes inyectado en ClienteHttp

(Alimenta el rubro de cliente y presupuesto de red.)

Problema: toda solicitud cuenta contra presupuesto_solicitudes, incluidos los reintentos por HTTP 429, y el programa no debe excederlo. Al final hay que reportar cuántas hizo.
Alternativas:
(a) Decorador sobre el puerto: no ve los reintentos, que ocurren dentro del cliente.
(b) Contar en ServicioDatos: haría que el modelo dependa de detalles de HTTP y tampoco vería los reintentos.
Decisión: un objeto ContadorSolicitudes se inyecta en ClienteHttp, que lo incrementa antes de cada intento real. El presupuesto se fija al conocer los datos generales de la cripta. Si el siguiente intento lo superaría, se lanza PresupuestoAgotado antes de enviar.
Complejidad: O(1) por solicitud.
Evidencia por medir: prueba con un servidor simulado que responde 429 varias veces, verificando que las solicitudes reportadas coinciden con los intentos reales. Reporte final en criptas de distintos tamaños.
Límites: si varios hilos usaran el mismo cliente, el contador necesitaría un Lock.
D3. Colecciones de los DTO con ListaEnlazada propia
Problema: representar las colecciones que devuelve el puerto (salidas, enemigos, objetos, trampas, ids) sin usar estructuras no permitidas.
Alternativas: list de Python (contigua, permitida por §7 como almacenamiento de bajo nivel), ListaEnlazada propia, o dict (prohibido como índice).
Decisión: ListaEnlazada propia, cargada con agregar_todos desde el JSON.
Complejidad: construir y recorrer son O(n). El acceso por índice es O(n), pero no se usa: los DTO solo se recorren. Las colecciones son pequeñas (decenas de elementos).
Evidencia por medir: construir y recorrer colecciones de 1 a 50 elementos con ListaEnlazada frente a list, y el costo de traducir un lote de 10 salas.
Límites: con miles de elementos y acceso por índice, list sería mejor. Aquí es válido concluir que la alternativa sencilla habría bastado, siempre que las mediciones lo respalden.
D4. Cola sobre ListaEnlazada con referencia a la cola
Problema: la cola de solicitudes pendientes recibe y entrega elementos constantemente, y ninguna de las dos operaciones debería recorrer la cola.
Alternativas: list con pop(0) (desplaza todos los elementos, O(n)), lista enlazada sin referencia a la cola (encolar sería O(n)), o dos pilas.
Decisión: Cola construida sobre ListaEnlazada, que guarda cabeza y cola.
Complejidad: encolar, desencolar y ver el frente son O(1).
Evidencia por medir: encolar y desencolar de 10³ a 10⁵ elementos contra list.pop(0). La alternativa descartada se mide directamente.
Límites: con colas de pocas decenas de elementos, pop(0) sería igual de rápido. La ventaja aparece cuando la cola crece. No es segura entre hilos por sí sola.

D5. Fichas: base más una subclase por clase del catálogo

(§4.3, resolución de referencias del catálogo.)

Problema: el catálogo devuelve fichas de 9 clases con campos distintos, y el programa debe leerlas sin confundir qué campo corresponde a cuál.
Alternativas: (a) una sola clase con todos los campos opcionales, descartada porque nada impediría leer un campo que no corresponde a la clase; (b) tres DTO (enemigo, objeto, trampa), descartada porque los objetos seguirían mezclando campos de siete clases.
Decisión: clase base FichaDTO, una clase intermedia FichaObjetoDTO con peso y valor (comunes a 7 clases) y una subclase por clase. La conversión usa if/elif, no un diccionario de funciones, porque §7 prohíbe dict como tabla de búsqueda.
Complejidad: convertir una ficha es O(1) (a lo sumo 9 comparaciones de texto). Convertir un lote de k fichas es O(k), con k ≤ 10.
Evidencia por medir: tiempo de convertir lotes de 1 a 10 fichas con la jerarquía frente a la clase única, y memoria por ficha.
Límites: cada clase nueva del catálogo exige tocar el convertidor. Con decenas de clases, el if/elif dejaría de ser adecuado.
D6. DTO inmutables con @dataclass(frozen=True)
Problema: una ficha se comparte entre todos los actores del mismo tipo, y modificarla por error alteraría toda la partida y la reproducción del replay.
Alternativas: atributos públicos mutables (descartada: cualquier módulo podría alterar una ficha compartida); atributos privados con @property (descartada: unas 200 líneas repetidas para ~70 campos).
Decisión: clases inmutables con @dataclass(frozen=True).
Complejidad: crear un objeto es O(1) por campo. Leer un campo es O(1).
Evidencia por medir: prueba que demuestra que asignar lanza FrozenInstanceError, y costo de crear DTO inmutables frente a clases normales al convertir un lote de 10 salas.
Límites: la inmutabilidad es superficial: las ListaEnlazada dentro de un DTO siguen siendo modificables por quien tenga la referencia. Se evita por convención de solo leerlas.
D7. Convertidor compartido por los dos adaptadores
Problema: ClienteHttp y FuenteOffline reciben el mismo JSON y deben entregar objetos idénticos (§3.4: el modelo no debe notar de dónde vienen los datos).
Alternativas: un método desde_json dentro de cada DTO (el modelo conocería el formato del JSON); duplicar la conversión en cada adaptador (dos copias que pueden divergir).
Decisión: módulo único convertidor_json.py, usado por ambos.
Complejidad: O(n) en el tamaño de la respuesta.
Evidencia por medir: prueba con las mismas respuestas convertidas por cada adaptador que verifica que los campos coinciden, y tiempo de convertir respuestas de 1 a 50 salas.
Límites: si HTTP y el paquete offline usaran formatos distintos de JSON, haría falta un convertidor por formato.
D8. Orden fijo de salidas N, S, E, O
Problema: el enemigo errante elige al azar una salida abierta. Si el orden de las salidas cambia entre ejecuciones, con la misma semilla elegiría otra y la partida no sería reproducible.
Alternativas: conservar el orden del JSON (depende del servidor); ordenar por id de la sala destino (depende de la cripta).
Decisión: el convertidor entrega las salidas siempre en el orden N, S, E, O.
Complejidad: O(4) por sala, constante.
Evidencia por medir: prueba que ejecuta la misma partida con las llaves del JSON en órdenes distintos y verifica que el resultado no cambia.
Límites: si el juego añadiera más direcciones, habría que ampliar DIRECCIONES.
Avisos para tu compañero
Las salidas de una Sala llegan siempre en el orden N, S, E, O, y conviene que el modelo conserve ese orden.
comportamiento llega tal cual del servidor, con tilde en "guardián". Que lo compare con una constante.
El campo daño de la trampa se llama dano en el DTO.
Las fichas son inmutables: si el modelo necesita estado propio (vida actual, por ejemplo), va en la instancia del actor, no en la ficha.

D9. Un único puerto abstracto FuenteDatos para red y offline

(§6, Adaptadores, y el rubro de cliente y presupuesto.)

Problema: el modelo debe funcionar igual con datos de HTTP o de archivos, y --offline debe cambiar la fuente sin propagar if por todo el modelo (§6).
Alternativas:
(a) Una bandera offline consultada dentro del modelo: se descarta porque el modelo conocería la infraestructura.
(b) typing.Protocol: descartada porque una clase que olvide un método solo falla al usarlo, mientras que con ABC falla al crearla.
Decisión: interfaz FuenteDatos con abc.ABC y @abstractmethod, definida en el paquete de puertos del modelo. Los adaptadores la implementan.
Complejidad: despachar por herencia es O(1). No hay if en el camino.
Evidencia por medir: ejecutar la misma secuencia de consultas con ClienteHttp (contra un servidor simulado) y con FuenteOffline sobre el mismo contenido, y comprobar que los DTO son iguales campo por campo. Buscar en el código del modelo cualquier import de requests, open u offline: debe haber cero.
Límites: un contrato con 9 métodos es grande. Si crece más, convendría separarlo en dos interfaces (cripta y catálogo).
D10. El consumo del presupuesto se lee desde el propio puerto
Problema: ServicioDatos necesita saber cuántas solicitudes van y cuál es el presupuesto para planificar la precarga, y el reporte final debe mostrarlos (§5.1). Pero los reintentos por 429 solo son visibles dentro del cliente.
Alternativas: una interfaz separada MedidorRed (más limpia, pero otra pieza que conectar al armar la aplicación); que ServicioDatos lleve su propia cuenta (descartada: no ve los reintentos y subestimaría el gasto).
Decisión: dos métodos de solo lectura, solicitudes_realizadas() y presupuesto(). El presupuesto es None hasta conocerlo, y FuenteOffline responde 0 y None.
Complejidad: O(1).
Evidencia por medir: prueba con un servidor simulado que responde 429 varias veces, comprobando que solicitudes_realizadas() coincide con los intentos reales que llegaron al servidor.
Límites: si hubiera más de una fuente de red activa, un solo contador ya no bastaría.
D11. Los adaptadores rechazan lotes fuera de rango
Problema: el servicio acepta hasta 10 salas o fichas por solicitud y cuesta lo mismo con 1 que con 10. Quién parte un lote grande decide cuánto presupuesto se gasta.
Alternativas: que el adaptador parta automáticamente el lote en varias solicitudes (cómodo, pero gasta presupuesto sin que nadie lo decida); enviar tal cual y dejar que el servidor rechace (gasta una solicitud en un error).
Decisión: validar_lote lanza LoteInvalido antes de enviar nada. La política de armar lotes es de ServicioDatos.
Complejidad: O(1) por validación, porque len() de ListaEnlazada no recorre.
Evidencia por medir: con una cripta sintética de N salas, comparar las solicitudes gastadas con lotes armados por ServicioDatos frente a un adaptador que parte automáticamente. Esto mide directamente la alternativa descartada.
Límites: si el servicio cambiara el tamaño máximo de lote, LIMITE_LOTE habría que actualizarlo.

D12. Contador protegido con Lock

(Rubro de cliente y presupuesto de red.)

Problema: el hilo de FuenteAsincrona escribe el contador mientras el hilo del juego lo lee y hace consultas directas. Sumar sobre un entero compartido no es una operación indivisible: dos hilos podrían leer el mismo valor y ambos gastar la última solicitud.
Alternativas: dejarlo sin protección y documentar que solo un hilo lo usa (más simple, pero cualquier cambio futuro de uso introduciría un error casi irreproducible); un contador por hilo sumados al final (no permite bloquear antes de superar el límite).
Decisión: un threading.Lock que cubre la comprobación del margen y la suma como un solo paso.
Complejidad: O(1) por operación. Se añade el costo constante de tomar y soltar el cerrojo.
Evidencia por medir: prueba de 8 hilos × 50 intentos con presupuesto 100, exigiendo exactamente 100 registrados y 300 bloqueados. En --bench, tiempo de registrar_intento con y sin Lock sobre 10⁶ llamadas, midiendo directamente la alternativa descartada.
Límites: el Lock no es reentrante, así que no se puede llamar a un método bloqueado desde otro. Si hubiera cientos de hilos compitiendo, el cerrojo sería un cuello de botella, pero aquí hay dos.
D13. Bloqueo previo al agotarse el presupuesto
Problema: presupuesto_solicitudes es un máximo, y superarlo invalida el rubro de red. Los reintentos por 429 también gastan.
Alternativas: solo advertir y seguir enviando (contradice el "máximo"); comprobar después de enviar (ya se gastó la solicitud cuando se descubre el exceso).
Decisión: registrar_intento lanza PresupuestoAgotado antes de enviar y sin sumar. La reserva de margen para casos críticos queda en ServicioDatos, usando restantes().
Complejidad: O(1).
Evidencia por medir: partida completa contra un servidor simulado con presupuestos ajustados (incluido uno menor al mínimo necesario), verificando que el conteo del servidor nunca supera el presupuesto y que el reporte final coincide con las solicitudes que realmente llegaron.
Límites: si el presupuesto se agota, ciertas salas no podrán cargarse y el juego quedará limitado a lo ya descargado. Por eso la precarga debe planificarse con restantes().
D14. Reinicio del conteo por partida
Problema: el presupuesto pertenece a "esa partida", y la lista de criptas también cuenta. Un programa puede jugar varias partidas seguidas.
Alternativas: acumular por ejecución sin reiniciar (una segunda partida podría empezar con gasto previo o bloqueada); reiniciar automáticamente al pedir los datos generales (dejaría fuera del conteo la lista de criptas, que sí cuenta).
Decisión: método reiniciar() que el controlador invoca al volver al menú, expuesto a través del puerto como reiniciar_conteo().
Complejidad: O(1).
Evidencia por medir: dos partidas seguidas en una ejecución con criptas de presupuestos distintos, comprobando que cada una reporta solo lo suyo.
Límites: depende de que el controlador llame a reiniciar al iniciar cada partida. Si se olvida, el conteo se acumula.
Avisos
Para tu compañero (controlador): al volver al menú antes de una nueva partida hay que llamar a servicio_datos.reiniciar_sesion(). Esa función la escribo yo en el Paso 5, y por dentro llama a reiniciar_conteo() del puerto. Por ahora anótalo como pendiente.
Para mí, en la 1.6: ClienteHttp llamará a registrar_intento en cada intento, y a establecer_presupuesto cuando reciba los datos generales.

D15. requests.Session con una solicitud en vuelo

(Rubro de cliente y presupuesto de red.)

Problema: cada solicitud tarda unos 400 ms y el servicio limita la frecuencia. Abrir una conexión segura nueva en cada una suma tiempo, y una Session de requests no está garantizada como segura entre hilos.
Alternativas: requests.get sin sesión (conexión nueva cada vez); varias solicitudes en paralelo (más rápido, pero aumenta el riesgo de 429, y cada uno gasta presupuesto).
Decisión: una única Session con un Lock que permite una sola solicitud a la vez.
Complejidad: O(1) por solicitud; la latencia la domina la red. Con el cerrojo, k solicitudes concurrentes tardan k veces la latencia de una.
Evidencia por medir: tiempo de 20 solicitudes seguidas con Session frente a requests.get (alternativa descartada), y cantidad de 429 con solicitudes en paralelo frente a serializadas.
Límites: si el servidor permitiera paralelismo sin límite, serializar desperdiciaría capacidad. Una consulta directa del hilo del juego espera si el hilo de fondo tiene una solicitud en curso.
D16. Política ante HTTP 429
Problema: un 429 debe manejarse sin que el programa se caiga (§3.1), el reintento cuenta contra el presupuesto, y el tiempo real de espera no puede mover el reloj virtual.
Alternativas: sin tope de reintentos (podría vaciar el presupuesto); 5 reintentos (más gasto); esperar exactamente reintentar_en (arriesga un segundo 429 que costaría otra solicitud); abortar al primer 429.
Decisión: hasta 3 reintentos, espera de reintentar_en más 1 s, 5 s si el servidor no indica el tiempo, y error inmediato si pide esperar más de 60 s.
Complejidad: como máximo 4 solicitudes por consulta, y la espera total está acotada.
Evidencia por medir: servidor simulado que responde 429 k veces, verificando reintentos, esperas y conteo. Contra el servicio real, comparar cuántos 429 secundarios ocurren con margen 0 frente a margen 1.
Límites: si el límite de frecuencia fuera muy estricto, 3 reintentos podrían no bastar. Las esperas dependen del reloj real de la máquina.
D17. Errores con contexto y sin reintento de fallas de conexión
Problema: §3.1 no acepta terminar con una excepción de requests sin contexto, y ante un timeout no sabemos si el servidor llegó a procesar la solicitud.
Alternativas: reintentar automáticamente los timeouts (podría gastar presupuesto en solicitudes que quizá sí llegaron); dejar propagar la excepción original (incumple §3.1).
Decisión: traducir toda falla a ErrorDeRed con operación, causa y código HTTP, y no reintentar timeouts ni fallos de conexión. Quien llama decide, con el presupuesto a la vista.
Complejidad: O(1).
Evidencia por medir: pruebas con servidor simulado para HTTP 500, JSON inválido, timeout y conexión rechazada, verificando que cada mensaje nombra la operación.
Límites: en una red inestable habrá más errores visibles. ServicioDatos puede reintentar sabiendo cuánto presupuesto queda.

D18. Orden de incorporación con recoger_listas()

(§2.4 "Determinismo de red" y §4.2.)

Problema: la latencia real no puede cambiar la partida. Si dos respuestas llegan en distinto orden entre ejecuciones y el modelo las incorpora al llegar, el estado podría variar.
Alternativas: que ServicioDatos guarde sus propias solicitudes y decida el orden (reparte una regla delicada entre dos clases); incorporar en orden de llegada (no determinista).
Decisión: recoger_listas() entrega las solicitudes terminadas en orden de envío y se detiene en la primera que no ha terminado. Cada solicitud se entrega una sola vez. Con el hilo único la terminación ya sigue el orden de envío, y el método vuelve explícita esa garantía y la mantendría si algún día hubiera más de un hilo.
Complejidad: O(m) donde m es la cantidad de solicitudes entregadas. Cada solicitud entra y sale de la cola una vez, así que el costo total es O(1) amortizado por solicitud.
Evidencia por medir: pruebas con demoras aleatorias por solicitud que verifican que el orden entregado es siempre el de envío. Repetir la misma partida simulada con distintas latencias y comparar el estado final.
Límites: el orden es de envío, no de "importancia": una solicitud lenta retrasa la incorporación de las siguientes, aunque ya hayan terminado.
D19. Sin cancelación de solicitudes pendientes
Problema: cancelar una solicitud que aún no empezó ahorra presupuesto, pero que dé tiempo a cancelarla depende de la velocidad de la red.
Alternativas: una bandera de cancelación que el hilo revisa antes de enviar (ahorra presupuesto pero hace el gasto dependiente de la latencia); vaciar la cola al cambiar de zona (mismo problema).
Decisión: toda solicitud enviada se atiende. La disciplina queda en ServicioDatos: solo encolar lo necesario y guardar un margen con restantes().
Complejidad: O(1) por envío y por atención.
Evidencia por medir: con una fuente simulada de latencia variable, ejecutar la misma partida 20 veces y comparar el conteo de solicitudes con y sin cancelación. Sin cancelación debe ser idéntico siempre. La variante con cancelación mide directamente la alternativa descartada.
Límites: se puede gastar una solicitud inútil. Con presupuestos muy ajustados, esa pérdida puede importar y habría que replantear la decisión.
D20. cerrar() termina la solicitud en curso y descarta las pendientes
Problema: al terminar el programa, seguir atendiendo solicitudes gasta presupuesto y hace esperar al usuario, sin beneficio.
Alternativas: completar todas las pendientes antes de cerrar (puede tardar segundos y gastar solicitudes que nadie usará); matar el hilo al instante (dejaría a medio enviar una solicitud y una conexión abierta).
Decisión: se termina la solicitud que ya está en curso, las pendientes se marcan con ErrorDeRed para que nadie se quede esperándolas, y se espera al hilo hasta espera_maxima segundos. Además el hilo es daemon, por lo que no impide cerrar el programa si algo lo detuviera.
Complejidad: O(p) donde p es la cantidad de solicitudes pendientes descartadas, más el tiempo de la solicitud en curso.
Evidencia por medir: prueba con una solicitud en curso y varias pendientes, comprobando que la fuente solo recibe la primera y que las descartadas fallan con un mensaje claro. Tiempo de cierre con 0, 10 y 100 pendientes.
Límites: una solicitud en curso puede tardar mucho si hay 429 con esperas largas. espera_maxima acota lo que se espera al cerrar.
D21. Hilo único, Cola propia protegida con Condition, y copia defensiva del pedido
Problema: el hilo de fondo y el del juego comparten la cola, y queue.Queue de la biblioteca estándar equivale a una estructura que §7 obliga a implementar nosotros.
Alternativas: queue.Queue (prohibida como sustituto); varios hilos (respuestas más rápidas, pero más 429, orden menos claro y contador más disputado); sondeo con sleep en lugar de Condition (desperdicia CPU y añade latencia).
Decisión: un solo hilo que duerme en Condition.wait() y despierta con notify() cuando llega una solicitud. La Cola propia solo se toca dentro del cerrojo. Los ids del pedido se copian al enviarlos, porque la lista que pasa el llamador podría modificarse mientras el hilo la lee. Los errores del hilo se guardan en la Solicitud y se relanzan en quien pide el resultado.
Complejidad: encolar y desencolar son O(1). Copiar el pedido es O(k) con k ≤ 10.
Evidencia por medir: tiempo desde el envío hasta el inicio de la atención con Condition frente a sondeo con sleep (alternativa descartada). Rendimiento de 10³ envíos con la cola propia.
Límites: con un solo hilo, las solicitudes se atienden una tras otra: k solicitudes tardan k veces la latencia. Con un servicio que aceptara paralelismo, esa decisión se revisaría.
Avisos
Para mí, en el Paso 5: ServicioDatos tendrá dos referencias, la FuenteDatos síncrona (lista de criptas, datos generales, versiones, solicitudes_realizadas()) y la FuenteAsincrona (esqueleto, contenido y catálogo). Para incorporar resultados: esperar() sobre la solicitud que hace falta y luego recoger_listas() para procesar todo en orden.
Para la 1.7: FuenteOffline deberá ser segura entre hilos, porque el hilo de fondo y el del juego podrían usarla a la vez. Lo más fácil es que no guarde estado mutable compartido.
Para el arranque: FabricaAplicacion llamará a cerrar() de la FuenteAsincrona y de ClienteHttp al salir.

D22. Pruebas de integración con un servidor simulado y verificación por mutación

(Rubro de cliente y presupuesto de red, y evidencia para D18, D19 y D2.)

Problema: no se puede probar a fondo el 429, el presupuesto agotado ni la latencia contra el servicio real: cuesta presupuesto, es lento y no es reproducible.
Alternativas: probar solo contra el servicio real (gasta solicitudes, depende de internet y del estado del servidor); probar solo cada pieza por separado (no detecta errores en la unión, como un contador que no ve reintentos).
Decisión: un servidor HTTP local que imita el API (con latencia configurable, respuestas en orden inverso y 429 inyectables), una prueba de integración que recorre una partida completa de datos, y una comparación de esa misma partida con latencias distintas.
Complejidad: el conteo esperado se deduce del diseño: menú 2 + esqueleto ⌈salas/salas_por_página⌉ + contenido ⌈salas/10⌉ + catálogo (en cadena, ≥ 2).
Evidencia obtenida: las 12 solicitudes, sus rutas y su orden de recolección fueron idénticos con latencia de 50 ms y de 0 ms. El contador coincidió con las solicitudes que el servidor recibió realmente, incluido el 429. Se introdujeron tres fallas a propósito (reintentos sin contar, recolección desordenada, UUID variable) y las pruebas las detectaron todas.
Límites: el servidor simulado solo es tan fiel como nuestra lectura del contrato. Por eso se complementa con real_1_9.py contra el servicio real.

D23. Montículo con nodos enlazados en lugar de arreglo

(§4.1, agenda de eventos.)

Problema: obtener el próximo evento (menor (tiempo, secuencia)) sin examinar todos, con cientos de eventos y decenas de miles de extracciones. La restricción del equipo es usar solo estructuras propias, sin list de Python.
Alternativas:
(a) Heap sobre list de Python: el más rápido en la práctica, pero el equipo decidió no usarla.
(b) Heap dentro de una ListaEnlazada: acceder a la posición i cuesta O(i), y las operaciones pasarían a O(n log n).
(c) Búsqueda lineal del mínimo o lista ordenada: O(n) por operación.
Decisión: árbol binario completo de nodos enlazados, con punteros a hijo izquierdo, derecho y padre. A la posición p se llega bajando según los bits de p, en O(log n), sin arreglos ni recorridos completos.
Complejidad: insertar y extraer O(log n); mínimo O(1); recorrer O(n).
Evidencia por medir (2.3): ciclos de "extraer y reprogramar" con 100, 300, 1000 y 10 000 eventos, comparando nodos enlazados contra el arreglo (alternativa descartada por decisión, se implementa solo para medir) y contra la búsqueda lineal.
Límites: con nodos hay más memoria por elemento (cuatro referencias) y peor localidad de memoria que un arreglo. Con cientos de eventos no importa; con millones sí, y ahí convendría el arreglo.
D24. Comparación mediante __lt__
Problema: la agenda debe ordenar por (tiempo, secuencia), pero el montículo debe ser reutilizable (números, texto, eventos).
Alternativas: pasar una función de comparación al constructor (más flexible, pero introduce funciones como valores y más partes móviles); guardar pares (prioridad, dato) (duplica objetos y acopla la estructura al uso).
Decisión: el montículo solo usa <; el orden de desempate vive en Evento.__lt__.
Complejidad: cada comparación cuesta O(1) si __lt__ compara dos números. Ojo con comparaciones costosas en otros usos (§4.9).
Evidencia por medir: número de comparaciones por operación, contado con una clase de prueba que las cuenta.
Límites: si dos elementos quedan "empatados" con <, el orden entre ellos no está definido. Para eventos no ocurre gracias a la secuencia única.
D25. Cancelación perezosa
Problema: al morir un actor o cancelarse un efecto sus eventos no deben ejecutarse, y no se puede recorrer toda la agenda para buscarlos (§4.1, §2.10).
Alternativas: montículo indexado con eliminación inmediata (cada nodo guarda su posición y se saca del medio en O(log n); más código, acopla el TDA a Evento y complica el deshacer); reconstruir el montículo sin los cancelados (O(n) por cancelación).
Decisión: montículo simple; la Agenda marca cancelado y descarta los eventos cancelados al llegar a la raíz. Reprogramar es cancelar e insertar uno nuevo; deshacer es quitar la bandera.
Complejidad: cancelar es O(1). Cada evento cancelado cuesta una extracción O(log n) en total, una sola vez.
Evidencia por medir: carga con un porcentaje de eventos cancelados (10 %, 50 %, 90 %) y crecimiento del tamaño del montículo frente a la cantidad de eventos vivos.
Límites: los eventos cancelados ocupan memoria hasta llegar a la raíz. Si se cancelaran masivamente eventos muy lejanos en el tiempo, convendría una limpieza periódica.

D23. Estructura de la agenda: montículo de nodos enlazados
Problema: la agenda debe entregar siempre el evento de menor (tiempo, secuencia) sin examinar todos los pendientes. Hay cientos de eventos simultáneos y esta operación se ejecuta decenas de miles de veces (§4.1). El equipo decidió además usar solo estructuras propias y ninguna lista de Python (D27).
Alternativas:
(a) Vector (montículo sobre arreglo). Es la forma clásica. Se descarta por dos razones. Capacidad: un vector de tamaño fijo puede desbordarse, y como los eventos cancelados ocupan lugar hasta llegar a la raíz, el máximo simultáneo no se puede predecir; la revisión usa una cripta no vista (§9), así que un tope sería una suposición escondida en el código. Política: un vector que crece necesita reservar memoria con una lista de Python, y el equipo decidió no usarla. Esta alternativa no se mide.
(b) Montículo sobre lista enlazada (los mismos pasos, pero accediendo a cada posición). Medida.
(c) Búsqueda lineal sobre una lista enlazada sin orden. Medida.
(d) Lista enlazada ordenada, con inserción lineal. Medida.
Decisión: árbol binario completo de nodos enlazados (NodoArbol, con punteros a hijo izquierdo, hijo derecho y padre), sin arreglos. A la posición p se llega bajando según los bits de p en binario, en O(log n), sin necesitar acceso por índice.
Complejidad: insertar y extraer son O(log n), ver el mínimo es O(1) y recorrer todos es O(n). Las alternativas medidas cuestan O(n) por operación (b, c) o por inserción (d).
Evidencia: tablas 1 y 2 del benchmark de la agenda (anota tu sistema operativo y versión de Python; los números siguientes son de mi entorno y deben sustituirse por los tuyos).
Al pasar de 100 a 10 000 eventos pendientes (100 veces más), el tiempo por ciclo de la decisión apenas se duplica (de unos 4 a unos 8 µs), mientras la búsqueda lineal se multiplica por unas 100 (de unos 12 a unos 1 300 µs).
Con 10 000 eventos, la decisión es unas 140 veces más rápida que el montículo sobre lista, unas 160 veces más que la búsqueda lineal y unas 38 veces más que la lista ordenada. Es la más rápida de las alternativas medidas en todos los tamaños.
El montículo sobre lista hace exactamente las mismas comparaciones que la decisión (15.7 y 18.4 por ciclo con 300 y 1 000 eventos): es el mismo algoritmo. Todo su retraso viene de que llegar a una posición cuesta O(i), y por eso demuestra por qué una lista enlazada no sirve para guardar un montículo.
Con 10 000 eventos pendientes, un evento cuesta unos 8 µs, así que en los 20 ms de §5.2 caben unos 2 400. Se cumple con mucho margen.
Límites: un vector tendría constantes menores (acceso directo en vez de seguir punteros), pero eso es una expectativa, no una medición del programa. La decisión se sostiene por la política de no usar listas y por escalar de forma logarítmica sin capacidad máxima. Cada elemento ocupa más memoria (cuatro referencias por nodo). Con cientos de eventos no importa; con millones, sí. Los resultados dependen de la máquina y de su carga al medir.
D24. Comparación de eventos con < (__lt__)
Problema: el montículo debe ordenar los eventos por (tiempo, secuencia), con un desempate determinista (§2.3), pero debe seguir siendo una estructura reutilizable con números, texto o eventos. Cada operación del montículo hace del orden de log n comparaciones, así que el costo de comparar importa.
Alternativas:
(a) Pasarle al montículo una función de comparación por parámetro. Es más flexible, pero introduce funciones como valores, un concepto que el equipo aún no domina, y reparte la regla de orden entre la estructura y quien la crea.
(b) Guardar pares (prioridad, dato). Duplica información y acopla el montículo a ese formato.
Decisión: el montículo compara solo con el operador < (_antes(a, b) devuelve a < b). La clase Evento define __lt__, que compara (tiempo, secuencia). Como la secuencia es única, nunca hay empates: el orden es total y determinista sin importar el orden de inserción.
Complejidad: cada comparación cuesta O(1) mientras __lt__ compare dos números. Una operación del montículo hace del orden de log n comparaciones.
Evidencia: tabla 2 del benchmark, que cuenta las llamadas a < por ciclo (con 300 y 1 000 eventos: 15.7 y 18.4 en el montículo). Ese conteo no depende de la velocidad de la máquina. La prueba_2_2 (prueba 5) comprueba que 200 eventos con muchos tiempos repetidos salen siempre en el mismo orden aunque se inserten ordenados, al revés o mezclados.
Límites: dos elementos que < no distinga pueden salir en cualquier orden, algo que en los eventos no ocurre por la secuencia única. Si __lt__ se vuelve costoso (§4.9 advierte de comparaciones caras), el conteo de comparaciones domina el tiempo. Y < debe ser un orden estricto y consistente, o el montículo se corrompe.

Un detalle sobre D24: su evidencia mide el costo del algoritmo, pero no mide la alternativa descartada (la función de comparación). Como §8 pide al menos una alternativa medida en el documento, y D23 ya cumple, no es obligatorio. Si quieres que D24 también tenga su tabla, puedo agregar una cuarta tabla al benchmark que compare __lt__ contra una función de comparación.

Tabla 3: la cancelación perezosa cuesta de 15 a 75 veces menos que reconstruir, y su costo casi no depende de cuántos se cancelan.

D26. Método de medición y alternativas dentro del programa
Problema: §5.3 y §8 exigen mediciones propias con --bench que incluyan la alternativa descartada. Medir mal (una sola vez, con el recolector de basura activo, o comparando estructuras que no hacen lo mismo) produce números sin valor.
Alternativas: medir con scripts sueltos fuera del programa (no cumple que --bench las reproduzca); una sola repetición (afectada por el ruido del sistema); promediar todas las repeticiones (el promedio mezcla ruido, y el mínimo se acerca más al costo real).
Decisión: un Medidor que repite cada escenario 5 veces con la misma semilla, desactiva el recolector de basura mientras cronometra y reporta mínimo y promedio. Antes de medir se verifica que todas las agendas sacan los eventos en el mismo orden. Las alternativas viven en bench/, marcadas como "solo para medir".
Complejidad: el modo completo tarda unos 16 s.
Evidencia obtenida: al romper el código a propósito de cinco maneras, las pruebas detectaron las cinco.
Límites: las mediciones dependen de la computadora y de la carga del sistema en ese momento. Se recomienda cerrar otros programas y repetirlas, y anotar siempre el sistema y la versión de Python.

D27. Sin listas de Python: se usa ListaEnlazada, y una prueba lo hace cumplir
Problema: §7 exige implementar las estructuras evaluadas, y la regla debe cumplirse también en el código que solo sirve para medir. Una regla que solo se recuerda de memoria se rompe sin querer.
Alternativas: permitir list como memoria interna de estructuras propias (lo permite §7, pero deja una zona gris); revisar el código a mano antes de entregar (falla con el tiempo y el cansancio); buscar texto con grep (da falsas alarmas y se le escapan casos).
Decisión: ninguna list de Python en cripta/; donde hace falta una lista se usa ListaEnlazada. La prueba prueba_reglas lee el código con ast y falla, con archivo y línea, ante [ ], list(), comprensiones de lista, .append/.pop/.insert/.extend/.remove, lambda, sorted, .sort, heapq, bisect, queue o deque.
Complejidad: el acceso por posición cuesta O(i) en vez de O(1); el diseño evita necesitarlo.
Evidencia obtenida: la primera auditoría encontró listas de Python en 5 archivos, incluida la propia ListaEnlazada; tras corregirlos, la prueba pasa con 26 archivos revisados. El detector tiene una autoprueba de 17 casos, y al introducir fallas a propósito (una lista en el medidor, un [] en el convertidor) las detectó.
Límites: solo revisa cripta/. No prueba que no se use dict como índice, y las tuplas se permiten.

D28. ListaDoble con nodos como posiciones validadas

(§4.5, inventario.)

Problema: el inventario se recorre hacia adelante y hacia atrás desde la posición actual, se suelta el objeto que se está viendo sin que el costo dependa de su posición, y equipar mueve el objeto al frente. Todo sin arreglos.
Alternativas: (a) ListaEnlazada simple: eliminar un nodo exige llegar a su anterior, O(n), y no se puede retroceder. (b) ListaDoble con un cursor interno: interfaz simple, pero la estructura carga con un estado de navegación, admite un solo cursor y es menos reutilizable.
Decisión: ListaDoble cuyos métodos devuelven y reciben NodoDoble como "posición". Cada nodo recuerda su lista y la lista lo valida (ValueError con nodos ajenos o eliminados). El dato del nodo es de solo lectura. mover_al_inicio conserva el mismo nodo, así quien lo guardó no pierde su lugar.
Complejidad: agregar en los extremos, eliminar por nodo, insertar antes o después, mover al inicio y navegar son O(1). obtener(i) es O(mín(i, n − i)). Buscar, vaciar y recorrer son O(n).
Evidencia: tabla 1 y 2 de benchListaDoble. Con ListaDoble, soltar un objeto cuesta lo mismo al inicio, en el medio y al final (0.35, 0.33 y 0.33 µs con 100 000 objetos, peor caso 1.1 veces el mejor), y con la lista simple por índice pasa de 0.19 µs al inicio a 937 µs en el medio y 1 805 µs al final (hasta 5 512 veces más lento). Equipar un objeto del medio: 0.29 µs contra 879 µs. Ambas estructuras dejan el inventario idéntico (verificado antes de medir). Prueba aleatoria de 3 000 operaciones y 6 fallas provocadas detectadas.
Límites: al inicio de la lista, la lista simple es más rápida (unos 0.1 µs); la ListaDoble gana cuando la posición no es la primera. Guardar una posición exige actualizarla si ese objeto se elimina. Cada nodo guarda dos punteros más. No es segura entre hilos. Buscar por valor sigue siendo O(n).

D29. Pila y PilaAcotada como dos clases

(§2.11 y §4.6, historial reversible.)

Problema: revertir los cambios de una acción en orden inverso, y conservar como máximo las últimas 5 acciones descartando la más antigua, sin copiar el estado completo (prohibido).
Alternativas: (a) una sola Pila con capacidad opcional (mezcla dos comportamientos y la versión simple pagaría una lista doble sin necesitarla); (b) PilaAcotada sobre lista simple (descartar el fondo cuesta O(n)); (c) copias completas del estado (prohibido por el enunciado).
Decisión: Pila sobre ListaEnlazada para los cambios de cada acción, y PilaAcotada sobre ListaDoble para las 5 acciones. Apilar en una pila llena devuelve el elemento descartado, y no se admite None.
Complejidad: apilar, desapilar, ver el tope y descartar el fondo son O(1).
Evidencia: tabla de benchHistorial. Con la capacidad real (5) la diferencia es de 1.1 veces, es decir, no hay ventaja práctica. Con capacidad 500 la lista doble es 13 veces más rápida; con 5 000, 120 veces; con 50 000, 1 182 veces. La lista doble mantiene su costo casi constante (de 0.55 a 0.74 µs). Ambas pilas devuelven y descartan exactamente lo mismo (verificado con 2 000 operaciones aleatorias por capacidad).
Límites: con las 5 acciones del juego, la elección de lista doble o simple no afecta el rendimiento; se justifica porque la ListaDoble se necesita de todos modos para el inventario y porque la ventaja crecería si la capacidad aumentara. Devolver el descartado no libera nada por sí solo. None no se admite.

D30. ColaAcotada para la bitácora en pantalla

(§4.8.)

Problema: mostrar solo los últimos 20 mensajes, con memoria constante durante toda la partida y sin desplazar físicamente los otros 19 al agregar uno. BufferCircular no está entre los TDA permitidos.
Alternativas: (a) lista con pop(0) (desplaza todos los elementos y usa la lista de Python, prohibida); (b) buffer circular sobre un arreglo (no permitido); (c) cola sin tope que se recorta al mostrar (la memoria crece con la partida).
Decisión: ColaAcotada sobre Cola: al llenarse, se descarta el más antiguo. La capacidad la define quien la crea.
Complejidad: encolar y desencolar son O(1). Recorrer es O(capacidad).
Evidencia: tablas 1 a 3 de benchBitacora. Mostrar los últimos 20 cuesta unos 5.4 a 5.9 µs con ColaAcotada sin importar cuántos mensajes se hayan generado, mientras que con la cola sin tope crece linealmente (4 489 µs con 100 000 mensajes, 755 veces más). La ColaAcotada nunca pasa de 20 nodos (1.9 KiB); la cola sin tope crece hasta 100 000 nodos (7 813 KiB). Ambas muestran exactamente los mismos mensajes (verificado).
Límites: agregar un mensaje cuesta unas 2.7 veces más que en la cola sin tope (0.61 µs contra 0.23 µs) por el control de capacidad. El 20 lo define quien la crea, y None no se admite.

D31. Caché LRU implementada sobre ListaDoble
Problema: la caché de fichas recibe muchas más lecturas que inserciones (§4.4), tiene capacidad acotada (25 por defecto, configurable con --cache-size), y las fichas en uso no pueden desalojarse.
Alternativas: (a) FIFO (más simple, pero desaloja fichas que siguen consultándose seguido solo porque entraron primero); (b) sin política, limpiar todo al llenarse (pierde el beneficio del caché).
Decisión: LRU sobre ListaDoble: cada acierto mueve la entrada al frente en O(1); el desalojo busca desde el fondo la primera entrada sin referencias activas.
Complejidad: obtener/insertar son O(capacidad) por la búsqueda lineal (ver D32); mover al frente y desalojar son O(1) una vez localizado el nodo.
Evidencia: prueba del ejemplo A-B-C-A-D verificando el orden exacto de desalojo; prueba aleatoria de 3000 operaciones que nunca desaloja algo fijado. Falta (5.7): medir aciertos/fallos con un patrón de acceso realista (algunas fichas mucho más frecuentes que otras) contra FIFO.
Límites: si todas las fichas caben en uso simultáneo, la caché crece sin tope — es una decisión deliberada (preferir correctitud sobre memoria) que se documenta, no un error.

D32. Búsqueda en caché sin dict: O(capacidad), decisión del equipo
Problema: el enunciado (§4.4) señala explícitamente que el costo de "¿está esta ficha en caché?" importa, lo cual normalmente se resuelve con tabla hash O(1).
Alternativas: (a) dict como índice interno de la caché (O(1), pero rompe la política D27 del equipo de no usar estructuras de Python en ningún punto del programa).
Decisión: el equipo mantiene la política sin excepciones: búsqueda lineal en ListaDoble, O(capacidad).
Complejidad: O(capacidad) por búsqueda; con 25 (o incluso cientos) es insignificante frente al costo real del sistema (una solicitud HTTP tarda ~400 ms).
Evidencia: falta (5.7) — medir el tiempo de obtener/contiene con capacidades crecientes (25, 100, 500) para mostrar numéricamente que sigue siendo despreciable frente a la latencia de red.
Límites: si --cache-size se configurara en varios miles, esta decisión dejaría de ser trivial y convendría revisarla; con los valores esperados del proyecto no es un problema.

D33. AlmacenLocalDisco: un archivo JSON por ficha
Problema: persistir fichas entre ejecuciones (§4.4), validando por versión del catálogo, sin que un archivo corrupto haga caer el programa.
Alternativas: (a) un único archivo con todas las fichas (más compacto, pero obliga a leer/escribir todo el archivo por cada ficha nueva); (b) una base de datos embebida (fuera del alcance permitido por el enunciado, que pide persistencia en archivo propio).
Decisión: un archivo JSON por ficha, nombrado por su id (saneado). Reutiliza la jerarquía de clases de dto.py para la conversión, con if/elif en vez de un diccionario de funciones (§7).
Complejidad: guardar/cargar una ficha es O(1) en cantidad de archivos tocados (no depende de cuántas otras fichas haya guardadas).
Evidencia: 9 clases de ficha guardadas y recuperadas con sus campos exactos, incluidos campos None; prueba explícita de versión desactualizada tratada como "no encontrada"; archivo corrupto no detiene el programa; sobrevive a reabrir el almacén.
Límites: muchos archivos pequeños pueden ser más lentos en discos mecánicos por la sobrecarga del sistema de archivos (no medido); se acepta dict/list de Python como excepción documentada, solo para empaquetar hacia json.dump/json.load de la biblioteca estándar — mismo criterio que la excepción ya existente en clienteHttp.py.

D34. Planificación de precarga con BFS determinista
Problema: anticipar qué salas pedir antes de que el jugador las necesite, sin desperdiciar solicitudes, con un orden que no dependa de la latencia de la red (§2.4, §4.2).
Alternativas: (a) pedir solo al entrar a una sala (lo que el enunciado dice explícitamente que hay que evitar); (b) precargar toda la cripta de una vez al inicio (desperdicia presupuesto en salas que tal vez nunca se visiten).
Decisión: BFS desde la sala actual sobre el esqueleto ya descargado, siguiendo solo salidas abiertas en el orden fijo N-S-E-O, acotado a lotes de 10.
Complejidad: O(salas visitadas × búsqueda de vecina) ≈ O(salas² en el peor caso), aceptable a la escala de una cripta.
Evidencia: prueba con una cripta de 30 salas en pasillo, verificando que el lote son exactamente las 10 más cercanas en orden; 4 fallas provocadas detectadas, incluida una que probaba justo el determinismo.
Límites: no tiene en cuenta cuáles salas tienen más probabilidad real de visitarse (por ejemplo, el camino hacia la salida); es puramente geográfico.
D35. ServicioDatos como único punto de acceso a los datos
Problema: el modelo no debe conocer HTTP, archivos ni la diferencia entre --offline y en línea (§6).
Decisión: ServicioDatos recibe por inyección la fuente síncrona, la asíncrona, la caché y el almacén, y es la única clase que los toca. El resto del modelo solo llama a sus métodos públicos.
Evidencia: prueba de integración (prueba_5_5) ejercitando el flujo completo con una fuente falsa, sin que ninguna otra pieza del modelo necesite saber que es falsa.
Límites: la responsabilidad de esta clase es amplia (arranque, contenido, catálogo, presupuesto); si creciera más, convendría partirla.
D36. Catálogo "en cadena" vía resolver_ficha_y_dependientes
Problema: un enemigo puede "soltar" objetos cuyo id de catálogo no se conoce hasta leer la ficha del enemigo (§4.3).
Decisión: resolver_ficha_y_dependientes resuelve primero la ficha pedida y, si es un enemigo con suelta no vacía, encadena una segunda resolución (que a su vez pasa por caché/disco/red con la misma lógica).
Evidencia: prueba con una rata que suelta una poción no pedida explícitamente, verificando que ambas llegan resueltas.
Límites: solo encadena un nivel (lo que suelta un enemigo); si un objeto sólido pudiera a su vez referenciar otro id, haría falta recursión, que el enunciado no exige.
D37. Corrección de la medición de aciertos/fallos: CacheFichas.ver()
Problema: al revisar la implementación, se encontró que resolver_fichas consultaba la caché dos veces por ficha, contando como "acierto" una ficha recién insertada en la misma llamada — inflando artificialmente la estadística que pide §4.4.
Decisión: se separó la consulta real (obtener, que sí afecta estadísticas y orden LRU) de una consulta silenciosa (ver, que no afecta nada), usada solo para leer el valor final de algo que se acaba de resolver.
Evidencia: prueba específica de ver() verificando que no toca aciertos/fallos ni el orden interno; se mantiene como caso de la autoauditoría del equipo (en la línea de lo que ya pasó con el diccionario olvidado en el Paso 4).
Límites: este tipo de error (una métrica contaminada por una consulta interna) es fácil de repetir en otras partes; conviene revisar con el mismo criterio cuando se agregue el reporte final de --bench.

D38. ObjetoInventario: instancia separada de la ficha compartida
Problema: §2.7 exige distinguir instancias del mismo tipo de objeto (dos dagas son dos objetos, aunque compartan ficha).
Decisión: una clase mínima con id_instancia (autoincremental) y una referencia a la FichaDTO inmutable del catálogo.
Evidencia: prueba 11 (dos pergaminos distintos, misma ficha, cantidad_pergaminos() == 2).
Límites: el contador de instancias es por Inventario, no global a la cripta; si se necesitara un id único de instancia en todo el mundo (por ejemplo para el guardado binario del Paso 6), habría que revisar este esquema.
D39. Inventario fija/suelta referencias en CacheFichas automáticamente
Problema: un objeto en el inventario del jugador es, por definición, una ficha "en uso" (D31/D32): si se desaloja de la caché mientras el jugador lo lleva encima, se perdería la referencia.
Alternativas: dejar que quien construya el inventario del jugador llame a fijar/soltar_referencia manualmente (más desacoplado, pero fácil de olvidar).
Decisión: el propio Inventario llama a cache.fijar en recoger y a cache.soltar_referencia en _quitar_nodo (usado por soltar y usar). Como consecuencia, recoger exige que la ficha ya esté en caché, lo cual documenta el orden correcto de llamadas (resolver antes de recoger).
Complejidad: O(capacidad de la caché) por cada fijación/suelta (D32), ya asumido.
Evidencia: pruebas 3, 6, 7, 8 y 10 verifican que esta_en_uso sigue exactamente el ciclo de vida del objeto en el inventario; mutación M1 y M2 confirmaron que, sin esta integración, un objeto quedaría sin protección o con una referencia de equipo colgante.
Límites: acopla Inventario a CacheFichas; si en el futuro el inventario necesitara existir sin caché (por ejemplo, en una prueba aislada), habría que inyectar una caché "de mentira".
D40. Ordenación temporal por inserción, con punto único de reemplazo
Problema: §4.5 exige vistas ordenadas por peso, valor y nombre sin alterar el orden real, pero el Ordenamiento con selector de algoritmos (§4.9) es del Paso 6, que aún no existe.
Decisión: Inventario._ordenar_insercion implementa inserción directamente, documentada como temporal, sobre una copia (nunca la estructura real). Cuando llegue el Paso 6, se sustituye por una llamada al Ordenamiento definitivo sin tocar el resto de Inventario.
Complejidad: O(n²) en el peor caso, pero n está acotado por inventario_max (del orden de decenas), así que el costo real es insignificante.
Evidencia: pruebas con 4 criterios y verificación explícita de que el orden real no cambia tras tres llamadas a vista_ordenada; la mutación M4 (que intentó ordenar la lista real por error) ni siquiera llegó a ejecutarse, porque ListaDoble no tiene los métodos de acceso por índice que usa el ordenamiento — una protección estructural, no solo una prueba.
Límites: esta es una implementación a reemplazar, no la decisión final; el Documento debe dejarlo explícito para no presentarla como si fuera la solución definitiva de §4.9.

D31 (evidencia agregada)
Evidencia: con un patrón de acceso 80/20 sobre 100 fichas y capacidad 25, LRU alcanza 67.0–70.5 % de aciertos contra 59.6–62.3 % de FIFO con la misma secuencia exacta de accesos (verificado antes de medir). El tiempo por acceso es equivalente entre ambas (diferencia menor al 20 %), así que la ventaja de LRU en aciertos no tiene costo adicional relevante en velocidad.
Límites (ampliación): con un patrón de acceso uniforme (sin fichas "populares"), la ventaja de LRU se reduciría o desaparecería — no se midió ese caso, pero es consistente con la teoría de las políticas de reemplazo.

D41. Dos algoritmos sobre listas enlazadas: inserción y mezcla
Problema: ordenar en varios contextos (tabla de puntajes, vistas del inventario, índices del archivo de guardado, listas del catálogo) con al menos dos algoritmos de características distintas, sin sort()/sorted() ni arreglos de Python (§4.9, §7).
Alternativas: inserción + rápida (quicksort). Se descarta: sobre listas enlazadas no hay acceso aleatorio barato para elegir un buen pivote, y su peor caso sigue siendo O(n²) — exactamente lo que se busca evitar con el segundo algoritmo.
Decisión: inserción (construida insertando cada nodo en su lugar dentro de una cadena ya ordenada) y mezcla (técnica clásica de paso lento/paso rápido para dividir, y fusión de dos cadenas ordenadas), ambas trabajando directamente sobre Nodo, ambas estables.
Complejidad: inserción, O(n) mejor caso / O(n²) peor caso. Mezcla, O(n log n) siempre. Ambas usan O(n) de memoria extra (no modifican la lista de entrada).
Evidencia: 60 casos aleatorios contrastados contra sorted(); verificación de estabilidad; con datos casi ordenados localmente, inserción es de 1.7 a 2.8 veces más rápida que mezcla (n=1000 a 20 000); con datos muy desordenados, mezcla llega a ser 335 veces más rápida que inserción en n=20 000 (35.57 ms contra 11 915 ms). Con comparaciones artificialmente costosas, mezcla hace hasta 29 veces menos comparaciones que inserción (n=1000).
Límites: la mezcla usa memoria adicional proporcional a n (no ordena "en el lugar"); con conjuntos muy grandes eso podría importar, aunque los usos previstos (inventario, catálogo, puntajes) son pequeños.
D42. Selector automático: tamaño O casi ordenado → inserción; si no, mezcla
Problema: elegir el algoritmo sin "adivinar", basado en propiedades medibles, y sustentado con evidencia (no basta con el argumento teórico de complejidad, según el criterio explícito de §8).
Alternativas: seleccionar solo por tamaño. Se descarta porque deja fuera justo el caso "datos casi ordenados" que el enunciado pide medir explícitamente: una lista grande pero casi ordenada iría a mezcla cuando inserción sería más rápida ahí.
Decisión: inversiones_adyacentes cuenta en O(n) cuántos pares consecutivos están fuera de orden (no el conteo completo de inversiones, que sería O(n²)); si esa proporción es baja (≤10%) o el tamaño es pequeño (≤32), se usa inserción; si no, mezcla.
Complejidad: decidir qué algoritmo usar cuesta O(n), un costo menor comparado con el propio ordenamiento.
Evidencia: con datos casi ordenados localmente, el selector elige inserción y le gana a "usar siempre mezcla" por 1.8–1.9 veces en los tres tamaños medidos.
Límites: inversiones_adyacentes es una medida local. Con 371 intercambios lejanos entre sí en 5000 elementos (7.4 % de inversiones adyacentes, bajo el umbral del 10 %), el heurístico sigue diciendo "casi ordenada" y el selector elige inserción — pero esta resulta 9.8 veces más lenta que mezcla (61.41 ms contra 6.29 ms); con 20 000 elementos, 35 veces más lenta (994.88 ms contra 28.36 ms). Es un límite real del heurístico barato, no solo una posibilidad teórica: el costo de la inserción depende de cuánto viaja cada elemento desplazado, no solo de cuántos vecinos quedan invertidos.