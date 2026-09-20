# Cripta: guía de diseño MVC

Proyecto de Estructuras de Datos, II Ciclo 2026. Python 3.11+, grupos de hasta 4 personas, 15 % de la nota final.

Esta guía organiza el proyecto según las cuatro secciones que exige el enunciado (§6): Modelo, Vista, Controlador y Adaptadores. Para cada sección indica sus clases y lo que cada clase debe cumplir.

---

## 1. Resumen del proyecto

- Juego de mazmorra dirigido por eventos con un reloj virtual entero.
- Lo que se evalúa son las decisiones de estructuras de datos, justificadas con mediciones propias. Las reglas del juego están fijadas, las estructuras no.
- El contenido de las criptas viene de un API HTTP (o de un paquete offline) con un presupuesto limitado de solicitudes por cripta.
- La revisión se hace con una cripta nueva: no puede haber ids, cantidades de salas ni presupuestos escritos en el código.
- Pesos: cliente y presupuesto de red 25 %, juego funcional 20 %, caché, persistencia, retroceso y mediciones 25 %, Documento de Decisiones 15 %, rendimiento 15 %.

## 2. Reglas del juego (resumen)

- **Mundo:** salas conectadas por salidas N, S, E y O. Una salida puede no existir, estar abierta o estar cerrada con llave. No hay cuadrícula: todos los actores de una sala son adyacentes.
- **Reloj virtual:** siempre se ejecuta el evento con menor `(tiempo_siguiente, secuencia)`. Nunca se usa la hora real ni el orden de llegada de las respuestas HTTP.
- **Costos base:** mover, atacar y esperar 100. Usar y equipar 50. Abrir puerta con llave 50. Recoger y soltar 25.
- **Intervalo:** `max(1, costo * 100 // velocidad)`.
- **Cambio de velocidad:** reescala el tiempo restante con `max(1, (t_sig - t) * v_ant // v_nueva)` y asigna una secuencia nueva.
- **Activación de enemigos:** al entrar el jugador a su sala (los de la sala inicial, en t=0). Primera acción con costo 100. Si varios se activan a la vez, por id de instancia ascendente. Un enemigo activo que cambia de sala sigue activo.
- **Puertas:** abrir y atravesar son acciones distintas. La llave no se consume. Los enemigos no abren puertas. El cierre automático se programa como evento.
- **Contenido de la sala destino:** debe estar en memoria antes de confirmar el movimiento. Esperar la red nunca avanza el reloj.
- **Combate:** `daño = max(1, ataque + azar.randint(0, 4) - defensa)`, con un `random.Random(semilla)` propio (nunca el generador global). Al morir, un actor deja de ejecutar eventos y suelta sus objetos.
- **Enemigos:** si comparten sala con el jugador, atacan. Si no: el guardián espera, el errante sale al azar por una salida abierta (o espera), el rastreador sigue el rastro más fresco (menos de 400 unidades, empate por menor id) o espera.
- **Efectos:** veneno (daño cada 80, dura 400), velocidad temporal, antorcha, regeneración (cada 200), trampas (se activan al entrar, se desarman y se rearman a los 300), cierre de puerta.
- **Inventario:** tope `inventario_max`, una posición por objeto, como máximo un arma y una armadura equipadas. Equipar mueve el objeto al frente.
- **Pergamino de retroceso:** revierte hasta antes de la última acción del jugador, como máximo 5 acciones hacia atrás. No consume tiempo ni cuenta como acción. Su cantidad y la caché quedan fuera de la reversión. Prohibido guardar copias completas del estado.
- **Fin:** derrota si la vida llega a 0. Victoria al entrar a la sala de salida tras abrir con la llave correspondiente. Se registra nombre, cripta y versión, acciones, enemigos derrotados y tiempo final.
- **Determinismo:** misma cripta, semilla y secuencia de acciones producen la misma partida.
- **Apéndice B:** recoger con el inventario lleno o abrir sin la llave se rechazan sin consumir tiempo. Dos pergaminos seguidos retroceden dos acciones.

## 3. Restricciones y condiciones

