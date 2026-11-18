# CRIPTA-Proyecto-de-Estructuras-de-Datos-II-Ciclo-2026

Juego por turnos de exploración de criptas (Estructuras de Datos II, ciclo
2026), con arquitectura Modelo-Vista-Controlador más puertos y adaptadores, y
estructuras de datos propias (sin listas, dict ni ordenamientos de Python en
`cripta/`). Las decisiones de diseño están en `DECISIONES.md` y el uso de
herramientas de IA en `PROMPTS_LLM.md`.

## Requisitos

- Python 3.11 o superior (probado con 3.14 en Windows 11).
- Dependencias: `arcade` y `requests`.

```bash
py -m pip install -r requirements.txt
```

## Cómo correrlo

| Comando | Qué hace |
|---|---|
| `py main.py --offline` | Juega con los datos de `datos_offline/` (sin red). |
| `py main.py` | Juega contra el API real (gasta solicitudes del presupuesto). |
| `py main.py --replay partidas/<cripta>.log` | Reproduce un log en la terminal y verifica que sea fiel. |
| `py main.py --replay partidas/<cripta>.log --hasta T` | Reproduce el log y además imprime el estado del instante T (el mismo resumen que la tecla H). Si la partida terminó antes de T, muestra el estado final y lo dice. `--hasta` sin `--replay` o con un T que no es un entero ≥ 0 termina con código 2. |
| `py main.py --checkpoint-cada K` | Acciones entre puntos de control de la línea de tiempo (entero ≥ 1; 25 por defecto). También sirve con `--replay`. |
| `py main.py --verificar <cripta>` (con `--offline` o `--offline=CARPETA`) | Solo verifica si la cripta se puede ganar: imprime el reporte y sale con 0 (resoluble), 1 (no resoluble) o 2 (no se pudo verificar). No abre la ventana ni crea partida. |
| `py main.py --forzar` | Permite jugar una cripta no resoluble (o que no se pudo verificar) después de ver su reporte. |
| `py main.py --bench` (o `--bench --rapido`) | Mide las estructuras (§5.3). |
| `py main.py --cache-size N` | Cambia el tope de fichas en memoria (25 por defecto). |
| `py pruebas/ejecutar_pruebas.py` | Corre las 76 pruebas sin red. Las `prueba_real_*` usan el API real (gastan presupuesto) y se corren aparte. |
| `py pruebas/prueba_reglas.py` | Verifica las reglas del proyecto sobre `cripta/`. |
| `py main.py --offline=pruebas/datos/terreno_cazador` | Juega con el paquete de prueba de terreno y cazador (costos de salida y un cazador). |
| `py -m cripta.controlador.bench.benchCazador` (o `--rapido`) | Mide el cazador: ciclo con 20, 50 y 100 cazadores, política de cota y salas examinadas. |
| `py main.py --offline=pruebas/datos/resolubilidad` | Juega con el paquete de prueba de resolubilidad (criptas resolubles, con ciclos y sin ubicación de llaves). |
| `py -m cripta.controlador.bench.benchNiebla` (o `--rapido`) | Mide la niebla y «ir a»: paso de «ir a» en la cripta de referencia (5 ms) y en una malla de 1024 salas, consultas y exploración con antorcha según el tamaño del mapa conocido, frente a las alternativas descartadas. |
| `py -m cripta.controlador.bench.benchResolubilidad` (o `--rapido`) | Mide la verificación de resolubilidad: cripta de referencia (200 ms) y cadenas de llaves frente a la alternativa ingenua. |

En Windows se usa `py`; `python` puede abrir la Microsoft Store.

## Pantallas y controles

**Título.** La bienvenida a la entrada de la cripta. **ENTER** entra al menú; **ESC** sale.

**Menú principal.**

| Tecla | Acción |
|---|---|
| Flecha arriba/abajo | Elegir cripta |
| ENTER | Jugar (o continuar la partida guardada de esa cripta) |
| X | Partida nueva desde cero, aunque haya una guardada |
| N | Escribir tu nombre (ENTER confirma, ESC cancela) |
| Flecha izquierda/derecha | Cambiar la skin del héroe (el tigre es la predeterminada) |
| P | Puntajes y replays |
| B | Benchmark rápido en la ventana |
| ESC | Salir del juego |

**Partida.**

