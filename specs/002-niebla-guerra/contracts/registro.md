# Contrato de partida.log: comentario de «ir a»

Cambio respecto del formato actual (`cripta/adaptadores/registroArchivo.py`).

```text
CRIPTA <id> <version_cripta> <version_catalogo> <semilla> [marcas...]   # encabezado, sin cambios
MOVER N
# IR_A 17          <- NUEVO: comentario, antes del primer paso de la orden
MOVER E            <- cada paso es un movimiento individual (FR-026)
MOVER E
MOVER S
PERGAMINO          <- si el jugador usa el pergamino con el viaje en curso
```

- Puerto: `RegistroAcciones.registrar_comentario(texto: str) -> None`. El
  Controlador lo llama con `IR_A <id>` cuando la orden fue aceptada, antes de
  aplicar el primer paso. El adaptador escribe `# ` + texto en una línea, en
  modo de solo anexado.
- Una orden rechazada (FR-018) no escribe ni el comentario ni movimientos.
- Lectura: `RegistroArchivo.leer()` salta toda línea que empiece con `#`
  (FR-027). Los logs sin comentarios se leen igual que antes.
- Un comentario no es una acción: no cuenta en el total de pasos del replay
  ni en los controles de avance/retroceso.
- El comentario lleva el id de la sala, no su nombre (los nombres pueden tener
  espacios y repetirse).
