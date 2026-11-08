# Contrato: texto del reporte de resolubilidad

**FR**: FR-007 a FR-016, FR-031; **SC**: SC-004

Un solo formateador produce estas líneas a partir del `ResultadoResolubilidad`.
`--verificar` las imprime y la Vista las muestra sin cambiarlas. Dos
verificaciones de la misma cripta dan el mismo texto carácter por carácter
(SC-004).

Convenciones:
- Los ids se escriben tal cual; las salas, como `sala N`; una puerta, como
  `sala O DIR -> sala D` (DIR ∈ N, S, E, O).
- Una ubicación es `sala N` o `sala N (suelta ENEMIGO)`. Varias van separadas
  por `; `, en orden (sala, enemigo).
- Los conteos van entre paréntesis después del título de cada sección.
- Sangría de dos espacios. Sin espacios al final de la línea.

## RESOLUBLE

```text
Cripta ID (versión V): RESOLUBLE
Orden de obtención de llaves (3):
  1. itm_a: sala 4
  2. itm_b: sala 9 (suelta e-7)
  3. itm_salida: sala 15
```

Cada llave muestra la ubicación por la que se obtiene en ese orden (R2).

## NO_RESOLUBLE

```text
Cripta ID (versión V): NO RESOLUBLE
Motivo: la llave de salida itm_salida no se puede obtener.
Llaves no obtenibles (2):
  - itm_salida: sala 15
  - itm_x: sin ubicación
Frontera bloqueada (2):
  - sala 3 S -> sala 7: requiere itm_salida
  - sala 5 E -> sala 9: sin llave
Ciclos (1):
  1. itm_salida, encerrada por sala 3 S -> sala 7 (requiere itm_salida)
```

Motivo, según el caso (FR-011):
- (a) `Motivo: la llave de salida L no se puede obtener.`
- (b) `Motivo: ninguna salida que requiere L da acceso a la sala de salida S desde la región alcanzable.`
- (b) con sala_salida alcanzada por otro camino: la línea anterior, y además
  `  La sala de salida S solo se alcanza por caminos sin esa salida.`

Ciclos (FR-014, FR-015): cada ciclo va en una línea numerada. Cada paso es
`K, encerrada por PUERTA (requiere Y)`, los pasos van separados por ` -> ` y
el último vuelve a la primera llave. Ejemplo con dos llaves:

```text
  1. k_a, encerrada por sala 2 N -> sala 6 (requiere k_b) -> k_b, encerrada por sala 6 E -> sala 8 (requiere k_a) -> k_a
```

Sin ciclos: `Ciclos: ninguno.`

Las secciones vacías se escriben igual, con conteo 0:
`Llaves no obtenibles (0):` o `Frontera bloqueada (0):`.

## NO_VERIFICADA

```text
Cripta ID: NO SE PUDO VERIFICAR
Motivo: <mensaje del error>
```

## Aviso corto en la partida (FR-019)

Mensaje en la bitácora al iniciar una cripta resoluble:
`La cripta es resoluble. V muestra el reporte.`
