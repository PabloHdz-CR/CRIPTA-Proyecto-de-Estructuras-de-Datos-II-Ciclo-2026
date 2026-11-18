# Data Model: Niebla de guerra e «ir a»

**Feature**: `002-niebla-guerra` | **Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md)

Todas las colecciones son propias (`ListaEnlazada`, `ListaDoble`,
`HeapMinimo`); no hay dict, set, list de Python, heapq, bisect ni collections
en `cripta/` (principio I).

---

## Constantes de conocimiento (`modelo/mundo/conocimiento.py`)

| Nombre | Valor | Significado |
|---|---:|---|
| `DESCONOCIDA` | 0 | el jugador no sabe nada de la sala |
| `AVISTADA` | 1 | destino de una salida de una sala explorada; solo se conoce su id |
| `EXPLORADA` | 2 | entró al menos una vez, la exploró la antorcha o es la inicial |
| `NO_OBSERVADA` | 0 | la cara nunca se observó |
| `ABIERTA` | 1 | la última observación la vio abierta |
| `CERRADA` | 2 | la última observación la vio cerrada |

Enteros pequeños y no texto: se guardan con el `uentero32` que ya tiene el codificador binario (R9) y se comparan en O(1).

---

## Sala (`modelo/mundo/sala.py`, se amplía)

| Campo | Tipo | Reversible | Descripción |
|---|---|:--:|---|
| `conocimiento` | int | sí (Mutador `ATRIBUTO`) | `DESCONOCIDA`, `AVISTADA` o `EXPLORADA` (FR-001). Por omisión `DESCONOCIDA` |
| `_sello_ruta` | int | no (caché de búsqueda) | sello de la última búsqueda de «ir a» que la tocó (R5) |
| `_costo_ruta` | int | no | costo acumulado de la mejor ruta conocida en esa búsqueda |
| `_paso_ruta` | int | no | clave del primer paso de esa ruta: `id_vecina × 4 + índice_dirección` |
| `_fijada_ruta` | bool | no | la sala ya salió del heap en esa búsqueda |

**Transiciones de `conocimiento`** (solo hacia arriba durante el juego; solo
el Diario las baja al revertir):

```text
DESCONOCIDA ──(destino de una salida de una explorada)──▶ AVISTADA
DESCONOCIDA ──(entrar / antorcha / sala inicial)────────▶ EXPLORADA
AVISTADA    ──(entrar / antorcha)───────────────────────▶ EXPLORADA
```

Una sala que deja de ser `DESCONOCIDA` se agrega al registro de conocidas en
el mismo cambio (ver abajo).

## Salida (`modelo/mundo/salida.py`, se amplía)

| Campo | Tipo | Reversible | Descripción |
|---|---|:--:|---|
| `recordada` | int | sí (Mutador `ATRIBUTO`) | `NO_OBSERVADA`, `ABIERTA` o `CERRADA`: estado de esta cara en la última observación (FR-005 a FR-007). Por omisión `NO_OBSERVADA` |

`cerrada` (estado real) no cambia de significado: es infraestructura y solo la
leen las reglas del juego (movimiento, cazador, verificación).

**Regla de observación** (R3): estando el jugador en la sala A, observar es
`recordada ← ABIERTA si not cerrada else CERRADA` para cada cara de
`A.salidas` y de `A.entrantes`, asignando por el Mutador solo si cambia.

## Mundo (`modelo/mundo/mundo.py`, se amplía)

| Campo | Tipo | Reversible | Descripción |
|---|---|:--:|---|
| `conocidas` | `RegistroConocidas` | sí (Mutador `CONOCIDA_AGREGAR`) | salas no desconocidas, en orden de descubrimiento |
| `_sello_ruta` | int | no | último sello reservado por una búsqueda de «ir a» (como `_sello_mapa` de 001) |

## RegistroConocidas (`modelo/mundo/conocimiento.py`, nuevo)

Envuelve una `ListaDoble` de `Sala`.

| Operación | Costo | Uso |
|---|---|---|
| `agregar(sala)` | O(1) | al pasar de `DESCONOCIDA` a otro estado (vía Mutador) |
| `quitar_ultima(sala)` | O(1) | inverso en el Diario; verifica que la última sea `sala` |
| `__iter__` / `__len__` | O(k) / O(1) | armar el panel (R4) |
| `ordenadas_por_id()` | O(k log k) | copia + `ordenamiento.mezcla`; solo con el panel abierto |
| `reconstruir(mundo)` | O(salas) | después de cargar una partida (R4), una vez por carga |

Invariante: una sala está en el registro si y solo si su `conocimiento` no es
`DESCONOCIDA`, y aparece una sola vez.

## ConocimientoJugador (`modelo/mundo/conocimiento.py`, nuevo)

Servicio del Modelo, uno por Partida. No guarda estado propio: lee y escribe
los campos de arriba por el Mutador.

