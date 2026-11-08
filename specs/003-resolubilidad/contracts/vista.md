# Contrato: Vista

**FR**: FR-019, FR-020, FR-037

La Vista sigue siendo pasiva: solo recibe DTO inmutables
(`ReporteResolubilidadVisible`, ver [data-model.md](../data-model.md) §4) y
manda `Comando`. Nunca conoce el modelo ni el resultado de la verificación.

## Puerto `VistaJuego`

| Método nuevo | Abstracto | Contrato |
|---|---|---|
| `mostrar_resolubilidad(reporte)` | no (como `mostrar_benchmark`) | Muestra la pantalla de reporte. `VistaNula` no hace nada |

`EstadoVista.resolubilidad` lleva el reporte de la partida en curso (None si
no hay, por ejemplo en el replay).

## Pantalla de reporte (antes de la partida)

Se muestra cuando la cripta es NO_RESOLUBLE o NO_VERIFICADA.

| Tecla | `puede_continuar = False` (sin `--forzar`) | `puede_continuar = True` (con `--forzar`) |
|---|---|---|
| ENTER | `Comando("volver")`: vuelve al menú | `Comando("aceptar_resolubilidad")`: inicia la partida forzada |
| ESC | `Comando("volver")` | `Comando("volver")`: no inicia |
| Flecha arriba/abajo, RePág/AvPág | desplaza el texto si no cabe | igual |

La línea de ayuda al pie dice "ENTER volver al menú" o "ENTER jugar de todos
modos · ESC volver", según el caso.

## Tecla V en la partida (FR-019, FR-037)

- **V** abre y cierra un panel superpuesto con `EstadoVista.resolubilidad.lineas`.
  Es estado local de la Vista, como **L** con la bitácora: no manda comando,
  no es acción del jugador, no va al log y no gasta reloj.
- Si `resolubilidad` es None en una partida (por ejemplo, una partida
  cargada: FR-021, cargar no verifica), V manda `Comando("ver_resolubilidad")`
  y la bitácora muestra "Esta partida no tiene reporte de resolubilidad."
  Esa línea no va al log ni gasta reloj.
- En el replay, V no hace nada.
- V no está asignada en el menú, la partida ni el replay. Letras en uso antes
  de esta capacidad: A, B, C, G, L, N, O, P, Q, R, S, U, X. Se coordina con el
  otro integrante del grupo (niebla, ir a, línea de tiempo).
- `prueba_vista_*` comprueba que ninguna otra tecla de la partida quedó
  asignada a V.

## README (FR-037)

En la tabla "Partida" se agrega la fila:

| Tecla | Acción |
|---|---|
| V | Mostrar / ocultar el reporte de resolubilidad (orden de llaves) |

En una sección nueva "Resolubilidad" se explican `--verificar`, `--forzar` y
la pantalla de reporte.
