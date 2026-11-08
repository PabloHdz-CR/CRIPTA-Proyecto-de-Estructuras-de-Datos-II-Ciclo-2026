# Contrato: ubicación de llaves

**FR**: FR-004, FR-016, FR-025 a FR-030

## Servicio en línea

`GET /criptas/<id>/llaves`, con el encabezado `X-Cripta-Client-Id` de
siempre. Cuenta como **una** solicitud, más una por cada reintento por 429,
dentro de `presupuesto_solicitudes` (FR-026).

```json
{
  "llaves": [
    {"id": "itm_llave_bronce", "sala": 4},
    {"id": "itm_llave_negra", "sala": 12, "enemigo": "e-1203"}
  ]
}
```

| Campo | Obligatorio | Tipo | Significado |
|---|---|---|---|
| `llaves` | sí | lista | una entrada por ubicación; puede estar vacía |
| `llaves[i].id` | sí | texto no vacío | id de la llave |
| `llaves[i].sala` | sí | entero (no bool) | sala del suelo, o sala donde inicia el enemigo |
| `llaves[i].enemigo` | no | texto o null | instancia que la suelta; ausente o null = en el suelo |

Campos extra se ignoran. Un id repetido es válido: son varias ubicaciones de
la misma llave (FR-016).

## Errores de datos (FR-030)

`DatosInvalidos`, con un mensaje que nombra la entrada, por ejemplo
`"La entrada 3 de la ubicación de llaves no tiene 'sala'"`, cuando:

- la raíz no es un objeto con `llaves` de tipo lista;
- una entrada no es un objeto, le falta `id` o `sala`, o tiene un tipo
  inválido (`id` vacío o no texto, `sala` bool o no entero, `enemigo` no
  texto);
- `sala` no existe en el esqueleto de la cripta (se detecta al armar el
  grafo).

Un error HTTP, un JSON inválido o un tiempo agotado son `ErrorDeRed`, igual
que en las demás consultas.

## Paquete sin conexión

`<carpeta>/criptas/<id>/llaves.json`, con el **mismo** JSON de la respuesta
del API. Se convierte con la misma función, así que entrega las mismas
ubicaciones (FR-029). Si falta el archivo: `ErrorDeRed` ("no se encontró el
archivo offline ..."), que la verificación reporta como NO_VERIFICADA. Nunca
se toma como una lista vacía.

`guardar_respuestas.py` descarga este archivo junto con los demás datos de
cada cripta.

## Caché local

`<carpeta de fichas>/llaves/<id_cripta>.json`:

```json
{"version_cripta": "v7", "llaves": [{"id": "...", "sala": 4}, ...]}
```

Se usa solo si `version_cripta` coincide con la versión de los datos
generales actuales. Si no coincide, si falta o si está dañado, se pide de
nuevo y se sobrescribe (FR-027, FR-028).