- **Estructuras propias:** prohibido usar `dict` como índice, caché o tabla de búsqueda (solo se permite para leer el JSON). `list` solo como almacenamiento contiguo. Permitidos `struct`, `json`, `requests` y bibliotecas de interfaz.
- **Ordenamientos de §4.9:** prohibido `list.sort()` y `sorted()`.
- **Azar:** solo una instancia propia de `random.Random(semilla)`.
- **Red:**
  - `X-Cripta-Client-Id` (UUID) generado una vez por ejecución.
  - HTTP 429: esperar `reintentar_en` y reintentar, sin caerse. El reintento cuenta.
  - Timeout explícito y errores con contexto.
  - Cada solicitud tarda unos 400 ms sin importar cuántos elementos traiga.
  - Contenido y catálogo aceptan hasta 10 elementos por solicitud.
- **Presupuesto:** `presupuesto_solicitudes` viene en los datos de cada cripta. Cuenta toda solicitud (lista de criptas, datos generales, páginas, contenido, catálogo, verificaciones de versión y reintentos). Las lecturas de disco y `--offline` no cuentan.
- **Rendimiento:** un ciclo completo de eventos entre dos decisiones del jugador debe tomar menos de 20 ms, sin contar red ni render.
- **Modos:** `--offline`, `--replay partida.log`, `--bench` y `--cache-size N` (25 por defecto). `--replay` y `--bench` deben correr sin instanciar la vista interactiva.

---

## 4. Arquitectura: MVC más adaptadores

```
   ┌──────────────────────────────────────────────────────────────┐
   │ VISTA                                                        │
   │ VistaJuego · VistaConsola · VistaNula · EstadoVista · Comando │
   └───────────────────────────┬──────────────────────────────────┘
                               │ Comando  /  EstadoVista
   ┌───────────────────────────▼──────────────────────────────────┐
   │ CONTROLADOR                                                  │
   │ ControladorJuego · TraductorComandos · GestorGuardado        │
   │ ModoReplay · ModoBench · FabricaAplicacion                   │
   └───────────────────────────┬──────────────────────────────────┘
                               │ Accion  /  estado del modelo
   ┌───────────────────────────▼──────────────────────────────────┐
   │ MODELO (sin red, archivos ni interfaz)                       │
   │ Partida · Agenda y Eventos · Actores · Sala y Mundo          │
   │ Inventario · Diario y Cambios · ServicioDatos · CacheFichas  │
   │ Estructuras propias                                          │
   │ [ Puertos (interfaces): FuenteDatos, AlmacenLocal, ... ]     │
   └───────────────────────────▲──────────────────────────────────┘
                               │ implementan los puertos
   ┌───────────────────────────┴──────────────────────────────────┐
   │ ADAPTADORES (red y disco)                                    │
   │ ClienteHttp · FuenteOffline · ContadorRed · AlmacenLocalDisco│
   │ PartidaBinaria · PartidaJson · RegistroArchivo · Puntajes    │
   └──────────────────────────────────────────────────────────────┘
```

### Regla de oro de cada sección

| Sección | Puede conocer | No puede conocer |
|---|---|---|
| Vista | `EstadoVista` y `Comando` | El modelo, la red y el disco |
| Controlador | El modelo, la interfaz `VistaJuego` y los puertos | Detalles de HTTP, formatos de archivo, `print` e `input` |
| Modelo | Solo sus propias clases y sus puertos | `requests`, `open()`, la vista y el controlador |
| Adaptadores | Los puertos del modelo, `requests`, `struct`, `json` y el disco | Reglas del juego |

---

## 5. MODELO

Reglas del juego, entidades y estructuras de datos propias.

### 5.1 Núcleo de la partida

