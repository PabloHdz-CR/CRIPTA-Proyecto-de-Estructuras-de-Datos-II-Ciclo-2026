---
description: "Lista de tareas de Resolubilidad"
---

# Tasks: Resolubilidad

**Input**: Design documents from `specs/003-resolubilidad/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: se piden de forma explícita (constitución, "Flujo y definición de hecho"; spec SC-001). En cada fase, las pruebas se escriben **antes** del código, citan los FR-xxx y la marca `# H<historia>.E<n>` de cada escenario (tabla en plan.md), y **deben fallar** antes de implementar. La tarea "confirmar que fallan" deja anotado en el commit por qué falla cada una.

**Organization**: una fase por historia de usuario de spec.md. Cada fase termina con la suite en verde y **un commit**. La historia 4 (datos de llaves, P2) va **antes** que las historias 2 y 3: las dos necesitan la consulta de llaves para iniciar una partida o verificar desde la terminal. La historia 1 no la necesita (verifica sobre datos en memoria).

**Regla de la spec (principio VII)**: si al implementar cualquier tarea aparece algo que contradice spec.md (un escenario imposible, un FR ambiguo, una cifra que no se puede cumplir), **se para**. Se enmienda spec.md en un commit propio, se ajusta plan.md o research.md si hace falta, y recién entonces se sigue. Nunca se cambia una regla, un umbral ni una prueba en silencio para que pase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (otro archivo y sin dependencias pendientes).
- **[Story]**: historia a la que pertenece (US1 a US5).
- **[EQUIPO]**: la hace el equipo, no el agente (necesita red o una decisión humana).
- Cada tarea cita los FR-xxx que cubre y la ruta exacta del archivo.

## Path Conventions

Proyecto único (plan.md, "Project Structure"): código en `cripta/`, pruebas en
`pruebas/` (scripts `py -m pruebas.<nombre>` con `assert`, que se registran en
`PRUEBAS` de `pruebas/ejecutar_pruebas.py`), mediciones en
`cripta/controlador/bench/`. Las pruebas pueden usar estructuras de Python; el
código de `cripta/` no puede usar dict, set, list, heapq, bisect, collections
ni sorted (`prueba_reglas`). Una prueba **salta** imprimiendo el motivo y
saliendo con código 0 (el ejecutor solo mira el código de salida).

---

## Phase 1: Setup (línea base, datos y ayudas de prueba)

**Purpose**: dejar la línea base verde, la descarga de llaves y el paquete sin conexión que usan las pruebas.

- [ ] T001 Confirmar la línea base antes de cambiar código: `py pruebas/ejecutar_pruebas.py` completa y en verde con las **46** pruebas de `main`, y `py -m pruebas.prueba_reglas` sin hallazgos. Si algo falla, se corrige o se documenta en este mismo commit antes de seguir.
- [ ] T002 [P] Extender `guardar_respuestas.py` para descargar `GET /criptas/<id>/llaves` y guardarlo tal cual en `datos_offline/criptas/<id>/llaves.json` (contracts/datos-llaves.md, "Paquete sin conexión"). Actualizar el docstring con el archivo nuevo. Contar la solicitud igual que las demás y respetar 429. FR-025, FR-029.
- [ ] T003 [EQUIPO] Regenerar `datos_offline/` con las versiones de la segunda parte ejecutando `python guardar_respuestas.py` (necesita red y que el servicio ya publique `/llaves`; depende de T002). Comprobar que cada `criptas/<id>/version.json` cambió respecto de la Parte I y que cada cripta tiene `llaves.json`. Commit propio: "Datos sin conexión de la Parte II con ubicación de llaves". **No bloquea** las fases 2 a 7; **sí bloquea** T062 (H5.E1 obligatorio). Mientras no se haga, H5.E1 salta con "SIN DATOS" y el juego con `datos_offline/` exige `--forzar` (research.md R12). **Después de regenerar**: correr la suite completa y `py main.py --bench --rapido`, y documentar en el commit lo que cambie respecto de la Parte I (pruebas o tablas que dependan de `datos_offline/`, como la cripta de referencia de `benchCazador`, y cifras distintas). Si una prueba falla por los datos nuevos, se investiga antes de seguir.
- [ ] T004 [P] Crear el paquete sin conexión `pruebas/datos/resolubilidad/` con el formato de FuenteOffline (`criptas.json`, `catalogo/version.json`, fichas de llave y de enemigo, y por cripta `general.json`, `version.json`, `esqueleto/pagina_1.json`, `contenido/<sala>.json`, `llaves.json`). Ids sintéticos (`res-...`), nunca de criptas publicadas (FR-036). Criptas:
  - `res-cadena`: llave A abre la zona de B y B la de llave_salida; la puerta de llave_salida lleva a sala_salida (H1.E4, resoluble).
  - `res-autociclo`: llave_salida detrás de la única puerta que ella abre (H1.E1).
  - `res-ciclo-dos`: k_a detrás de la puerta de k_b y viceversa (H1.E8).
  - `res-errante`: la llave la suelta un enemigo errante que inicia en una sala alcanzable (H1.E2, resoluble).
  - `res-sin-llaves`: igual a `res-cadena` pero **sin** `llaves.json` (FR-029, FR-031).
  Cada cripta debe poder jugarse (contenido de todas las salas y fichas del catálogo).
- [ ] T005 [EQUIPO] Confirmar con Pablo las letras que usan sus features de niebla, ir a y línea de tiempo, y dejar la respuesta anotada en este archivo. Si alguna es V, se para y se enmiendan la aclaración 4 y FR-037 de spec.md en un commit propio antes de implementar la tecla. **Bloquea T040**. FR-037.

**Checkpoint**: línea base verde; commit "Setup de resolubilidad: descarga de llaves y paquete de prueba".

---

## Phase 2: Foundational (tipos compartidos)

**Purpose**: los tipos de datos que comparten todas las historias y las ayudas de prueba que dependen de ellos (incluido el oráculo). Los tipos no tienen lógica, así que no llevan prueba propia: los ejercen las pruebas de la fase 3.

