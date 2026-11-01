# Contrato Controlador → Vista (DTOs inmutables)

La Vista solo recibe estos DTOs (principio III). Campos nuevos:

```text
SalidaVisible(frozen)
  direccion: str           # "N" | "S" | "E" | "O"
  estado: str              # SALIDA_ABIERTA | SALIDA_CERRADA_CON_LLAVE | SALIDA_SIN_SALIDA
  costo: int | None        # NUEVO: costo efectivo (100 si no se declaró); None si estado == SALIDA_SIN_SALIDA

ActorVisible(frozen)
  etiqueta: str
  vida: int
  vida_max: int
  es_cazador: bool = False # NUEVO: True si el comportamiento del enemigo es cazador
```

Obligaciones de la Vista:

- Muestra `costo` junto a cada salida con `estado != SALIDA_SIN_SALIDA`,
  abierta o cerrada (FR-023).
- Dibuja a los enemigos con `es_cazador = True` de forma distinguible de los
  demás, con un marcador o un prefijo en la etiqueta del HUD además del color:
  la distinción no depende solo del color (FR-024).

Los valores por omisión mantienen compatibles las pruebas de vista existentes
que construyen estos DTOs a mano.
