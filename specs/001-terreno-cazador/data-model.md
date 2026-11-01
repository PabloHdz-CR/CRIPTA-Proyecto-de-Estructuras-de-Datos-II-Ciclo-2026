# Data Model: Terreno y cazador

**Feature**: `001-terreno-cazador` | **Fecha**: 2026-10-31 | **Plan**: [plan.md](plan.md)

Notación: los campos **nuevos** van en negrita; los demás ya existen. Los
atributos internos llevan prefijo `_` y se exponen con propiedades (restricción
de la constitución). Ninguna estructura usa dict, set, list de Python ni
heapq.

---

## Datos de entrada (puertos / DTO)

### SalidaDTO (`cripta/modelo/puertos/dto.py`)

| Campo | Tipo | Regla |
|---|---|---|
| direccion | str | N, S, E u O |
| sala | int | id de la sala destino |
| cerrada | bool | por omisión False |
| llave | str \| None | |
| cierre_automatico | int \| None | |
| **costo** | **int \| None** | **None = no declarado. Si viene, entero ≥ 1 (sin bool). Si no, se lanza error de datos con sala y dirección (FR-001, FR-003)** |

Se conserva `None` (y no se pone 100 enseguida) porque la regla de las dos caras
(FR-027) distingue "no declarado" de "declarado 100".

### FichaEnemigoDTO (`dto.py`)

| Campo | Tipo | Regla |
|---|---|---|
| comportamiento | str | se agrega el valor reconocido "cazador" |
| **rango** | **int \| None** | **Obligatorio si el comportamiento es cazador: entero ≥ 0, sin bool. Se ignora en los demás comportamientos. Ausente o inválido en un cazador: error de datos (FR-009)** |

Validez: la ficha vale mientras coincida la versión global del catálogo
(contrato existente, FR-020).

---

## Modelo

### Salida (`cripta/modelo/mundo/salida.py`)

| Campo | Tipo | Notas |
|---|---|---|
| direccion | str | |
| destino | int | id; se mantiene para el guardado y el log |
| **_cerrada / propiedad `cerrada`** | **bool** | **el setter incrementa `RegistroPuertas.version` (R2). Todo el código actual que lee o escribe `salida.cerrada`, incluidos Mutador, Diario y carga, sigue funcionando sin cambios** |
| llave, cierre_automatico, evento_cierre | | sin cambios |
| **_costo_declarado** | **int \| None** | **lo que trajo el esqueleto** |
| **_costo / propiedad `costo`** | **int ≥ 1** | **costo efectivo, resuelto en el enlace según la tabla de R8** |
| **_origen / `origen`** | **Sala** | **referencia directa, fijada en el enlace** |
| **_sala_destino / `sala_destino`** | **Sala** | **referencia directa, fijada en el enlace** |
| **_registro** | **RegistroPuertas \| None** | **None antes del enlace: cambiar `cerrada` en ese estado no avisa a nadie (construcción y carga)** |

`transitable()` sigue siendo `not cerrada`.

### Sala (`cripta/modelo/mundo/sala.py`)

| Campo | Tipo | Notas |
|---|---|---|
| salidas | tupla (N, S, E, O) | sin cambios |
| **_entrantes / `entrantes`** | **ListaEnlazada de Salida** | **salidas de otras salas cuyo destino es esta. Se llena en el enlace en orden de construcción, que es determinista** |
| **_sello_mapa / `sello_mapa`** | **int** | **número del último cálculo de distancias que la tocó (R5)** |
| **_distancia_mapa / `distancia_mapa`** | **int** | **válida solo si `sello_mapa` coincide con el sello del mapa vigente. Las dos se escriben juntas con `anotar_distancia(sello, distancia)`, en O(1)** |

### RegistroPuertas (nuevo, `cripta/modelo/mundo/registroPuertas.py`)

| Campo | Tipo | Notas |
|---|---|---|
| _version / `version` | int | arranca en 0; `avisar_cambio()` lo incrementa |

Hay una instancia por Mundo, compartida por todas sus salidas. No forma parte
del estado reversible: deshacer la incrementa en lugar de restaurarla, porque
lo único que importa es que *cambie* (R2).