- [ ] T006 Agregar `UbicacionLlaveDTO` (`@dataclass(frozen=True)`) en `cripta/modelo/puertos/dto.py` con los campos de data-model.md §1: `id: str` ("id de la llave, texto no vacío (FR-030)"), `sala: int` ("sala del suelo, o sala donde **inicia** el enemigo; entero, sin bool"), `enemigo: str | None` ("id de la instancia que la suelta; None si está en el suelo"), con `enemigo = None` por omisión. FR-004, FR-025.
- [ ] T007 Crear el paquete `cripta/modelo/resolubilidad/` (`__init__.py`) y `cripta/modelo/resolubilidad/resultadoResolubilidad.py`:
  - constantes de veredicto `RESOLUBLE`, `NO_RESOLUBLE`, `NO_VERIFICADA` y de motivo `LLAVE_SALIDA_NO_OBTENIBLE`, `SIN_PUERTA_DE_SALIDA`;
  - las clases inmutables `ResultadoResolubilidad`, `LlaveOrdenada`, `LlaveNoObtenible`, `PuertaFrontera`, `PasoCiclo` y `CicloLlaves`, con exactamente los campos de data-model.md §3 y colecciones `ListaEnlazada`;
  - docstrings y tipos en toda firma pública.
  FR-007, FR-011 a FR-015, FR-031.

- [ ] T008 [P] Crear `pruebas/apoyo_resolubilidad.py` (no va en la suite, como `apoyo_terreno.py`):
  - una descripción compacta de cripta: salas con salidas `(dir, destino, cerrada, llave, cierre_automatico)`, sala_inicial, sala_salida, llave_salida y ubicaciones `(id, sala, enemigo)`;
  - conversión a `SalaDTO`, `DatosCriptaDTO` y `UbicacionLlaveDTO` en `ListaEnlazada`, con una opción para **desordenar** salas, salidas de páginas y entradas de llaves (FR-010, SC-004);
  - `FuenteMemoria` con `llaves()` y un contador de llamadas;
  - un generador de criptas pequeñas al azar con `random.Random(semilla)` (de 3 a 12 salas, de 0 a 5 llaves; puertas de una sola cara, sin llave, con cierre automático; llaves repetidas, de enemigo e inexistentes; R13);
  - reexporta `VistaRegistradora` de `apoyo_terreno.py`.
  Depende de T006.
- [ ] T009 [P] Crear `pruebas/oraculo_resolubilidad.py` con las definiciones **literales** de la spec, sin optimizar (research.md R13). Arma un `ResultadoResolubilidad` (T007) que se formatea con el mismo formateador del programa:
  - **orden**: en cada paso, recorrido desde cero con las llaves ya ordenadas; se elige la disponible de menor id (FR-007, FR-009);
  - **veredicto y motivo**: FR-001 y FR-011;
  - **frontera**: FR-012;
  - **dependencias**: una búsqueda por cada puerta bloqueada (FR-014);
  - **grupos**: clausura transitiva;
  - **ciclos**: la regla de FR-015.
  Puede usar dict, set y list (está fuera de `cripta/`). Depende de T006 y T007.

**Checkpoint**: suite verde (46) y `prueba_reglas` limpia; commit "Tipos de resolubilidad, ayudas y oráculo de prueba".

---

## Phase 3: User Story 1 - Saber si la cripta puede ganarse y por qué no (Priority: P1) 🎯 MVP

**Goal**: veredicto, orden de obtención lexicográficamente menor y reporte de no resolubilidad (motivo, no obtenibles, frontera, ciclos) sobre datos en memoria, con texto canónico.

**Independent Test**: verificar las criptas sintéticas de `apoyo_resolubilidad` y comparar el veredicto, el orden y el texto exacto del reporte (contracts/reporte.md), sin vista, red ni partida.

### Tests for User Story 1 (escribir primero; deben fallar)

- [ ] T010 [P] [US1] Escribir `pruebas/prueba_resolubilidad_reglas.py` (FR-001 a FR-010, FR-016, FR-017). Llama al verificador con datos en memoria. Escenarios:
  - H1.E2: la llave de un errante se obtiene en su sala inicial;
  - H1.E3: dos ejecuciones, el mismo orden y el menor por id; con itm_llave_bronce e itm_llave_azul disponibles a la vez, va antes itm_llave_azul;
  - H1.E4: cadena A, B, llave_salida;
  - H1.E5: una llave que no hace falta va en el orden una sola vez;
  - H1.E9: el cierre automático no bloquea;
  - H1.E10: caras de puerta distintas, cada una en su sentido;
  - H1.E12: dos caminos a sala_salida, uno por la salida de llave_salida: resoluble, aunque el camino abierto se recorra antes.
  Casos borde, marcados `# borde:`:
  - una llave abre varias puertas;
  - la llave está en la sala inicial;
  - una llave con varias ubicaciones, una alcanzable;
  - una salida abierta que declara llave no la requiere;
  - la verificación no pide contenido de salas ni catálogo (FR-017: la fuente falsa falla si se le piden).
- [ ] T011 [P] [US1] Escribir `pruebas/prueba_resolubilidad_reporte.py` (FR-011 a FR-016, SC-004). Compara el **texto exacto** de contracts/reporte.md. Escenarios:
  - H1.E1: ciclo de una llave;
  - H1.E6: llave sin ubicación en la frontera;
  - H1.E7: llave de enemigo en región inalcanzable, con `(suelta e-…)`;
  - H1.E8: ciclo de dos llaves en el mismo orden;
  - H1.E11: no resoluble sin ciclo ("Ciclos: ninguno.").
  Casos borde:
  - varios grupos, ordenados por menor id;
  - dentro de un grupo: k_a depende de k_b y k_c, y k_b y k_c de k_a → `k_a -> k_b -> k_a`;
  - la puerta mostrada en cada paso es la de menor sala de origen y luego N, S, E, O;
  - una puerta cerrada cuyo destino es alcanzable no es frontera;
  - la ubicación de llaves vacía;
  - motivo (b) con y sin la línea "solo se alcanza por caminos sin esa salida";
  - sala_salida solo alcanzable sin su puerta;
  - el texto es idéntico carácter por carácter con las entradas desordenadas (FR-010, SC-004);
  - "Llaves no obtenibles (0):" y "Frontera bloqueada (0):" con conteo 0.