| Clase | Funcionalidades a cumplir | Ref. |
|---|---|---|
| `Partida` | Fachada del modelo y dueña del estado (reloj, semilla, `random.Random(semilla)`, agenda, jugador, mundo). `iniciar(cripta, semilla)`: reloj en 0, jugador en la sala inicial con acción en t=0, rastro de la sala inicial en 0, activa sus enemigos. `aplicar_accion(accion)`: valida, ejecuta, programa la siguiente acción del jugador y procesa eventos hasta su próxima decisión. También `deshacer()`, `terminada()`, `resultado()`, `exportar_estado()` y `cargar_estado()`. | §2.3, 2.4, 2.12 |
| `Accion` (`Mover`, `AbrirPuerta`, `Atacar`, `Esperar`, `Recoger`, `Soltar`, `Usar`, `Equipar`, `UsarPergamino`) | Objeto inmutable con tipo, argumentos y `costo_base`. | §2.3 |
| `ResultadoAccion` | Aceptada o rechazada, con motivo y mensajes generados. Un rechazo no consume tiempo. | Ap. B |
| `ValidadorAcciones` | Precondiciones: la salida existe y está abierta, la llave es la correcta, el inventario no está lleno, el objetivo está en la misma sala, el contenido de la sala destino está en memoria. | §2.5, Ap. B |
| `Combate` | `calcular_dano` con la fórmula de §2.6. `resolver_ataque` aplica el daño, mata al actor si la vida llega a 0 y suelta sus objetos al suelo. | §2.6 |
| `TablaPuntajes` y `RegistroPuntaje` | Guardan nombre, cripta y versión, acciones, enemigos derrotados y tiempo final. Vista ordenada con `Ordenamiento`. | §2.12 |

### 5.2 Reloj, eventos y efectos

| Clase | Funcionalidades a cumplir | Ref. |
|---|---|---|
| `Agenda` | Cola de prioridad por `(tiempo, secuencia)`. `programar`, `extraer_siguiente`, `cancelar`, `reprogramar` y contador de secuencia. Obtener el siguiente evento no puede examinar todos los pendientes. | §2.3, 4.1 |
| `Evento` (abstracta) | Guarda tiempo, secuencia, dueño y bandera `cancelado`. Define `ejecutar(partida)`. | §2.3 |
| `EventoAccionActor` | Turno de un actor. El jugador espera una decisión, el enemigo decide según su comportamiento. Luego se reprograma con `max(1, costo * 100 // velocidad)`. | §2.3, 2.8 |
| `EventoVeneno` | Daño cada 80 unidades durante 400. Un antídoto lo cancela. | §2.10 |
| `EventoCambioVelocidad` | Inicio y fin del efecto. Reescala el tiempo restante y asigna una secuencia nueva. | §2.3, 2.10 |
| `EventoApagarAntorcha`, `EventoRegeneracion`, `EventoRearmeTrampa`, `EventoCierrePuerta` | Ejecutan el efecto de §2.10. La regeneración no supera `vida_max`. El rearme dura 300 salvo que la ficha diga otro valor. | §2.10 |
| `Efecto` | Maneja un efecto activo y guarda sus eventos para cancelarlos sin recorrer la agenda: `aplicar`, `cancelar`, `terminar`. | §4.1 |

### 5.3 Mundo

| Clase | Funcionalidades a cumplir | Ref. |
|---|---|---|
| `Mundo` | Guarda las salas indexadas por id (con estructura propia), la sala inicial, la de salida, la llave de salida, `inventario_max` y las estadísticas del jugador. `sala(id)`, `agregar_esqueleto`, `incorporar_contenido`, `tiene_contenido(id)`, `vecinas(id)`. | §2.1, 3.3 |
| `Sala` | Id, nombre, 4 salidas, enemigos dormidos y activos, objetos del suelo, trampas y rastro. `marcar_rastro(t)`, `rastro_fresco(reloj)` (menos de 400, caducidad detectada al consultar), `vecinas_abiertas()`, `activar_enemigos()` por id ascendente. | §2.4, 2.9, 4.7 |
| `Salida` | Destino, cerrada, llave y cierre automático. `abrir(reloj)` (programa el cierre), `cerrar()`, `transitable()`. | §2.5 |
| `Trampa` | Se activa al entrar el jugador, justo después del movimiento y antes del siguiente evento. Aplica su efecto, se desarma y programa el rearme. | §2.10 |

### 5.4 Actores

| Clase | Funcionalidades a cumplir | Ref. |
|---|---|---|
| `Actor` (abstracta) | Id de instancia, ficha, vida, `vida_max`, ataque, defensa, velocidad, sala y si está vivo. `recibir_dano`, `curar` (sin pasar de `vida_max`), `cambiar_velocidad`, `morir()` (cancela sus eventos futuros). | §2.2 |
| `Jugador` | Inventario, equipo, efectos activos y contadores (acciones y enemigos derrotados). `ataque_efectivo()` y `defensa_efectiva()` con bonos de equipo. | §2.7 |
| `Enemigo` | Ficha, vida inicial (puede ser menor que `vida_max`), estado activo, comportamiento, regeneración y lista `suelta`. `activar(reloj)` programa su primera acción con costo 100. | §2.4 |
| `Guardian`, `Errante`, `Rastreador` (estrategias) | `decidir(enemigo, partida)` devuelve una `Accion`. Si comparten sala con el jugador, atacan. El guardián espera. El errante elige al azar entre las salidas abiertas (o espera). El rastreador examina solo las vecinas abiertas y toma el rastro más fresco (menos de 400, empate por menor id), o espera. | §2.8, 2.9 |

