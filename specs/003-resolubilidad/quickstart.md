# Quickstart: validar la resolubilidad

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Guía para comprobar la capacidad de punta a punta. Los comandos se corren
desde la raíz del repositorio. Los nombres de pruebas y archivos son los que
fija el plan; `tasks.md` los asigna.

## 1. Requisitos

- Python 3.11 o superior con `requirements.txt` instalado.
- Paquete de pruebas `pruebas/datos/resolubilidad/` (criptas sintéticas con
  `llaves.json`).
- Para el juego sin conexión y el bench: `datos_offline/` descargado de nuevo
  con `python guardar_respuestas.py`, que ahora incluye
  `criptas/<id>/llaves.json`. **Tarea del equipo**: necesita red y que el
  servicio publique `/llaves`. Mientras no se haga, la referencia del bench
  dice SIN DATOS, H5.E1 salta con el mensaje "SIN DATOS" y jugar con
  `datos_offline/` exige `--forzar`.

## 2. Suite automática

```text
py pruebas/ejecutar_pruebas.py
```

Todas pasan, incluidas `prueba_reglas` (sin dict, set, list, heapq, bisect ni
collections en `cripta/`) y las pruebas nuevas de resolubilidad (la tabla de
escenarios hacia pruebas está en [plan.md](plan.md)). Cada escenario de la
spec (H1.E1 a H1.E12, H2.E1 a H2.E4, H3.E1 a H3.E3, H4.E1 a H4.E6, H5.E1 a
H5.E3) está marcado en su prueba con los FR que ejerce (SC-001). H5.E1 salta
con "SIN DATOS" mientras `datos_offline/` no tenga llaves (tasks.md T061 la
vuelve obligatoria).

`prueba_resolubilidad_oraculo` compara el reporte con el oráculo en unas 200
criptas al azar con semilla fija. Si falla, imprime la semilla y la cripta.

## 3. Solo verificación

```text
py main.py --verificar <id> --offline=pruebas/datos/resolubilidad
echo $LASTEXITCODE        # PowerShell (en cmd: echo %ERRORLEVEL%)
```

`--offline` admite las dos formas que lee `FabricaAplicacion._leer_offline`:
`--offline` (carpeta `datos_offline/`) y `--offline=CARPETA`, con el signo
igual y sin espacio. `--offline CARPETA` **no** funciona: la carpeta se
tomaría como otro argumento.

| Cripta del paquete de pruebas | Esperado |
|---|---|
| cadena de llaves A, B, salida | `RESOLUBLE`, orden A, B, salida; código 0 |
| llave_salida detrás de su propia puerta | `NO RESOLUBLE`, ciclo de una llave; código 1 |
| dos llaves en ciclo (`res-ciclo-dos`) | `NO RESOLUBLE`, ciclo `itm_res_ka -> itm_res_kb -> itm_res_ka`; código 1 |
| sin `llaves.json` | `NO SE PUDO VERIFICAR`; código 2 |

No se abre ninguna ventana y no aparecen archivos nuevos en `partidas/`,
`guardados/` ni `puntajes.jsonl` (FR-023). Correr dos veces la misma cripta
da el mismo texto (SC-004). El formato está en
[contracts/reporte.md](contracts/reporte.md).

## 4. Inicio de partida

```text
py main.py --offline=pruebas/datos/resolubilidad
py main.py --offline=pruebas/datos/resolubilidad --forzar
```

1. Sin `--forzar`, una cripta no resoluble muestra la pantalla de reporte;
   ENTER o ESC vuelven al menú y no se crea log (FR-019).
2. Con `--forzar`, la misma pantalla deja seguir con ENTER; la partida
   inicia y su log termina el encabezado con `FORZADA NO_RESOLUBLE` (o
   `FORZADA NO_VERIFICADA` en `res-sin-llaves`)
   ([contracts/registro.md](contracts/registro.md)).
3. En una cripta resoluble, la bitácora dice "La cripta es resoluble. V
   muestra el reporte."; V abre y cierra el panel con el orden de llaves
   ([contracts/vista.md](contracts/vista.md)).
4. Guardar con G, volver al menú y continuar con ENTER: V escribe en la
   bitácora "Esta partida no tiene reporte de resolubilidad." (cargar no
   verifica, FR-021).
5. `py main.py --offline=pruebas/datos/resolubilidad --replay partidas/<log forzado>`
   reproduce sin bloquearse (FR-021).

## 5. Rendimiento

```text
py main.py --bench --rapido
py main.py --bench
```

Tablas de `benchResolubilidad`
([contracts/linea-de-comandos.md](contracts/linea-de-comandos.md)):

- cripta de referencia por debajo de 200 ms: PASA (SC-002), o SIN DATOS si
  `datos_offline/` no tiene llaves;
- cocientes de **salidas examinadas** (no de tiempo) al duplicar las llaves:
  verificación ≤ 2,5 y alternativa ingenua ≥ 3,5, PASA (SC-003);
- "mismo reporte: sí" en todas las filas (FR-035).

Las cifras medidas van a DECISIONES.md (principio VI).

## 6. Presupuesto en línea (opcional, necesita red)

```text
py main.py --verificar <id de una cripta publicada>
py main.py --verificar <el mismo id>
```

El resumen de red de la primera ejecución incluye la consulta de llaves; la
segunda no la repite, porque la caché coincide con la versión (FR-027,
SC-007). Nunca se supera el presupuesto.