- [ ] T012 [P] [US1] Escribir `pruebas/prueba_resolubilidad_oraculo.py` (FR-001, FR-007, FR-009, FR-011 a FR-016; research.md R13): 200 criptas de `apoyo_resolubilidad` con semillas fijas 0 a 199, y para cada una, texto del reporte del programa == texto del oráculo (T009). Ante una diferencia, imprime la semilla, la descripción de la cripta y los dos textos, y sale con 1.
- [ ] T013 [US1] Registrar T010 a T012 en `PRUEBAS` de `pruebas/ejecutar_pruebas.py` bajo el comentario `# 003-resolubilidad`, con los FR y las marcas de cada una, correr la suite y **confirmar que las tres fallan** (no existen el grafo ni el verificador). Anotar el motivo en el commit de la fase.

### Implementation for User Story 1

- [ ] T014 [US1] Implementar `cripta/modelo/resolubilidad/grafoVerificacion.py` (research.md R1, data-model.md §2):
  - las clases `NodoSala`, `AristaSalida` y `NodoLlave` (`__lt__` por id como texto);
  - la función de construcción a partir de las salas del esqueleto, los datos generales y las ubicaciones. Ordena con `ordenamiento.mezcla` y `ClaveOrden`, y fusiona en una pasada: destinos de salidas, ids de llave deduplicados (de salidas cerradas con llave, ubicaciones y llave_salida) y ubicaciones a salas (ordenadas por sala y enemigo);
  - sin dict, set, list ni búsqueda por id;
  - una sala de ubicación o un destino que no existen lanzan `DatosInvalidos`, con un mensaje que nombra la entrada (FR-030).
  FR-006, FR-010, FR-016, FR-017.
- [ ] T015 [US1] Implementar la fase 1 en `cripta/modelo/resolubilidad/verificadorResolubilidad.py` (research.md R2, R3):
  - recorrido en anchura con `Cola` propia desde sala_inicial, salidas en orden N, S, E, O;
  - puertas pendientes por `NodoLlave` y bloqueadas sin llave;
  - `HeapMinimo` de llaves disponibles; se extrae solo con la cola vacía;
  - la marca `entra_por_puerta_salida`: al **examinar** una salida cerrada que requiere llave_salida, con llave_salida obtenida y destino sala_salida, **aunque sala_salida ya esté alcanzada**. Se pone en los dos momentos: al sacar la sala y al reexaminar pendientes (H1.E12);
  - `sala_salida_alcanzada`, la ubicación mostrada de cada llave del orden (la primera ya alcanzada al elegirla) y el contador `salidas_examinadas`;
  - veredicto, motivo (a)/(b), frontera filtrada por destino no alcanzado y no obtenibles.
  FR-001 a FR-009, FR-011 a FR-013, FR-016, FR-033, FR-034.
- [ ] T016 [US1] Implementar la fase 2 en `cripta/modelo/resolubilidad/verificadorResolubilidad.py` (research.md R4), solo si NO_RESOLUBLE:
  - grafo de bloqueo sobre las salas no alcanzadas y las llaves no obtenidas;
  - Tarjan **iterativo** con `Pila` propia (índices en campos de los nodos, sin recursión);
  - grupos = componentes con al menos una llave y más de un nodo;
  - relleno por prioridad: puertas que requieren una llave del grupo hacia salas del grupo, ordenadas por (id de Y, sala de origen, dirección N, S, E, O) con `mezcla`; cada sala se etiqueta una vez;
  - la dependencia mínima de cada llave y el ciclo de FR-015 desde la llave de menor id del grupo hasta repetir; grupos ordenados por menor id.
  Ninguna pasada por llave. FR-014, FR-015, FR-033, FR-034.
- [ ] T017 [US1] Implementar `cripta/controlador/textoResolubilidad.py`: `ResultadoResolubilidad` → `ListaEnlazada` de líneas, con el formato **exacto** de contracts/reporte.md (encabezado, orden, motivo (a)/(b) con su línea extra, secciones con conteo, ciclos en una línea con ` -> `, "Ciclos: ninguno.", NO_VERIFICADA, y el aviso corto `La cripta es resoluble. V muestra el reporte.` como constante). FR-007, FR-011 a FR-015, FR-031, SC-004.
- [ ] T018 [US1] Correr la suite completa y `prueba_reglas` hasta que estén en verde (49). Si el oráculo discrepa, se corrige el programa, o el oráculo si este no aplica la spec al pie de la letra; nunca se acepta la diferencia. Si la discrepancia muestra que la **spec** es ambigua, se para y se enmienda spec.md en un commit propio (regla de arriba). Commit: "Resolubilidad US1: verificación y reporte (T010 a T018)".

**Checkpoint**: el veredicto, el orden y el reporte se pueden demostrar sin red ni vista.

---

## Phase 4: User Story 4 - Obtener la ubicación de las llaves dentro del presupuesto (Priority: P2)

**Goal**: la consulta `GET /criptas/<id>/llaves` en línea y sin conexión, con validación, presupuesto, caché por versión de cripta y el resultado NO_VERIFICADA.

**Independent Test**: con `ServidorFalso` y `FuenteOffline`, contar las solicitudes de dos verificaciones de la misma versión y de una versión nueva, y comparar lo que entregan las dos fuentes.

### Tests for User Story 4 (escribir primero; deben fallar)