### Mundo (`cripta/modelo/mundo/mundo.py`)

- **`registro_puertas`**: el RegistroPuertas de este mundo.
- **`enlazar()`**: se ejecuta una vez, tras `agregar_esqueleto` y tras cargar
  una partida guardada. Para cada salida resuelve `origen` y `sala_destino`,
  la agrega a `entrantes` de su destino, resuelve el costo efectivo con su
  contraparte (R8) y conecta el registro. Si las dos caras declaran costos
  distintos lanza `DatosInvalidos` con ambas salas y ambos costos (FR-027).
  Costo: O(salas²) por la búsqueda lineal por id, una sola vez.
- Que una salida apunte a una sala inexistente ya es un error del esqueleto
  (`ErrorCripta`) y conserva su mensaje actual.
- **`_sello_mapa` / `sello_mapa`** y **`nuevo_sello_mapa()`**: el contador de
  sellos de los cálculos de distancias vive en el Mundo, no en cada mapa.
  Cada cálculo reserva el siguiente con `nuevo_sello_mapa()`. Así, si dos
  mapas usan el mismo mundo (por ejemplo, el bench que compara P1, P2 y P3),
  cada uno detecta que otro sobrescribió los campos de las salas (el sello
  del mundo ya no es el suyo) y recalcula, en vez de leer distancias ajenas.

### MapaDistancias (nuevo, `cripta/modelo/mundo/mapaDistancias.py`)

Mapa de distancias de costo mínimo **hacia** la sala del jugador (R1 a R3).
Lo posee la Partida (`Partida.mapa_distancias`, creado en `iniciar()` después
de `enlazar()`); hay uno por partida.

| Campo | Tipo | Notas |
|---|---|---|
| _sello | int | sello de su último cálculo, reservado con `Mundo.nuevo_sello_mapa()`; 0 = todavía no se calculó |
| _id_objetivo | int \| None | sala del jugador cuando se calculó |
| _version_puertas | int | `registro_puertas.version` cuando se calculó |
| _cota | int | costo máximo explorado |
| _cota_reutilizable | int | la cota anterior si el objetivo y la versión no cambiaron, o 0; la lee `_cota_nueva` |
| _salas_examinadas / `salas_examinadas` | int | contador acumulado, para el bench y FR-026 |
| _examinadas_ultimo / `examinadas_ultimo_calculo` | int | salas examinadas por el último cálculo: las fijadas a costo ≤ cota y sus vecinas inmediatas (FR-026(b), SC-004) |
| _calculos / `calculos` | int | cuántas veces se recalculó (bench) |

Operaciones:

- `asegurar(id_objetivo, cota_minima)`: recibe el **id** de la sala del
  jugador, no la Sala, para no buscarla en el mundo (búsqueda lineal, D32)
  cuando el mapa sigue valiendo, que es lo más común entre los cazadores de
  un mismo ciclo; solo la busca al recalcular. Reutiliza el mapa si el
  objetivo y la versión de las puertas no cambiaron, el sello del mundo
  sigue siendo el suyo y la cota es ≥ `cota_minima`. Si no, recalcula desde
  cero con la cota que devuelve `_cota_nueva(cota_minima)`.
- `_cota_nueva(cota_minima)`: la regla de la cota, aislada para que las
  subclases del bench (P2, P3) sobrescriban solo este método. La política se
  decide con el bench (research.md R3; plan.md, "Política de cota del mapa").
  La base es P1: `max(cota_anterior si el objetivo y la versión no
  cambiaron, cota_minima)`.
- El cálculo es un Dijkstra hacia atrás por `entrantes` abiertas, con el
  `HeapMinimo` y eliminación perezosa (R6), sin pasar de la cota: una vecina
  a más de la cota queda anotada (cuenta como examinada) pero no entra al
  heap.
