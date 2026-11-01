# Contrato de datos de entrada: esqueleto y catálogo

Aplica por igual a la fuente en línea (API) y a la fuente sin conexión
(`datos_offline/`, `--offline`): las dos pasan por el mismo convertidor (FR-021).

## Salida del esqueleto

`GET /criptas/{id}/salas?pagina=n` → `salas[i].salidas.<DIR>`

```json
{
  "sala": 7,
  "cerrada": true,
  "llave": "itm_llave_bronce",
  "cierre_automatico": 300,
  "costo": 250
}
```

| Campo | Obligatorio | Tipo | Regla |
|---|---|---|---|
| `costo` | no | entero | ≥ 1. Ausente o `null` = no declarado (vale 100 si la otra cara tampoco declara). `true`/`false`, `0`, negativos, decimales o texto: **error de datos** que nombra la sala y la dirección |

Validez: mientras coincida la versión de la cripta (`version.json` /
`GET .../version`).

Regla entre caras (FR-002, FR-027): la contraparte de `A.<DIR> → B` es
`B.<opuesta(DIR)>` si conduce a `A`.

| A→B | B→A | Resultado |
|---|---|---|
| — | — | 100 en ambos sentidos |
| k | — | k en ambos sentidos |
| — | k | k en ambos sentidos |
| k | k | k |
| k₁ | k₂ ≠ k₁ | la cripta se rechaza: `DatosInvalidos("Las caras de la puerta entre la sala A (DIR, costo k₁) y la sala B (DIR', costo k₂) declaran costos distintos")` |
| k | no existe | k (salida de un solo sentido) |

## Ficha de enemigo cazador

`GET /catalogo?ids=...` → elemento con `clase: "enemigo"`

```json
{
  "id": "ent_acechador",
  "nombre": "Acechador",
  "clase": "enemigo",
  "vida_max": 14,
  "ataque": 5,
  "defensa": 1,
  "velocidad": 110,
  "comportamiento": "cazador",
  "rango": 400,
  "suelta": []
}
```

| Campo | Obligatorio | Tipo | Regla |
|---|---|---|---|
| `comportamiento` | sí | texto | se reconoce "cazador" (en minúsculas, por prefijo, igual que los otros comportamientos) |
| `rango` | sí si es cazador | entero | ≥ 0, en unidades de costo. Ausente o inválido en un cazador: **error de datos** que nombra la ficha. En otros comportamientos se ignora |

Validez: mientras coincida la versión global del catálogo. La caché local de
fichas guarda y devuelve `rango` sin cambios.

(Los ids y valores del ejemplo son ilustrativos: no aparecen en el código,
principio IV.)