- [ ] T019 [P] [US4] Agregar la ruta `/criptas/<id>/llaves` a `ServidorFalso` en `pruebas/prueba_falso_1_6.py`, con ubicaciones configurables en el constructor y sujeta a `inyectar_429` igual que las otras rutas.
- [ ] T020 [P] [US4] Escribir `pruebas/prueba_datos_llaves.py` (FR-025 a FR-031).
  Escenarios:
  - H4.E1: una consulta, que cuenta en el presupuesto; un 429 reintentado cuenta dos;
  - H4.E2: la caché de la misma versión no pide;
  - H4.E3: con otra versión guardada, se pide de nuevo y se sobrescribe;
  - H4.E4: `ClienteHttp` contra `ServidorFalso` y `FuenteOffline` sobre el mismo JSON dan las mismas ubicaciones;
  - H4.E5: cada caso de error de contracts/datos-llaves.md da `DatosInvalidos` con la entrada nombrada. Los casos: raíz sin `llaves`, entrada que no es objeto, sin `id`, `id` vacío, sin `sala`, `sala` bool, `enemigo` no texto, y sala inexistente en el esqueleto vía `verificar_cripta`. Se aceptan campos extra y ids repetidos;
  - H4.E6: con un presupuesto que no alcanza, no se supera, y el resultado es NO_VERIFICADA.
  Casos de NO_VERIFICADA:
  - falta `llaves.json` sin conexión: NO_VERIFICADA, nunca lista vacía (FR-029);
  - un error de red;
  - datos inválidos.
  Un archivo de caché dañado se ignora (FR-027).
- [ ] T021 [US4] Registrar T020 en `pruebas/ejecutar_pruebas.py` y confirmar que falla (no existe `FuenteDatos.llaves`). Anotarlo para el commit.

### Implementation for User Story 4

- [ ] T022 [P] [US4] Implementar `llaves_desde_json(datos)` en `cripta/adaptadores/convertidorJson.py` con las reglas de contracts/datos-llaves.md: `id` "texto no vacío", `sala` "entero (no bool)", `enemigo` "texto o null; ausente o null = en el suelo", campos extra ignorados, `DatosInvalidos` con el índice de la entrada y el campo. Devuelve una `ListaEnlazada` de `UbicacionLlaveDTO`. FR-025, FR-030.
- [ ] T023 [US4] Agregar el método abstracto `llaves(id_cripta)` a `cripta/modelo/puertos/fuenteDatos.py` (docstring: `ListaEnlazada` de `UbicacionLlaveDTO`, puede lanzar `ErrorDeRed` o `PresupuestoAgotado`) e implementarlo en:
  - `cripta/adaptadores/clienteHttp.py`, por `_pedir`, que cuenta intentos y reintentos (FR-026);
  - `cripta/adaptadores/fuenteOffline.py`, sobre `criptas/<id>/llaves.json` con `_leer` (FR-029).
  Actualizar también todas las demás implementaciones del puerto para que sigan instanciándose:
  - `cripta/controlador/bench/benchPrecarga.py` (`FuenteLenta`);
  - `pruebas/apoyo_terreno.py` (`FuenteMemoria`);
  - `pruebas/prueba_1_4.py` (`Falsa`; `Incompleta` sigue sin implementar a propósito);
  - `pruebas/prueba_1_8.py` y `pruebas/prueba_5_5.py` (`FuenteFalsa`).
  Las que no la usan devuelven una `ListaEnlazada` vacía. FR-025, FR-026, FR-029.
- [ ] T024 [US4] Agregar `guardar_llaves(id_cripta, version_cripta, ubicaciones)` y `cargar_llaves(id_cripta, version_cripta)` a `cripta/modelo/puertos/almacenLocal.py` (`cargar_llaves` devuelve None si no existe, si la versión no coincide o si el archivo está dañado) e implementarlos en `cripta/adaptadores/almacenLocalDisco.py` en `<carpeta>/llaves/<id_cripta>.json` con `{"version_cripta", "llaves"}`, reutilizando `llaves_desde_json` al leer. FR-027, FR-028.
- [ ] T025 [US4] Implementar `ServicioDatos.ubicacion_llaves()` en `cripta/modelo/datos/servicioDatos.py`. Resuelve en cascada: memoria (id y versión de la cripta actual), luego disco (`cargar_llaves`) y por último red (`self._sincrona.llaves`, que después se guarda). Usa la versión de `datos_cripta()`. FR-027, SC-007.
- [ ] T026 [US4] Implementar `verificar_cripta(servicio)` en `cripta/modelo/resolubilidad/verificacion.py`: obtiene las ubicaciones, arma el grafo y verifica. Cualquier `ErrorCripta` (red, presupuesto, datos inválidos o ausentes) da un `ResultadoResolubilidad` NO_VERIFICADA con el mensaje, nunca NO_RESOLUBLE. Requiere que `servicio.iniciar_cripta` ya se haya llamado. FR-017, FR-029, FR-031.
- [ ] T027 [US4] Suite completa y `prueba_reglas` en verde (50). Commit: "Resolubilidad US4: consulta de llaves con presupuesto y caché (T019 a T027)".

**Checkpoint**: la ubicación de llaves llega por las dos fuentes, cuenta en el presupuesto y se reutiliza por versión.

---

## Sincronización con main (antes de la Fase 5)

**Purpose**: traer lo que Pablo ya integró antes de tocar `EstadoVista`, el encabezado del log, la Vista y las teclas.

- [ ] T028 `git fetch origin` y `git merge origin/main` en `003-resolubilidad`. Resolver los conflictos conservando lo de las dos ramas: campos de `EstadoVista` con nombre, palabras de marca del encabezado, filas de `PRUEBAS`, `benchTodo` y README, y numeración de DECISIONES.md y PROMPTS_LLM.md. Suite completa y `prueba_reglas` en verde después del merge. Si `main` cambió algo que esta feature asume (por ejemplo, el encabezado del log o las teclas), se para y se ajustan primero spec.md o plan.md, en commits propios. Commit del merge. T058 queda como segundo repaso antes de documentar.

---

## Phase 5: User Story 2 - No empezar una partida imposible, salvo que se fuerce (Priority: P1)

**Goal**: verificar al iniciar una partida nueva, pantalla de reporte, `--forzar`, aviso, tecla V, anotación `FORZADA` en el log y ningún bloqueo al cargar ni en los replays.

**Independent Test**: con `pruebas/datos/resolubilidad`, pedir "jugar" en una cripta no resoluble con y sin `forzar`, y comprobar si se creó partida y log, la pantalla de reporte, el encabezado y el replay.

### Tests for User Story 2 (escribir primero; deben fallar)