### 5.5 Objetos e inventario

| Clase | Funcionalidades a cumplir | Ref. |
|---|---|---|
| `Objeto` y sus clases (`Arma`, `Armadura`, `Pocion`, `Antidoto`, `Llave`, `Antorcha`, `PergaminoRetroceso`) | Instancias que referencian su ficha. `usar` o `equipar` según la clase: la poción cura sin pasar de `vida_max` o cambia la velocidad, el antídoto cancela el veneno, la llave no se consume, la antorcha programa su apagado y el pergamino invoca `deshacer`. | §2.7 |
| `Inventario` | Estructura secuencial con cursor. `recoger` se rechaza si está lleno, `soltar_actual` no depende de la posición, `siguiente` y `anterior` recorren en ambos sentidos, `equipar` mueve el objeto al frente. `vista_ordenada` (peso, valor o nombre) sin alterar el orden real. `cantidad_pergaminos()`. | §2.7, 4.5 |
| `Equipo` | Máximo un arma y una armadura. Equipar otra del mismo tipo sustituye a la anterior, que sigue en el inventario. | §2.7 |

### 5.6 Retroceso y mensajes

| Clase | Funcionalidades a cumplir | Ref. |
|---|---|---|
| `Diario` | Guarda como máximo 5 intervalos de decisión. `abrir_intervalo()`, `registrar(cambio)`, `cerrar_intervalo()` y `deshacer()`, que revierte en orden inverso. Descarta el intervalo más antiguo al pasar de 5. Excluye los pergaminos de la reversión. Prohibido guardar copias completas del estado. | §2.11, 4.6 |
| `Cambio` (abstracta) y subclases (`CambioVida`, `CambioReloj`, `CambioAgenda`, `CambioInventario`, `CambioSuelo`, `CambioPuerta`, `CambioTrampa`, `CambioRastro`, `CambioUbicacion`) | Cada uno guarda el valor anterior y sabe hacer `revertir()`. Toda mutación del modelo debe pasar por un único punto que la registre. | §2.11 |
| `Bitacora` | Buffer circular de 20 mensajes con memoria constante. `agregar(msg)` y `ultimos()`. | §4.8 |

### 5.7 Servicio de datos

| Clase | Funcionalidades a cumplir | Ref. |
|---|---|---|
| `ServicioDatos` | Orquesta caché, disco y red. `iniciar_cripta(id)`: datos generales, esqueleto por páginas y validación de las versiones persistidas. `asegurar_contenido(salas)`, `precargar(sala_actual)`, `contenido_listo(id)` y `esperar_contenido(id)` (espera sin mover el reloj). `resolver_fichas(ids)` pide en lotes de 10 sin repetir. `incorporar_pendientes()` procesa las respuestas en orden de solicitud. | §4.2, 4.3 |
| `PlanificadorPrecarga` | Elige las hasta 10 salas del siguiente lote por cercanía (recorrido en anchura sobre el esqueleto) y no repite salas ya pedidas. | §4.2 |
| `CacheFichas` | Memoria acotada por `--cache-size`. `obtener(id)` rápido, `insertar`, `fijar` y `soltar_referencia` (las fichas en uso no se desalojan), política de desalojo justificada, conteo de aciertos y fallos. Recupera fichas liberadas desde `AlmacenLocal` (disco, no red). | §4.4 |
| `Ficha`, `FichaEnemigo`, `FichaObjeto`, `FichaTrampa` | Datos compartidos e inmutables del catálogo. | §3.2 |
| `DatosCriptaDTO`, `SalaDTO`, `ContenidoSalaDTO`, `FichaDTO` | Objetos simples que devuelven los puertos. Se traducen a entidades una sola vez, al cargar. | §3.3 |

### 5.8 Estructuras propias y puertos