| Método | Costo | Descripción |
|---|---|---|
| `iniciar(sala_inicial)` | O(grado) | con el Mutador en pausa: inicial `EXPLORADA`, sus destinos `AVISTADA`, observa sus caras (FR-001, FR-003) |
| `entrar(sala, antorcha)` | O(grado) sin antorcha; O(Σ grados de sala y vecinas) con antorcha | explora la sala, aviva sus destinos, observa sus caras; con antorcha explora las vecinas y aviva sus destinos, sin observar sus caras (FR-004, FR-008, FR-009) |
| `observar_cara(salida)` | O(1) | copia el estado real a `recordada` si cambió (FR-005) |
| `estado(sala)` / `recuerdo(salida)` | O(1) | consultas (FR-032) |

## Mutador y Diario (`modelo/nucleo/`, se amplían)

| Tipo | Objetivo | `nuevo` | Inverso en el Diario |
|---|---|---|---|
| `CONOCIDA_AGREGAR` (nuevo) | `RegistroConocidas` | `Sala` | `objetivo.quitar_ultima(nuevo)` |
| `ATRIBUTO` (existente) | `Sala` / `Salida` | `conocimiento` / `recordada` | `setattr` (sin cambios) |

## BuscadorRuta (`modelo/mundo/buscadorRuta.py`, nuevo)

Dijkstra hacia adelante sobre el subgrafo conocido (R5).

| Método | Costo | Descripción |
|---|---|---|
| `primer_paso(origen, destino)` | O((V + E) log V) sobre lo explorado, con parada al fijar el destino | devuelve la `Salida` del primer paso o `None` si no hay ruta conocida (FR-019 a FR-021) |
| `salas_fijadas_ultima` | O(1) | conteo para el bench y las pruebas |

`EntradaRuta`: `(costo, paso, sala)`, ordenada por `(costo, paso, sala.id)`;
orden total y determinista (FR-030).

## ViajeIrA (`modelo/nucleo/viajeIrA.py`, nuevo)

Estado de un viaje en curso. **No es estado del juego**: no se guarda, no se
revierte y no está en el log (FR-026: el log tiene los movimientos). Vive en
el Controlador mientras dura el viaje.

| Campo | Tipo | Descripción |
|---|---|---|
| `destino` | `Sala` | sala explorada elegida |
| `pasos` | int | pasos dados |
| `motivo` | `Optional[str]` | `None` mientras sigue; si no, uno de los motivos de abajo |

**Motivos** (constantes, FR-025): `LLEGADA` "llegada", `ENEMIGOS` "enemigos en
la sala", `DANO` "daño recibido", `SIN_RUTA` "sin ruta conocida", `FIN`
"partida terminada", `PERGAMINO` "pergamino de retroceso", `INTERRUMPIDO`
"interrumpido".

**Validación de la orden** (`Partida.validar_ir_a(id)` → motivo de rechazo o
`None`): destino inexistente o no `EXPLORADA` → "Esa sala no está explorada."
(el mismo texto para ambos, FR-018); destino = sala actual → "Ya estás en esa
sala."; sin primer paso → "No hay ruta conocida hasta esa sala.".

**Ciclo de un paso** (lo dirige el Controlador):

```text
1. paso ← buscador.primer_paso(sala_actual, destino)
2. si paso es None: motivo ← SIN_RUTA (no se aplica nada: sin tiempo)
3. resultado ← partida.aplicar_accion(Mover(paso.direccion))   # intervalo propio del Diario
4. registro.registrar_accion(...)                               # MOVER <dir>
5. motivo ← FIN si terminada; ENEMIGOS si resultado.entro_con_enemigos;
           DANO si resultado.dano_recibido; LLEGADA si sala_actual es destino
```

## ResultadoAccion (`modelo/nucleo/resultadoAccion.py`, se amplía)

| Campo | Tipo | Descripción |
|---|---|---|
| `entro_con_enemigos` | bool (por omisión False) | el movimiento entró a una sala con enemigos activos o dormidos, medido antes de activarlos |
| `dano_recibido` | bool (por omisión False) | `Partida.danar` dañó al jugador durante la acción o los eventos que la siguieron |

Transitorios: `Partida` los limpia al empezar cada `aplicar_accion`.

## DTOs de la Vista (`vista/estadoVista.py`, se amplían)

| DTO | Campos |
|---|---|
| `SalidaConocidaVisible` (nuevo) | `direccion`, `destino` (id), `costo`, `estado` (`"abierta"`, `"cerrada"`, `"no observada"`) |
| `SalaConocidaVisible` (nuevo) | `id`, `nombre` (None si avistada), `explorada`, `actual`, `salidas` (tupla de 4 `SalidaConocidaVisible` o None; vacía si avistada) |
| `MapaConocidoVisible` (nuevo) | `salas` (`ListaEnlazada` de `SalaConocidaVisible`, ordenadas por id), `cantidad_exploradas`, `cantidad_avistadas` |
| `ViajeVisible` (nuevo) | `destino_id`, `destino_nombre`, `pasos` |
| `EstadoVista` (se amplía) | `mapa: Optional[MapaConocidoVisible] = None` (solo con el panel abierto), `viaje: Optional[ViajeVisible] = None` |

Todos `frozen=True`, con valores por omisión para no romper los DTOs que las
pruebas arman a mano.

## Archivo de partida (`adaptadores/partidaBinaria.py`)

Ver [contracts/partida-binaria.md](contracts/partida-binaria.md):
`FORMATO_VERSION = 3`, un `uentero32` de `conocimiento` por sala y uno de `recordada`
por salida.
