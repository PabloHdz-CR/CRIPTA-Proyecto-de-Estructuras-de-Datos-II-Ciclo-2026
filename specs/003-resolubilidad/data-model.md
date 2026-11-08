# Data Model: Resolubilidad

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md)

Todas las colecciones son `ListaEnlazada` (o `HeapMinimo`, `Pila` y `Cola`
propios); no hay dict, set ni list de Python en `cripta/`. Los DTO son
`@dataclass(frozen=True)`. Los atributos internos de las clases nuevas llevan
prefijo `_` y se leen con propiedades.

---

## 1. Datos de entrada (puerto)

### UbicacionLlaveDTO (`modelo/puertos/dto.py`)

Una entrada de `GET /criptas/<id>/llaves` ([contracts/datos-llaves.md](contracts/datos-llaves.md)).

| Campo | Tipo | Regla |
|---|---|---|
| `id` | str | id de la llave, texto no vacío (FR-030) |
| `sala` | int | sala del suelo, o sala donde **inicia** el enemigo; entero, sin bool (FR-004, FR-030) |
| `enemigo` | str \| None | id de la instancia que la suelta; None si está en el suelo (FR-025) |

Las ubicaciones de una cripta son una `ListaEnlazada` de `UbicacionLlaveDTO`
y pertenecen a una versión de cripta (FR-027). Puede haber varias entradas con
el mismo `id` (FR-016).

### Persistencia (`AlmacenLocal`)

| Método nuevo | Contrato |
|---|---|
| `guardar_llaves(id_cripta, version_cripta, ubicaciones)` | Sobrescribe lo guardado para esa cripta |
| `cargar_llaves(id_cripta, version_cripta)` | `ListaEnlazada` o None si no existe, si la versión no coincide o si el archivo está dañado (FR-027, FR-028) |

Archivo de `AlmacenLocalDisco`: `<carpeta>/llaves/<id_cripta>.json` con
`{"version_cripta": "...", "llaves": [...]}`, en el mismo formato de entrada
que la respuesta del API.

---

## 2. Grafo de verificación (`modelo/resolubilidad/grafoVerificacion.py`)

Se construye de nuevo en cada verificación a partir del esqueleto, de los
datos generales y de las ubicaciones (FR-017), y se descarta al terminar. No
es estado de la partida ni se guarda (principio V).

### NodoSala

| Campo | Significado |
|---|---|
| `id` | id de la sala |
| `salidas` | `ListaEnlazada` de `AristaSalida`, en orden N, S, E, O |
| `llaves_aqui` | `ListaEnlazada` de `NodoLlave` ubicadas en esta sala (por ubicación) |
| `alcanzada` | fase 1: True si es parte de la región alcanzable |
| `indice`, `enlace`, `en_pila`, `componente` | fase 2: Tarjan iterativo (R4) |
| `etiqueta` | fase 2: menor `AristaSalida` (puerta) del grupo que la alcanza, o None |

### AristaSalida

Una cara de puerta, en el sentido en que se recorre (FR-006).

| Campo | Significado |
|---|---|
| `origen`, `destino` | `NodoSala` (referencias directas, resueltas por fusión, R1) |
| `direccion` | N, S, E u O |
| `cerrada` | estado del esqueleto |
| `llave` | `NodoLlave` o None; solo importa si `cerrada` |

Transitable en la verificación ⇔ `not cerrada` o (`llave` no es None y
`llave.obtenida`) (FR-002, FR-005). Requiere llave_salida ⇔ `cerrada` y
`llave` es el nodo de llave_salida (R3).

### NodoLlave

| Campo | Significado |
|---|---|
| `id` | id de la llave |
| `ubicaciones` | `ListaEnlazada` de `UbicacionLlaveDTO`, ordenadas por (sala, enemigo); vacía = "sin ubicación" |
| `puertas` | `ListaEnlazada` de `AristaSalida` cerradas que la requieren |
| `pendientes` | fase 1: puertas que la requieren y se encontraron bloqueadas |
| `disponible`, `obtenida` | fase 1 (entra al heap una vez; se ordena una vez) |
| `indice`, `enlace`, `en_pila`, `componente` | fase 2 |

Orden entre nodos de llave: por `id` como texto (`__lt__`), lo que usa el
`HeapMinimo` de disponibles (FR-009).

### Construcción

1. Nodos de sala ordenados por id; aristas ordenadas por id de destino; una
   fusión resuelve `destino` (un destino inexistente lanza `DatosInvalidos`).
2. Ids de llave de las aristas cerradas con llave, de las ubicaciones y de
   llave_salida, ordenados y deduplicados → `NodoLlave`.
3. Ubicaciones ordenadas por (sala, enemigo) y fusionadas con los nodos de
   sala (una sala inexistente lanza `DatosInvalidos`, FR-030).

---

## 3. Resultado (`modelo/resolubilidad/resultadoResolubilidad.py`)

Datos puros e inmutables que entrega el modelo. No llevan texto de interfaz.

### ResultadoResolubilidad