| Clase | Funcionalidades a cumplir | Ref. |
|---|---|---|
| `MonticuloBinario`, `TablaHash`, `ListaDoble` (con `Nodo`), `BufferCircular`, `Pila`, `Cola` | Estructuras implementadas por ustedes. Nada de `dict` como índice ni `list.pop(0)` como cola. | §7 |
| `Ordenamiento` (`insercion`, `mezcla` o `rapido`, `SelectorOrdenamiento`) | Al menos dos algoritmos distintos. El selector elige solo según tamaño, grado de orden y costo de comparación. Prohibido `sort` y `sorted`. | §4.9 |
| `FuenteDatos` (puerto) | `listar_criptas`, `datos_generales`, `esqueleto(pagina)`, `contenido(salas)`, `catalogo(ids)`, `version_cripta`, `version_catalogo`. Mismo contrato para HTTP y offline. | §3, 6 |
| `AlmacenLocal`, `AlmacenPartida`, `RegistroAcciones`, `AlmacenPuntajes` (puertos) | Respectivamente: fichas y contenido persistidos por versión; `guardar`, `cargar` y `cargar_sala`; `abrir`, `anexar` y `leer`; `cargar` y `guardar`. | §4.4, 4.10, 4.11 |
| `ErrorDeRed`, `PresupuestoAgotado`, `VersionIncompatible` | Excepciones con contexto de la operación que falló. | §3.1 |

---

## 6. VISTA

Presenta el estado y recoge la interacción. No calcula nada y nunca importa el modelo.

| Clase | Funcionalidades a cumplir | Ref. |
|---|---|---|
| `VistaJuego` (interfaz) | `mostrar_estado(EstadoVista)`, `mostrar_mensajes`, `pedir_comando()`, `mostrar_menu(criptas)`, `mostrar_puntajes`, `mostrar_fin` y `mostrar_error`. | §6 |
| `VistaConsola` | Muestra la sala actual, las salidas (abierta, cerrada o con llave), los enemigos identificables ("Rata gigante #1"), los objetos del suelo, la vida y estadísticas, los efectos activos y los últimos 20 mensajes. Muestra el inventario con cursor y vistas ordenadas. Convierte lo que escribe el usuario en un `Comando`. | §10.2 |
| `VistaNula` | Implementa la interfaz sin mostrar nada, para que `--replay` y `--bench` no necesiten vista interactiva. | §6 |
| `EstadoVista` | Foto de solo lectura con todo lo que la vista necesita mostrar. | §10.2 |
| `Comando` | Verbo y argumentos como los escribió el usuario, sin interpretar. | |
| `Etiquetador` | Genera los nombres "Rata gigante #1", "#2"... para distinguir instancias. | §2.6 |

## 7. CONTROLADOR

Traduce las acciones del usuario en operaciones del modelo y coordina el flujo de la aplicación.

| Clase | Funcionalidades a cumplir | Ref. |
|---|---|---|
| `ControladorJuego` | Bucle interactivo: pide el comando, lo traduce, llama a `Partida.aplicar_accion`, registra en el log y actualiza la vista. Detecta victoria o derrota y guarda el puntaje. | §6 |
| `TraductorComandos` | Convierte `Comando` en `Accion`, resolviendo el objetivo (enemigo elegido, objeto bajo el cursor, dirección). Reporta errores de sintaxis al usuario. | §10.2 |
| `ConstructorEstadoVista` | Arma el `EstadoVista` a partir del modelo. | §10.2 |
| `ControladorMenu` | Elegir cripta, partida nueva o cargada, ver puntajes y salir de forma controlada. | §10.2 |
| `GestorGuardado` | Guarda y carga vía `AlmacenPartida`, incluida la carga de una sala específica. | §4.10 |
| `ModoReplay` | Lee el log, valida versiones (si no puede garantizar fidelidad, lo reporta) y reproduce sin vista. | §4.11 |
| `ModoBench` | Ejecuta cargas sintéticas y reporta tiempos de agenda, caché, fichas liberadas, inventario, retroceso, ordenamientos y guardado contra JSON. | §5.3 |
| `FabricaAplicacion` (`main.py`) | Lee `--offline`, `--replay`, `--bench` y `--cache-size`, elige los adaptadores e inyecta dependencias. Es el único lugar donde se decide HTTP u offline. | §6 |
| `ReporteFinal` | Reporta solicitudes realizadas, presupuesto, aciertos y fallos de caché. | §5.1 |