- [ ] T029 [P] [US2] Escribir `pruebas/prueba_resolubilidad_inicio.py` (FR-018 a FR-021, FR-031). Usa `ControladorMenu` sobre `pruebas/datos/resolubilidad`, una `VistaRegistradora` que registra `mostrar_resolubilidad` y carpetas temporales.
  Escenarios:
  - H2.E1: no resoluble sin `forzar`: no hay partida ni archivo de log, se muestra el reporte y "volver" regresa al menú;
  - H2.E2: con `forzar`, pantalla con `puede_continuar=True`; `aceptar_resolubilidad` inicia y el encabezado del log termina en ` FORZADA`;
  - H2.E3: resoluble: el aviso en la bitácora y `EstadoVista.resolubilidad` con las líneas del reporte;
  - H2.E4: `ModoReplay` reproduce el log forzado sin bloquear.
  Además:
  - `res-sin-llaves`: NO_VERIFICADA bloquea sin `forzar` y deja iniciar con él;
  - continuar una partida guardada no consulta llaves (contador de la fuente);
  - con `resolubilidad` None, `ver_resolubilidad` escribe "Esta partida no tiene reporte de resolubilidad." en la bitácora sin anexar nada al log.
  Encabezado (contracts/registro.md):
  - un log de 4 campos se lee igual;
  - `FORZADA` se lee como `forzada=True`;
  - una palabra desconocida o repetida es `ErrorCripta`.
  Reproducción y guardado:
  - **replay fiel**: jugar por el menú una partida corta en una cripta resoluble (`res-cadena`: unas pocas acciones hasta ganar o hasta un estado intermedio), reproducir su log con `ModoReplay` y comparar el estado final con el original. Se compara el binario de `partidaBinaria.guardar` de las dos partidas (o, si incluye datos que no se reproducen, reloj, sala, vida, inventario, enemigos y `fin`). Verificar no debe cambiar la partida (FR-018, FR-021);
  - **guardado idéntico tras V**: en una partida cargada, guardar el binario, pulsar V (`ver_resolubilidad`), guardar otra vez y comprobar que los dos archivos son **idénticos** byte a byte. Si el aviso de la bitácora rompe la igualdad, **se para y se decide** con el usuario entre sacar la bitácora del estado serializado o mostrar el aviso desde la Vista, sin tocar el modelo. Se registra la decisión en DECISIONES.md antes de seguir (FR-021).
- [ ] T030 [P] [US2] Escribir `pruebas/prueba_vista_resolubilidad.py` (FR-019, FR-020, FR-037; H2.E3):
  - la pantalla de reporte manda `volver` con ENTER y ESC si `puede_continuar` es False, y `aceptar_resolubilidad` con ENTER y `volver` con ESC si es True;
  - en la partida, V alterna el panel sin encolar comandos cuando hay reporte;
  - con reporte None, V encola `ver_resolubilidad`; en el replay, V no hace nada;
  - ninguna otra tecla de la partida, el menú ni el replay está asignada a V (se recorren las teclas que maneja cada pantalla).
  Sigue el estilo de `prueba_vista_10.py`.
- [ ] T031 [US2] Adaptar las pruebas existentes que inician por el menú (research.md R12):
  - `pruebas/prueba_datos_costo.py`: armar `ControladorMenu` con `forzar=True` y mandar `Comando("aceptar_resolubilidad")` después de cada "jugar". Comprobar que el error de caras distintas sigue apareciendo (al convertir o al iniciar la partida forzada, según dónde salte hoy);
  - `pruebas/prueba_controlador.py` y `pruebas/prueba_replay_menu.py`: agregar `llaves.json` al paquete temporal que escriben, con la llave en una sala alcanzable, y confirmar a mano con la regla de FR-001 que la cripta es resoluble. Si no lo fuera, usar `forzar=True` como arriba y anotar por qué.
- [ ] T032 [US2] Registrar T029 y T030 en `pruebas/ejecutar_pruebas.py`, correr la suite y confirmar que T029, T030 y las tres adaptadas en T031 fallan por lo que falta (sin `forzar`, sin pantalla, sin palabra `FORZADA`). La lista de pruebas que fallan debe ser **exactamente** esas cinco (`prueba_resolubilidad_inicio`, `prueba_vista_resolubilidad`, `prueba_datos_costo`, `prueba_controlador` y `prueba_replay_menu`). Si falla otra, se investiga antes de seguir. Anotarlo para el commit.

### Implementation for User Story 2

- [ ] T033 [US2] `EncabezadoPartida` en `cripta/modelo/puertos/registroAcciones.py` gana `forzada: bool = False`. `cripta/adaptadores/registroArchivo.py` escribe la palabra `FORZADA` después de los 4 campos solo si es True. Al leer, acepta después de los 4 fijos palabras **conocidas** (`FORZADA`) en cualquier orden, cada una a lo sumo una vez; una desconocida o repetida es `ErrorCripta` (contracts/registro.md). FR-020, FR-021.
- [ ] T034 [P] [US2] Agregar `ReporteResolubilidadVisible(veredicto: str, lineas: ListaEnlazada, puede_continuar: bool)` en `cripta/vista/estadoVista.py` y el campo `resolubilidad: Optional[ReporteResolubilidadVisible] = None` **al final** de `EstadoVista`, con nombre. Revisar que todo constructor de `EstadoVista` use argumentos con nombre (plan.md, "Posibles choques"). FR-019.
- [ ] T035 [P] [US2] Agregar `mostrar_resolubilidad(reporte)` **no abstracto** a `cripta/vista/vistaJuego.py` (como `mostrar_benchmark`); `cripta/vista/vistaNula.py` no hace nada. FR-019, FR-023.
- [ ] T036 [US2] En `cripta/controlador/controladorJuego.py`:
  - `preparar_nueva(id_cripta) -> ResultadoResolubilidad`: llama a `servicio.iniciar_cripta` y a `verificar_cripta`, y guarda el resultado;
  - `iniciar_preparada(semilla, forzada)`: usa `iniciar_nueva` por dentro, escribe el encabezado con `forzada`, guarda las líneas del reporte para el `EstadoVista` y, si es RESOLUBLE, llama a `partida.avisar` con el aviso corto;
  - el verbo de sesión `ver_resolubilidad`: `partida.avisar("Esta partida no tiene reporte de resolubilidad.")`, sin log ni reloj;
  - `iniciar_nueva(id_cripta, semilla)` se **conserva** con su firma y sin verificar (camino de pruebas; el bench y los replays no pasan por aquí).
  FR-018, FR-019, FR-020, FR-021.