| Campo | Tipo | Regla |
|---|---|---|
| `veredicto` | str | `RESOLUBLE`, `NO_RESOLUBLE` o `NO_VERIFICADA` (FR-031) |
| `id_cripta`, `version_cripta` | str | de los datos generales (None si no se pudieron obtener) |
| `llave_salida` | str | |
| `sala_salida` | int | la usa el texto del motivo (b); se agregó al implementar (T008) |
| `orden` | ListaEnlazada de `LlaveOrdenada` | solo si RESOLUBLE; todas las obtenibles, cada una una vez (FR-007, FR-008, FR-009) |
| `motivo` | str \| None | `LLAVE_SALIDA_NO_OBTENIBLE` (a) o `SIN_PUERTA_DE_SALIDA` (b) si NO_RESOLUBLE (FR-011) |
| `sala_salida_solo_sin_puerta` | bool | caso (b) con sala_salida alcanzada por otro camino |
| (interno de la fase 1) `entra_por_puerta_salida` | bool | se pone al examinar una salida cerrada que requiere llave_salida, con esa llave obtenida y destino sala_salida, aunque sala_salida ya estuviera alcanzada (H1.E12; research.md R3) |
| `no_obtenibles` | ListaEnlazada de `LlaveNoObtenible` | ordenadas por id (FR-011, FR-013, FR-016) |
| `frontera` | ListaEnlazada de `PuertaFrontera` | ordenadas por (origen, dirección N, S, E, O) (FR-012) |
| `ciclos` | ListaEnlazada de `CicloLlaves` | uno por grupo, ordenados por el menor id del grupo (FR-014, FR-015) |
| `error` | str \| None | mensaje si NO_VERIFICADA |
| `salidas_examinadas` | int | para el bench (FR-033) |

Un resultado RESOLUBLE puede tener llaves no obtenibles. No se muestran en el
reporte (Assumption: no se exigen), pero quedan en el resultado para las
pruebas.

### LlaveOrdenada
`id`, `ubicacion` (`UbicacionLlaveDTO`: la primera ya alcanzada al elegirla, R2).

### LlaveNoObtenible
`id`, `ubicaciones` (`ListaEnlazada` de `UbicacionLlaveDTO`; vacía = sin ubicación).

### PuertaFrontera
`origen` (int), `direccion` (str), `destino` (int), `llave` (str \| None = "sin llave").

### CicloLlaves
`pasos`: `ListaEnlazada` de `PasoCiclo(llave, puerta)`. `llave` es K y
`puerta` es una `PuertaFrontera` (origen, dirección, destino, llave Y): la
salida que encierra a K. La llave del paso siguiente es Y. El último paso vuelve a la
primera llave (FR-015).

### Transiciones de veredicto

```text
error al obtener datos o armar el grafo ──► NO_VERIFICADA
fase 1 termina:
  llave_salida obtenida y entra_por_puerta_salida ──► RESOLUBLE (+ orden)
  llave_salida no obtenida ──► NO_RESOLUBLE, motivo (a)  ─┐
  en otro caso            ──► NO_RESOLUBLE, motivo (b)  ─┴► fase 2: frontera, no obtenibles, ciclos
```

---

## 4. Interfaz y registro

### ReporteResolubilidadVisible (`vista/estadoVista.py`)

| Campo | Tipo | Regla |
|---|---|---|
| `veredicto` | str | el mismo del resultado |
| `lineas` | ListaEnlazada de str | el texto canónico de [contracts/reporte.md](contracts/reporte.md) |
| `puede_continuar` | bool | True solo en la pantalla de una cripta no resoluble con `--forzar` |

`EstadoVista.resolubilidad: ReporteResolubilidadVisible | None`, al final,
con nombre y con None por omisión. Es None en el replay y en una partida
cargada (FR-021). En una partida cargada, V manda el verbo de sesión
`ver_resolubilidad` y `ControladorJuego` escribe en la bitácora "Esta partida
no tiene reporte de resolubilidad."; en el replay, V no hace nada.

### EncabezadoPartida (`modelo/puertos/registroAcciones.py`)

Gana `forzada: bool = False` y `veredicto_forzado: str | None = None`
(`NO_RESOLUBLE` o `NO_VERIFICADA`; None si no es forzada) (FR-020). Se
escriben como las palabras de marca `FORZADA` y el veredicto, después de los 4
campos fijos. Formato en [contracts/registro.md](contracts/registro.md).

---

## 5. Validaciones por requisito

| Regla | Dónde | FR |
|---|---|---|
| Entrada sin id, sin sala, tipos inválidos | `convertidorJson.llaves_desde_json` → `DatosInvalidos` | FR-030 |
| Sala de ubicación o destino de salida que no existe en el esqueleto | construcción del grafo → `DatosInvalidos` | FR-030 |
| Falta el archivo de llaves sin conexión | `FuenteOffline._leer` → `ErrorDeRed` → NO_VERIFICADA | FR-029, FR-031 |
| Presupuesto agotado | `ContadorSolicitudes` → `PresupuestoAgotado` → NO_VERIFICADA | FR-026, FR-031 |
| Versión guardada distinta | `cargar_llaves` → None → se pide de nuevo | FR-027, FR-028 |
