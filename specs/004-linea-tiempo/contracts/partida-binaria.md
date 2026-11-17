# Contrato: archivo de partida, formato 4 (004)

`FORMATO_VERSION = 4`. Todo lo del formato 3 (feature 002) sigue igual y en el
mismo orden. Al final se agrega la sección de la línea de tiempo:

```text
k                         entero   (acciones por bloque)
acciones                  entero   (n, acciones que siguen existiendo)
cantidad_contenidos       entero
  por contenido: id_sala (entero) + contenido inicial (enemigos, objetos,
  trampas, con el mismo codificador que las salas)
cantidad_bloques          entero
  por bloque:
    primera_accion        entero
    tiempo_inicio         entero
    longitud              entero   + punto de control (bytes crudos, formato 4 sin línea)
    cantidad_entradas     entero
      por entrada: tipo (texto "A" o "P")
        "A": texto de la acción (Accion.texto()) + tiempo_decision (entero)
        "P": tiempo (entero), inventario (cantidad + id_objeto, id_ficha, equipado),
             pergaminos en el suelo (cantidad + id_sala, id_objeto, id_ficha)
```

- Los puntos de control dentro del archivo usan el mismo formato sin la sección
  de la línea (una partida no guarda la línea dentro de sus propios puntos).
- Cargar reconstruye la línea entera; las consultas dan lo mismo que antes de
  guardar (FR-009).
- Un archivo de versión 3 o anterior: `VersionIncompatible` con la versión
  encontrada y la esperada; no se carga (FR-010).
- `cargar_sala` (carga parcial de §4.10) sigue funcionando: el índice de salas
  no cambia de lugar.
