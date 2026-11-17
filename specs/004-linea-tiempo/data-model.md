# Data Model: Línea de tiempo (004)

Todas las colecciones son estructuras propias (`ListaEnlazada`, `ListaDoble`,
`ArregloArbol`); no hay dict, set, list de Python, heapq, bisect, collections,
pickle ni deepcopy. Un punto de control es un objeto `bytes` (almacenamiento
contiguo de bajo nivel, como el archivo de partida).

## LineaTiempo (`modelo/nucleo/lineaTiempo.py`)

La historia de la partida tal como quedó. La Partida real la alimenta; las
consultas trabajan sobre copias.

| Campo | Tipo | Descripción |
|---|---|---|
| `_k` | int ≥ 1 | Acciones del jugador por bloque (`--checkpoint-cada`, por omisión 25). |
| `_bloques` | `ArregloArbol` de `Bloque` | En orden de historia; acceso a la posición i en O(log n). |
| `_contenidos` | `ListaEnlazada` de `(id_sala, ContenidoSalaDTO)` | Contenido inicial de cada sala, registrado la primera vez que la partida real lo carga (R5). |
| `_acciones` | int | Acciones del jugador que siguen existiendo (n). |
| `_copiador` | `CopiadorEstado` (puerto) | Toma y restaura puntos de control (R1). |

Operaciones:

- `antes_de_accion(partida, tiempo_decision)`: si `_acciones % K == 0`, toma un
  punto de control y abre un `Bloque` nuevo. O(tamaño del estado) cada K
  acciones; O(1) las demás.
- `registrar_accion(accion, tiempo_decision)`: agrega una `EntradaAccion` al
  último bloque y suma 1 a `_acciones`. O(1).
- `al_usar_pergamino(partida)`: quita la última `EntradaAccion` (y el último
  bloque si se quedó sin su primera acción) y agrega una `AjustePergamino` con
  el inventario y los pergaminos en el suelo de la partida real (R6).
  O(1 + log n + salas) por pergamino.
- `registrar_contenido(id_sala, contenido)`: O(1) (solo la primera vez por sala).
- `reconstruir_instante(t, servicio_real) -> Partida` y
  `reconstruir_accion(k, servicio_real) -> Partida`: copia nueva, sin diario,
  vista ni registro (R2, R3). Aplica o deshace como mucho K acciones.
- `ultimo_reloj` y `acciones`: para validar consultas (FR-003).

Reglas de validación: `K ≥ 1`; t entero ≥ 0 y ≤ reloj actual; 1 ≤ k ≤ n + 1.
Sin estado propio fuera de lo descrito: consultar no modifica nada (FR-011).

## Bloque

| Campo | Tipo | Descripción |
|---|---|---|
| `punto_control` | bytes | Estado completo justo antes de la primera acción del bloque (formato 4 con `con_linea` falso). |
| `primera_accion` | int | Número (desde 1) de la primera acción del bloque. |
| `tiempo_inicio` | int | Instante de decisión de la primera acción (clave de la búsqueda binaria). |
| `entradas` | `ListaDoble` de `EntradaAccion` o `AjustePergamino` | En orden; quitar la última es O(1). |

Invariantes: a lo sumo K `EntradaAccion` por bloque; los `tiempo_inicio` crecen
con la posición; un bloque existe solo si su primera acción sigue existiendo.

## EntradaAccion

| Campo | Tipo | Descripción |
|---|---|---|
| `accion` | `Accion` | La acción del jugador (inmutable, la misma clase que va al log). |
| `tiempo_decision` | int | Tiempo del turno del jugador en que la tomó. |

## AjustePergamino

| Campo | Tipo | Descripción |
|---|---|---|
| `tiempo` | int | Instante al que volvió el reloj al usar el pergamino. |
| `inventario` | `ListaEnlazada` de `(id_objeto, id_ficha, equipado)` | Inventario de la partida real después del pergamino, en orden. |
| `pergaminos_suelo` | `ListaEnlazada` de `(id_sala, id_objeto, id_ficha)` | Pergaminos que quedaron en el suelo (D50). |

Al re-simular: la copia deja su inventario y sus pergaminos en el suelo iguales
a estos, moviendo objetos por `id_objeto` o creándolos desde su ficha.

## ArregloArbol (`modelo/estructuras/arregloArbol.py`)

Arreglo de nodos en un árbol binario completo; la posición i (desde 1) se
alcanza bajando por los bits de i, como el montículo de D23.

| Operación | Costo |
|---|---|
| `obtener(i)` | O(log n) |
| `agregar_al_final(dato)` | O(log n) |
| `quitar_ultimo()` | O(log n) |
| `__len__` | O(1) |

## ServicioSoloLectura (`modelo/datos/servicioSoloLectura.py`)

Lo que `Partida` le pide al servicio, sin red: `asegurar_contenido` desde
`LineaTiempo._contenidos`; `precargar` vacío; `resolver_fichas` con
`ServicioDatos.resolver_fichas_sin_red` (memoria y disco; error claro si falta);
`datos_cripta` y `esqueleto` delegan en el servicio real (ya están en memoria).

## Puerto CopiadorEstado (`modelo/puertos/copiadorEstado.py`)

`tomar(partida) -> bytes` y `restaurar(datos, servicio) -> Partida`.
Adaptador: `PartidaBinaria.a_bytes` y `PartidaBinaria.desde_bytes` (R1).
Los bytes de un punto de control llevan la bandera `con_linea` en falso y no
tienen la sección de la línea; `desde_bytes` la usa para distinguirlos de un
guardado del mismo formato 4 (contracts/partida-binaria.md, análisis F3).

## ResumenInstante (`vista/estadoVista.py`, DTO inmutable)

| Campo | Contenido |
|---|---|
| `pedido` | El texto consultado (`"120"` o `"#3"`). |
| `reloj` | Instante del estado mostrado. |
| `numero_accion` | Próxima acción del jugador en ese estado (k). |
| `sala` | id y nombre. |
| `vida`, `vida_max`, `ataque`, `defensa`, `velocidad` | Estadísticas del jugador. |
| `inventario` | Objetos con su nombre y marca de equipado. |
| `efectos` | Tipo y tiempo restante. |
| `enemigos` | Nombre, vida y vida máxima de los enemigos de esa sala. |
| `mapa` | `MapaConocidoVisible` de ese instante (feature 002). |
| `aviso` | `None` o "La partida terminó antes, en el instante F" (FR-013). |

Se arma una sola vez en el Controlador (`ConstructorResumen`) y se usa igual en
el panel de la ventana y en el texto de `--replay … --hasta`.

## Partida (cambios)

- `linea`: la `LineaTiempo` conectada, o None (copias, pruebas sin línea).
- `aplicar_accion(accion, limite=None)` y `_procesar_eventos(limite=None)`: con
  límite, el bucle se detiene antes del primer evento con tiempo > límite (R3);
  solo lo usan las copias.
- `aplicar_accion` llama a `linea.antes_de_accion` y `linea.registrar_accion`;
  `_usar_pergamino` llama a `linea.al_usar_pergamino`; `_asegurar_contenido`
  llama a `linea.registrar_contenido`.
