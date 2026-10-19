# Documento de Decisiones de Diseño: CRIPTA

Cada problema de §4 tiene al menos una sección con Problema, Alternativas,
Decisión, Complejidad, Evidencia y Límites (§8). Las mediciones se reproducen
con `py main.py --bench` (o `--bench --rapido`); los números de este documento
salieron de Windows 11 con Python 3.14 y cambian con la máquina y su carga.

| Problema del enunciado | Secciones | Evidencia con --bench |
|---|---|---|
| §4.1 Qué ocurre a continuación (agenda) | D23, D24, D25, D26 | benchAgenda (tablas 1 a 3, mide las alternativas) |
| §4.2 Traer el contenido antes de que haga falta | D1, D15–D22, D34 | benchPrecarga (mide pedir al entrar), benchDatos; prueba_falso_1_9 |
| §4.3 Resolución de referencias del catálogo | D5, D36 | prueba_5_5 y prueba_falso_1_9 (catálogo en cadena) |
| §4.4 Reutilización y caché persistente | D31, D32, D33, D37, D39 | benchCache (tablas 1 a 3, mide FIFO) |
| §4.5 Inventario | D28, D38, D40, D69 | benchListaDoble (mide la lista simple) |
| §4.6 Pergaminos e historial reversible | D29, D49, D50 | benchHistorial (mide la pila sobre lista simple) |
| §4.7 El rastro del jugador | D67 | benchRastro (mide la lista de visitas) |
| §4.8 Bitácora en pantalla | D30, D69 | benchBitacora (mide la cola sin tope) |
| §4.9 Ordenamiento | D41, D42, D59 | benchOrdenamiento (7 tablas) |
| §4.10 Guardado binario de la partida | D68, D48 | benchGuardado (mide JSON) |
| §4.11 Bitácora de partida y reproducción | D70, D49, D56, D61 | prueba_controlador, prueba_replay_menu |

Otras decisiones: cliente HTTP y presupuesto de red (D2, D9–D14), estructuras
base (D3, D4, D6, D7, D8, D27), Vista y Controlador (D43–D48, D51–D66).

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
Evidencia (--bench, benchPrecarga, que mide directamente la alternativa (a) con el ServicioDatos, la FuenteAsincrona y el PlanificadorPrecarga reales sobre una fuente simulada de 40 ms por solicitud, escala 1:10 de los 400 ms): recorriendo entera una cuadrícula de 20 y de 50 salas, pedir al entrar hace esperar al jugador en CADA sala (20 de 20 y 50 de 50 veces, unos 807 y 2 020 ms de espera en total) y gasta una solicitud por sala. Con la decisión espera 1 o 2 veces (40 a 61 ms en total: la primera sala y, si piensa menos que la latencia, una más) y gasta 3 y 6 solicitudes. Con precarga las solicitudes son las mismas con 40 ms y con 1 ms de latencia, y prueba_falso_1_9 (D22) obtiene las mismas 12 solicitudes, en el mismo orden, con 50 ms y con 0 ms.
Límites: si el servidor permitiera solicitudes en paralelo, un solo hilo desperdiciaría esa capacidad. Una precarga demasiado agresiva gasta presupuesto.
D2. Contador de solicitudes inyectado en ClienteHttp

(Alimenta el rubro de cliente y presupuesto de red.)

Problema: toda solicitud cuenta contra presupuesto_solicitudes, incluidos los reintentos por HTTP 429, y el programa no debe excederlo. Al final hay que reportar cuántas hizo.
Alternativas:
(a) Decorador sobre el puerto: no ve los reintentos, que ocurren dentro del cliente.
(b) Contar en ServicioDatos: haría que el modelo dependa de detalles de HTTP y tampoco vería los reintentos.
Decisión: un objeto ContadorSolicitudes se inyecta en ClienteHttp, que lo incrementa antes de cada intento real. El presupuesto se fija al conocer los datos generales de la cripta. Si el siguiente intento lo superaría, se lanza PresupuestoAgotado antes de enviar.
Complejidad: O(1) por solicitud.
Evidencia: prueba_falso_1_9 (D22): el 429 recuperable gasta exactamente 2 solicitudes (el 429 y el reintento) y el contador coincide con lo que recibió el servidor simulado. El reporte final de cada partida (D51) muestra ese mismo contador.
Límites: si varios hilos usaran el mismo cliente, el contador necesitaría un Lock.
D3. Colecciones de los DTO con ListaEnlazada propia
Problema: representar las colecciones que devuelve el puerto (salidas, enemigos, objetos, trampas, ids) sin usar estructuras no permitidas.
Alternativas: list de Python (contigua, permitida por §7 como almacenamiento de bajo nivel), ListaEnlazada propia, o dict (prohibido como índice).
Decisión: ListaEnlazada propia, cargada con agregar_todos desde el JSON.
Complejidad: construir y recorrer son O(n). El acceso por índice es O(n), pero no se usa: los DTO solo se recorren. Las colecciones son pequeñas (decenas de elementos).
Evidencia: tabla 1 de benchDatos. Traducir una respuesta a DTO (construir y recorrer sus ListaEnlazada) cuesta 3.4 µs con 1 sala, 27 µs con 10, 133 µs con 50 y 531 µs con 200; el contenido de 10 salas, 19 µs. Es como mucho el 0.13 % de una solicitud (400 ms): la estructura de las colecciones no pesa. La alternativa list no se mide porque el equipo la prohibió también en el código de medición (D27); con estos números no podría cambiar la conclusión.
Límites: con miles de elementos y acceso por índice, list sería mejor. Aquí es válido concluir que la alternativa sencilla habría bastado, siempre que las mediciones lo respalden.
D4. Cola sobre ListaEnlazada con referencia a la cola
Problema: la cola de solicitudes pendientes recibe y entrega elementos constantemente, y ninguna de las dos operaciones debería recorrer la cola.
Alternativas: list con pop(0) (desplaza todos los elementos, O(n)), lista enlazada sin referencia a la cola (encolar sería O(n)), o dos pilas.
Decisión: Cola construida sobre ListaEnlazada, que guarda cabeza y cola.
Complejidad: encolar, desencolar y ver el frente son O(1).
Evidencia: tabla 2 de benchDatos, que mide la alternativa de una cola enlazada sin referencia al último nodo. La Cola cuesta unos 0.2 µs por elemento con n = 500, 2000 y 5000 (constante); sin la referencia sube a 2.0, 7.8 y 19.2 µs (10, 39 y 96 veces más), lineal con n como se esperaba. list.pop(0) no se mide por D27.
Límites: con colas de pocas decenas de elementos, pop(0) sería igual de rápido. La ventaja aparece cuando la cola crece. No es segura entre hilos por sí sola.

D5. Fichas: base más una subclase por clase del catálogo

(§4.3, resolución de referencias del catálogo.)

Problema: el catálogo devuelve fichas de 9 clases con campos distintos, y el programa debe leerlas sin confundir qué campo corresponde a cuál.
Alternativas: (a) una sola clase con todos los campos opcionales, descartada porque nada impediría leer un campo que no corresponde a la clase; (b) tres DTO (enemigo, objeto, trampa), descartada porque los objetos seguirían mezclando campos de siete clases.
Decisión: clase base FichaDTO, una clase intermedia FichaObjetoDTO con peso y valor (comunes a 7 clases) y una subclase por clase. La conversión usa if/elif, no un diccionario de funciones, porque §7 prohíbe dict como tabla de búsqueda.
Complejidad: convertir una ficha es O(1) (a lo sumo 9 comparaciones de texto). Convertir un lote de k fichas es O(k), con k ≤ 10.
Evidencia: tabla 1 de benchDatos: traducir 10 fichas de clases mezcladas (enemigo, arma, poción y trampa) cuesta 9.7 µs, menos de 1 µs por ficha. La clase única no se implementó para medirla: la jerarquía se eligió para que cada ficha tenga solo sus campos, y su costo ya es despreciable frente a una solicitud. La memoria por ficha no se midió.
Límites: cada clase nueva del catálogo exige tocar el convertidor. Con decenas de clases, el if/elif dejaría de ser adecuado.
D6. DTO inmutables con @dataclass(frozen=True)
Problema: una ficha se comparte entre todos los actores del mismo tipo, y modificarla por error alteraría toda la partida y la reproducción del replay.
Alternativas: atributos públicos mutables (descartada: cualquier módulo podría alterar una ficha compartida); atributos privados con @property (descartada: unas 200 líneas repetidas para ~70 campos).
Decisión: clases inmutables con @dataclass(frozen=True).
Complejidad: crear un objeto es O(1) por campo. Leer un campo es O(1).
Evidencia: prueba_1_3 comprueba que asignar lanza FrozenInstanceError. Crear los DTO está incluido en la tabla 1 de benchDatos (todas las traducciones crean DTO inmutables): microsegundos por lote. No se comparó con clases normales.
Límites: la inmutabilidad es superficial: las ListaEnlazada dentro de un DTO siguen siendo modificables por quien tenga la referencia. Se evita por convención de solo leerlas.
D7. Convertidor compartido por los dos adaptadores
Problema: ClienteHttp y FuenteOffline reciben el mismo JSON y deben entregar objetos idénticos (§3.4: el modelo no debe notar de dónde vienen los datos).
Alternativas: un método desde_json dentro de cada DTO (el modelo conocería el formato del JSON); duplicar la conversión en cada adaptador (dos copias que pueden divergir).
Decisión: módulo único convertidor_json.py, usado por ambos.
Complejidad: O(n) en el tamaño de la respuesta.
Evidencia: prueba_1_3 (respuestas HTTP) y prueba_1_7 (FuenteOffline) convierten un esqueleto con las salidas desordenadas y obtienen el mismo orden N, S, E y los mismos campos, porque los dos usan el mismo convertidor. Tabla 1 de benchDatos: convertir de 1 a 200 salas cuesta de 3.4 a 531 µs.
Límites: si HTTP y el paquete offline usaran formatos distintos de JSON, haría falta un convertidor por formato.
D8. Orden fijo de salidas N, S, E, O
Problema: el enemigo errante elige al azar una salida abierta. Si el orden de las salidas cambia entre ejecuciones, con la misma semilla elegiría otra y la partida no sería reproducible.
Alternativas: conservar el orden del JSON (depende del servidor); ordenar por id de la sala destino (depende de la cripta).
Decisión: el convertidor entrega las salidas siempre en el orden N, S, E, O.
Complejidad: O(4) por sala, constante.
Evidencia: prueba_1_3 convierte un esqueleto con las salidas en orden E, S, N en el JSON y comprueba que salen en N, S, E. Como el modelo solo ve DTO, el orden del JSON no puede llegar a la partida; el replay fiel de partidas reales (D70) lo confirma de punta a punta.
Límites: si el juego añadiera más direcciones, habría que ampliar DIRECCIONES.

D9. Un único puerto abstracto FuenteDatos para red y offline

(§6, Adaptadores, y el rubro de cliente y presupuesto.)