| Tecla | Acción |
|---|---|
| Flechas | Moverse |
| Shift + flecha | Abrir la puerta en esa dirección (la llave no se gasta) |
| Espacio | Esperar |
| R | Recoger del suelo |
| A | Atacar (se elige el enemigo) |
| U / Q / S | Usar / equipar / soltar (se elige el objeto) |
| Tab / Shift + Tab | Bajar / subir en el inventario (da la vuelta en los extremos y sigue la vista ordenada) |
| O | Cambiar la vista del inventario: real → peso → valor → nombre (el orden real no cambia) |
| P | Leer un pergamino: deshace tu última acción (máximo 5) |
| G / C | Guardar / cargar la partida de esa cripta |
| L | Mostrar / ocultar la bitácora completa (últimos 20 mensajes) |
| V | Mostrar / ocultar el reporte de resolubilidad (orden de llaves) |
| M | Mostrar / ocultar el mapa conocido; con el mapa abierto, flecha arriba/abajo eligen una sala explorada, **ENTER** viaja a ella («ir a») y RePág/AvPág desplazan |
| I | Detener el viaje «ir a» en curso |
| H | Consultar la línea de tiempo: escribe un instante (`120`) o un número de acción (`#3`), **ENTER** consulta, flechas y RePág/AvPág desplazan el resumen y **ESC** vuelve. Con un viaje en curso, primero lo detiene |
| ESC | Volver al menú (lo no guardado se descarta) |

Al elegir objetivo: flecha arriba/abajo, ENTER confirma y ESC cancela.

**Fin de partida.** Muestra el resultado y el resumen de red y caché. **R** reproduce esa partida; **ENTER** vuelve al menú.

**Puntajes.** Primero las victorias, luego las derrotas; dentro de cada grupo, menos tiempo es mejor. Flecha arriba/abajo elige una partida y **R** la reproduce (las que tienen ▶). **ENTER** vuelve.

**Replay.**

| Tecla | Acción |
|---|---|
| Espacio | Pausa / seguir |
| Flecha derecha / izquierda | Un paso adelante / atrás |
| Flecha arriba / abajo | Más rápido / más lento |
| L | Bitácora completa |
| ESC | Salir del replay |

Al terminar, la pantalla indica si el replay llegó exactamente al mismo final que la partida.

## Spec Kit

La Parte II se desarrolló con **Spec Kit (specify CLI) 1.2.6.dev0**, la misma
versión con la que se inicializó el proyecto (`speckit_version` en
`.specify/init-options.json`), con el agente **Claude Code**. Cada feature
siguió `/speckit-specify`, `/speckit-clarify`, `/speckit-plan`,
`/speckit-tasks`, `/speckit-analyze` y `/speckit-implement`, bajo la
constitución de `.specify/memory/constitution.md`; sus artefactos (spec, plan,
investigación, contratos y tareas) están en `specs/001-terreno-cazador/`,
`specs/002-niebla-guerra/`, `specs/003-resolubilidad/` y
`specs/004-linea-tiempo/`, y cada prompt usado está en `PROMPTS_LLM.md`.

## Terreno y cazador

Especificación, plan y tareas en `specs/001-terreno-cazador/`.

- **Costo de las salidas.** Cada salida puede declarar un costo de tránsito
  (entero ≥ 1; 100 si no lo declara o viene `null`), el mismo en los dos
  sentidos. Moverse cuesta el costo de la salida para todos los actores. Si
  las dos caras de una puerta declaran costos distintos, la cripta no se
  inicia y se muestra un error con las dos salas y los dos costos.
- **El cazador.** Un enemigo con un `rango` en su ficha. Se activa como los
  demás (al entrar el jugador a su sala). Si comparte sala con el jugador,
  ataca; si no, avanza un paso por la ruta de costo mínimo cuando esa ruta no
  supera su rango, y si no, espera. No abre puertas.
- **En la vista.** El costo aparece junto a cada salida de la sala y en la
  brújula del panel de salidas. El cazador lleva un anillo y el prefijo «» »
  en su etiqueta, además del color.

## Resolubilidad

Especificación, plan y tareas en `specs/003-resolubilidad/`.

- **Antes de cada partida nueva** el juego verifica si la cripta se puede
  ganar, con el esqueleto y la ubicación de las llaves (`GET
  /criptas/<id>/llaves`, que cuenta en el presupuesto y se guarda por versión
  de cripta). Una llave que suelta un enemigo cuenta en la sala donde el
  enemigo empieza.
- **Si es resoluble**, la partida empieza con el aviso «La cripta es
  resoluble. V muestra el reporte.» y **V** abre o cierra el reporte con el
  orden en que se pueden obtener las llaves (no se muestra solo porque es la
  solución).
- **Si no es resoluble** (o no se pudo verificar), se muestra una pantalla con
  el reporte: el motivo, las llaves que no se pueden obtener y dónde están,
  las puertas que bloquean el avance y, si una llave queda encerrada detrás de
  puertas que solo ella abre, el ciclo. **ENTER** o **ESC** vuelven al menú y
  la partida no empieza. Con `--forzar`, **ENTER** la inicia igual y el log lo
  anota (`FORZADA NO_RESOLUBLE` o `FORZADA NO_VERIFICADA`).
- **Continuar una partida guardada** y los replays no verifican: en una
  partida cargada, **V** dice en la bitácora que no hay reporte.
- **`datos_offline/`** tiene las criptas de la segunda parte (cripta-02 a
  cripta-06) con su `llaves.json`, descargadas con
  `python guardar_respuestas.py` (necesita red). cripta-05 es la no resoluble
  publicada. Si un paquete sin conexión no trae `llaves.json`, la cripta da
  «no se pudo verificar» y jugarla exige `--forzar`.