## 8. ADAPTADORES

Acceso a red y a disco detrás de interfaces. No contienen reglas del juego.

| Clase | Funcionalidades a cumplir | Ref. |
|---|---|---|
| `ClienteHttp` (implementa `FuenteDatos`) | `X-Cripta-Client-Id` único por ejecución, timeout explícito y manejo de 429 (espera `reintentar_en`, y el reintento cuenta). Reporta los errores con contexto. Permite solicitudes anticipadas con una cola FIFO. | §3.1, 4.2 |
| `FuenteOffline` | Lee el paquete de respuestas desde disco por el mismo contrato lógico. No cuenta como red. | §3.4 |
| `ContadorRed` (decorador de `FuenteDatos`) | Cuenta toda solicitud, incluidos reintentos, verificaciones de versión y la lista de criptas. Compara con `presupuesto_solicitudes` y falla con claridad al agotarse. | §5.1 |
| `AlmacenLocalDisco` | Persiste fichas, esqueleto y contenido, validando con la versión de catálogo y de cripta. Sobrevive al cierre del programa. | §4.4 |
| `PartidaBinaria` | Formato propio con `struct`: cabecera con versión de formato, tabla de offsets por sala y secciones. Detecta incompatibilidad. `cargar_sala` sin leer todo el archivo. | §4.10 |
| `PartidaJson` | El mismo estado en JSON, solo para comparar tamaño y tiempo en `--bench`. | §4.10 |
| `RegistroArchivo` | Log de texto solo anexado, con encabezado (id y versión de cripta, versión de catálogo, semilla). Lo lee también el replay. | §4.11 |
| `PuntajesArchivo` | Tabla de puntajes local. | §2.12 |

---

## 9. Recorrido de una acción del jugador

1. **Vista:** `VistaConsola` lee lo que escribe el usuario y produce un `Comando`.
2. **Controlador:** `TraductorComandos` lo convierte en una `Accion` y la envía a `Partida`.
3. **Modelo:** `Partida` valida, ejecuta y registra los cambios en el `Diario`. Si falta el contenido de la sala destino, `ServicioDatos` lo pide a los adaptadores y espera sin mover el reloj.
4. **Modelo:** la `Agenda` entrega eventos en orden hasta la próxima decisión del jugador.
5. **Controlador:** anexa la acción al log (`RegistroArchivo`) y arma el `EstadoVista`.
6. **Vista:** dibuja el estado y los últimos 20 mensajes.

## 10. Estructura de carpetas sugerida

```
cripta/
  modelo/
    nucleo/        partida, acciones, validador, combate, puntajes
    reloj/         agenda, eventos, efectos
    mundo/         mundo, sala, salida, trampa
    actores/       actor, jugador, enemigo, comportamientos
    objetos/       objetos, inventario, equipo
    retroceso/     diario, cambios
    datos/         servicio_datos, cache_fichas, precarga, fichas, dto
    estructuras/   monticulo, tabla_hash, lista_doble, buffer_circular, ordenamiento
    puertos/       fuente_datos, almacen_local, almacen_partida, registro_acciones, errores
  vista/           vista_juego, vista_consola, vista_nula, estado_vista, comando
  controlador/     controlador_juego, traductor, constructor_estado, gestor_guardado,
                   modo_replay, modo_bench
  adaptadores/     cliente_http, fuente_offline, contador_red, almacen_local_disco,
                   partida_binaria, partida_json, registro_archivo
  main.py          fábrica: flags y composición
```

## 11. Problemas de §4 y hipótesis inicial de estructura

Son hipótesis de partida. El Documento de Decisiones exige medir cada una contra al menos una alternativa descartada con `--bench`.