- [ ] T037 [US2] En `cripta/controlador/constructorEstadoVista.py`, pasar el reporte de la partida en curso a `EstadoVista.resolubilidad` (None si no hay). FR-019.
- [ ] T038 [US2] En `cripta/controlador/controladorMenu.py`: parámetro `forzar: bool = False`. En `_empezar_partida`, para una partida nueva: si es RESOLUBLE, inicia; si no, `vista.mostrar_resolubilidad(..., puede_continuar=forzar)` y guarda el juego pendiente. Verbos `aceptar_resolubilidad` (solo con un pendiente y `forzar`: `iniciar_preparada(semilla, True)`) y `volver` (descarta el pendiente, `servicio.reiniciar_sesion()` y vuelve al menú). Continuar una guardada no verifica. FR-018 a FR-021, FR-031.
- [ ] T039 [US2] En `cripta/controlador/fabricaAplicacion.py`, leer `--forzar` y pasarlo a `ControladorMenu`; actualizar los docstrings de `fabricaAplicacion.py` y `main.py` (contracts/linea-de-comandos.md). FR-020.
- [ ] T040 [US2] Vista arcade:
  - `cripta/vista/pantallaResolubilidad.py` (nueva): las líneas, desplazamiento con flechas y RePág/AvPág, ENTER y ESC según `puede_continuar`, y la línea de ayuda de contracts/vista.md;
  - `cripta/vista/vistaArcade.py`: `mostrar_resolubilidad` y el estado del panel;
  - `cripta/vista/pantallaJuego.py`: la tecla V alterna el panel si hay reporte, encola `ver_resolubilidad` si no, y no hace nada en el replay;
  - `cripta/vista/hudJuego.py`: el panel superpuesto.
  **Depende de T005** (confirmación de Pablo, fase 1): no se implementa la tecla sin esa confirmación. Si V choca, se para y se enmiendan la aclaración 4 y FR-037 de spec.md en un commit propio. FR-019, FR-020, FR-037.
- [ ] T041 [US2] Suite completa y `prueba_reglas` en verde (52). Commit: "Resolubilidad US2: inicio de partida, --forzar y tecla V (T029 a T041)".

**Checkpoint**: una cripta no resoluble no inicia sin `--forzar`; con él inicia y queda anotada en el log.

---

## Phase 6: User Story 3 - Verificar una cripta desde la terminal (Priority: P2)

**Goal**: `--verificar ID` imprime el reporte y sale con 0, 1 o 2, sin vista, partida, log ni puntaje.

**Independent Test**: correr `main.py --verificar` en un subproceso con `--offline=pruebas/datos/resolubilidad` y revisar la salida, el código y los archivos creados.

### Tests for User Story 3 (escribir primero; deben fallar)

- [ ] T042 [P] [US3] Escribir `pruebas/prueba_verificar.py` (FR-022 a FR-024).
  Escenarios:
  - H3.E1: en un subproceso con directorio de trabajo temporal y ruta absoluta del paquete, el reporte sale por la terminal y no aparecen `partidas/`, `guardados/` ni `puntajes.jsonl`. Además, en el mismo proceso, `FabricaAplicacion(("--verificar", id, "--offline=..."))` no deja `arcade` en `sys.modules`;
  - H3.E2: códigos 0 (`res-cadena`), 1 (`res-autociclo`) y 2 (`res-sin-llaves`); `--verificar` sin ID da 2 con el mensaje de uso;
  - H3.E3: el texto con `--offline` es idéntico al obtenido con `ClienteHttp` contra `ServidorFalso` sirviendo el mismo JSON de la misma versión.
  `--forzar` no cambia el código de `--verificar`.
- [ ] T043 [US3] Registrar T042 en `pruebas/ejecutar_pruebas.py` y confirmar que falla (no existe `--verificar`). Anotarlo para el commit.

### Implementation for User Story 3

- [ ] T044 [US3] Crear `cripta/controlador/modoVerificar.py`. Llama a `servicio.iniciar_cripta(id)` (captura `ErrorCripta` → NO_VERIFICADA) y a `verificar_cripta`, imprime las líneas de `textoResolubilidad` con `Reporte` y el resumen de red de `ReporteFinal`, y devuelve 0, 1 o 2 según contracts/linea-de-comandos.md. FR-022, FR-024, FR-031.
- [ ] T045 [US3] En `cripta/controlador/fabricaAplicacion.py`, leer `--verificar ID` antes de `--replay`, armar el servicio (en línea o `--offline`), ejecutar `ModoVerificar` y `sys.exit(codigo)`, sin importar `vistaArcade` ni crear `ControladorMenu`. Sin ID: mensaje de uso y salida con 2. Docstring de uso en `main.py`. FR-022, FR-023, FR-024.
- [ ] T046 [US3] Suite completa y `prueba_reglas` en verde (53). Commit: "Resolubilidad US3: --verificar (T042 a T046)".

**Checkpoint**: cualquier cripta se revisa por terminal con un código de salida útil en revisión.

---

## Phase 7: User Story 5 - Verificación rápida y que escala (Priority: P3)

**Goal**: medir con `--bench` los 200 ms de la cripta de referencia y comparar con la alternativa ingenua por **salidas examinadas** (SC-003).

**Independent Test**: `py main.py --bench --rapido` muestra las tablas de `benchResolubilidad` y la prueba de rendimiento pasa (H5.E1 salta con "SIN DATOS" mientras `datos_offline/` no tenga llaves).

### Tests for User Story 5 (escribir primero; deben fallar)

