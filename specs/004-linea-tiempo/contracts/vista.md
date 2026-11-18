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
  borra; Enter encola `Comando("historia", (texto,))` (sin texto no encola
  nada); ESC cierra el panel y encola `Comando("cerrar_historia")`, que le dice
  al Controlador que deje de mandar el resumen. Las demás teclas no hacen nada:
  no mueven al jugador ni abren otras selecciones.
- Así quedó en el código (T029, T038): lo escrito, si la consulta está abierta
  y el desplazamiento del resumen viven en `VistaArcade` (cada `EstadoVista`
  trae una `PantallaJuego` nueva, como el cursor del mapa de 002); los dígitos
  y `#` llegan por `on_text`, así `#` sirve con cualquier distribución de
  teclado, y el eco de la propia H es una letra y no se escribe. Como mucho 12
  caracteres. Con la consulta abierta, el panel de Controles muestra
  `0-9 y #`, `ENTER`, `Flechas` y `ESC`; fuera de ella, la fila `H Historia`.
- Con el panel del mapa abierto, H lo cierra antes de abrir la consulta (igual
  que FR-037 de la feature 002 para las selecciones): encola
  `Comando("alternar_mapa")`.
- `caso_tecla_m` de `prueba_vista_mapa` (002) recorre A a Z en la misma
  ventana; desde 004 cierra la consulta entre tecla y tecla, porque después de
  H la consulta abierta se traga la M.

## Verbo `historia`

- Verbo de sesión: no consume tiempo, no va a `partida.log`, no detiene viajes
  (la detención la hace la tecla H antes, con `interrumpir`).
- El Controlador interpreta `"<t>"` o `"#<k>"`; si es inválido (FR-003) manda
  `mostrar_error` con el motivo y la consulta sigue abierta.
- Con la consulta abierta, el HUD dibuja el motivo dentro del panel, debajo
  de la línea de entrada, partido en filas con `partir_lineas` (sin "…"), y
  no arma el cartel de arriba del mapa, para no tapar el título (FR-027,
  enmienda posterior al código de 59dcbc5). `HudJuego.filas_aviso_historia`
  expone esas filas; `prueba_vista_historia` las revisa a 1024×720 y
  1280×720 con el motivo de «#99999».
- Si es válido, el `EstadoVista` trae `historia: ResumenInstante`; el HUD lo
  dibuja en el panel con `partirLineas`, desplazable con ↑/↓ y RePág/AvPág,
  con el mismo texto que la salida de `--replay … --hasta` (contracts/cli.md).
- ESC con el resumen abierto vuelve a la partida; el reloj no cambió.

## README

La tabla de teclas de la partida agrega **H** (consultar la línea de tiempo).