| Problema | Operación que domina | Estructura candidata | Alternativa a medir |
|---|---|---|---|
| 4.1 Agenda | Extraer el mínimo, cancelar y reprogramar, decenas de miles de veces | Heap binario propio con clave `(tiempo, secuencia)` y cancelación perezosa | Lista ordenada o búsqueda lineal |
| 4.2 Precarga | Elegir hasta 10 salas por lote | Recorrido en anchura desde la sala actual sobre el esqueleto (cola propia) | Pedir sala por sala al entrar |
| 4.3 Catálogo | Juntar ids sin repetir | Cola de ids pendientes y conjunto propio, en lotes de 10 | Un id por solicitud |
| 4.4 Caché | Búsqueda muy frecuente y desalojo de fichas sin uso | Tabla hash propia, lista enlazada de uso (tipo LRU) y contador de referencias | Búsqueda lineal, FIFO |
| 4.5 Inventario | Recorrer en ambos sentidos, soltar en cualquier posición, equipar al frente | Lista doblemente enlazada con cursor | `list` de Python (soltar cuesta O(n)) |
| 4.6 Retroceso | Registrar y revertir cambios de hasta 5 acciones | Pila acotada de registros de cambio inverso | Otra granularidad de registro (las copias completas están prohibidas) |
| 4.7 Rastro | Decidir en O(salidas) | Un campo de rastro por sala, con caducidad detectada al consultar | Limpieza activa con eventos |
| 4.8 Bitácora en pantalla | Agregar un mensaje con memoria constante | Buffer circular de 20 | `list` con `pop(0)` |
| 4.9 Ordenamiento | Puntajes, vistas del inventario, índices | Inserción (pocos o casi ordenados) y mezcla o rápido (grandes), con selector automático | Un solo algoritmo para todo |
| 4.10 Guardado binario | Leer una sala sin cargar todo el archivo | Cabecera con versión, tabla de offsets y `struct` | JSON |
| 4.11 Replay | Anexar acciones y reproducir | Log de texto solo anexado con encabezado | Sin alternativa relevante |

## 12. Decisiones por tomar (y documentar) antes de programar

- **Generador aleatorio al deshacer:** decidir si el pergamino restaura el estado del `Random`. Propuesta: guardar `azar.getstate()` al abrir cada intervalo. Es solo el generador, no una copia del estado del juego, y así lo re-jugado es coherente con el log.
- **Contador de secuencia:** también debe restaurarse al deshacer, o el desempate de eventos cambia después de un retroceso.
- **Pergamino en el log:** aunque no cuente como acción en el historial de retroceso, debe quedar en el log de partida para que `--replay` lo reproduzca.
- **Veneno:** decidir si el último pulso cae exactamente en t+400 (pulsos en 80, 160, 240, 320 y 400) y dejarlo escrito.
- **Mensajes de la bitácora:** decidir si el retroceso los revierte. Propuesta: no, porque son presentación.
- **Rastro:** §2.9 dice que se actualiza al completar un movimiento, y el Apéndice B dice que el de la sala actual se refresca en cada acción del jugador. Propuesta: seguir el Apéndice B y confirmarlo con el profesor.
- **Sin `dict`:** hasta `id de sala -> Sala` necesita una estructura propia. No asumir que los ids son consecutivos.
- **Respuestas de red:** una opción simple es un hilo de fondo con cola FIFO, incorporando siempre en orden de solicitud y bloqueando la acción si falta el contenido.
- **Campos del catálogo:** revisar en el Swagger los nombres exactos (veneno, regeneración, modificador de velocidad).

## 13. Entregables y evaluación

- Repositorio en GitHub con README ejecutable desde un entorno limpio (versión de Python, dependencias, comandos, `--offline`, `--replay`, `--bench`, ubicación de archivos generados).
- `PROMPTS_LLM.md`: bitácora obligatoria de prompts (fecha, herramienta, prompt textual y para qué se usó la respuesta).
- Documento de Decisiones: una sección por problema de §4 con problema, alternativas (al menos dos), decisión, análisis de complejidad, evidencia con `--bench` (midiendo al menos una alternativa descartada) y límites conocidos.
- Al terminar cada partida: reportar solicitudes realizadas, presupuesto, aciertos y fallos de caché.
- Defensa con una cripta nueva. Cada integrante debe poder explicar cualquier decisión.

## 14. Orden de trabajo sugerido

1. Puerto `FuenteDatos`, cliente HTTP, modo offline y conteo del presupuesto.
2. Agenda y reloj virtual, con su medición en `--bench`.
3. Mundo, actores, combate y comportamientos.
4. Diario de retroceso.
5. Caché persistente e inventario.
6. Guardado binario, replay y ordenamientos.
7. Vista de consola.