- [ ] T047 [P] [US5] Escribir `pruebas/prueba_rendimiento_resolubilidad.py` (FR-032 a FR-035, SC-002, SC-003).
  Escenarios:
  - H5.E1: la cripta de referencia (la de más salas de `datos_offline/`, elegida en ejecución, sin ids) se verifica en menos de 200 ms (mínimo de varias repeticiones, sin red ni renderizado). **Si esa cripta no tiene `llaves.json`, imprime `H5.E1 SIN DATOS: datos_offline/ no tiene llaves.json; se salta` y sigue con lo demás**;
  - H5.E2: en cadenas de 100, 200 y 400 llaves, resolubles y con ciclo, el texto del reporte de la verificación es igual al de la alternativa ingenua;
  - H5.E3: los cocientes de **salidas examinadas** 200/100 y 400/200 son ≤ 2,5 en la verificación y ≥ 3,5 en la ingenua. Se mide el contador, no el tiempo.
- [ ] T048 [US5] Registrar T047 en `pruebas/ejecutar_pruebas.py` y confirmar que falla (no existen la alternativa ni el bench). Anotarlo para el commit.

### Implementation for User Story 5

- [ ] T049 [US5] Crear `cripta/controlador/bench/alternativasResolubilidad.py` con la alternativa ingenua (research.md R11). Repite la fase 1 **desde cero** por cada llave obtenida, eligiendo la disponible de menor id, y cuenta sus salidas examinadas. Reutiliza la fase 2 y el formateador, así que solo difiere en cómo obtiene el orden. Sin estructuras prohibidas (vive en `cripta/`). FR-035.
- [ ] T050 [US5] Crear `cripta/controlador/bench/benchResolubilidad.py` con las dos tablas de contracts/linea-de-comandos.md:
  - (1) la referencia: salas, salidas, llaves, ms mínimo y PASA/FALLA contra 200 ms, o **SIN DATOS** (nunca PASA) si no hay `llaves.json`;
  - (2) las cadenas de 100, 200 y 400 llaves, resolubles y con ciclo: ms (informativo), salidas examinadas de las dos, cocientes con PASA/FALLA contra ≤ 2,5 y ≥ 3,5, y "mismo reporte: sí/no".
  Generar las cadenas en el mismo módulo, sin ids de criptas reales; `--rapido` reduce las repeticiones, no los tamaños. Registrar en `cripta/controlador/bench/benchTodo.py`. FR-032 a FR-035.
- [ ] T051 [US5] Correr `py main.py --bench` completo y anotar las cifras reales (referencia o SIN DATOS, ms y salidas examinadas por tamaño, cocientes) para DECISIONES.md (T060). Si un criterio de SC-002 o SC-003 **falla**, se para: se diagnostica con mediciones (principio VI), y solo si la spec pide algo imposible se enmienda spec.md en un commit propio. Nunca se relaja un umbral en la prueba.
- [ ] T052 [US5] Suite completa y `prueba_reglas` en verde (54, con H5.E1 saltada si no hay datos). Commit: "Resolubilidad US5: bench y alternativa ingenua (T047 a T052)".

**Checkpoint**: la escalabilidad queda demostrada por conteo; los 200 ms, por tiempo cuando haya datos.

---

## Phase 8: Polish, coordinación y cierre

**Purpose**: coordinación con la otra rama, documentación con cifras reales y cierre.

- [ ] T053 [P] Revisar `cripta/` contra la constitución: tipos y docstrings en lo nuevo, atributos `_` con propiedades, nombres camelCase y ninguna estructura prohibida (`prueba_reglas`). Buscar en `cripta/` los ids, versiones y cantidades de las criptas de `datos_offline/` y de `pruebas/datos/`: no debe aparecer ninguno (FR-036).
- [ ] T054 [P] Cobertura: cada FR-001 a FR-037 aparece citado en al menos una prueba (`grep -o "FR-0[0-9][0-9]" pruebas/prueba_*resolub* pruebas/prueba_verificar.py pruebas/prueba_datos_llaves.py pruebas/prueba_vista_resolubilidad.py`, salvo FR-036, que cubren `prueba_reglas` y T053) y las 28 marcas H*.E* de plan.md están en su prueba. Completar lo que falte.
- [ ] T055 Validar quickstart.md §3 a §5 a mano (`--verificar` con los tres códigos, pantalla de reporte con y sin `--forzar`, V, partida cargada y replay forzado, `--bench --rapido`). Corregir quickstart.md si algo no coincide.
- [ ] T056 [P] README.md (FR-037):
  - en la tabla "Partida", la fila `| V | Mostrar / ocultar el reporte de resolubilidad (orden de llaves) |`;
  - una sección "Resolubilidad" con `--verificar ID` y sus códigos 0, 1 y 2, `--forzar`, la pantalla de reporte (ENTER y ESC), el aviso y la V en una partida cargada;
  - el total de pruebas actualizado;
  - la nota de que `datos_offline/` debe regenerarse para la Parte II.
- [ ] T057 [P] Actualizar `contracts/vista.md`, `plan.md` o `research.md` si la implementación cambió un detalle de diseño (no de regla). Un cambio de regla va por spec.md (regla de arriba).
- [ ] T058 Conflicto con Pablo, **segundo repaso** (el primero es la sincronización antes de la Fase 5, T028), **antes** de documentar números: `git fetch` y `git pull origin main` (o merge de `main` en la rama), y revisar:
  - numeración de DECISIONES.md: el siguiente D libre después de lo que trajo `main`;
  - numeración de PROMPTS_LLM.md: continua; si se repite un número, renumerar las entradas de esta rama;
  - el último campo de `EstadoVista`: conservar los dos campos, con nombre;
  - el encabezado del log: sumar las palabras de marca de Pablo a la lista de conocidas, si las hay;
  - las teclas: ninguna repetida en la partida, el menú y el replay.
  Suite y `prueba_reglas` en verde después del merge. Commit: "Merge de main en resolubilidad y coordinación con las features de Pablo".
- [ ] T059 DECISIONES.md, con los números libres de T058, una sección por decisión **con las cifras reales de T051**:
  - grafo enlazado por ordenamiento y fusión (R1);
  - fase 1 con puertas pendientes y heap mínimo, y la marca de la puerta de salida (R2, R3);
  - fase 2 con Tarjan iterativo y relleno por prioridad (R4);
  - consulta de llaves síncrona con caché por versión (R5);
  - encabezado con palabras de marca (R9);
  - V como estado local de la Vista y el verbo para la partida cargada (R8).
  Agregar la fila de la sección del problema a la tabla del inicio.