- `distancia(sala) -> int | None`: devuelve la distancia guardada solo si el
  sello de la sala coincide con el del mapa, ese sello sigue siendo el último
  del mundo **y** la distancia es ≤ `_cota`.
  En cualquier otro caso devuelve None: sala no alcanzada (infinito), o un
  valor provisional mayor que la cota, por ejemplo el de una vecina de una
  sala del borde que se anotó sin llegar a fijarse. Así el mapa solo expone
  distancias exactas. O(1). Ocultar esos valores no cambia ninguna decisión:
  una sala con distancia real mayor que la cota nunca forma parte de una ruta
  admisible para un cazador de rango ≤ cota (research.md R3).

Entrada del heap (**EntradaMapa**, clase interna): (distancia, sala) con
`__lt__` por (distancia, sala.id). El orden es total porque dos entradas
vivas de la misma sala nunca tienen la misma distancia (solo se inserta al
mejorar).

### Cazador (nuevo comportamiento, `cripta/modelo/actores/comportamientos.py`)

| Campo | Tipo | Notas |
|---|---|---|
| NOMBRE | "cazador" | |
| _rango | int ≥ 0 | sale de la ficha |

`decidir_sin_jugador(enemigo, partida)`:

1. `mapa.asegurar(id de la sala del jugador, rango)`.
2. Recorre las salidas abiertas de la sala del cazador, en orden fijo N, S, E,
   O. Para cada `u → v` con `distancia(v)` definida calcula
   `t = costo + distancia(v)` y se queda con el menor `t`. En un empate gana
   el menor `v.id` (FR-014).
3. Si no hay candidata o `t > rango`, devuelve `Esperar()`. Si no, devuelve
   `Mover(dirección de esa salida)`.

El paso "comparte sala, entonces ataca" ya lo hace `Comportamiento.decidir`
(FR-010). `crear_comportamiento` recibe la ficha (o el nombre y el rango) para
construir `Cazador(rango)`, reconocido por el prefijo "cazad", en minúsculas.

### Costo de las acciones (`cripta/modelo/nucleo/partida.py`)

- **`costo_de(actor, accion) -> int`**: si `accion` es `Mover` y existe la
  salida en esa dirección de la sala **actual** del actor, devuelve su `costo`.
  Si no, devuelve `accion.costo_base`. Se evalúa **antes** de ejecutar la
  acción (R7).
- `aplicar_accion` (jugador) y `EventoAccionActor.ejecutar` (enemigos)
  programan el siguiente turno con `costo_de(...)` en vez de
  `accion.costo_base`.
- `cambiar_velocidad` no cambia (FR-008).

### Error nuevo (`cripta/modelo/puertos/errores.py`)

- **`DatosInvalidos(ErrorCripta)`**: datos de la cripta o del catálogo
  inconsistentes entre sí (FR-027) o fuera de rango. El mensaje identifica
  salas, dirección y valores.

---

## DTOs de la vista (`cripta/vista/estadoVista.py`)

| DTO | Campo nuevo | Tipo | Origen |
|---|---|---|---|
| SalidaVisible | **costo** | **int \| None** | `salida.costo`; None si no hay salida en esa dirección (FR-023) |
| ActorVisible | **es_cazador** | **bool** | el comportamiento del enemigo es Cazador (FR-024) |

---

## Ciclo de vida y estados

```text
JSON del esqueleto ──convertidor──▶ SalidaDTO(costo opcional)
        │
        ▼
Mundo.agregar_esqueleto ──▶ Salida(_costo_declarado, sin registro)
        │
        ▼
Mundo.enlazar() ──▶ costo efectivo, origen/destino, entrantes, registro conectado
        │                     └─ caras con costos distintos ──▶ DatosInvalidos (la partida no empieza)
        ▼
Partida en curso: cambiar `cerrada` ──▶ registro.version += 1 ──▶ el mapa queda obsoleto
                  jugador cambia de sala ──▶ el mapa queda obsoleto
                  turno de cazador ──▶ mapa.asegurar() (recalcula solo si está obsoleto) ──▶ decisión O(salidas)
```

Mapa: **vacío** → (asegurar) → **vigente** → (puerta cambia / jugador cambia de
sala / se pide cota mayor) → **obsoleto** → (asegurar) → **vigente**.