Problema: el modelo debe funcionar igual con datos de HTTP o de archivos, y --offline debe cambiar la fuente sin propagar if por todo el modelo (§6).
Alternativas:
(a) Una bandera offline consultada dentro del modelo: se descarta porque el modelo conocería la infraestructura.
(b) typing.Protocol: descartada porque una clase que olvide un método solo falla al usarlo, mientras que con ABC falla al crearla.
Decisión: interfaz FuenteDatos con abc.ABC y @abstractmethod, definida en el paquete de puertos del modelo. Los adaptadores la implementan.
Complejidad: despachar por herencia es O(1). No hay if en el camino.
Evidencia: prueba_1_7 comprueba que FuenteOffline rechaza los lotes inválidos igual que ClienteHttp, y las criptas del paquete offline se juegan completas (D53). En cripta/modelo no hay ningún import de requests ni de adaptadores, ni open() (verificado con grep: solo aparecen en comentarios); únicamente FabricaAplicacion conoce las clases concretas (D48).
Límites: un contrato con 9 métodos es grande. Si crece más, convendría separarlo en dos interfaces (cripta y catálogo).
D10. El consumo del presupuesto se lee desde el propio puerto
Problema: ServicioDatos necesita saber cuántas solicitudes van y cuál es el presupuesto para planificar la precarga, y el reporte final debe mostrarlos (§5.1). Pero los reintentos por 429 solo son visibles dentro del cliente.
Alternativas: una interfaz separada MedidorRed (más limpia, pero otra pieza que conectar al armar la aplicación); que ServicioDatos lleve su propia cuenta (descartada: no ve los reintentos y subestimaría el gasto).
Decisión: dos métodos de solo lectura, solicitudes_realizadas() y presupuesto(). El presupuesto es None hasta conocerlo, y FuenteOffline responde 0 y None.
Complejidad: O(1).
Evidencia: prueba_falso_1_9: tras el 429 recuperable, solicitudes_realizadas() coincide con total_recibidas() del servidor.
Límites: si hubiera más de una fuente de red activa, un solo contador ya no bastaría.
D11. Los adaptadores rechazan lotes fuera de rango
Problema: el servicio acepta hasta 10 salas o fichas por solicitud y cuesta lo mismo con 1 que con 10. Quién parte un lote grande decide cuánto presupuesto se gasta.
Alternativas: que el adaptador parta automáticamente el lote en varias solicitudes (cómodo, pero gasta presupuesto sin que nadie lo decida); enviar tal cual y dejar que el servidor rechace (gasta una solicitud en un error).
Decisión: validar_lote lanza LoteInvalido antes de enviar nada. La política de armar lotes es de ServicioDatos.
Complejidad: O(1) por validación, porque len() de ListaEnlazada no recorre.
Evidencia: prueba_1_4 (caso 4) y prueba_1_7 comprueban que un lote vacío o de más de 10 se rechaza al instante con los dos adaptadores, y prueba_5_5 que ServicioDatos parte 12 fichas en 2 lotes de hasta 10. Las dos alternativas gastan las mismas solicitudes (⌈ids/10⌉): cambia quién decide el lote, no el costo, así que no hay una diferencia que medir.
Límites: si el servicio cambiara el tamaño máximo de lote, LIMITE_LOTE habría que actualizarlo.

D12. Contador protegido con Lock

(Rubro de cliente y presupuesto de red.)

Problema: el hilo de FuenteAsincrona escribe el contador mientras el hilo del juego lo lee y hace consultas directas. Sumar sobre un entero compartido no es una operación indivisible: dos hilos podrían leer el mismo valor y ambos gastar la última solicitud.
Alternativas: dejarlo sin protección y documentar que solo un hilo lo usa (más simple, pero cualquier cambio futuro de uso introduciría un error casi irreproducible); un contador por hilo sumados al final (no permite bloquear antes de superar el límite).
Decisión: un threading.Lock que cubre la comprobación del margen y la suma como un solo paso.
Complejidad: O(1) por operación. Se añade el costo constante de tomar y soltar el cerrojo.
Evidencia: prueba_1_5 (caso 6) corre 8 hilos × 50 intentos con presupuesto 100 y exige exactamente 100 registrados y 300 bloqueados. No se midió el costo del Lock: registrar_intento ocurre una vez por solicitud (decenas o cientos por partida), y cada una tarda unos 400 ms de red.
Límites: el Lock no es reentrante, así que no se puede llamar a un método bloqueado desde otro. Si hubiera cientos de hilos compitiendo, el cerrojo sería un cuello de botella, pero aquí hay dos.
D13. Bloqueo previo al agotarse el presupuesto
Problema: presupuesto_solicitudes es un máximo, y superarlo invalida el rubro de red. Los reintentos por 429 también gastan.
Alternativas: solo advertir y seguir enviando (contradice el "máximo"); comprobar después de enviar (ya se gastó la solicitud cuando se descubre el exceso).
Decisión: registrar_intento lanza PresupuestoAgotado antes de enviar y sin sumar. La reserva de margen para casos críticos queda en ServicioDatos, usando restantes().
Complejidad: O(1).
Evidencia: prueba_falso_1_9 juega una partida de datos con presupuesto 12 y comprueba que la solicitud que lo superaría NO llega al servidor, y otra con presupuesto 6 y 429 persistente.
Límites: si el presupuesto se agota, ciertas salas no podrán cargarse y el juego quedará limitado a lo ya descargado. Por eso la precarga debe planificarse con restantes().
D14. Reinicio del conteo por partida
Problema: el presupuesto pertenece a "esa partida", y la lista de criptas también cuenta. Un programa puede jugar varias partidas seguidas.
Alternativas: acumular por ejecución sin reiniciar (una segunda partida podría empezar con gasto previo o bloqueada); reiniciar automáticamente al pedir los datos generales (dejaría fuera del conteo la lista de criptas, que sí cuenta).
Decisión: método reiniciar() que el controlador invoca al volver al menú, expuesto a través del puerto como reiniciar_conteo().
Complejidad: O(1).
Evidencia: prueba_falso_1_9 (caso 8): en una partida nueva el conteo vuelve a 0 y el presupuesto se olvida.
Límites: depende de que el controlador llame a reiniciar al iniciar cada partida. Si se olvida, el conteo se acumula.

D15. requests.Session con una solicitud en vuelo

(Rubro de cliente y presupuesto de red.)

Problema: cada solicitud tarda unos 400 ms y el servicio limita la frecuencia. Abrir una conexión segura nueva en cada una suma tiempo, y una Session de requests no está garantizada como segura entre hilos.
Alternativas: requests.get sin sesión (conexión nueva cada vez); varias solicitudes en paralelo (más rápido, pero aumenta el riesgo de 429, y cada uno gasta presupuesto).
Decisión: una única Session con un Lock que permite una sola solicitud a la vez.
Complejidad: O(1) por solicitud; la latencia la domina la red. Con el cerrojo, k solicitudes concurrentes tardan k veces la latencia de una.
Evidencia: tabla 3 de benchDatos, que mide la alternativa: 20 solicitudes seguidas a un servidor HTTP local cuestan 0.63 ms cada una con Session y 1.68 ms con requests.get suelto (2.7 veces más), por abrir una conexión nueva cada vez. Contra el servidor real (HTTPS) se suma la negociación TLS de cada conexión nueva, que no se midió. Paralelo contra serializado no se midió para no gastar presupuesto del API real.
Límites: si el servidor permitiera paralelismo sin límite, serializar desperdiciaría capacidad. Una consulta directa del hilo del juego espera si el hilo de fondo tiene una solicitud en curso.
D16. Política ante HTTP 429
Problema: un 429 debe manejarse sin que el programa se caiga (§3.1), el reintento cuenta contra el presupuesto, y el tiempo real de espera no puede mover el reloj virtual.
Alternativas: sin tope de reintentos (podría vaciar el presupuesto); 5 reintentos (más gasto); esperar exactamente reintentar_en (arriesga un segundo 429 que costaría otra solicitud); abortar al primer 429.
Decisión: hasta 3 reintentos, espera de reintentar_en más 1 s, 5 s si el servidor no indica el tiempo, y error inmediato si pide esperar más de 60 s.
Complejidad: como máximo 4 solicitudes por consulta, y la espera total está acotada.
Evidencia: prueba_falso_1_9 cubre un 429 recuperable (2 solicitudes) y uno persistente (termina en ErrorDeRed con código 429).
Límites: si el límite de frecuencia fuera muy estricto, 3 reintentos podrían no bastar. Las esperas dependen del reloj real de la máquina.
D17. Errores con contexto y sin reintento de fallas de conexión
Problema: §3.1 no acepta terminar con una excepción de requests sin contexto, y ante un timeout no sabemos si el servidor llegó a procesar la solicitud.
Alternativas: reintentar automáticamente los timeouts (podría gastar presupuesto en solicitudes que quizá sí llegaron); dejar propagar la excepción original (incumple §3.1).
Decisión: traducir toda falla a ErrorDeRed con operación, causa y código HTTP, y no reintentar timeouts ni fallos de conexión. Quien llama decide, con el presupuesto a la vista.
Complejidad: O(1).
Evidencia: prueba_errores_red, contra un servidor HTTP local. HTTP 500: el mensaje nombra la operación, trae el texto del servidor y el código, y gasta 1 solicitud. JSON inválido: ErrorDeRed, no un ValueError. Timeout: no se reintenta (el contador y el servidor registran 1). Conexión rechazada: ErrorDeRed con la operación (en Windows llega como timeout de conexión).
Límites: en una red inestable habrá más errores visibles. ServicioDatos puede reintentar sabiendo cuánto presupuesto queda.

D18. Orden de incorporación con recoger_listas()

(§2.4 "Determinismo de red" y §4.2.)

Problema: la latencia real no puede cambiar la partida. Si dos respuestas llegan en distinto orden entre ejecuciones y el modelo las incorpora al llegar, el estado podría variar.
Alternativas: que ServicioDatos guarde sus propias solicitudes y decida el orden (reparte una regla delicada entre dos clases); incorporar en orden de llegada (no determinista).
Decisión: recoger_listas() entrega las solicitudes terminadas en orden de envío y se detiene en la primera que no ha terminado. Cada solicitud se entrega una sola vez. Con el hilo único la terminación ya sigue el orden de envío, y el método vuelve explícita esa garantía y la mantendría si algún día hubiera más de un hilo.
Complejidad: O(m) donde m es la cantidad de solicitudes entregadas. Cada solicitud entra y sale de la cola una vez, así que el costo total es O(1) amortizado por solicitud.
Evidencia: prueba_1_8 (casos 2 y 7) comprueba que recoger_listas se detiene en la primera sin terminar y que 30 solicitudes salen en orden de envío; prueba_falso_1_9 repite la partida con 50 ms y 0 ms de latencia y obtiene las mismas 12 solicitudes en el mismo orden. benchPrecarga repite el recorrido con 40 ms y 1 ms de latencia y obtiene las mismas solicitudes.
Límites: el orden es de envío, no de "importancia": una solicitud lenta retrasa la incorporación de las siguientes, aunque ya hayan terminado.
D19. Sin cancelación de solicitudes pendientes
Problema: cancelar una solicitud que aún no empezó ahorra presupuesto, pero que dé tiempo a cancelarla depende de la velocidad de la red.
Alternativas: una bandera de cancelación que el hilo revisa antes de enviar (ahorra presupuesto pero hace el gasto dependiente de la latencia); vaciar la cola al cambiar de zona (mismo problema).
Decisión: toda solicitud enviada se atiende. La disciplina queda en ServicioDatos: solo encolar lo necesario y guardar un margen con restantes().
Complejidad: O(1) por envío y por atención.
Evidencia: sin cancelación el conteo es idéntico con cualquier latencia: prueba_falso_1_9 (12 solicitudes con 50 y 0 ms) y benchPrecarga (las mismas solicitudes con 40 ms y con 1 ms). La variante con cancelación no se implementó: por diseño su conteo dependería de la latencia, justo lo que §2.4 prohíbe.
Límites: se puede gastar una solicitud inútil. Con presupuestos muy ajustados, esa pérdida puede importar y habría que replantear la decisión.
D20. cerrar() termina la solicitud en curso y descarta las pendientes
Problema: al terminar el programa, seguir atendiendo solicitudes gasta presupuesto y hace esperar al usuario, sin beneficio.
Alternativas: completar todas las pendientes antes de cerrar (puede tardar segundos y gastar solicitudes que nadie usará); matar el hilo al instante (dejaría a medio enviar una solicitud y una conexión abierta).
Decisión: se termina la solicitud que ya está en curso, las pendientes se marcan con ErrorDeRed para que nadie se quede esperándolas, y se espera al hilo hasta espera_maxima segundos. Además el hilo es daemon, por lo que no impide cerrar el programa si algo lo detuviera.
Complejidad: O(p) donde p es la cantidad de solicitudes pendientes descartadas, más el tiempo de la solicitud en curso.
Evidencia: prueba_1_8 (caso 8): cerrar() termina la solicitud en curso y las pendientes fallan con ErrorDeRed.
Límites: una solicitud en curso puede tardar mucho si hay 429 con esperas largas. espera_maxima acota lo que se espera al cerrar.
D21. Hilo único, Cola propia protegida con Condition, y copia defensiva del pedido
Problema: el hilo de fondo y el del juego comparten la cola, y queue.Queue de la biblioteca estándar equivale a una estructura que §7 obliga a implementar nosotros.
Alternativas: queue.Queue (prohibida como sustituto); varios hilos (respuestas más rápidas, pero más 429, orden menos claro y contador más disputado); sondeo con sleep en lugar de Condition (desperdicia CPU y añade latencia).
Decisión: un solo hilo que duerme en Condition.wait() y despierta con notify() cuando llega una solicitud. La Cola propia solo se toca dentro del cerrojo. Los ids del pedido se copian al enviarlos, porque la lista que pasa el llamador podría modificarse mientras el hilo la lee. Los errores del hilo se guardan en la Solicitud y se relanzan en quien pide el resultado.
Complejidad: encolar y desencolar son O(1). Copiar el pedido es O(k) con k ≤ 10.
Evidencia: prueba_1_8 (casos 1, 3 y 6): una sola solicitud a la vez, los errores del hilo se relanzan en quien pide el resultado y modificar el lote después de enviarlo no cambia el pedido. No se midió el sondeo con sleep: con Condition el hilo despierta en cuanto llega una solicitud, y la pausa de un sondeo se sumaría entera a la latencia.
Límites: con un solo hilo, las solicitudes se atienden una tras otra: k solicitudes tardan k veces la latencia. Con un servicio que aceptara paralelismo, esa decisión se revisaría.