- [ ] T060 PROMPTS_LLM.md al día: cada prompt de la implementación registrado, con numeración continua revisada en T058.
- [ ] T061 Cierre parcial: suite completa, `prueba_reglas` y `--bench --rapido` en verde. Marcar las tareas hechas en este archivo. Commit: "Resolubilidad: documentación y cierre (T053 a T061)". El push lo pide el usuario.
- [ ] T062 **H5.E1 obligatorio** (depende de T003): con `datos_offline/` regenerado, quitar el salto "SIN DATOS" de `pruebas/prueba_rendimiento_resolubilidad.py`: sin `llaves.json`, la prueba **falla**. Correr la suite y `--bench` con la cripta de referencia real (< 200 ms, PASA), y actualizar la cifra en DECISIONES.md (T059) y plan.md. Si no pasa, se aplica la regla de T051. Correr además la suite completa y `py main.py --bench --rapido` con los datos regenerados y documentar en el commit y en DECISIONES.md lo que cambie (tablas de otras features que usan `datos_offline/`, cifras de referencia). Commit: "Resolubilidad: H5.E1 obligatorio con datos de la Parte II".

---

## Escenarios de aceptación → pruebas (SC-001)

| Marca | Prueba | Tarea |
|---|---|---|
| H1.E1 (B), H1.E6, H1.E7, H1.E8, H1.E11 | `prueba_resolubilidad_reporte` | T011 |
| H1.E2 (B), H1.E3 (B), H1.E4, H1.E5, H1.E9, H1.E10, H1.E12 | `prueba_resolubilidad_reglas` | T010 |
| H2.E1 (B), H2.E2, H2.E3, H2.E4 | `prueba_resolubilidad_inicio` (+ `prueba_vista_resolubilidad` para H2.E3) | T029, T030 |
| H3.E1, H3.E2, H3.E3 | `prueba_verificar` | T042 |
| H4.E1 a H4.E6 | `prueba_datos_llaves` | T020 |
| H5.E1 (salta con SIN DATOS hasta T062), H5.E2, H5.E3 | `prueba_rendimiento_resolubilidad` | T047, T062 |
| oráculo (R13) | `prueba_resolubilidad_oraculo` | T012 |

## Cobertura de requisitos

| FR | Tareas |
|---|---|
| FR-001 a FR-010 | T010, T012, T014, T015 |
| FR-011 a FR-016 | T011, T012, T015, T016, T017 |
| FR-017 | T010, T026 |
| FR-018 a FR-021 | T029, T031, T033, T036 a T038 |
| FR-022 a FR-024 | T042, T044, T045 |
| FR-025 a FR-031 | T002, T020, T022 a T026 |
| FR-032 a FR-035 | T047, T049 a T051, T062 |
| FR-036 | T004, T053, `prueba_reglas` |
| FR-037 | T005, T030, T040, T056 |

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (fase 1)**: sin dependencias.
- **Foundational (fase 2)**: bloquea todo lo demás. T008 y T009 dependen de T006 y T007.
- **US1 (fase 3)**: depende de la fase 2. Es el MVP.
- **US4 (fase 4)**: depende de la fase 2 y usa el verificador de US1 en `verificar_cripta`.
- **Sincronización con main (T028)**: después de US4 y antes de US2.
- **US2 (fase 5)**: depende de US1, US4 y T028. T040 (tecla V) depende además de T005 (equipo).
- **US3 (fase 6)**: depende de US1 y US4 (no de US2).
- **US5 (fase 7)**: depende de US1 (el bench no usa red).
- **Cierre (fase 8)**: depende de todas. T062 depende además de T003 (equipo).

### Within Each Phase

- Pruebas primero y en rojo (tarea "confirmar que fallan"), después el código, y al final la suite verde y el commit.
- Si algo contradice la spec: parar y enmendar spec.md en un commit propio.

### Parallel Opportunities

- Fase 1: T002 y T004 en paralelo. T003 y T005 corren en paralelo a todo, a cargo del equipo.
- Fase 2: T006 y T007 en paralelo; después, T008 y T009 en paralelo.
- Fase 3: T010, T011 y T012 en paralelo.
- Fase 4: T019, T020 y T022 en paralelo.
- Fase 5: T029 y T030 en paralelo; T034 y T035 en paralelo.
- US3 y US5 pueden avanzar en paralelo después de US4.

## Parallel Example: User Story 1

```text
Task: "T010 prueba_resolubilidad_reglas.py (H1.E2, E3, E4, E5, E9, E10, E12)"
Task: "T011 prueba_resolubilidad_reporte.py (H1.E1, E6, E7, E8, E11, SC-004)"
Task: "T012 prueba_resolubilidad_oraculo.py (200 criptas, semillas 0 a 199)"
```

## Parallel Example: User Story 2

```text
Task: "T029 prueba_resolubilidad_inicio.py (H2.E1 a H2.E4, encabezado)"
Task: "T030 prueba_vista_resolubilidad.py (pantalla, tecla V)"
Then: "T034 ReporteResolubilidadVisible" y "T035 VistaJuego.mostrar_resolubilidad"
```

## Implementation Strategy

### MVP First (User Story 1)

1. Fases 1 y 2.
2. Fase 3 (US1): la verificación y el reporte, probados contra el oráculo.
3. **Parar y validar**: el algoritmo es la parte de mayor riesgo; se revisa antes de conectar datos e interfaz.

### Incremental Delivery

1. US4: datos reales de llaves por las dos fuentes.
2. US2: el bloqueo de inicio y la tecla V (lo que el jugador ve).
3. US3: `--verificar` para la revisión.
4. US5: mediciones.
5. Cierre, y T062 cuando el equipo regenere `datos_offline/`.

## Notes

- El total de pruebas por checkpoint (49, 50, 52, 53, 54) supone la línea base de 46 de T001; se ajusta si `main` trajo otras.
- Cada commit de fase deja anotado por qué fallaban sus pruebas antes del código.
- Ninguna tarea hace push; lo pide el usuario.
