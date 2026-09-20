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