D22. Pruebas de integración con un servidor simulado y verificación por mutación

(§4.2. Rubro de cliente y presupuesto de red, y evidencia para D18, D19 y D2.)

Problema: no se puede probar a fondo el 429, el presupuesto agotado ni la latencia contra el servicio real: cuesta presupuesto, es lento y no es reproducible.
Alternativas: probar solo contra el servicio real (gasta solicitudes, depende de internet y del estado del servidor); probar solo cada pieza por separado (no detecta errores en la unión, como un contador que no ve reintentos).
Decisión: un servidor HTTP local que imita el API (con latencia configurable, respuestas en orden inverso y 429 inyectables), una prueba de integración que recorre una partida completa de datos, y una comparación de esa misma partida con latencias distintas.
Complejidad: el conteo esperado se deduce del diseño: menú 2 + esqueleto ⌈salas/salas_por_página⌉ + contenido ⌈salas/10⌉ + catálogo (en cadena, ≥ 2).
Evidencia obtenida: las 12 solicitudes, sus rutas y su orden de recolección fueron idénticos con latencia de 50 ms y de 0 ms. El contador coincidió con las solicitudes que el servidor recibió realmente, incluido el 429. Se introdujeron tres fallas a propósito (reintentos sin contar, recolección desordenada, UUID variable) y las pruebas las detectaron todas.
Límites: el servidor simulado solo es tan fiel como nuestra lectura del contrato. Por eso se complementa con real_1_9.py contra el servicio real.


D23. Estructura de la agenda: montículo de nodos enlazados

(§4.1, agenda de eventos.)

Problema: la agenda debe entregar siempre el evento de menor (tiempo, secuencia) sin examinar todos los pendientes. Hay cientos de eventos simultáneos y esta operación se ejecuta decenas de miles de veces (§4.1). El equipo decidió además usar solo estructuras propias y ninguna lista de Python (D27).
Alternativas:
(a) Vector (montículo sobre arreglo). Es la forma clásica. Se descarta por dos razones. Capacidad: un vector de tamaño fijo puede desbordarse, y como los eventos cancelados ocupan lugar hasta llegar a la raíz, el máximo simultáneo no se puede predecir; la revisión usa una cripta no vista (§9), así que un tope sería una suposición escondida en el código. Política: un vector que crece necesita reservar memoria con una lista de Python, y el equipo decidió no usarla. Esta alternativa no se mide.
(b) Montículo sobre lista enlazada (los mismos pasos, pero accediendo a cada posición). Medida.
(c) Búsqueda lineal sobre una lista enlazada sin orden. Medida.
(d) Lista enlazada ordenada, con inserción lineal. Medida.
Decisión: árbol binario completo de nodos enlazados (NodoArbol, con punteros a hijo izquierdo, hijo derecho y padre), sin arreglos. A la posición p se llega bajando según los bits de p en binario, en O(log n), sin necesitar acceso por índice.
Complejidad: insertar y extraer son O(log n), ver el mínimo es O(1) y recorrer todos es O(n). Las alternativas medidas cuestan O(n) por operación (b, c) o por inserción (d).
Evidencia: tablas 1 y 2 de benchAgenda (Windows 11, Python 3.14).
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

D25. Cancelación perezosa
Problema: al morir un actor o cancelarse un efecto sus eventos no deben ejecutarse, y no se puede recorrer toda la agenda para buscarlos (§4.1, §2.10).
Alternativas: montículo indexado con eliminación inmediata (cada nodo guarda su posición y se saca del medio en O(log n); más código, acopla el TDA a Evento y complica el deshacer); reconstruir el montículo sin los cancelados (O(n) por cancelación).
Decisión: montículo simple; la Agenda marca cancelado y descarta los eventos cancelados al llegar a la raíz. Reprogramar es cancelar e insertar uno nuevo; deshacer es quitar la bandera.
Complejidad: cancelar es O(1). Cada evento cancelado cuesta una extracción O(log n) en total, una sola vez.
Evidencia: tabla 3 de benchAgenda, que cancela el 10 %, 50 % y 90 % de los eventos y vacía la agenda: la cancelación perezosa cuesta de 15 a 75 veces menos que la alternativa medida (reconstruir el montículo sin los cancelados) en el modo completo, y su costo casi no depende de cuántos se cancelan (0.13 a 0.14 ms con 100 eventos en el modo rápido, contra 0.77 a 3.18 ms al reconstruir).
Límites: los eventos cancelados ocupan memoria hasta llegar a la raíz. Si se cancelaran masivamente eventos muy lejanos en el tiempo, convendría una limpieza periódica.


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
Evidencia: tablas 1 y 2 de benchCache, que miden directamente la alternativa (a). Con un patrón de acceso 80/20 sobre 100 fichas y capacidad 25, LRU alcanza 67.0–70.5 % de aciertos contra 59.6–62.3 % de FIFO con la misma secuencia exacta de accesos (verificado antes de medir), y el tiempo por acceso es equivalente (FIFO 1.1 veces el de LRU): la ventaja en aciertos no cuesta velocidad. Además, prueba del ejemplo A-B-C-A-D verificando el orden exacto de desalojo y prueba aleatoria de 3000 operaciones que nunca desaloja algo fijado.
Límites: si todas las fichas caben en uso simultáneo, la caché crece sin tope — es una decisión deliberada (preferir correctitud sobre memoria) que se documenta, no un error. Con un patrón de acceso uniforme (sin fichas "populares") la ventaja de LRU se reduciría o desaparecería; ese caso no se midió.

D32. Búsqueda en caché sin dict: O(capacidad), decisión del equipo
Problema: el enunciado (§4.4) señala explícitamente que el costo de "¿está esta ficha en caché?" importa, lo cual normalmente se resuelve con tabla hash O(1).
Alternativas: (a) dict como índice interno de la caché (O(1), pero rompe la política D27 del equipo de no usar estructuras de Python en ningún punto del programa). (b) una tabla hash propia como índice: O(1) promedio, pero es una segunda estructura que hay que mantener sincronizada con la ListaDoble en cada inserción y desalojo, para ahorrar microsegundos frente a los 400 ms de una solicitud (ver la evidencia).
Decisión: el equipo mantiene la política sin excepciones: búsqueda lineal en ListaDoble, O(capacidad).
Complejidad: O(capacidad) por búsqueda; con 25 (o incluso cientos) es insignificante frente al costo real del sistema (una solicitud HTTP tarda ~400 ms).
Evidencia: tabla 3 de benchCache. Buscar una ficha AUSENTE (peor caso: recorre toda la caché llena) cuesta 1.6 µs con capacidad 25, 6.3 µs con 100, 31 µs con 500 y 126 µs con 2000: crece lineal, como se esperaba, y aun con 2000 es el 0.03 % de lo que cuesta el fallo que va a la red (400 ms). Con la capacidad por defecto es el 0.0004 %.
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
Alternativas: (a) que cada pieza del modelo llame directamente a la fuente: lo acopla a HTTP y al disco y repite en varios lugares la lógica de caché y presupuesto. (b) un objeto global accesible desde cualquier parte: esconde la dependencia y obliga a las pruebas a reemplazar un global.
Decisión: ServicioDatos recibe por inyección la fuente síncrona, la asíncrona, la caché y el almacén, y es la única clase que los toca. El resto del modelo solo llama a sus métodos públicos.
Complejidad: la indirección es O(1) por consulta; el costo real es el de la caché (D32) y, en un fallo, el de la red.
Evidencia: prueba de integración (prueba_5_5) ejercitando el flujo completo con una fuente falsa, sin que ninguna otra pieza del modelo necesite saber que es falsa.
Límites: la responsabilidad de esta clase es amplia (arranque, contenido, catálogo, presupuesto); si creciera más, convendría partirla.
D36. Catálogo "en cadena" vía resolver_ficha_y_dependientes
Problema: un enemigo puede "soltar" objetos cuyo id de catálogo no se conoce hasta leer la ficha del enemigo (§4.3).
Alternativas: (a) pedir todo el catálogo al empezar: gasta presupuesto en fichas que quizás nunca aparecen. (b) resolver lo que suelta un enemigo recién cuando muere: el combate esperaría a la red (unos 400 ms) en medio de la partida.
Decisión: resolver_ficha_y_dependientes resuelve primero la ficha pedida y, si es un enemigo con suelta no vacía, encadena una segunda resolución (que a su vez pasa por caché/disco/red con la misma lógica).
Complejidad: O(f + s) fichas, con s las fichas que se descubren en "suelta"; a lo sumo dos rondas de solicitudes, en lotes de 10.
Evidencia: prueba con una rata que suelta una poción no pedida explícitamente, verificando que ambas llegan resueltas.
Límites: solo encadena un nivel (lo que suelta un enemigo); si un objeto sólido pudiera a su vez referenciar otro id, haría falta recursión, que el enunciado no exige.
D37. Corrección de la medición de aciertos/fallos: CacheFichas.ver()
Problema: al revisar la implementación, se encontró que resolver_fichas consultaba la caché dos veces por ficha, contando como "acierto" una ficha recién insertada en la misma llamada — inflando artificialmente la estadística que pide §4.4.
Alternativas: (a) contar aciertos y fallos fuera de la caché, en ServicioDatos: duplica la lógica de qué es un acierto. (b) dejarlo así: la estadística del reporte final quedaría inflada.
Decisión: se separó la consulta real (obtener, que sí afecta estadísticas y orden LRU) de una consulta silenciosa (ver, que no afecta nada), usada solo para leer el valor final de algo que se acaba de resolver.
Complejidad: ver() es O(capacidad), como obtener(), pero no mueve el nodo ni cuenta.
Evidencia: prueba específica de ver() verificando que no toca aciertos/fallos ni el orden interno; se mantiene como caso de la autoauditoría del equipo (en la línea de lo que ya pasó con el diccionario olvidado en el Paso 4).
Límites: este tipo de error (una métrica contaminada por una consulta interna) es fácil de repetir en otras partes; conviene revisar con el mismo criterio cuando se agregue el reporte final de --bench.

D38. ObjetoInventario: instancia separada de la ficha compartida
Problema: §2.7 exige distinguir instancias del mismo tipo de objeto (dos dagas son dos objetos, aunque compartan ficha).
Alternativas: (a) usar la FichaDTO compartida como el objeto: dos dagas serían el mismo objeto y soltar una "soltaría" las dos. (b) copiar la ficha entera por instancia: duplica datos inmutables que no cambian nunca.
Decisión: una clase mínima con id_instancia (autoincremental) y una referencia a la FichaDTO inmutable del catálogo.
Complejidad: crear una instancia es O(1); memoria O(1) por instancia (un id y una referencia).
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
Alternativas: (a) esperar al Paso 6 para tener vistas ordenadas: dejaba §4.5 sin probar mientras tanto. (b) ordenar la lista real y restaurarla después: arriesga perder el orden real ante un error a mitad de camino.
Decisión: Inventario._ordenar_insercion implementa inserción directamente, documentada como temporal, sobre una copia (nunca la estructura real). Cuando llegue el Paso 6, se sustituye por una llamada al Ordenamiento definitivo sin tocar el resto de Inventario.
Complejidad: O(n²) en el peor caso, pero n está acotado por inventario_max (del orden de decenas), así que el costo real es insignificante.
Evidencia: pruebas con 4 criterios y verificación explícita de que el orden real no cambia tras tres llamadas a vista_ordenada; la mutación M4 (que intentó ordenar la lista real por error) ni siquiera llegó a ejecutarse, porque ListaDoble no tiene los métodos de acceso por índice que usa el ordenamiento — una protección estructural, no solo una prueba.
Límites: esta es una implementación a reemplazar, no la decisión final; el Documento debe dejarlo explícito para no presentarla como si fuera la solución definitiva de §4.9.
Actualización: ya se reemplazó. Inventario.vista_ordenada arma claves (ClaveOrden) sobre una copia y llama a ordenar(), el selector de D41 y D42; _ordenar_insercion ya no existe. La interfaz expone las vistas con Tab y O (D69).

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

