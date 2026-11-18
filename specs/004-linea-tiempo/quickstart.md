# Quickstart: validar la línea de tiempo (004)

Desde la carpeta del proyecto, en la rama `004-linea-tiempo`.

## 1. Pruebas automáticas

```bash
py pruebas/ejecutar_pruebas.py
```

```bash
py pruebas/prueba_reglas.py
```

Las pruebas nuevas citan el FR o escenario que cubren (§2.5). La referencia de
las comparaciones es el estado que la partida real tuvo en cada instante de la
historia que quedó (ver research R6).

## 2. Consulta sin interacción

Jugar una partida corta con `py main.py --offline`, salir y luego:

```bash
py main.py --replay partidas/<cripta>.log --hasta 300
```

Esperado: el resumen del instante 300, sin ventana. Con un t mayor que el final
de la partida: el estado final y "La partida terminó antes, en el instante F."
(US3, escenario 1 del Apéndice B).

```bash
py main.py --hasta 300
```

Esperado: mensaje de uso y código de error, sin ventana (FR-015).

## 3. En la ventana (`py main.py --offline`, partida nueva con X)

1. Jugar unas 10 acciones. Apretar **H**, escribir `0` y Enter: el estado
   inicial (sala inicial, vida completa). ESC: el reloj no cambió.
2. **H**, `#3`, Enter: el estado justo antes de la tercera acción.
3. **H** con un instante mayor que el reloj actual: el motivo del rechazo y la
   consulta sigue abierta (escenario 1 del Apéndice B).
4. Usar un pergamino; **H** con el número de la acción revertida: ya no existe
   (escenario 2 del Apéndice B).
5. Ordenar un «ir a» largo y apretar **H** a mitad del viaje: el viaje se
   detiene con "interrumpido" y se abre la consulta.
6. Guardar (G), volver al menú, continuar, y repetir 1 y 2: mismos resúmenes.

## 4. Mediciones

```bash
py main.py --bench --rapido
```

Esperado en `benchLineaTiempo`: consulta peor < 50 ms con el K por defecto en
5000 acciones; tabla de memoria y tiempo para K = 10, 25 y 50 y sin puntos de
control; búsqueda del bloque contra la lineal; recorte del pergamino constante;
y `benchHistorial` con la carga nueva (§5.6).

## 5. Formato anterior

Cargar un guardado de la versión 3 (generado por
`pruebas/generar_guardado_formato_anterior.py`): se reporta incompatible, no se
carga (escenario 6 del Apéndice B).
