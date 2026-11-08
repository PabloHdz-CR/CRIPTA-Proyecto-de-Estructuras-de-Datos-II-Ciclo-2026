# Contrato: encabezado del registro de partida

**FR**: FR-020, FR-021

La primera línea del `partida.log` puede llevar, después de los 4 campos
fijos, **palabras de marca** opcionales. Esta feature define tres:

```text
CRIPTA <id_cripta> <version_cripta> <version_catalogo> <semilla>                          # partida normal (sin cambios)
CRIPTA <id_cripta> <version_cripta> <version_catalogo> <semilla> FORZADA NO_RESOLUBLE     # forzada: la cripta no era resoluble
CRIPTA <id_cripta> <version_cripta> <version_catalogo> <semilla> FORZADA NO_VERIFICADA    # forzada: no se pudo verificar
```

- `FORZADA` se escribe solo si el jugador inició con `--forzar` una cripta
  NO_RESOLUBLE o NO_VERIFICADA. Siempre va junto a **exactamente una**
  palabra de veredicto, para que el log diga si la cripta no era resoluble o
  si no se pudo verificar (FR-020).
- Una cripta RESOLUBLE iniciada con `--forzar` no lleva palabras de marca.
- El lector acepta, después de los 4 fijos, palabras de marca **conocidas**
  en cualquier orden, cada una a lo sumo una vez. Es un error de encabezado
  (`ErrorCripta`), como hoy:
  - una palabra desconocida o repetida;
  - `FORZADA` sin palabra de veredicto, o con las dos;
  - una palabra de veredicto sin `FORZADA`.
- Palabras conocidas: `FORZADA`, `NO_RESOLUBLE`, `NO_VERIFICADA`. Otra feature
  que necesite una marca la agrega a esta lista; no hay campos por posición
  después de la semilla.
- Los logs existentes (4 campos) se leen igual: no hace falta migración.
- `--replay` y el replay en la ventana leen las marcas y las ignoran para
  decidir: nunca verifican ni bloquean (FR-021).
- El archivo binario de partida no cambia (`FORMATO_VERSION` sigue igual).