D43. Cola de comandos: pedir_comando() nunca bloquea
Problema: VistaJuego.pedir_comando() (§6, §10.2) se pensó como una llamada bloqueante al estilo input() de consola, pero pyarcade corre su propia máquina de eventos (on_update/on_draw/on_key_press) que nunca se detiene a esperar una tecla: una Vista real con pyarcade no puede implementar ese contrato tal cual.
Alternativas: (a) que VistaArcade bloquee de verdad metiendo su propio sub-bucle de eventos dentro de pedir_comando() hasta que el jugador presione algo -- descartada: congelaría el redibujado (la ventana se vería "trabada") mientras se espera, y acoplaría a VistaArcade una forma de esperar que VistaNula no necesita ni puede imitar.
Decisión: cada tecla que el jugador presiona se encola como Comando en una Cola interna (la del Paso 4, TDA permitido) dentro de la propia Vista; pedir_comando() saca el siguiente comando si hay uno encolado, o devuelve None si no hay ninguno todavía. El Controlador debe tratar None como "todavía no hay decisión" y seguir su propio bucle en vez de quedarse esperando.
Complejidad: encolar y pedir_comando() son O(1) (Cola, construida sobre ListaEnlazada).
Evidencia: prueba_vista_3.py confirma que una tecla produce exactamente un Comando (pedir_comando() lo da una sola vez y después vuelve a None), que dos teclas seguidas se entregan en el mismo orden en que llegaron (FIFO), y que una tecla sin mapear no encola nada; mutación (pedir_comando() dejado para que no vaciara la cola, usando ver_frente() en vez de desencolar()) fue atrapada por la prueba.
Límites: con VistaNula no hay cola real (no hay jugador presionando nada): pedir_comando() ahí siempre es None, lo cual es correcto para --replay/--bench (la partida se conduce leyendo un archivo o generando comandos de otra forma, no desde una Vista interactiva).

D44. Dueño del bucle: el Controlador, nunca arcade.run()
Problema: pyarcade asume normalmente que arcade.run() es quien controla el programa (su propio bucle infinito de cuadros), pero VistaJuego ya asumía lo contrario: que el Controlador tiene su propio bucle y llama a pedir_comando() en cada vuelta (D43). Los dos no pueden ser dueños del bucle principal al mismo tiempo.
Alternativas: que VistaArcade llame arcade.run() y reciba del Controlador una función de "tick" para invocar en cada on_update -- descartada: invierte quién maneja a quién (el Controlador pasaría a reaccionar a la Vista en vez de dirigir su propio flujo), y el Controlador dejaría de tener un bucle explícito y medible, lo cual complica --replay/--bench (que si necesitan correr lo más rápido posible, sin esperar al ritmo de cuadros de pyarcade).
Decisión: el Controlador sigue siendo el único dueño del bucle principal; VistaArcade nunca llama arcade.run(). Se agrega un octavo método a VistaJuego, actualizar(), que el Controlador llama una vez por vuelta de su bucle, antes de pedir_comando(): en VistaArcade bombea a mano los eventos pendientes de la ventana real (equivalente a lo que arcade.run() haría internamente en una vuelta) y redibuja; en VistaNula no hace nada, porque no hay ventana.
Complejidad: actualizar() es O(1) de parte del Controlador (una llamada); el costo real de bombear eventos y redibujar lo determina pyarcade/pyglet, no el diseño de Cripta.
Evidencia: prueba_vista_3.py abre una ventana real (con Xvfb, dado que el entorno de pruebas no tiene pantalla física) y confirma que actualizar() no revienta ni bloquea después de cada cambio de pantalla (mostrar_menu, mostrar_estado, mostrar_puntajes, mostrar_fin).
Límites: esta decisión obliga a que cualquier Vista futura con su propio bucle de eventos (no solo pyarcade) implemente actualizar() de forma no bloqueante, igual que VistaArcade; si alguna librería de UI no permitiera bombear eventos "a mano" sin ceder el control permanentemente, este patrón no serviría y habría que revisar el contrato de VistaJuego otra vez.

D45. Las teclas las interpreta cada pantalla, no VistaArcade de forma global
Problema: el esqueleto del Paso 3 mapeaba las flechas a "mover" en un solo lugar (VistaArcade), pensando ya en la Pantalla Juego. Al construir la Pantalla Menú (Paso 4) quedó claro que eso estaba mal: en el Menú las flechas significan "mover el cursor entre criptas", no "mover al jugador" -- un mapeo global de teclas no puede servir para dos significados distintos de la misma tecla según la pantalla.
Alternativas: seguir con el mapeo centralizado en VistaArcade y que cada método mostrar_* le avise qué modo de teclas activar (p. ej. un "modo menú" vs "modo juego").
Se descarta: VistaArcade terminaría conociendo el significado de cada tecla en cada pantalla, justo el acoplamiento que se quiere evitar -- y cada pantalla nueva (Puntajes, Fin) obligaría a tocar ese método central otra vez.
Decisión: cada pantalla (subclase de la nueva _PantallaCripta) implementa su propio tecla_propia(symbol, modifiers) y llama directamente a vista_arcade._encolar(Comando(...)) con lo que corresponda; VistaArcade ya no sabe qué tecla significa qué, solo sabe cambiar de pantalla y sacar comandos de la cola. Lo único verdaderamente igual en las 4 pantallas (ESCAPE -> "salir") lo atiende _PantallaCripta.on_key_press antes de delegar a tecla_propia(), así ninguna pantalla se puede olvidar de implementarlo.
Complejidad: O(1) por tecla: cada pantalla compara la tecla con las suyas y encola a lo sumo un Comando; cambiar de pantalla no recorre nada.
Evidencia: prueba_vista_3.py confirma que en una pantalla sin teclas propias (el relleno de Juego/Puntajes/Fin, Pasos 5-7 todavía no construidos) solo ESCAPE hace algo; prueba_vista_4.py confirma que en PantallaMenu las mismas flechas mueven el cursor (sin salir de rango) y no encolan ningún Comando por sí solas, mientras que ENTER sí arma "jugar" con el id de la cripta bajo el cursor. Mutación (el clamp del cursor dejado para que aceptara un índice de más) fue atrapada por la prueba.
Límites: el vocabulario de verbos que cada pantalla puede usar ("jugar", "ver_puntajes", "mover", "esperar", "salir"...) queda implícito en el código de Vista; como TraductorComandos (del lado de Controlador) es quien interpreta esos verbos, hay que avisarle al compañero qué verbos y argumentos arma cada pantalla a medida que se construyen (por ahora: "jugar" con el id de la cripta como único argumento, y "ver_puntajes" sin argumentos).

D45 (vocabulario agregado): Puntajes y Fin (Pasos 6 y 7) son pantallas de solo lectura -- no hay cursor que mover ni objetivo que elegir, así que ENTER tiene un único significado posible ahí: volver al Menú. Se agrega el verbo "volver" (sin argumentos) para eso. Con esto, Vista queda completa (Pasos 4 a 8): el vocabulario final que TraductorComandos necesita reconocer es "mover" (N/S/E/O), "esperar", "atacar" (etiqueta), "usar"/"equipar"/"soltar" (id_objeto), "jugar" (id de cripta), "ver_puntajes", "volver" y "salir" -- todos sin adivinar nada del lado de Vista, que nunca interpreta lo que el jugador pidió (§10.2).

D46. Elegir objetivo (atacar/usar/equipar/soltar): modo de selección con flechas, no teclas numéricas
Problema: atacar necesita elegir un enemigo de la sala; usar/equipar/soltar necesitan elegir un objeto del inventario. A diferencia de moverse o esperar, estos verbos necesitan un argumento que el jugador tiene que escoger con el teclado, no uno fijo.
Alternativas: numerar cada enemigo/objeto en pantalla (1, 2, 3...) y que la tecla de acción más el número arme el Comando de una sola vez, sin pantalla de selección aparte. Se descarta: dependería de que nunca haya más de 9 enemigos u objetos a la vez (arbitrario, no garantizado por el modelo), y cambiaría el significado de las teclas numéricas según cuántos objetivos hubiera en ese momento (frágil para el jugador).
Decisión: PantallaJuego gana un segundo modo ("objetivo"), separado del modo normal. A/U/Q/S (atacar/usar/equipar/soltar) entran a ese modo apuntando a la lista que corresponda (sala.enemigos para atacar; inventario.objetos para los otros tres) -- si esa lista está vacía, no pasa nada, ni siquiera cambia de modo. Dentro de modo objetivo, las mismas flechas que mueven al jugador en modo normal mueven un cursor sobre la lista (clampado, igual que en PantallaMenu), ENTER arma el Comando con el objetivo bajo el cursor y vuelve a modo normal, y ESCAPE cancela sin encolar nada (vuelve a modo normal) -- un significado de ESCAPE distinto al de cualquier otra pantalla, donde siempre es "salir" (D45), así que PantallaJuego sobreescribe on_key_press para interceptar ese único caso antes de que llegue a _PantallaCripta.
Complejidad: entrar/salir de modo objetivo y mover el cursor son O(1); construir la lista de textos de la pantalla de selección es O(n) en la cantidad de objetivos, igual que ya pasaba en PantallaMenu.
Evidencia: prueba_vista_6.py confirma que A/U/Q/S apuntan a la lista correcta, que el cursor no sale de rango, que ENTER arma "atacar" con la ETIQUETA del enemigo (no su posición ni su vida) y "usar"/"equipar"/"soltar" con el ID_OBJETO real (no el nombre, que se puede repetir), que ESCAPE en modo objetivo NO encola "salir" (a diferencia del modo normal, probado aparte en el mismo archivo), y que sin enemigos/inventario ninguna tecla de acción cambia de modo. Mutación (dejar que ESCAPE en modo objetivo también pasara a la clase base) fue atrapada por la prueba: ese es justo el caso que esta decisión existe para evitar.
Límites: el jugador no puede cancelar a medias el ENTER (una vez confirmado ya se encoló el Comando); si el Controlador llegara a rechazar ese Comando (por ejemplo, un objeto que ya no está donde se pensaba), el error vuelve por mostrar_error(), no hay forma de "deshacerlo" del lado de Vista. También: como con D45, el vocabulario nuevo ("atacar" con etiqueta, "usar"/"equipar"/"soltar" con id_objeto) hay que compartírselo al compañero para TraductorComandos.

