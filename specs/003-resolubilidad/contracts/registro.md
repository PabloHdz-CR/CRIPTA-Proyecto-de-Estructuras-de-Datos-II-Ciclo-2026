# Contrato: encabezado del registro de partida

**FR**: FR-020, FR-021

La primera línea del `partida.log` puede llevar, después de los 4 campos
fijos, **palabras de marca** opcionales. Esta feature define una:

```text
CRIPTA <id_cripta> <version_cripta> <version_catalogo> <semilla>            # partida normal (sin cambios)
CRIPTA <id_cripta> <version_cripta> <version_catalogo> <semilla> FORZADA    # partida iniciada con --forzar
```

- `FORZADA` se escribe solo si la cripta no era resoluble (o no se pudo
  verificar) y el jugador la inició con `--forzar` (FR-020).
- El lector acepta, después de los 4 fijos, palabras de marca **conocidas**
  en cualquier orden, cada una a lo sumo una vez. Una palabra desconocida o
  repetida es un error de encabezado (`ErrorCripta`), como hoy.
- Palabras conocidas: `FORZADA`. Otra feature que necesite una marca la agrega
  a esta lista; no hay campos por posición después de la semilla.
- Los logs existentes (4 campos) se leen igual: no hace falta migración.
- `--replay` y el replay en la ventana leen el campo y lo ignoran para
  decidir: nunca verifican ni bloquean (FR-021).
- El archivo binario de partida no cambia (`FORMATO_VERSION` sigue igual).