## Niebla de guerra e «ir a»

Especificación, plan y tareas en `specs/002-niebla-guerra/`.

- **Niebla.** Cada sala está explorada (entraste, la exploró la antorcha o es
  la inicial), avistada (una salida de una explorada lleva a ella: solo sabes
  que existe) o desconocida. La ventana muestra solo lo que conoces.
- **Puertas recordadas.** Ves una puerta mientras estás en una de las dos
  salas que conecta; el mapa recuerda cómo la viste por última vez, aunque
  después cambie (una puerta que se cierra sola puede figurar abierta).
- **Antorcha.** Con la antorcha encendida, al entrar a una sala también
  quedan exploradas sus vecinas (nombre y salidas, sin contenido, sin
  despertar enemigos ni disparar trampas). Sus puertas que no tocan tu sala
  figuran «no observada».
- **Mapa (M).** Lista las salas por id: las exploradas con cada salida, su
  costo y su estado recordado (abierta, cerrada o no observada), y las
  avistadas solo con su id.
- **«ir a» (M, flechas y ENTER).** Viaja a una sala explorada por la ruta más
  barata que conoces: solo salas exploradas y puertas que recuerdas abiertas
  (sin costo declarado vale 100; a igual costo, el primer paso va a la vecina
  de menor id). No abre puertas. Cada paso es un movimiento normal, con su
  tiempo y sus eventos, y se ve con una pausa breve. Se detiene al llegar, al
  entrar a una sala con enemigos, al recibir daño (incluido el veneno), si ya
  no hay ruta conocida, si termina la partida, con **I** o con cualquier
  acción, guardar, cargar o salir; la bitácora dice el motivo. Abrir el mapa,
  Tab y O no lo detienen.
- **Pergamino durante un viaje.** **P** detiene el viaje y deshace solo el
  último paso; el viaje no sigue.
- **Log.** Cada orden queda como una línea `# IR_A <id>` y cada paso como un
  `MOVER`; `--replay` salta los comentarios.

## Línea de tiempo

Especificación, plan y tareas en `specs/004-linea-tiempo/`.

- **Qué muestra.** El estado de la partida en cualquier instante pasado:
  reloj, sala, vida y estadísticas, inventario, efectos, enemigos de esa sala
  con su vida y el mapa conocido en ese momento. `historia 120` es el estado
  después de todos los eventos con tiempo ≤ 120 (si a 120 le toca una
  decisión tuya, justo antes de tomarla); `historia #3`, justo antes de tu
  acción número 3 (cada paso de «ir a» cuenta como una acción).
- **Solo mira.** Consultar no gasta tiempo, no va a `partida.log`, no cambia
  la partida ni lo que puede deshacer el pergamino. Un instante posterior al
  reloj actual se rechaza con el motivo.
- **Pergamino.** Lo que deshaces con un pergamino deja de existir en la
  línea: la línea es la historia tal como quedó.
- **Puntos de control.** Cada K acciones (`--checkpoint-cada K`, 25 por
  defecto) se guarda una copia completa del estado; una consulta parte de la
  copia más cercana y vuelve a simular como mucho K acciones.
- **Guardar y cargar** conservan la línea completa (formato de guardado 4).


No se suben al repositorio (están en `.gitignore`):

- `guardados/<cripta>.bin`: la partida guardada de cada cripta (formato binario propio, §4.10). Se borra al ganar o morir la partida que lo usó. Desde la línea de tiempo el formato es la **versión 4** (además del costo de cada salida de la versión 2 y el conocimiento de cada sala y el recuerdo de cada puerta de la versión 3, guarda la línea de tiempo completa): **un guardado de un formato anterior (1, 2 o 3) se reporta incompatible y no se migra**; hay que empezar una partida nueva de esa cripta.
- `partidas/<cripta>.log`: el log de la partida en curso; `partidas/historial/`: un log archivado por partida terminada, para el replay.
- `puntajes.jsonl`: la tabla de puntajes.
- `fichas_guardadas/`: copia en disco de las fichas del catálogo, para no volver a pedirlas a la red, y en `fichas_guardadas/llaves/` la ubicación de llaves de cada cripta con su versión.

## Créditos de gráficos

- **16x16 DungeonTileset II** de 0x72 (https://0x72.itch.io/dungeontileset-ii), licencia CC0: piso, muros, puertas, las skins del héroe (caballero, caballera, elfa, mago, lagarto, enano), esqueleto, frascos, espada y corazones.
- **8 bit art pack rat monster** de Imogia Games (https://imogiagames.itch.io/8-bit-art-pack-rat-monster), licencia CC BY 4.0: la rata gigante.
- Llave de Kenney (https://kenney.nl), licencia CC0, incluida en arcade.
- El tigre humanoide (skin por defecto del héroe) es pixel art propio del equipo (`cripta/vista/pixelTigre.py`).

Las licencias completas están en `cripta/vista/recursos/*/LICENCIA.txt`.