D47. Etiquetas estables de enemigos: MapaEtiquetas (ListaEnlazada de pares)
Problema: la Vista muestra "Rata gigante #1", "#2"... (§2.6) y el jugador ataca eligiendo esa etiqueta (D46), pero la Vista nunca ve el id de instancia real. El Controlador tiene que ir de instancia a etiqueta al dibujar y de etiqueta a instancia al atacar, y la etiqueta no puede cambiar entre turnos: Etiquetador genera una etiqueta nueva cada vez que se le pregunta.
Alternativas: (a) recalcular con un Etiquetador nuevo en cada turno: O(e) y no depende de la partida, pero cuando cambia el grupo de enemigos visibles "Rata #1" pasa a ser otra rata y el ataque iría al enemigo equivocado. Se descarta por incorrecta. (b) dict id -> etiqueta: prohibido como tabla de búsqueda (§7). (c) tabla hash propia: O(1) promedio, pero haría falta un índice por id y otro por etiqueta, y con k de decenas el costo de hashear supera al de recorrer.
Decisión: MapaEtiquetas guarda pares (id_instancia, etiqueta) en una ListaEnlazada. La etiqueta se asigna la primera vez que el enemigo se ve y se recuerda toda la partida, aunque cambie de sala. ConstructorEstadoVista y TraductorComandos comparten la MISMA instancia (inyectada). Se reinicia al empezar o cargar una cripta.
Complejidad: etiqueta_de y resolver son O(k) en tiempo, con k enemigos etiquetados en la partida; memoria O(k). Construir el EstadoVista cuesta O(e·k) en la parte de enemigos.
Evidencia (--bench, benchEtiquetas, comparando con la alternativa (a)): un turno con 5 enemigos en sala más un resolver cuesta 1.9 µs con k=10, 7.4 µs con k=50, 27.1 µs con k=200 y 133.2 µs con k=1000, contra unos 2 µs constantes al recalcular. Incluso con k=1000 es el 0.67 % del presupuesto de 20 ms por ciclo (§5.2). prueba_controlador verifica que la etiqueta se mantiene después de un retroceso.
Límites: si una cripta llegara a decenas de miles de enemigos vistos en una sola partida, el costo lineal empezaría a notarse; ahí convendría una tabla hash propia con dos índices.

D48. El Controlador no toca el disco: puertos AlmacenPartida, RegistroAcciones/AlmacenRegistros y AlmacenPuntajes
Problema: la guía (§4, regla de oro) prohíbe que el Controlador conozca rutas, formatos de archivo o print. La primera versión del Controlador armaba rutas con Path, creaba carpetas e instanciaba PartidaBinaria y RegistroArchivo directamente.
Alternativas: (a) dejar GestorGuardado como un adaptador disfrazado dentro del Controlador: se descarta porque viola la separación MVC + adaptadores y obliga a tocar disco en las pruebas. (b) pasarle rutas ya armadas desde FabricaAplicacion: el Controlador seguiría sabiendo que hay archivos.
Decisión: puertos en modelo/puertos (AlmacenPartida: existe, guardar, cargar, cargar_sala; RegistroAcciones: iniciar, registrar_accion, leer, respaldar, restaurar; AlmacenRegistros: registro_de(id_cripta); AlmacenPuntajes: agregar, cargar), con sus adaptadores AlmacenPartidaDisco, RegistroArchivo/CarpetaRegistros y PuntajesArchivo. EncabezadoPartida pasa al puerto como dato puro; el formato de texto queda en el adaptador. FabricaAplicacion es el único lugar que conoce las clases concretas.
Complejidad: las mismas del adaptador (guardar/cargar O(S) en el estado; cargar_sala O(una sala) por la tabla de offsets; anexar al log O(1)). El puerto solo agrega una llamada indirecta, O(1).
Evidencia: después del cambio, en cripta/controlador solo fabricaAplicacion.py importa de adaptadores (verificado con grep). prueba_controlador ejercita guardar, cargar y replay a través de los puertos.
Límites: PartidaBinaria se sigue usando directamente en benchGuardado (medición del formato), lo cual es intencional.

D49. El log se respalda junto con el guardado y se restaura al cargar
Problema: si el jugador guarda, sigue jugando y después carga, el log de solo anexado conserva las acciones que la carga deshizo, y --replay llega a un estado distinto al de la partida real (§4.11).
Alternativas: (a) al cargar, reescribir el log quitando las últimas líneas: rompe la regla de solo anexado y obliga a saber cuántas acciones había al guardar. (b) guardar las acciones dentro del .bin: mezcla dos formatos y el replay dejaría de leer un texto simple.
Decisión: GestorGuardado.guardar() guarda la partida y llama registro.respaldar() en el mismo momento (copia del log a <log>.respaldo); cargar() reconstruye la partida y llama registro.restaurar(). Durante la partida el log sigue siendo de solo anexado.
Complejidad: respaldar y restaurar son O(A) en bytes del log, una vez por guardado o carga; anexar sigue siendo O(1).
Evidencia: prueba_controlador guarda, espera, carga y comprueba que el log es idéntico al del momento de guardar; después termina la partida y verifica que --replay llega al mismo reloj final y a la victoria.
Límites: el historial de retroceso no se persiste (son referencias a objetos vivos y §4.6 prohíbe copias completas): una partida cargada empieza con el Diario vacío.

D50. Pergaminos fuera del retroceso: se filtran al REGISTRAR, solo si los movió el jugador
Problema: §2.11 y el Apéndice B piden que la reversión no devuelva al suelo un pergamino que el jugador recogió (ni le quite uno que soltó) durante el intervalo revertido. Una primera versión filtraba todo pergamino al revertir, pero eso también afectaba al pergamino que suelta un enemigo al morir: al revertir la muerte, el enemigo revivía, el pergamino se quedaba en el suelo y matarlo de nuevo lo duplicaba.
Alternativas: (a) filtrar al revertir por clase de objeto: O(1), pero no distingue si lo movió el jugador o un enemigo (es el error descrito). (b) marcar los objetos con su origen: agrega un campo al modelo solo para esto.
Decisión: Diario.registrar() descarta los movimientos de pergamino del jugador. Partida registra recoger como suelo_quitar + inventario_agregar y soltar como inventario_quitar + suelo_agregar, siempre seguidos. Por eso al ver inventario_agregar de un pergamino se desapila el suelo_quitar del tope, y al ver inventario_quitar se recuerda el objeto para descartar el suelo_agregar que viene enseguida. Lo que suelta un enemigo (suelo_agregar de un objeto nuevo) sí se registra y se revierte. Si ese pergamino ya se recogió en un intervalo posterior, revertir la muerte lo deja donde está.
Complejidad: O(1) por registro (comparar con el tope de la Pila); nada extra al revertir.
Evidencia: prueba_controlador cubre los dos casos: el pergamino recogido en el intervalo revertido no vuelve al suelo y solo se descuenta la unidad usada; la muerte de una rata que suelta un pergamino se revierte sin dejarlo en el suelo, y al matarla de nuevo hay uno solo. Con la versión (a) la prueba falla.
Límites: depende de que Partida registre recoger y soltar como pares consecutivos; si eso cambia, hay que ajustar Diario.

D51. ReporteFinal imprime con Reporte (excepción documentada a "el Controlador no usa print")
Problema: §5.1 exige reportar al final de cada partida las solicitudes, el presupuesto y los aciertos y fallos de caché, también en --replay, que corre con VistaNula (no muestra nada).
Alternativas: (a) un método nuevo en VistaJuego para el reporte: obligaría a VistaNula a imprimir y mezclaría la interfaz del juego con la salida para quien evalúa. (b) pasarlo por mostrar_mensajes: en --replay no se vería y el Apéndice B prohíbe fallar en silencio.
Decisión: ReporteFinal usa Reporte, el formateador que ya usa --bench. El print queda encerrado en esa única clase, que se inyecta (las pruebas usan Reporte(imprimir=False) y leen las notas). ModoReplay reporta sus errores por el mismo camino.
Complejidad: O(1), son cuatro contadores.
Evidencia: --replay con versión incompatible imprime el motivo y sale con código 1; prueba_controlador lo verifica leyendo las notas del Reporte.
Límites: si se quisiera mostrar el reporte dentro de la ventana, habría que agregar una pantalla en la Vista.

D52. "jugar <id> [nueva|cargar]": partida nueva o cargada desde el menú
Problema: §10.2 pide elegir una cripta e iniciar una partida nueva o cargada, pero PantallaMenu solo manda "jugar" con el id de la cripta.
Alternativas: (a) dos verbos distintos ("jugar" y "continuar"): obliga a cambiar la Vista antes de que nada funcione. (b) reanudar siempre que haya guardado: el jugador no podría empezar de cero esa cripta.
Decisión: segundo argumento opcional. Sin él se reanuda si hay guardado y, si no, se empieza una partida nueva (lo que hacía la versión anterior, así que la Vista actual no se rompe). "nueva" siempre empieza de cero; "cargar" solo reanuda e informa si no hay guardado o si la carga falla.
Complejidad: O(1) más la carga o el inicio de la partida.
Evidencia: prueba_controlador cubre "cargar" sin guardado (error), un modo desconocido (error), el caso sin modo y "nueva" con un guardado existente (reloj en 0, sala inicial).
Límites: desde la interfaz, ENTER manda "jugar" sin modo (continúa si hay guardado) y X manda "nueva" (D64); "cargar" solo se usa desde las pruebas.

D53. Paquete --offline con la organización de FuenteOffline
Problema: datos_offline/ tenía archivos planos (cripta-01_general.json...) con el contenido de solo 3 salas de 6 y sin catálogo, mientras que FuenteOffline lee criptas/<id>/general.json, esqueleto/, contenido/<sala>.json y catalogo/<id>.json. --offline no podía iniciar ninguna cripta.
Alternativas: (a) adaptar FuenteOffline a los archivos planos: un archivo por combinación de salas pedidas obliga a adivinar los lotes (ver la decisión del propio FuenteOffline). (b) armar los archivos a mano: propenso a errores y no escala a criptas nuevas.
Decisión: guardar_respuestas.py descarga del API, para todas las criptas publicadas (o las indicadas), datos generales, versión, todas las páginas, todo el contenido en lotes de 10 y el catálogo en lotes de 10 (incluidas las fichas que aparecen en "suelta"), con manejo de 429. Lo escribe con la organización de FuenteOffline.
Complejidad: O(salas/10 + fichas/10) solicitudes por cripta; la descarga completa de las 4 criptas publicadas costó 28 solicitudes.
Evidencia: con el paquete nuevo, las 4 criptas (6, 20, 40 y 50 salas) inician, mueven al jugador y procesan eventos en modo offline.
Límites: si el profesor publica su propio paquete con otra organización, hay que convertirlo o ajustar FuenteOffline.

D54. Vista gráfica: la sala dibujada y animada sin tocar Modelo ni Controlador
Problema: PantallaJuego solo mostraba texto. Hacía falta un dibujo de la sala sin que el Modelo ni el Controlador supieran nada de gráficos (§6), y sin romper la regla de no usar listas, lambda ni dict (D27), que también vale en la Vista.
Alternativas: (a) SpriteList o ShapeElementList de arcade para agrupar lo que se dibuja: solo se llenan con .append, que prueba_reglas rechaza. (b) dibujar cada baldosa como sprite suelto en cada cuadro: unas 144 llamadas por cuadro solo para el fondo. (c) mantener una sola PantallaJuego y mutarla en cada turno: obliga a llevar estado de presentación entre turnos.
Decisión: DibujoSala solo lee el EstadoVista. El fondo de cada sala se arma una vez con Pillow (dependencia de arcade) y se dibuja como una sola textura; la sala se vuelve a armar solo al cambiar de sala. Las animaciones (antorcha, enemigos que se balancean, destello y número de daño, barras que bajan de a poco, enemigo derrotado que se desvanece, fundido al entrar a una sala) salen de comparar el EstadoVista actual con el anterior, que VistaArcade le pasa a cada PantallaJuego nueva. Las animaciones son tuplas de cuadros; los sprites se guardan en atributos de una clase, no en un dict.
Complejidad: comparar con el estado anterior es O(e·e') una vez por turno (e y e' enemigos de antes y de ahora, decenas a lo sumo); cada cuadro dibuja en O(enemigos + objetos); armar el fondo es O(144) baldosas por sala.
Evidencia: prueba_reglas sigue pasando (111 archivos), las 10 pruebas de la batería pasan sin cambios, y las capturas de la ventana muestran la sala con antorcha encendida y apagada, el modo objetivo y el daño.
Límites: la posición de cada enemigo y objeto en el dibujo es decorativa (se reparten en filas); el modelo no tiene coordenadas dentro de la sala. Las trampas no se dibujan porque SalaVisible no las incluye.

