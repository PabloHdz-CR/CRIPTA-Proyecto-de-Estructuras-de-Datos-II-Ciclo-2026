# Contrato: ventana (004)

## Tecla H en la partida

- Solo en `PantallaJuego` durante una partida (no en el replay en la ventana ni
  en otras pantallas) (FR-017).
- Si `EstadoVista.viaje` no es None, H encola primero `Comando("interrumpir")`
  (motivo "interrumpido", excepción deliberada a la regla de la feature 002) y
  después abre la consulta.
- Abre el modo **historia**: una línea de entrada en un panel sobre el mapa,
  con el texto `Historia: instante (120) o acción (#3) - Enter consulta, ESC vuelve`.
- En el modo historia (FR-018): dígitos y `#` se agregan al texto; Retroceso
  borra; Enter encola `Comando("historia", (texto,))`; ESC cierra el panel. Las
  demás teclas no hacen nada: no mueven al jugador ni abren otras selecciones.
- Con el panel del mapa abierto, H lo cierra antes de abrir la consulta (igual
  que FR-037 de la feature 002 para las selecciones).

## Verbo `historia`

- Verbo de sesión: no consume tiempo, no va a `partida.log`, no detiene viajes
  (la detención la hace la tecla H antes, con `interrumpir`).
- El Controlador interpreta `"<t>"` o `"#<k>"`; si es inválido (FR-003) manda
  `mostrar_error` con el motivo y la consulta sigue abierta.
- Si es válido, el `EstadoVista` trae `historia: ResumenInstante`; el HUD lo
  dibuja en el panel con `partirLineas`, desplazable con ↑/↓ y RePág/AvPág,
  con el mismo texto que la salida de `--replay … --hasta` (contracts/cli.md).
- ESC con el resumen abierto vuelve a la partida; el reloj no cambió.

## README

La tabla de teclas de la partida agrega **H** (consultar la línea de tiempo).
