# Contrato: línea de comandos (004)

## `--checkpoint-cada K`

- K entero ≥ 1. Sin la opción, K = 25 (R10).
- Vale para la partida en la ventana, `--replay` y `--bench` no lo usa (el bench
  recorre sus propios valores de K).
- Valor inválido (0, negativo, texto): mensaje `--checkpoint-cada necesita un
  entero mayor o igual que 1` y código de salida 2, antes de abrir la ventana o
  leer el log (FR-022).

## `--replay partida.log --hasta t`

- t entero ≥ 0 (instante del reloj del juego).
- No abre la ventana (constitución III).
- Reproduce el log completo con la línea de tiempo conectada y después imprime
  el resumen del instante t de la historia tal como quedó (FR-013, FR-014).
- Si t es mayor que el reloj final: imprime el estado final y la línea
  `La partida terminó antes, en el instante F.` (FR-013).
- Versión de cripta o catálogo no disponible: el mismo mensaje y código de
  salida 1 que `--replay` (FR-016); no imprime resumen.
- `--hasta` sin `--replay`, o t inválido: mensaje de uso y código de salida 2
  (FR-015).

## Formato del resumen en texto

Una sección por campo de `ResumenInstante`, en este orden, con el mismo texto
que el panel de la ventana:

```text
Instante <reloj> (próxima acción #<k>)
Sala <id> - <nombre>
Vida <vida>/<vida_max>   Ataque <a>   Defensa <d>   Velocidad <v>
Inventario: <objeto> [equipado], ...   (o "vacío")
Efectos: <tipo> (<restante>), ...      (o "ninguno")
Enemigos en la sala: <nombre> <vida>/<vida_max>, ...   (o "ninguno")
Mapa conocido:
  <filas del panel del mapa de la feature 002>
[La partida terminó antes, en el instante F.]
```