D55. Pixel art de 0x72 (CC0) como recurso externo
Problema: las figuras dibujadas a mano y los sprites de Kenney que trae arcade son de vista lateral y no se ven como un calabozo visto desde arriba.
Alternativas: (a) Dungeon Crawl 32x32 (CC0): el más completo, pero de muchos artistas y estilo desparejo. (b) Kenney Tiny Dungeon + Tiny Creatures (CC0): estilo coherente, pero las páginas no confirman rata ni esqueleto. (c) combinar 0x72 con Dungeon Crawl: cubre todo, pero mezcla tamaños (16 y 32 px) y estilos.
Decisión: "16x16 DungeonTileset II" v1.7 de 0x72 (https://0x72.itch.io/dungeontileset-ii), licencia CC0, con autorización del profesor para usar recursos externos (17/10/2026). Se copiaron a cripta/vista/recursos/dungeon_0x72/ solo los cuadros que se usan (65, contando los 3 corazones de D62 y las skins de D63), sin modificarlos, con un LICENCIA.txt. Se usan para el piso, los muros, los estandartes, las calaveras, las puertas, el caballero (jugador, con cuadro de golpe), el esqueleto (guardián óseo), los frascos (poción y antídoto) y la espada (armas). Lo que el paquete no trae se completa con lo que ya había: llave de Kenney (incluida en arcade), la rata de Imogia (ver D58) y figuras para la armadura, la antorcha y el pergamino. El pixel art se escala con vecino más cercano para que no se vea borroso.
Complejidad: no cambia la de D54; cargar cada textura ocurre una sola vez.
Evidencia: capturas de una sala de prueba con todos los tipos de enemigo, objeto y puerta; la carpeta de recursos pesa unos 57 kB.
Límites: las puertas sur, este y oeste usan la misma hoja frontal de 0x72 aplastada, porque el paquete no trae puertas vistas de costado.

D56. Replay en la ventana (ControladorReplay), además de --replay
Problema: --replay reproduce el log con VistaNula y solo imprime un resumen. Para analizar una partida (y mostrar en la defensa que el replay es fiel) hace falta verla paso a paso en la ventana, lanzándola desde la pantalla de fin o desde la tabla de puntajes (D61).
Alternativas: (a) que ModoReplay acepte VistaArcade: ModoReplay reproduce todo en un solo llamado, y la ventana no se redibujaría hasta el final. (b) guardar fotos del estado en cada paso de la partida original para mostrarlas después: es una copia del estado, prohibida por §4.6, y no probaría que el log reproduce la partida. (c) que la Vista lleve el ritmo con arcade.run(): rompe D44 (el Controlador es el dueño del bucle).
Decisión: ControladorReplay vive en el Controlador. Lee el log por el puerto RegistroAcciones, valida versiones con la misma función que --replay (motivo_version_incompatible, ahora compartida) y aplica las acciones con la misma Partida.aplicar_accion. ControladorMenu le pasa cada vuelta del bucle, también las vueltas sin comando, porque el replay avanza por tiempo: un paso cada 0.8 s a velocidad x1, con pausa, paso adelante, paso atrás y velocidad x1 a x16. Retroceder reconstruye la partida: una Partida nueva con la misma semilla vuelve a aplicar las primeras k-1 acciones y llega exactamente al estado anterior, porque la partida es determinista. Se descartó Diario.deshacer, que solo guarda 5 acciones y excluye los pergaminos que puede traer el log, y también guardar una foto por paso, que es una copia del estado prohibida por §4.6. El reloj real se inyecta (las pruebas usan uno falso) y solo decide cuándo se muestra el próximo paso: el resultado no depende de él. Al terminar se compara con el puntaje de esa partida (resultado, acciones, enemigos derrotados y tiempo final) y la pantalla dice si coincide. Una acción rechazada detiene el replay con el motivo, igual que en --replay. El EstadoVista lleva un InfoReplay opcional (paso, total, pausa, velocidad) para que PantallaJuego muestre el HUD y cambie sus teclas.
Complejidad: leer el log es O(A); cada paso cuesta una acción del modelo (< 20 ms, §5.2) más armar la foto; retroceder desde el paso k cuesta O(k) acciones. Memoria O(A).
Evidencia: prueba_replay_menu gana una partida, la reproduce desde la pantalla de fin y comprueba que coincide; prueba también pausa, paso adelante, paso atrás (vuelve al mismo reloj, vida y enemigos que la primera vez, y no baja del paso 0), velocidad, replay desde el menú (sin comparación), un log adulterado (se detiene con error) y ESC (vuelve al menú, no cierra). Dos fallas inyectadas a propósito (comparación del tiempo invertida y velocidad que sube con "-") fueron detectadas. En un recorrido completo del juego real en modo offline, el replay de la derrota llegó al mismo final.
Límites: solo tienen replay las partidas terminadas (las que tienen puntaje, D61).

D57. Menú con nombre, replay y benchmark; nombre bajo el jugador
Problema: el menú era una lista de texto. El jugador no podía poner su nombre (la tabla de puntajes guardaba siempre "Jugador"), y para el replay o el benchmark había que usar la terminal.
Alternativas: (a) un menú por pasos (opción principal y después la cripta): rompe la prueba de vista existente (flechas sobre las criptas, ENTER juega, P puntajes) y suma pantallas. (b) pedir el nombre por la terminal antes de abrir la ventana: rompe la interfaz única de §10.2.
Decisión: una sola pantalla. Las criptas aparecen como tarjetas (dificultad en calaveras, marca de replay disponible) y se conservan las teclas que ya probaba prueba_vista_4. Se suman atajos: N para escribir el nombre (mientras se escribe, las letras no son atajos; el eco de la propia N se descarta por orden de eventos, no por tiempo) y B para el benchmark rápido. El replay no se elige aquí sino en la tabla de puntajes (D61). El nombre lo valida ControladorMenu (sin espacios a los lados, máximo 16 caracteres, vacío vuelve a "Jugador"); llega a la tabla de puntajes y al EstadoVista, y DibujoSala lo dibuja en una placa bajo el caballero. Los métodos nuevos de VistaJuego (mostrar_nombre_jugador, mostrar_benchmark, mostrar_espera) no son abstractos: las Vistas de prueba y VistaNula siguen funcionando sin cambios. El benchmark corre con un Reporte callado y la pantalla muestra las mismas tablas que --bench, con desplazamiento.
Complejidad: armar el menú es O(c) con c criptas; existe() es O(1) por cripta; el benchmark rápido tarda unos 3 a 5 s.
Evidencia: prueba_vista_10 (edición del nombre, B, teclas del replay, R en la pantalla de fin y desplazamiento del benchmark) y prueba_replay_menu (nombre recortado, por defecto y llevado al EstadoVista; benchmark con un ModoBench falso). prueba_vista_4 sigue pasando sin cambios.
Límites: el nombre no se guarda entre ejecuciones. Los mensajes de combate del modelo siguen diciendo "Jugador", porque el modelo no conoce el nombre (es dato de la sesión). Mientras corre el benchmark la ventana no responde (unos segundos).

D58. Rata gigante de Imogia Games (CC BY 4.0)
Problema: 0x72 no trae ratas, y la de Kenney (un ratón de vista lateral, casi blanco) desentonaba con el pixel art de la sala.
Alternativas: (a) Rat 2D Pixel Art de abysx: 16x16 con 5 animaciones, pero es de pago y su licencia prohíbe redistribuirla como recurso (el repositorio la redistribuiría). (b) la rata de Dungeon Crawl 32x32 (CC0): sin animación, de 32 px y de otro estilo. (c) teñir un monstruo de 0x72: mismo estilo, pero no parece una rata. No se encontró ninguna rata de 16x16 con licencia CC0 que combine con 0x72.
Decisión: "8 bit art pack rat monster" de Imogia Games (https://imogiagames.itch.io/8-bit-art-pack-rat-monster), licencia CC BY 4.0, elegida por el equipo. Se copió SIN modificar solo la variante 04 (gris, la que mejor contrasta con el piso café de 0x72) a cripta/vista/recursos/rata_imogia/, con un LICENCIA.txt que da el crédito que exige la licencia ("rata por Imogia Games") y explica los cambios que hace el juego al cargarla. Al cargarla se recortan sus dos primeros cuadros de 16x16 (la rata de costado, que combina con la perspectiva 3/4 de 0x72) y se alternan como animación.
Complejidad: O(1); la tira se recorta una sola vez.
Evidencia: capturas del pasillo real y de la sala de prueba con la rata junto al esqueleto; las 12 pruebas y prueba_reglas pasan.
Límites: CC BY 4.0 exige mantener el crédito en cualquier copia del proyecto (README o créditos del juego, además del LICENCIA.txt).

D59. Tabla de puntajes: las victorias primero
Problema: TablaPuntajes.vista_ordenada("tiempo") ordenaba solo por tiempo final, mezclando victorias y derrotas: una muerte en 207 de tiempo quedaba primera, delante de cualquier victoria.
Alternativas: (a) reordenar en la Vista: la Vista no decide el orden (lo trae el Controlador) y el criterio quedaría en dos lugares. (b) dos tablas separadas (victorias y derrotas): duplica estructura para lo mismo. (c) excluir las derrotas: §2.12 pide registrar ambos resultados.
Decisión: la clave de orden pasa a ser la tupla (0 si es victoria y 1 si es derrota, valor del criterio). Escapar siempre es mejor que morir, y dentro de cada grupo manda el criterio elegido (tiempo, acciones o derrotados). Se compara con < como cualquier otra clave, así que el Ordenamiento propio y su selector (§4.9) no cambian, y el orden sigue siendo estable.
Complejidad: igual que antes, O(p log p) en el peor caso; comparar dos tuplas de dos elementos es O(1).
Evidencia: prueba_6_5 agrega un caso con una derrota rápida (207) que ya no pasa delante de las victorias (2890 y 5400); el resto de la batería pasa sin cambios.
Límites: no hay desempate entre registros con el mismo grupo y el mismo valor más allá del orden en que se guardaron (por la estabilidad).

D60. Pantalla de puntajes ("Salón de la fama")
Problema: la tabla era texto alineado con espacios, sin jerarquía visual, y no cabía si había muchas partidas.
Alternativas: (a) seguir con texto alineado y solo cambiar colores: con muchas partidas seguía sin caber. (b) paginar con teclas propias: suma teclas, y el cursor de flechas ya hace falta para elegir el replay (D61).
Decisión: el mismo estilo que el menú (estilo.py). Arriba, tres tarjetas de resumen (partidas, porcentaje de victorias y mejor victoria con su nombre y cripta), que la Vista calcula recorriendo la lista que ya recibe (presentación, O(p)). Abajo, una tabla con columnas, filas alternadas, el resultado como etiqueta verde o roja, medallas de oro, plata y bronce solo para los tres primeros puestos que sean victorias, y desplazamiento con flechas o rueda si no cabe. Se conservan ENTER (volver) y ESC (salir) que prueba_vista_7 exige, y el método _texto_fila que esa prueba usa.
Complejidad: armar es O(p); cada cuadro dibuja solo las filas visibles.
Evidencia: capturas con 18 partidas mezcladas y con la tabla vacía; prueba_vista_7 pasa sin cambios.
Límites: la columna Cripta muestra el id (p. ej. cripta-02), porque PuntajeVisible no trae el nombre de la cripta.

D61. Replay por partida, elegido desde la tabla de puntajes
Problema: había un solo log por cripta y cada partida nueva lo sobrescribía. El replay desde el menú reproducía la última partida de esa cripta sin decir cuál era ni quién la jugó.
Alternativas: (a) seguir eligiendo por cripta en el menú, con una lista de sus partidas: duplica lo que ya muestra la tabla de puntajes. (b) un log distinto por partida desde el inicio: guardar y cargar (respaldar y restaurar) trabajan sobre el log de la cripta, y habría que rastrear qué log continúa cada guardado.
Decisión: el log activo de la cripta no cambia (solo anexado, §4.11). Al terminar una partida, RegistroAcciones.archivar() copia ese log a partidas/historial/<id>.log, con un id que lleva la cripta, la fecha y hora, y 6 caracteres al azar. RegistroPuntaje gana id_partida (opcional: los puntajes viejos no lo tienen y se cargan igual) y PuntajesArchivo lo guarda. En la tabla de puntajes, las flechas eligen una fila y R reproduce ESA partida con su log archivado (verbo ver_replay_partida). La columna Replay marca cuáles lo tienen. El replay muestra en el HUD de quién es la partida, su cripta, su resultado y su tiempo; usa el nombre de quien la jugó (no el actual), se compara al final con ese puntaje y al salir vuelve a la tabla. Desde la pantalla de fin, R reproduce la partida recién terminada con su propio log archivado. Los métodos nuevos de los puertos (archivar, registro_archivado, existe_archivado) no son abstractos: sin historial, simplemente no hay replay. Se quitó el replay por cripta del menú.
Complejidad: archivar es O(A) en bytes del log, una vez por partida; buscar el puntaje de un id es O(p); saber si una fila tiene replay es O(1).
Evidencia: prueba_replay_menu juega dos partidas en la misma cripta con nombres y tiempos distintos y comprueba que el replay de la PRIMERA reproduce esa y no la última. Una mutación que vuelve a usar el log de la cripta fue detectada. La prueba también cubre un puntaje viejo sin id (sin replay), un log archivado adulterado (se detiene con error) y la vuelta a puntajes. prueba_vista_10 cubre el cursor y la tecla R en la tabla. Un recorrido completo en una carpeta temporal archivó un log por partida y el replay coincidió.
Límites: el historial crece con cada partida (de cien bytes a unos pocos kB por log) y no se poda. Las partidas guardadas a medias no tienen puntaje, así que tampoco replay hasta que terminan.

D62. HUD de la pantalla de juego (HudJuego)
Problema: alrededor de la sala, la información era una lista de líneas de texto (ataque, salidas, efectos, enemigos, inventario y la ayuda de teclas en dos renglones). Costaba encontrar un dato y no se notaba qué había cambiado en el último turno.
Alternativas: (a) retocar los textos dentro de PantallaJuego: la clase ya mezclaba teclas, modos y dibujo. (b) un HUD que se redibuja desde cero en cada cuadro: crearía textos nuevos 60 veces por segundo.
Decisión: un módulo propio, HudJuego, que solo lee el EstadoVista (igual que DibujoSala) y se arma cuando cambia algo visible (estado nuevo, modo objetivo o aviso); cada cuadro solo dibuja lo ya armado. Tiene:
- un encabezado con la sala, la cripta y el tiempo; la vida con el corazón de 0x72 (lleno, medio o vacío, y que late con poca vida), una barra animada y el cambio del último turno ("-3"); y la antorcha y los pergaminos (o el HUD del replay);
- tarjetas con ícono para ataque, defensa, velocidad, acciones y derrotados, que muestran la diferencia con el turno anterior;
- una brújula de salidas (verde abierta, dorado con llave, gris sin salida);
- los efectos con su color;
- "En la sala", con los enemigos y su minibarra de vida, y lo que hay en el suelo;
- el inventario con íconos, una marca de EQUIPADO y el cursor (la lista sigue al cursor si no cabe);
- una bitácora coloreada (daño recibido en rojo, logros en dorado, hallazgos en verde);
- un panel de controles con teclas dibujadas que cambia según el modo (juego, objetivo o replay);
- y los avisos como un cartel sobre el mapa que se desvanece.
En modo objetivo, la columna se reemplaza por la lista para elegir, con barras de vida o íconos. PantallaJuego queda con las teclas y los modos, y conserva los métodos de texto (_texto_salidas, etc.) que usan las pruebas. Se copiaron 3 cuadros más de 0x72 (corazones).
Complejidad: armar es O(enemigos + objetos + inventario + mensajes), una vez por cambio; cada cuadro dibuja O(elementos) sin crear textos.
Evidencia: capturas en modo normal, objetivo y replay, y un recorrido del juego real en una carpeta temporal; las 12 pruebas de la batería pasan sin cambiar sus asserts; prueba_reglas pasa (115 archivos). En prueba_vista_10, el assert del paso 1 se aisló de los eventos reales de la ventana (vaciar la cola antes y no bombear eventos entre escribir y comprobar): fue la causa probable del fallo intermitente que apareció al correrla detrás de otras pruebas de vista. Después, 32 de 32 corridas seguidas de las cuatro pruebas de vista pasaron.
Límites: el color de la bitácora se decide por palabras del mensaje (p. ej. "daño" o "recoges"); si el modelo cambia sus textos, hay que ajustar _color_mensaje.

D63. Skins del héroe, con un tigre humanoide propio como predeterminada
Problema: el héroe era siempre el caballero de 0x72. Se pidió poder elegir el aspecto y que el predeterminado sea un tigre humanoide bien diseñado y animado, pero ningún paquete de los revisados trae un tigre que combine con 0x72.
Alternativas: (a) buscar un sprite de tigre externo: no se encontró ninguno de 16x28 con una licencia que permita incluirlo, y los que hay no comparten el estilo. (b) teñir de naranja un personaje de 0x72: no parece un tigre.
Decisión: el tigre es pixel art propio (pixelTigre.py), hecho con las reglas de 0x72: 16x28 px, contorno de 1 px, cabeza grande, 2 o 3 tonos por color y mirando a la derecha. Tiene rayas en la frente y las mejillas, chaleco con hombrera y cola. Su animación es como la de 0x72: 4 cuadros de reposo (base; respira dos veces, con el torso 1 px más abajo y la cola mecida; y un parpadeo) y uno de golpe (aclarado y con los ojos cerrados). Los cuadros derivados se calculan desde la pose base, así un retoque se aplica a todos. El dibujo es un patrón de texto (una letra por pixel) con una paleta en tupla de pares (sin dict, §7). Las demás skins son personajes de 0x72 con el mismo formato: caballero, caballera, elfa, mago, lagarto y enano. En el menú se cambia con Flecha izquierda/derecha, con vista previa animada. La skin es una preferencia de presentación: la guarda VistaArcade, que se la pasa a DibujoSala; no es un Comando, y el Modelo y el Controlador no la conocen.
Complejidad: generar los 5 cuadros del tigre es O(16x28) por cuadro, una sola vez; buscar una skin ya cargada es O(7).
Evidencia: capturas del menú (tigre y otra skin) y de la sala con el tigre; prueba_vista_10 comprueba que la predeterminada es el tigre, que las flechas cambian de skin dando la vuelta sin encolar comandos, y que las 7 skins tienen 4 cuadros de reposo y uno de golpe (el tigre, con 4 cuadros distintos); las 12 pruebas y prueba_reglas pasan (116 archivos).
Límites: la skin no se guarda entre ejecuciones ni en el puntaje, así que un replay muestra la skin elegida ahora, no la que se usó en esa partida.

D64. Partida guardada: marca en el menú, X para empezar de cero, y se borra al terminar
Problema: el guardado (uno por cripta) nunca se borraba. Si se guardaba, se seguía jugando y se moría, al volver a esa cripta el menú reanudaba el guardado viejo de una partida ya terminada. Además, desde la ventana no había forma de pedir partida nueva si había un guardado, ni de saber que lo había.
Alternativas: (a) borrar el guardado siempre que termine una partida de esa cripta: si el jugador empezó una nueva con un guardado viejo y la terminó sin guardar, perdería ese guardado viejo sin haberlo usado. (b) borrarlo al empezar una partida nueva: perder el guardado por apretar una tecla es peor que conservarlo.
Decisión: ControladorJuego recuerda si ESTA partida usó el guardado (se cargó de él o se guardó durante ella), y solo entonces lo borra al ganar o morir. El puerto AlmacenPartida gana borrar(id_cripta), no abstracto (un almacén que no sepa borrar lo deja), y AlmacenPartidaDisco borra el .bin. CriptaVisible gana tiene_guardado (lo llena ConstructorEstadoVista con el GestorGuardado). La tarjeta de la cripta muestra "PARTIDA GUARDADA" y, si está elegida, "ENTER continúa · X empieza de cero". X manda "jugar" con el modo "nueva" (D52). El log y el replay no cambian: cada partida terminada ya tiene su log archivado (D61).
Complejidad: O(1); saber si una cripta tiene guardado es una consulta al sistema de archivos por cripta.
Evidencia: prueba_replay_menu guarda a medias y cierra; el menú nuevo marca la cripta; una partida nueva ganada sin guardar no borra el guardado viejo; ENTER retoma el guardado (mismo reloj y sala) y, al ganar, el guardado desaparece y la marca también. Dos mutaciones (borrar siempre y no borrar nunca) fueron detectadas. prueba_vista_10 cubre X y ENTER.
Límites: sigue habiendo un solo guardado por cripta: guardar una partida nueva reemplaza el anterior.

D65. Salir en medio de la partida vuelve al menú
Problema: ESC durante la partida cerraba toda la aplicación de golpe. Era fácil apretarlo sin querer y perder la sesión, y no quedaba claro qué pasaba con la partida.
Alternativas: (a) pedir confirmación con un segundo ESC: cambia la tecla que D45 y las pruebas de vista fijan (ESC manda "salir" en todas las pantallas). (b) guardar automáticamente al salir: sobrescribiría sin aviso un guardado que el jugador quizás quería conservar (hay uno solo por cripta, D64).
Decisión: la Vista no cambia (ESC sigue mandando "salir"). Cambia lo que hace ControladorMenu: durante la partida, "salir" abandona la partida (no hay puntaje, porque no terminó), reinicia el conteo de la sesión de red como al terminar una partida (§5.1) y vuelve al menú principal con un aviso: "tu partida guardada sigue ahí: ENTER la continúa" si había guardado, o "la partida sin guardar se descartó" si no. En el menú, ESC sigue cerrando el juego de forma controlada (§10.2), y su etiqueta dice "Salir del juego"; en el HUD, la de ESC dice "Volver al menú".
Complejidad: O(1) más mostrar el menú.
Evidencia: prueba_controlador (ESC en la partida vuelve al menú y un segundo ESC en el menú cierra) y prueba_replay_menu (con partida guardada: el aviso y la marca de la cripta); recorrido del juego real en una carpeta temporal: ESC en la partida deja la pantalla del menú con el aviso.
Límites: la partida abandonada no deja puntaje ni log archivado; su log activo queda en partidas/ hasta la próxima partida de esa cripta.

D66. Pantalla de título (bienvenida) antes del menú
Problema: el juego arrancaba directo en el menú, sin bienvenida ni ambientación.
Alternativas: (a) poner la bienvenida dentro del menú: lo recarga, y el menú ya tiene mucha información. (b) una pantalla que avanza sola tras unos segundos: el jugador no elige cuándo entrar.
Decisión: una PantallaTitulo propia. Muestra la entrada de la cripta, con el fondo armado una vez con baldosas de 0x72 (muro con estandartes, una gran puerta, piso con calaveras y sombra arriba), dos antorchas que parpadean con su resplandor, brasas que suben, el héroe con la skin elegida frente a la puerta junto al esqueleto guardián y una rata, el título "CRIPTA" con "Bienvenido, aventurero", una frase motivadora que cambia cada 7 s con un fundido (8 frases en una tupla, la primera al azar) y "Presiona ENTER para entrar", que late. ENTER manda Comando("entrar") y ControladorMenu muestra el menú; ESC sale del juego como en cualquier pantalla (D45). La pide FabricaAplicacion con con_pantalla_titulo=True; por defecto ControladorMenu va directo al menú, así las pruebas y otras Vistas no cambian. VistaJuego gana mostrar_titulo, no abstracto.
Complejidad: armar el fondo es O(baldosas) una vez; cada cuadro es O(brasas) (46).
Evidencia: capturas de la pantalla con dos frases distintas; prueba_vista_10 (ENTER manda "entrar", otras teclas nada, ESC "salir"); prueba_replay_menu (con título arranca en él, sin menú, y "entrar" muestra el menú); recorrido real con FabricaAplicacion: título, menú, partida, ESC al menú y ESC cierra.
Límites: el azar de la primera frase y de las brasas es solo de presentación (random.Random propio de la pantalla) y no afecta la semilla del juego (§2.6).

D67. Rastro del jugador: un solo instante por sala y caducidad al consultar

(§4.7.)

Problema: un rastreador que no comparte sala con el jugador va hacia la vecina con el rastro más fresco (§2.9). Decide cada vez que le toca actuar, y puede haber varios en la misma cripta. §4.7 pide que la decisión cueste según las salidas de su sala, no según el tamaño de la cripta ni lo largo del recorrido del jugador; que un rastro de 400 o más unidades ya no sirva; y que el trabajo por ciclo crezca a lo sumo lineal con los enemigos que actúan.
Alternativas:
(a) Guardar el recorrido como una lista de visitas (sala, instante) y buscar en ella la última visita de cada vecina. Es lo más directo de escribir, pero cada decisión recorre todo el recorrido: O(salidas × L). Medida.
(b) Borrar activamente los rastros vencidos con un evento de limpieza por sala visitada. Cumple la regla de 400, pero suma un evento a la agenda por cada paso del jugador (cientos por partida) solo para poner en None un campo que nadie mira hasta que pasa un rastreador, y el pergamino tendría que revertir también esos eventos.
(c) Recorrer el mundo buscando la sala con el rastro más fresco: O(salas), justo lo que §4.7 prohíbe.
Decisión: Sala.rastro es un solo entero, el instante de la última presencia del jugador. Se actualiza por el Mutador al entrar a una sala y en cada acción en ella (Apéndice B), así que el pergamino también lo revierte. La caducidad se detecta al consultar: rastro_fresco(reloj) devuelve None si no hay rastro o si reloj − rastro ≥ VIGENCIA_RASTRO (400). Rastreador.decidir_sin_jugador recorre solo vecinas_abiertas() de su sala (orden fijo N, S, E, O), pide rastro_fresco a cada destino y se queda con el mayor instante; si empatan, gana el menor id de sala destino (determinismo, §2.6). Sin ningún rastro fresco, espera.
Complejidad: consultar un rastro es O(1); una decisión es O(salidas), como mucho 4, sin depender de n salas ni de L pasos; k rastreadores que actúan cuestan O(k) por ciclo. Mantener el rastro es O(1) por acción del jugador y la memoria es un entero por sala, constante aunque la partida dure mucho.
Evidencia (--bench, benchRastro): en un pasillo de n salas después de un recorrido de L pasos, una decisión cuesta 0.64–0.70 µs con n = 50, 500 y 5000 y L = 100, 2000 y 20 000: no cambia con ninguno de los dos. La alternativa (a) cuesta 5.5 µs con L = 100, unos 99 µs con L = 2000 y 973–994 µs con L = 20 000 (hasta 1 477 veces más); no depende de n, pero crece lineal con el recorrido. Con k rastreadores en el mismo ciclo: 0.8 µs (k = 1), 7.0 µs (10), 63.7 µs (100) y 634 µs (1000), unos 0.63–0.80 µs por rastreador, es decir lineal; 1000 rastreadores usan el 3.2 % del presupuesto de 20 ms de §5.2. Antes de medir, el benchmark comprueba que sigue el rastro más fresco, que empata hacia el menor id y que un rastro de exactamente 400 unidades ya no se sigue.
Límites: solo se guarda la ÚLTIMA presencia por sala, así que un rastreador no puede reconstruir el camino completo del jugador. Basta para la regla de §2.9, pero si se pidiera seguir la ruta entera haría falta otra estructura. La alternativa (b) convendría si muchos actores consultaran el rastro de muchas salas a la vez y casi siempre estuviera vencido, cosa que con la regla de §2.9 (solo las vecinas) no pasa.

D68. Guardado binario con encabezado fijo e índice de salas al final

(§4.10.)

Problema: guardar la partida completa en un formato binario propio, poder recuperar UNA sala sin leer el archivo entero, detectar un archivo de otra versión del formato y comparar tamaño y tiempo contra JSON. El guardado se hace cuando el jugador aprieta G y la carga al reanudar (pocas veces por partida), pero el archivo tiene que reconstruir todo: salas, jugador, efectos, la agenda con sus referencias cruzadas y el estado del azar, para que la partida siga igual que si no se hubiera cortado.
Alternativas:
(a) JSON con json.dump: más simple y, en carga completa, más rápido (el parser está en C). Se descarta como formato principal porque §4.10 pide un binario propio y porque sin un índice la única forma de sacar una sala es leer y parsear todo el archivo. Medida.
(b) Binario sin índice, con las salas una tras otra: cumple el formato, pero cargar_sala tendría que leer todas las salas anteriores, O(tamaño del archivo).
(c) pickle: es un formato de Python, no propio, depende de los nombres de las clases y no detecta versiones de nuestro formato.
Decisión: PartidaBinaria escribe con EscritorBinario/LectorBinario (little-endian). El encabezado fijo va siempre al inicio: magic "CRPB", version_formato (uentero32) y offset_indice. Después van el encabezado lógico (cripta, versiones, semilla, reloj, fin, secuencia de la agenda, siguiente id de objeto y el estado del Random), el jugador, las salas una tras otra, los eventos pendientes y, al final, el índice de salas: (id_sala, offset, longitud) por sala. offset_indice se rellena al terminar, cuando ya se conoce. Las referencias cruzadas (dueño de un evento, evento de cierre de una puerta, etc.) se guardan con claves naturales (sala + id de instancia, o sala + dirección) y se reconectan en una última pasada. Al cargar, un magic distinto da "no es una partida de Cripta" y una versión distinta lanza VersionIncompatible, sin intentar leer el resto. cargar_sala lee el encabezado fijo, salta al índice, busca la sala y lee solo sus bytes.
Complejidad: guardar y cargar completo son O(S) en el tamaño del estado; cargar_sala es O(salas) para recorrer el índice más O(una sala) de lectura, sin leer las demás. Detectar la versión es O(1) (8 bytes).
Evidencia (--bench, benchGuardado, misma partida sintética guardada de las dos formas): el binario pesa 1.45–1.49 veces menos que el JSON (8 108 contra 11 717 bytes con 10 salas, 61 902 contra 92 503 con 200). En carga COMPLETA el JSON gana: 0.45 ms contra 3.05 ms con 200 salas, porque el parser de json está en C y nuestro lector en Python puro; el resultado se deja tal cual. La ventaja del binario es la carga parcial: cargar una sala cuesta 0.13–0.19 ms, de 2.8 veces (10 salas) a 16 veces (200 salas) menos que cargar todo, y la diferencia crece con la cripta. prueba_6_3 comprueba la carga de una sola sala y la detección de versión (corrompe a mano los bytes 4 a 8 del encabezado), y que guardar no altera una partida en curso.
Límites: con criptas de este tamaño la carga completa en JSON sería suficiente en tiempo (milisegundos en ambos casos); el binario se justifica por el tamaño, por la carga parcial y porque §4.10 lo pide. Recorrer el índice es lineal en salas: con decenas de miles de salas convendría ordenarlo por id y buscar por bisección. Un cambio de formato obliga a subir FORMATO_VERSION, y los guardados viejos dejan de cargarse (se informa, no se adivina).

D69. Inventario y bitácora en la interfaz: Tab, O y L

(§4.5, §4.8 y §10.2.)

Problema: el modelo ya tenía el recorrido del inventario (siguiente y anterior desde la posición actual), las vistas ordenadas por peso, valor y nombre sin tocar el orden real, y la bitácora de los últimos 20 mensajes. Pero la ventana solo mostraba el inventario en su orden real y los últimos 5 mensajes: §10.2 pide "recorrer y consultar el inventario, incluyendo vistas ordenadas", y §4.8 que la interfaz muestre los últimos 20.
Alternativas: (a) ordenar el inventario en la Vista: la Vista no decide órdenes y repetiría lo que ya hace el modelo con el selector de D42. (b) mostrar los 20 mensajes siempre en el panel de abajo: no caben sin achicar la letra hasta que no se lea. (c) una pantalla aparte para la bitácora: obliga a salir del juego para leerla.
Decisión: tres teclas nuevas en PantallaJuego. Tab y Shift+Tab mandan "inventario_siguiente" e "inventario_anterior", que mueven la posición actual del inventario en el modelo. O manda "ordenar_inventario" con el criterio siguiente (real → peso → valor → nombre → real), ControladorJuego recuerda ese criterio y ConstructorEstadoVista arma en cada turno la vista ordenada (Inventario.vista_ordenada, sin tocar el orden real); el panel la muestra marcando el objeto actual por su id_objeto. L muestra u oculta, sobre el mapa, la bitácora completa: los 20 mensajes de la ColaAcotada (D30). L es solo presentación: no manda ningún Comando, no toca la partida ni el log, y la preferencia la recuerda VistaArcade entre turnos. También funciona en el replay.
Complejidad: cada tecla es O(1) en la Vista; recorrer es O(1) en la ListaDoble (D28); una vista ordenada es la de D41 y D42 sobre el inventario (n de decenas); mostrar la bitácora es O(20).
Evidencia: prueba_vista_10 (sección 4b) comprueba que Tab, Shift+Tab y O mandan los comandos correctos y que O da la vuelta de nombre a real; la sección 4c, que L alterna la bitácora completa, no encola nada y se mantiene en el turno siguiente. Las 12 pruebas de la batería y prueba_reglas pasan.
Límites: la vista ordenada se vuelve a calcular en cada turno, O(n log n) con n de decenas; con inventarios de miles de objetos convendría recalcularla solo cuando el inventario cambia. El criterio vuelve a "real" al empezar o cargar una partida. Con mensajes muy largos, cada línea de la bitácora se recorta al ancho del mapa.

D70. Bitácora de partida de solo anexado y reproducción fiel

(§4.11.)

Problema: cada acción del jugador debe quedar en un archivo de texto de solo anexado, con un encabezado (cripta, versión de cripta, versión de catálogo y semilla), y --replay debe reproducir la partida completa sin interacción. Si la versión del log ya no está disponible, el programa debe decirlo y no reproducir contra datos distintos. Se escribe una línea por acción (cientos o miles por partida) y se lee completo una vez por replay.
Alternativas: (a) guardar fotos del estado en cada paso: es una copia del estado, prohibida por §4.6, y no prueba que las acciones reproduzcan la partida. (b) un log binario: más compacto, pero deja de ser texto legible para reportar errores, que es para lo que se evalúa (§4.11). (c) reescribir el log al cargar un guardado para quitar lo que la carga deshizo: rompe el solo anexado (por eso existe D49).
Decisión: RegistroArchivo escribe la primera línea "CRIPTA <cripta> <versión cripta> <versión catálogo> <semilla>" y luego una acción por línea con Accion.texto() ("MOVER N", "RECOGER 2"...), abriendo en modo "a" y sin releer nada. --replay (ModoReplay, con VistaNula) lee el encabezado, valida las versiones con motivo_version_incompatible (compartida con el replay en la ventana, D56) y, si no coinciden, informa el motivo y sale con código 1; si coinciden, rearma la partida con la misma semilla y aplica las acciones en orden. Guardar respalda el log y cargar lo restaura (D49); al terminar una partida, el log se archiva por partida para el replay desde los puntajes (D61).
Complejidad: anexar una acción es O(1); reproducir es O(A) acciones, cada una con su costo normal en el modelo (§5.2). Validar las versiones es O(1).
Evidencia: prueba_controlador termina una partida, la reproduce con --replay y compara el reloj final y el resultado; con una versión incompatible comprueba el mensaje y el código 1. prueba_replay_menu reproduce desde la tabla de puntajes la partida elegida y no la última. El replay de una victoria real en cripta-02 llegó exactamente al mismo final. --replay y --bench corren sin abrir ventana.
Límites: el replay depende de que el modelo sea determinista (Random propio con la semilla del log, orden fijo de salidas y desempates); cualquier fuente de azar nueva fuera de ese Random rompería la reproducción. Si la versión cambió y no hay copia local de esos datos, no se puede reproducir: se informa en vez de adivinar.

Nota sobre veneno y regeneración: el modelo implementa los dos mecanismos (EfectoVeneno con curar_veneno del antídoto, y EfectoRegeneracion en Enemigo), pero el contrato del API no trae hoy ningún campo que los active: Enemigo.regeneracion queda en 0 y ninguna ficha envenena. Se dejaron implementados y probados por si una cripta nueva los usa; con los datos actuales no aparecen en una partida.

Nota sobre la llave y la antorcha (no son decisiones nuestras): la llave NO se consume al abrir una puerta, como pide la guía ("La llave no se consume"), así que sigue en el inventario. La antorcha se gasta al usarla y dura 2000 unidades del reloj virtual, no una cantidad de salas: unos 20 movimientos de 100. El texto del efecto ahora lo dice ("quedan N de tiempo (~M movimientos)").
