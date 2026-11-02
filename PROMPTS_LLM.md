## Diego:
## Entrada 1
- **Fecha:** 19/09/2026
- **Herramienta:** Claude
- **Prompt:** "En base a las instrucciones del proyecto vamos a 
  empezar por plantear la parte logica y la estructura de clases que vamos a seguir. 
  Necesito que me resumas en Funcionalidades, Requisitos y reglas a seguir, condiciones que tenemos que cumplir y demas. 
  Y me ayudas a plantear el esquema visual para entender la logica detras del juego que piden para luego ponernos a programar 
  y tener una idea mas clara de los problemas a resolver."
- **Uso:** entender cómo organizar los paquetes MVC, el orden de implementación y la lógica detrás del juego Cripta.
## Entrada 2
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "Somos dos compañeros, a mi se me asigno servicio de datos, estructuras, puertos y adaptadores es decir toda la parte tecnica detras de la parte creativa del juego. Respetemos el orden de trabajo. Aspectos clave: 
Los TDA permitidos son lista enlazada simple y doble; heap minimo, maximo y prioridad; cola, pila.
No usemos lambda ya que todavia no lo compendemos bien.
En desiciones de diseño claves quiero que me preguntes que me gustaria implementar, recomiendame las mejores opciones pero yo decido. 
De ahora en adeltante me vas a pasar lo siguiente por prompt resuelto:

```
## Entrada 1
- **Fecha:** 19/09/2026
- **Herramienta:** Claude
- **Prompt:** "En base a las instrucciones del proyecto vamos a 
  empezar por plantear la parte logica y la estructura de clases que vamos a seguir. 
  Necesito que me resumas en Funcionalidades, Requisitos y reglas a seguir, condiciones que tenemos que cumplir y demas. 
  Y me ayudas a plantear el esquema visual para entender la logica detras del juego que piden para luego ponernos a programar 
  y tener una idea mas clara de los problemas a resolver."
- **Uso:** entender cómo organizar los paquetes MVC, el orden de implementación y la lógica detrás del juego Cripta.
```

Ahora iniciemos segun el orden que corresponda. Paso a paso, seccion por seccion, me lo envias al chat, no me hagas archivos como tal para facilitar la correccion."
- **Uso:** dividir el trabajo entre los dos integrantes, ajustar el diseño a los TDA permitidos y planificar el Paso 1 (puerto FuenteDatos, cliente HTTP, modo offline y presupuesto de red).

## Entrada 3
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "P: 1. Espera de red y precarga: ¿cómo la implementamos?
R: Puerto síncrono + FuenteAsincrona con hilo y Cola propia (recomendada)

P: 2. Conteo de solicitudes: ¿dónde va?
R: ContadorSolicitudes inyectado en ClienteHttp (recomendada)

P: 3. Colecciones dentro de los DTO
R: ListaEnlazada propia

agregame tambien tipo asl explicaciones para luego desarrollarlas mejor yo para el documento de desiciones de diseño"
- **Uso:** definir las decisiones de diseño del Paso 1 (asincronía, contador de solicitudes y DTO), implementar las secciones 1.1 (excepciones) y 1.2 (Nodo, ListaEnlazada y Cola) y preparar notas para el Documento de Decisiones.

## Entrada 5
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** Te paso la estructura en que la Api va a responder para crear los DTO.
`````json
{
  "criptas": [
    {
      "id": "string",
      "nombre": "string",
      "salas": 0,
      "dificultad": 0
    }
  ]
}
`````
`````json
{
  "id": "string",
  "version": "string",
  "salas_total": 0,
  "paginas": 0,
  "salas_por_pagina": 0,
  "sala_inicial": 0,
  "sala_salida": 0,
  "llave_salida": "string",
  "presupuesto_solicitudes": 0,
  "inventario_max": 0,
  "jugador": {
    "vida_max": 1,
    "ataque": 0,
    "defensa": 0,
    "velocidad": 1
  }
}
`````

/v1/criptas/{dungeon_id}/version

`````json
{
  "id": "string",
  "version": "string"
}
`````

/v1/criptas/{dungeon_id}/salas

`````json
{
  "pagina": 0,
  "total_paginas": 0,
  "salas": [
    {
      "id": 0,
      "nombre": "string",
      "salidas": {
        "additionalProp1": {
          "sala": 0,
          "cerrada": true,
          "llave": "string",
          "cierre_automatico": 1
        },
        "additionalProp2": {
          "sala": 0,
          "cerrada": true,
          "llave": "string",
          "cierre_automatico": 1
        },
        "additionalProp3": {
          "sala": 0,
          "cerrada": true,
          "llave": "string",
          "cierre_automatico": 1
        }
      }
    }
  ]
}
`````

/v1/criptas/{dungeon_id}/contenido

`````json
{
  "contenido": [
    {
      "sala": 0,
      "enemigos": [
        {
          "instancia": "string",
          "tipo": "string",
          "vida": 0
        }
      ],
      "objetos": [
        "string"
      ],
      "trampas": [
        {
          "instancia": "string",
          "tipo": "string"
        }
      ]
    }
  ]
}
`````

/v1/catalogo/version

`````json
{
  "version": "string"
}
`````

/v1/catalogo

`````json
{
  "entidades": [
    {
      "id": "string",
      "nombre": "string",
      "clase": "enemigo",
      "vida_max": 1,
      "ataque": 0,
      "defensa": 0,
      "velocidad": 1,
      "comportamiento": "guardián",
      "suelta": [
        "string"
      ]
    },
    {
      "id": "string",
      "nombre": "string",
      "clase": "arma",
      "peso": 0,
      "valor": 0,
      "ataque_bonus": 0
    },
    {
      "id": "string",
      "nombre": "string",
      "clase": "armadura",
      "peso": 0,
      "valor": 0,
      "defensa_bonus": 0
    },
    {
      "id": "string",
      "nombre": "string",
      "clase": "pocion",
      "peso": 0,
      "valor": 0,
      "cura": 0,
      "modificador_velocidad": 0,
      "duracion": 0
    },
    {
      "id": "string",
      "nombre": "string",
      "clase": "antidoto",
      "peso": 0,
      "valor": 0
    },
    {
      "id": "string",
      "nombre": "string",
      "clase": "llave",
      "peso": 0,
      "valor": 0,
      "abre": "string"
    },
    {
      "id": "string",
      "nombre": "string",
      "clase": "antorcha",
      "peso": 0,
      "valor": 0,
      "duracion": 0
    },
    {
      "id": "string",
      "nombre": "string",
      "clase": "pergamino_retroceso",
      "peso": 0,
      "valor": 0
    },
    {
      "id": "string",
      "nombre": "string",
      "clase": "trampa",
      "daño": 0,
      "rearme": 0
    }
  ]
}
`````

/v1/catalogo/{catalog_id}

`````json
{
  "id": "string",
  "nombre": "string",
  "clase": "enemigo",
  "vida_max": 1,
  "ataque": 0,
  "defensa": 0,
  "velocidad": 1,
  "comportamiento": "guardián",
  "suelta": [
    "string"
  ]
}
`````
- **Uso:** obtener el contrato exacto del API para definir los DTO de la sección 1.3 y las decisiones de diseño asociadas (fichas del catálogo, estilo de atributos y ubicación del convertidor JSON).

## Entrada 7
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:**

"P: 1. ¿Cómo representamos las fichas del catálogo?
R: Clase base + una subclase por clase del catálogo

P: 2. Estilo de los atributos de los DTO
R: recomiendame lo que sea mas seguro pq pensando en ponerlos siempre publicos nose en lo que puede llegar afectar

P: 3. ¿Dónde va la conversión de JSON a DTO?
R: Módulo compartido convertidor_json.py (recomendada)"
- **Uso:** definir la representación de las fichas, el estilo de atributos de los DTO y la ubicación del convertidor; implementar la sección 1.3 (DTO inmutables y convertidor de JSON) con notas para el Documento de Decisiones.

## Entrada 8
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "sigamos hasta el momento realmente estamos preparando todo para poder programar los puertos y adaptadores!"
- **Uso:** planificar la sección 1.4 (puerto FuenteDatos): contrato de métodos y decisiones de diseño sobre el consumo del presupuesto y los lotes de más de 10 elementos.

## Entrada 9
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "P: 1. ¿Cómo informa el puerto el consumo del presupuesto?
R: Métodos de solo lectura en FuenteDatos (recomendada)

P: 2. Si piden más de 10 ids en una consulta, ¿qué hace el adaptador?
R: Rechazar con un error (recomendada)"
- **Uso:** definir cómo informa el puerto el consumo del presupuesto y cómo se manejan los lotes fuera de rango; implementar la sección 1.4 (puerto FuenteDatos con validación de lotes y excepción LoteInvalido) y preparar notas para el Documento de Decisiones.

## Entrada 10
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "muy buena estructura, sigamos adelante con el contador de solicitudes que es clave."
- **Uso:** planificar la sección 1.5 (ContadorSolicitudes) y definir decisiones sobre seguridad entre hilos, agotamiento del presupuesto y reinicio del contador.

## Entrada 11
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "P: 1. ¿El contador debe ser seguro entre hilos?
R: Protegerlo con Lock de threading (recomendada)

P: 2. ¿Qué pasa al agotarse el presupuesto?
R: Bloquear con PresupuestoAgotado antes de enviar (recomendada)

P: 3. ¿Cuándo se reinicia el contador?
R: Método reiniciar() que llama el controlador al volver al menú (recomendada)"
- **Uso:** definir la seguridad entre hilos, el bloqueo al agotarse el presupuesto y el reinicio del contador; implementar la sección 1.5 (ContadorSolicitudes con Lock, ajuste al puerto con reiniciar_conteo) y preparar notas para el Documento de Decisiones.

## Entrada 12
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "sigamos con Cliente Http"
- **Uso:** planificar la sección 1.6 (ClienteHttp) y definir decisiones sobre los reintentos ante HTTP 429, la espera entre reintentos y el uso de sesión de requests.

## Entrada 13
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "P: 1. ¿Cuántos reintentos ante un HTTP 429?
R: 3 reintentos y luego ErrorDeRed (recomendada)

P: 2. ¿Cuánto esperar antes de reintentar?
R: reintentar_en + 1 segundo de margen (recomendada)

P: 3. ¿Cómo hacemos las solicitudes con requests?
R: requests.Session con cerrojo de una solicitud a la vez (recomendada)"
- **Uso:** definir la política de reintentos ante HTTP 429, la espera entre reintentos y el uso de sesión de requests; implementar la sección 1.6 (ClienteHttp) con pruebas contra un servidor simulado y contra el servicio real, y preparar notas para el Documento de Decisiones.

## Entrada 16
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "Sigamos con FuenteAsincrona para crear la base de las solicitudes."
- **Uso:** Definir decisiones sobre el orden de incorporación de respuestas, la cancelación de solicitudes y el cierre del hilo.

## Entrada 17
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "P: 1. ¿Quién garantiza el orden de incorporación de las respuestas?
R: FuenteAsincrona.recoger_listas() en orden de envío (recomendada)

P: 2. ¿Se pueden cancelar solicitudes pendientes?
R: antes de que programes, explicame otra vez esto no me quedo claro

P: 3. ¿Qué hace cerrar() con las pendientes?
R: Terminar la solicitud en curso y descartar las pendientes (recomendada)"
- **Uso:** aclarar la decisión sobre cancelar solicitudes pendientes en FuenteAsincrona antes de implementar la sección 1.8.

## Entrada 18
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "P: ¿Se pueden cancelar solicitudes pendientes?
R: No permitir cancelar (recomendada)"
- **Uso:** implementar la sección 1.8 (Solicitud y FuenteAsincrona) con las decisiones de orden de incorporación, sin cancelación de solicitudes y cierre que descarta las pendientes; preparar notas para el Documento de Decisiones.

## Entrada 19
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "Todas las pruebas salieron exitosas, sigamos con el paso 2. Ya que estamos describeme cuantos pasos son lo que faltan."
- **Uso:** conocer cuántos pasos y secciones faltan del proyecto y planificar el Paso 2 (MonticuloMinimo para la agenda de eventos) con sus decisiones de diseño sobre almacenamiento, comparación y cancelación de eventos.

## Entrada 20
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "P: 1. ¿Con qué se guarda el montículo por dentro?
R: si con monticulo te refieres a un heap esta bien pero me parece que no vamos a usar list, si usamos una lista enlazada lo creamos en estructuras y de ahi lo implementamos.

P: 2. ¿Cómo compara el montículo dos elementos?
R: Los elementos se comparan con < (método __lt__) (recomendada)

P: 3. ¿Cómo se cancelan y reprograman los eventos?
R: igual si te refieres a un heap minimo como un monticulo si hagamos eso"
- **Uso:** definir el almacenamiento del heap mínimo con nodos enlazados, la comparación con __lt__ y la cancelación perezosa; implementar las secciones 2.1 (NodoArbol, MonticuloBinario y MonticuloMinimo) y 2.2 (pruebas), y preparar notas para el Documento de Decisiones.

## Entrada 21
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "ok hagamos los pasos 2.2 y el 2.3 de un solo con sus respectivas pruebas y procesos"
- **Uso:** ejecutar y verificar el montículo y la prueba 2.2, e implementar la sección 2.3 (alternativas descartadas de la agenda, medidor, reporte y benchmark de la agenda) con sus pruebas y una prueba de reglas del proyecto; preparar notas para el Documento de Decisiones.

## Entrada 22
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "P: 1. ¿Cómo guardamos el montículo de la agenda?
R: Mantener el montículo de nodos como decisión (recomendada)

P: 2. ¿Se permite usar list de Python solo como memoria interna de una estructura propia?
R: cuando queramos usar list de python, usemos la lista enlazada la clase pq para algo la tenemos no?"
- **Uso:** fijar la decisión de mantener el montículo de nodos y la política de no usar listas de Python (usar ListaEnlazada); auditar y corregir el código existente, reemplazar la prueba de reglas por un detector basado en ast que vigila todo el programa, y preparar las notas D23 y D27 para el Documento de Decisiones.

## Entrada 23
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "ahora si ya terminamos el paso 2 tengo entendido, empecemos con el siguiente que me toca trabajar"
- **Uso:** confirmar el cierre del Paso 2 y planificar el Paso 4 (ListaDoble, Pila, PilaAcotada y ColaAcotada para el historial de retroceso, el inventario y la bitácora en pantalla), con sus decisiones de diseño.

## Entrada 24
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "P: 1. ¿Cómo apunta el inventario al objeto que está viendo?
R: Nodos como posiciones que la lista valida (recomendada)

P: 2. ¿Cómo hacemos la pila con tope de 5?
R: Pila simple y PilaAcotada, dos clases (recomendada)"
- **Uso:** implementar las secciones 4.1 (NodoDoble y ListaDoble con nodos como posiciones validadas), 4.2 (Pila y PilaAcotada) y 4.3 (ColaAcotada para la bitácora), con sus pruebas, y preparar las notas D28, D29 y D30 para el Documento de Decisiones.

## Entrada 25
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "P: 1. ¿Qué capacidades medimos en la pila acotada?
R: 5 y capacidades mayores para ver la tendencia (recomendada)

P: 2. ¿Cómo medimos la memoria de la bitácora?
R: Contar nodos y tracemalloc como complemento (recomendada)"
- **Uso:** implementar la sección 4.4 (mediciones de ListaDoble, PilaAcotada y ColaAcotada con sus alternativas descartadas, prueba de la sección y benchTodo), ampliar la prueba de reglas para detectar diccionarios, actualizar el verificador de versiones y preparar la evidencia de D27 a D30 para el Documento de Decisiones.

## Entrada 26
- **Fecha:** 6/10/2026
- **Herramienta:** Claude
- **Prompt:** "P: 1. ¿Tu compañero ya tiene algo de Partida/Mundo/Sala armado que deba conocer?
R: No, todavía no empieza esa parte

P: 2. Política de desalojo de la caché de fichas
R: Implementameos LRU con Lista Doble pero explicamelo mejor en qué consiste

P: 3. ¿Qué guarda AlmacenLocalDisco en esta sección (5.3)?
R: Solo fichas del catálogo por ahora (recomendada)"
- **Uso:** explicar en qué consiste la política LRU con un ejemplo concreto antes de implementar CacheFichas, y plantear la tensión entre la pista del enunciado sobre el costo de búsqueda en caché y la política del equipo de no usar dict en el programa.

## Entrada 27
- **Fecha:** 6/10/2026
- **Herramienta:** Claude
- **Prompt:** "P: ¿Cómo buscamos si una ficha ya está en la caché?
R: Mantener la política sin excepción: búsqueda O(capacidad) en ListaDoble (recomendada)"
- **Uso:** implementar las secciones 5.1 (puerto AlmacenLocal), 5.2 (CacheFichas con política LRU sobre ListaDoble, incluido el ejemplo A-B-C-A-D) y 5.3 (AlmacenLocalDisco persistiendo solo fichas del catálogo como JSON), con sus pruebas verificadas por mutación, y preparar las notas D31, D32 y D33 para el Documento de Decisiones.

## Entrada 28
- **Fecha:** 6/10/2026
- **Herramienta:** Claude
- **Prompt:** "sigamos con el 5.4 y el 5.5!"
- **Uso:** implementar las secciones 5.4 (EsqueletoCripta y PlanificadorPrecarga con BFS determinista) y 5.5 (ServicioDatos: arranque de cripta, precarga sin bloquear, contenido bloqueante, resolución de catálogo en lotes y en cadena, persistencia), con sus pruebas verificadas por mutación; se detectó y corrigió un error real (contaminación de estadísticas de aciertos de caché) durante las pruebas, añadiendo CacheFichas.ver(); preparar las notas D34 a D37 para el Documento de Decisiones.

## Entrada 29
- **Fecha:** 6/10/2026
- **Herramienta:** Claude
- **Prompt:** "P: 1. ¿Cómo resolvemos la vista ordenada mientras no existe Ordenamiento (Paso 6)?
R: Ordenación simple temporal dentro de Inventario, reemplazable después (recomendada)

P: 2. Representación de un objeto dentro del inventario
R: ObjetoInventario (id_instancia + ficha) (recomendada)

P: 3. ¿El Inventario avisa a CacheFichas cuándo una ficha está en uso?
R: Sí: Inventario llama fijar/soltar_referencia automáticamente (recomendada)"
- **Uso:** implementar la sección 5.6 (Inventario: recoger/soltar/usar, navegación en ambos sentidos, equipar con sustitución, vista ordenada temporal, integración automática con CacheFichas) con sus pruebas verificadas por mutación; preparar las notas D38, D39 y D40 para el Documento de Decisiones.

## Entrada 30
- **Fecha:** 6/10/2026
- **Herramienta:** Claude
- **Prompt:** "P: 1. ¿Qué patrón de acceso usamos para medir la caché?
R: Desigual (80/20), muestra mejor la ventaja de LRU (recomendada)

P: 2. ¿Medimos LRU contra FIFO de verdad?
R: Sí, implementar CacheFichasFIFO solo para medir (recomendada)

P: 3. ¿Medimos la búsqueda del esqueleto contra una alternativa indexada?
R: No, dejamos D32 solo con el argumento razonado"
- **Uso:** implementar la sección 5.7 (CacheFichasFIFO como alternativa descartada, benchmark de la caché con patrón de acceso 80/20) con sus pruebas verificadas por mutación; se detectó y corrigió un hueco real en la prueba (no verificaba la reproducibilidad de tasa_de_acierto con semilla explícita); cerrar formalmente el Paso 5 con la evidencia agregada a D31.

## Entrada 31
- **Fecha:** 20/09/2026
- **Herramienta:** Claude
- **Prompt:** "P: 1. ¿Qué dos algoritmos de ordenamiento implementamos?
R: Inserción + Mezcla (recomendada)

P: 2. ¿Con qué criterio decide el selector automático?
R: Tamaño pequeño O casi ordenado -> inserción; si no, mezcla (recomendada)"
- **Uso:** implementar la sección 6.1 (módulo Ordenamiento: inserción y mezcla estables sobre Nodo, ClaveOrden para ordenar por clave calculada, selector automático con inversiones_adyacentes y casi_ordenada) con sus pruebas verificadas por mutación, incluida la estabilidad; preparar las notas D41 y D42 para el Documento de Decisiones.

## Entrada 32
- **Fecha:** 14/10/2026
- **Herramienta:** Claude
- **Prompt:** "Ayudame a implementar PyArcade dentro del proyecto como vista, explicame brevemente en que consiste, como funciona..."
- **Uso:** entender en qué consiste PyArcade y cómo se puede integrar dentro del proyecto.

## Entrada 33
- **Fecha:** 14/10/2026
- **Herramienta:** Claude
- **Prompt:** "En base a la estructura del proyecto armemos el esqueleto de lo que tenemos que implementar en vista."
- **Uso:** Creación de la base para poder implementar la vista con PyArcade.

## Entrada 34
- **Fecha:** 14/10/2026
- **Herramienta:** Claude
- **Prompt:** "Sigamos con la vistaArcade, que es clave para vistaJuego."
- **Uso:** Implementación de vistaArcade para tener la base de comandos importantes.

## Entrada 35
- **Fecha:** 14/10/2026
- **Herramienta:** Claude
- **Prompt:** "sigamos con la pantalla de juego de los pasos descritos a seguir, ya tengo hecho lo que iba antes."
- **Uso:** construir la Pantalla Juego (Paso 5a): mostrar sala, salidas, enemigos, objetos, jugador, inventario, efectos y mensajes, y las teclas de mover/esperar.

## Entrada 36
- **Fecha:** 15/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Quiero que me integres uno cambios que te voy a pasar a este proyecto en el que estas, puedes?"
- **Uso:** preparar la integración de la capa Controlador en la rama.

## Entrada 37
- **Fecha:** 15/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** se pegó el código completo de la capa Controlador generado en otra conversación (mapaEtiquetas, traductorComandos, constructorEstadoVista, controladorJuego, controladorMenu, gestorGuardado, modoReplay, modoBench, reporteFinal, fabricaAplicacion, main.py y los cambios en servicioDatos, diario, registroArchivo y estadoVista), que empezaba con: "El proyecto ya tiene un verificador de reglas (prueba_reglas.py: sin lambda, sin [], sin dict, sin sorted). Lo corro contra mi código:"
- **Uso:** integrar el Controlador al proyecto y verificarlo con prueba_reglas, la batería existente, --replay y --bench.

## Entrada 38
- **Fecha:** 15/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Necesito que el codigo que acabamos de implementar cumpla con esto y si no lo hace, dime que es lo que vas a cambiar [...] Y tiene que estar comentado en el código pq se toma esa decisión de diseño". Se adjuntaron el prompt de reglas del proyecto (arquitectura MVC + adaptadores, TDA permitidos, sin dict ni listas nativas como almacenamiento, ordenamientos propios, sin lambda, justificación con Big O), Cripta_Guia_MVC.md y el enunciado.
- **Uso:** auditar el Controlador contra las reglas; se encontraron 7 puntos (acceso a disco desde el Controlador, duplicación de pergaminos en el Diario, tipado, comentarios de decisión, print en ReporteFinal, partida nueva o cargada, prueba faltante).

## Entrada 39
- **Fecha:** 15/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Sí, aplica los 7 cambios (en el punto 5 deja Reporte documentado)."
- **Uso:** crear los puertos AlmacenPartida, RegistroAcciones/AlmacenRegistros y AlmacenPuntajes con sus adaptadores, corregir el Diario, agregar tipos y comentarios DECISIÓN, "jugar <id> [nueva|cargar]" y prueba_controlador.

## Entrada 40
- **Fecha:** 15/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Espera, primero reviso los cambios."
- **Uso:** revisar el diff antes de hacer el commit.

## Entrada 41
- **Fecha:** 15/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "ahora el codigo cumple con lo que te solicite al 100%?"
- **Uso:** listar lo que faltaba: entradas en DECISIONES.md y PROMPTS_LLM.md, tipado de puertos, paquete --offline incompatible, teclas pendientes en la Vista.

## Entrada 42
- **Fecha:** 15/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "pasame el comentario que vas a poner en el commit"
- **Uso:** redactar el mensaje del commit.

## Entrada 43
- **Fecha:** 15/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Resuelvelos"
- **Uso:** regenerar datos_offline/ con guardar_respuestas.py en el formato de FuenteOffline, completar tipos, agregar benchEtiquetas a --bench y escribir D47–D53 en DECISIONES.md.

## Entrada 44
- **Fecha:** 16/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "como hago para correr el programa o que hace falta?"
- **Uso:** instalar las dependencias (arcade y requests), correr la batería de pruebas y conocer los modos de ejecución (py main.py, --offline, --replay, --bench).

## Entrada 45
- **Fecha:** 16/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** se adjuntó una captura de la pantalla de juego con el texto: "Entre al primer nivel y solo me sale esta pantalla y no puedo interactuar con nada"
- **Uso:** diagnosticar que las flechas sí funcionaban pero la pantalla no lo indicaba, faltaban teclas para recoger, abrir puertas, pergamino, guardar y cargar, y mostrar_error no mostraba nada; agregar esas teclas, la ayuda en pantalla y los avisos en naranja.

## Entrada 46
- **Fecha:** 16/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Primero lo pruebo yo en la ventana, no hagas commit todavía."
- **Uso:** probar los cambios a mano antes de hacer el commit.

## Entrada 47
- **Fecha:** 16/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** se adjuntó una captura de la pantalla de juego con el texto: "Ahora si me puedo mover, pero no hay parte grafica solo texto en la pantalla, a que se debe esto?"
- **Uso:** entender que la vista era solo de texto por diseño (la guía describe una VistaConsola y los datos no traen imágenes) y qué se podía agregar sin tocar el modelo ni el controlador.

## Entrada 48
- **Fecha:** 16/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Quiero que me ayudes a implementar la parte visual"
- **Uso:** crear DibujoSala (sala vista desde arriba con muros, puertas según su estado, enemigos con barra de vida, objetos y jugador), reorganizar PantallaJuego en zonas y agrandar la ventana a 1024x720, respetando prueba_reglas (sin listas, lambda ni dict).

## Entrada 49
- **Fecha:** 16/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "En la pantalla de Derrota quiero que se vea el resumen de la partida"
- **Uso:** agregar a ResultadoFinVisible campos opcionales de red y caché que llena ControladorJuego, y mostrar en PantallaFin los recuadros "Tu partida" y "Red y caché"; ReporteFinal sigue imprimiendo en la terminal (§5.1).

## Entrada 50
- **Fecha:** 16/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Hay alguna manera de mejorar la calidad grafica, siguiendo el reglamento?"
- **Uso:** comparar tres opciones (animación con figuras, sprites que trae arcade en :resources:, y un paquete externo de pixel art que requiere consultar al profesor).

## Entrada 51
- **Fecha:** 16/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Haz el 1 y el 2, estoy esperando la respuesta de mi profesor para confirmar si se puede usar recursos externos"
- **Uso:** crear texturas.py (sprites de Kenney incluidos en arcade, fondo de sala y luz generados con Pillow una vez por sala, ya que ShapeElementList solo se llena con .append, prohibido por prueba_reglas) y animar en DibujoSala la antorcha, el daño, las barras de vida, los enemigos derrotados y el fundido al cambiar de sala.

## Entrada 52
- **Fecha:** 16/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "ya lo probe haz el commit"
- **Uso:** hacer el commit de la vista gráfica, las teclas y la pantalla de fin, dejando fuera los archivos que el juego genera al correr.

## Entrada 53
- **Fecha:** 16/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Sí, agrega guardados/, partidas/, puntajes.jsonl y fichas_guardadas/ al .gitignore."
- **Uso:** ignorar en git los guardados, logs, puntajes y fichas que el juego crea al correr.

## Entrada 54
- **Fecha:** 16/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Agrega los prompts de esta sesión por favor"
- **Uso:** registrar en PROMPTS_LLM.md los prompts de esta sesión.

## Entrada 55
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Mi profesor acaba de confirmar que  si se puede usar recursos externos, busca pixel arts para el proyecto y yo escojo cual implementar"
- **Uso:** comparar paquetes CC0 de pixel art (0x72 DungeonTileset II, Dungeon Crawl 32x32, Kenney Tiny Dungeon + Tiny Creatures) y elegir 0x72.

## Entrada 56
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Ya descargué 0x72_DungeonTilesetII_v1.7.zip, está en mi carpeta Descargas."
- **Uso:** revisar el paquete, copiar al proyecto solo los 37 cuadros usados con su licencia, armar el fondo de cada sala con sus baldosas y usar el caballero, el esqueleto, las puertas, los frascos y la espada (D55).

## Entrada 57
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Lo pruebo yo en la ventana y te digo qué ajustar."
- **Uso:** probar a mano el pixel art antes del commit.

## Entrada 58
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Creo que hay unos bugs, de momento las llaves no se gastan cuando se abre una puerta, y cuantas habitaciones/usos tiene la antorcha? Cuando se acaba la partida y se pone la pantalla de derrota o victoria podria aparecer el modo replay, para analizar la partida y ver que si funcione replay. Hay que hacer que ese menu sea mas visually appealing y mas amigable con el usuario, que tenga una opcion de Name, y que esa nametag aparezca debajo del jugador, y que salgan las opciones para hacer replay a las partidas y para hacer el benchmark, y cambiale el art a la rata gigante, busca uno en especifico o dame opciones y yo lo elijo, recuerda seguir las reglas"
- **Uso:** aclarar que la llave no se consume por regla de la guía y que la antorcha dura 2000 de tiempo (~20 movimientos); crear ControladorReplay (replay paso a paso en la ventana que verifica el final), el menú nuevo con nombre, replay y benchmark, el nombre bajo el jugador, y las pruebas prueba_replay_menu y prueba_vista_10 (D56, D57).

## Entrada 59
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** Se eligió la opción "Imogia 8-bit rat" entre cuatro sprites de rata propuestos.
- **Uso:** elegir la rata de Imogia Games (CC BY 4.0) entre las opciones encontradas.

## Entrada 60
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Lo vuelvo a descargar a Descargas y te aviso."
- **Uso:** volver a descargar el paquete de la rata, que no había quedado guardado.

## Entrada 61
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Ya descargué la rata de Imogia, está en mi carpeta Descargas."
- **Uso:** copiar la variante 04 de la rata con su licencia y crédito, y usarla animada en la sala (D58).

## Entrada 62
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Lo pruebo yo en la ventana y te digo qué ajustar."
- **Uso:** probar a mano el menú, el replay, el benchmark y la rata nueva.

## Entrada 63
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Soluciona el fallo de prueba_4_4 y prueba_vista_10, los dos commits anteriores yo les hice el push manualmente, y dale un retoque estético a la tabla de puntajes"
- **Uso:** corregir el conteo de tablas de prueba_4_4 (faltaba benchEtiquetas), quitar la dependencia del reloj en la edición del nombre y aislar los asserts de prueba_vista_10, poner las victorias primero en la tabla de puntajes (D59) y rediseñar la pantalla de puntajes (D60).

## Entrada 64
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Que seria mejor en el mapa seleccionar la partida que se quiere hacer el replay o en puntaje seleccionar la partida a la cual se le quiere hacer replay? Pq ahorita mismo cuando hago el replay de cualquiera cripta no se cual partida es en la ocurriendo el replay"
- **Uso:** comparar elegir el replay desde el menú o desde la tabla de puntajes, y decidir por puntajes con un log archivado por partida.

## Entrada 65
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "hazlo todo junto, reviso que todo funcione y haces el commit"
- **Uso:** archivar el log de cada partida terminada, guardar su id en el puntaje, elegir el replay con cursor y R en la tabla de puntajes, mostrar en el HUD qué partida es y quitar el replay por cripta del menú (D61).

## Entrada 66
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Lo reviso yo en la ventana y te aviso para el commit."
- **Uso:** revisar a mano el replay por partida desde la tabla de puntajes antes del commit.

## Entrada 67
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "haz el commit y sube los prompts de esta sesión"
- **Uso:** registrar los prompts de la sesión en PROMPTS_LLM.md y hacer el commit de todos los cambios.

## Entrada 68
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "el pergamino que es lo que hace, y el antidoto no aparece en los efectos o que es lo que hace?"
- **Uso:** entender que el pergamino deshace la última acción (máximo 5, no consume tiempo) y que el antídoto cura el veneno, pero que hoy nada en el juego envenena (envenenar() no tiene quién la llame).

## Entrada 69
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "la flecha izquierda en el replay no funciona para devolver la accion"
- **Uso:** agregar el paso atrás al replay (flecha izquierda), reconstruyendo la partida con la misma semilla hasta el paso anterior, con su prueba (D56).

## Entrada 70
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "ya hice el commit, ahora necesito que mejores el apartado visual de la interfaz de sala, vida, ataque y todo ese apartado, para que sea mas amigable con el usuario"
- **Uso:** rediseñar el HUD de la pantalla de juego en un módulo propio (HudJuego), con encabezado con corazón y barra de vida, tarjetas de estadísticas con diferencias por turno, brújula de salidas, efectos, enemigos con minibarra, inventario con íconos, bitácora coloreada, controles por modo y cartel de avisos; y aislar el assert intermitente de prueba_vista_10 (D62).

## Entrada 71
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "como funciona guardar y cargar"
- **Uso:** entender que G guarda la partida en guardados/<cripta>.bin (formato binario con tabla de offsets) y respalda el log al mismo tiempo, que C restaura los dos, y que el menú reanuda solo el guardado de una cripta si existe.

## Entrada 72
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "en el modo replay adelantar y retroceder accion van a ser con las flechas derecha e izquierda, y aumentar y  disminuir la velocidad con la flecha arriba y abajo"
- **Uso:** dejar la ayuda del replay con las cuatro flechas (derecha adelante, izquierda atrás, arriba más rápido, abajo más lento) y cubrir arriba/abajo en prueba_vista_10.

## Entrada 73
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Ponle Flecha + direccion"
- **Uso:** nombrar las teclas como "Flecha izquierda/derecha/arriba/abajo" en la ayuda del replay y "Flecha arriba/abajo" en el modo objetivo.

## Entrada 74
- **Fecha:** 17/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "haz el commit y agrega los prompts nuevos"
- **Uso:** registrar los prompts 71 a 74 y hacer el commit de los ajustes de controles del replay.

## Entrada 75
- **Fecha:** 18/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Agrega unas skins al héroe, y que la predeterminada sea de un tigre humanoide con muy buen diseño y animaciones"
- **Uso:** diseñar un tigre humanoide en pixel art propio con el estilo de 0x72 (4 cuadros de reposo con respiración, cola y parpadeo, más un cuadro de golpe), sumar 6 skins de 0x72 y elegirlas en el menú con Flecha izquierda/derecha (D63).

## Entrada 76
- **Fecha:** 18/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Ya lo revise, haz el commit y añade estos últimos prompts"
- **Uso:** registrar los últimos prompts y hacer el commit de las skins del héroe y el tigre humanoide.

## Entrada 77
- **Fecha:** 18/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "esto que es?" (con una captura de las carpetas fichas_guardadas/ y guardados/)
- **Uso:** entender que fichas_guardadas/ es la copia en disco del catálogo (caché persistente, D33) y guardados/ las partidas guardadas con G.

## Entrada 78
- **Fecha:** 18/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "mejorame esto" (pegando la explicación de que el guardado no se borra al terminar y de que el menú no permite elegir partida nueva)
- **Uso:** marcar en el menú las criptas con partida guardada, agregar X para empezar de cero y borrar el guardado al terminar la partida que lo usó (D64).

## Entrada 79
- **Fecha:** 18/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Ya lo revise, haz el commit y añade estos últimos prompts"
- **Uso:** registrar los últimos prompts y hacer el commit de las mejoras del guardado.

## Entrada 80
- **Fecha:** 18/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "cambia que cuando se le de a salir en medio de la partida se devuelva al menú principal y no que se cierre el juego tan abruptamente"
- **Uso:** hacer que ESC durante la partida vuelva al menú principal con un aviso (partida guardada o descartada) y que solo ESC en el menú cierre el juego (D65).

## Entrada 81
- **Fecha:** 18/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Lo reviso yo en la ventana y te aviso para el commit."
- **Uso:** revisar a mano la salida al menú con ESC antes del commit.

## Entrada 82
- **Fecha:** 18/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Implementa una pantalla principal, que tenga un mensaje  de bienvenida, una frase motivadora, tenga su ambientación respecto a la temática del proyecto y que pida un enter para entrar al menú principal, siempre siguiendo las reglas"
- **Uso:** crear la pantalla de título con la entrada de la cripta en pixel art de 0x72, antorchas, brasas, el héroe y sus enemigos, bienvenida, frases motivadoras que rotan y ENTER para entrar al menú (D66).

## Entrada 83
- **Fecha:** 18/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Yo lo revise, haz el commit y la documentación pertinente"
- **Uso:** completar el README (instalación, comandos, pantallas, controles y archivos que genera el juego) y hacer el commit de la pantalla de título y la salida al menú con ESC.

## Entrada 84
- **Fecha:** 18/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Revisa que el proyecto cumpla con todo lo que dice el pdf, para ya poder entregarlo" (con el enunciado en PDF adjunto)
- **Uso:** revisar el proyecto contra el enunciado sección por sección y corregir lo que faltaba: recorrer y ordenar el inventario desde la ventana (Tab, Shift+Tab, O) y ver la bitácora completa de 20 mensajes (L), con sus pruebas (§4.5, §4.8, §10.2); medir el rastro con --bench (benchRastro, §4.7) y la búsqueda de la caché según su capacidad (tabla 3 de benchCache, D32); completar el Documento de Decisiones (índice por problema de §4, secciones nuevas D67 a D70 para el rastro, el guardado binario, la interfaz del inventario y la bitácora de partida, quitar las D23/D24 duplicadas y las notas de trabajo, y completar los campos que faltaban); y actualizar el README (Python 3.11 o superior y las teclas nuevas).

## Entrada 85
- **Fecha:** 18/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Ya cumple con absolutamente todo?"
- **Uso:** pedir un balance honesto de lo que cumple y de lo que seguía flojo frente al enunciado (§4.2 sin medición con --bench, evidencias de red sin medir, veneno y regeneración sin datos que los activen).

## Entrada 86
- **Fecha:** 18/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Ya probe Tab, O and L funcionan, si puedes solucionar los que falla o esta flojo hazlo"
- **Uso:** medir la precarga contra pedir al entrar a cada sala (benchPrecarga, §4.2) y la capa de datos (benchDatos: traducción a DTO, Cola con y sin referencia al final, Session contra requests.get); agregar prueba_errores_red (HTTP 500, JSON inválido, timeout y conexión rechazada, D17); activar todas las pruebas sin red en ejecutar_pruebas (36); y reemplazar todas las "evidencias por medir" del Documento de Decisiones por la evidencia real o por la razón de no medirla.

## Entrada 87
- **Fecha:** 18/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Haz el commit"
- **Uso:** hacer el commit de la revisión contra el enunciado en la rama Pablo.

## Entrada 88
- **Fecha:** 18/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "hice checkout al main para actualizarlo y cuando hice el merge aperecieron unos issues, revisalos y solucionalos para que todo funcione correctamente"
- **Uso:** encontrar que el merge de Pablo en main se había quedado con las versiones viejas de 18 archivos, restaurarlos desde Pablo y conservar los cambios de Diego en el Documento de Decisiones.

## Entrada 89
- **Fecha:** 18/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Haz el commit del arreglo en main"
- **Uso:** hacer el commit del arreglo del merge en main.

## Entrada 90
- **Fecha:** 18/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Cuando se usa el Tab, baja el inventario y ya no se puede volver a subir"
- **Uso:** hacer que el cursor del inventario dé la vuelta en los extremos, que con una vista ordenada Tab siga el orden que se ve, mostrar Shift+Tab en la ayuda y agregar prueba_cursor_inventario.

## Entrada 91
- **Fecha:** 18/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Ya lo probe, haz la documentación y el commit"
- **Uso:** dejar documentado el recorrido del inventario (README, D69 y prompts) y hacer el commit.
- 
## Entrada 92
- **Fecha:** 31/10/2026
- **Herramienta:** Gemini (3.1 Pro)
- **Prompt:** "como ves ya esta el primer proyecto hecho y entregado, ocupo que me ayudes con el promopt para claude para que me haga el constitution que es clave en spec driven development. También agregar que despues de cada prompt, lo agregue automaticamente a PROMPTS_LLM.md."
- **Uso:** Plantear el prompt para la generación del constitution.md por claude.

## Entrada 93
Fecha: 31/10/2026
Herramienta: Claude
Prompt: “Actúa como un Arquitecto de Software Principal experto en Spec-Driven Development (SDD). Tu primera tarea es redactar la “Constitución del Proyecto”...”
Uso: revisar el prompt de constitución propuesto contra el enunciado, señalar lo que falta y lo que choca con el proyecto, y entregar una versión combinada.
## Entrada 94
- **Fecha:** 31/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5), comando de spec-kit `/speckit-specify`
- **Prompt:** "Terreno y cazador: las salidas de una sala tienen costo de tránsito y aparece un nuevo enemigo, el cazador, que calcula la ruta más barata hacia el jugador. ..." (texto completo con reglas del juego, contrato de datos, interfaz, rendimiento y escenarios de aceptación).
- **Uso:** generar specs/001-terreno-cazador/spec.md y su checklist de calidad (checklists/requirements.md).

## Entrada 95
- **Fecha:** 31/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "dejalo en la spec como requisito con su FR-xxx y como escenario de aceptación (“las dos caras declaran costos distintos: la cripta se rechaza con un error claro”). y haz el git commit y push"
- **Uso:** resolver la aclaración pendiente del spec 001-terreno-cazador agregando FR-027 y sus escenarios de aceptación, y actualizar el checklist de calidad.

## Entrada 96
- **Fecha:** 31/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5), comando de spec-kit `/speckit-clarify`
- **Prompt:** "/speckit-clarify" (sin texto), con respuestas "A", "D" y "A" a tres preguntas.
- **Uso:** aclarar el spec 001-terreno-cazador: el actor pasa a la sala de destino al iniciar el movimiento (FR-028); el límite de 20 ms se mide con 20, 50 y 100 cazadores (FR-025, SC-003); el costo de la decisión de un cazador se demuestra contando salas examinadas (FR-026, SC-004).

## Entrada 97
- **Fecha:** 31/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5), comando de spec-kit `/speckit-plan`
- **Prompt:** "/speckit-plan" (sin texto).
- **Uso:** generar plan.md, research.md, data-model.md, quickstart.md y contracts/ de 001-terreno-cazador; medir antes de decidir (búsqueda por cazador frente a mapa de distancias compartido) y proponer la enmienda de FR-026/SC-004.

## Entrada 98
- **Fecha:** 31/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "corrige y has los commit y push para revisar los archivos"
- **Uso:** aplicar la enmienda de FR-026/SC-004 al spec en un commit propio, actualizar el plan y confirmar los artefactos de la fase plan, con push.

## Entrada 99
- **Fecha:** 31/10/2026
- **Herramienta:** Claude
- **Prompt:** “revisa todo por si hay que correghir algo” (con spec.md, plan.md, research.md, data-model.md y quickstart.md de 001-terreno-cazador)
- **Uso:** revisar los artefactos de spec-kit de la feature terreno y cazador contra el enunciado y el código, y listar las correcciones antes de generar las tareas.

## Entrada 100
- **Fecha:** 31/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Aplica estas correcciones, cada grupo en su propio commit: 1) En spec.md: cambia SC-001 para cubrir todos los escenarios de aceptación de las Historias 1 a 4 ... 2) En plan.md y quickstart.md: (a) agrega pruebas automáticas para FR-021 y para los conteos de salas examinadas de FR-026/SC-004, y una verificación automática de FR-025; (b) ... DatosInvalidos ... mostrar_error; (c) ... 100 cazadores de rangos distintos ... cota al doble; (d) deja FORMATO_VERSION como pendiente de coordinar ... 3) Luego corre /speckit-analyze y corrige lo que reporte." Seguido de "2" (corregir solo las inconsistencias, porque /speckit-analyze exige tasks.md).
- **Uso:** SC-001 con los 21 escenarios; pruebas, captura de DatosInvalidos, bench de rangos distintos y FORMATO_VERSION pendiente en plan y quickstart; alinear research.md, data-model.md y el contrato del formato de guardado. /speckit-analyze no se pudo ejecutar porque todavía no existe tasks.md.

## Entrada 101
- **Fecha:** 31/10/2026
- **Herramienta** Claude
- **Prompt:** “[5 archivos adjuntos: data-model.md, quickstart.md, plan.md, research.md, spec.md] revisalos entonces antes”
- **Uso:** revisar los artefactos de la feature 001-terreno-cazador antes de generar tasks.md, corregir cuatro inconsistencias y ampliar la lista de tareas a pedir.

## Entrada 102
- **Fecha:** 31/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Aplica estas 4 correcciones en un commit propio, sin tocar spec.md: 1) plan.md, Summary: cambia "0,3 a 9,8 ms" por "0,2 a 9,8 ms" ... 2) research.md R3: reescribe la alternativa descartada "cota = rango máximo entre las fichas cargadas" para que no contradiga a P3 ... 3) data-model.md, MapaDistancias.distancia(): devuelve None si la distancia guardada es mayor que la cota ... 4) quickstart.md: verifica que "python -m pruebas.ejecutar_pruebas" corre; unifica el estilo de comandos con el README (py ...)."
- **Uso:** aplicar las cuatro correcciones al plan de 001-terreno-cazador y verificar la suite de pruebas: con el entorno .venv activo pasan las 37; con el py del sistema fallan 13 por falta de requests.

## Entrada 103
Fecha: 31/10/2026
Herramienta: Claude
Prompt: “osea pongo el comando y en el mismo espacio de escribir eso?”
Uso: aclarar cómo se escribe /speckit-tasks junto con el texto de instrucciones adicionales en un solo mensaje.

## Entrada 104
- **Fecha:** 31/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5), comando de spec-kit `/speckit-tasks`
- **Prompt:** "/speckit-tasks Genera tasks.md para 001-terreno-cazador. Cada tarea debe citar los FR-xxx que cubre. Incluye estas tareas de forma explícita: 1. Pruebas, antes del código que las hace pasar ... 2. La tabla de los 21 escenarios de aceptación ... 3. El bench de la cota con las reglas P1, P2 y P3 ... 4. Tarea condicional ... FR-026(b) ... 5. La equivalencia con el oráculo Bellman-Ford ... 6. modoReplay ... 7. El paquete sin conexión de prueba ... 8. benchCazador.py ejecutable con -m ... 9. Registrar las 9 pruebas nuevas ... 10. README ... 11. DECISIONES.md ... PROMPTS_LLM.md. 12. FORMATO_VERSION queda como tarea pendiente de coordinar con Pablo ..." (texto completo en la conversación).
- **Uso:** generar specs/001-terreno-cazador/tasks.md: 56 tareas en 8 fases, con pruebas antes del código, la tabla de los 21 escenarios, la cobertura de FR-001 a FR-028 y la tarea de cierre al final.

## Entrada 105
Fecha: 31/10/2026
Herramienta: Claude
Prompt: “[tasks.md adjunto] antes de analyze revisemos esto bien pq el paso que sigue es implementar y quiero que todo quede de la mejor manera”
Uso: revisar tasks.md de 001-terreno-cazador antes de /speckit-analyze, señalar 9 ajustes y dar el prompt para aplicarlos.

## Entrada 106
- **Fecha:** 31/10/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "corrige esto: Aplica estos ajustes a specs/001-terreno-cazador/tasks.md en un commit propio: 1) Fase 1: agrega una tarea al inicio que confirme que `py pruebas/ejecutar_pruebas.py` corre completa y en verde ... y otra que genere con el código ACTUAL un archivo de guardado del formato anterior como fixture ... 2) T013: enlazar() debe ser idempotente ... 3) T025: aísla la regla de la cota en un método `_cota_nueva(cota_minima)` ... 4) T003: el oráculo corre Bellman-Ford desde cada vecina abierta v ... 5) T053: mover el registro en PROMPTS_LLM.md a cada commit de fase ... 6) T051 ... T052 ... git pull de main y usar el siguiente número D libre. 7) T038 y T039: ... prueba_reglas lo revisa ... 8) Actualiza la tabla de cobertura y las dependencias si cambia algún ID." (texto completo en la conversación).
- **Uso:** aplicar los ocho ajustes a tasks.md: dos tareas nuevas al inicio (línea base verde y fixture del formato anterior), renumerar a T001–T058 y actualizar la tabla de escenarios, la cobertura y las dependencias. Las prueba_real_* siguen comentadas porque usan el API real y gastan presupuesto.

## Entrada 107
- **Fecha:** 01/11/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "revisa el codigo porque creo que solo falta el implement de speckit, ayer hicimos ya un analyze pero revisalo un momento nada mas"
- **Uso:** revisar el estado de 001-terreno-cazador: tasks.md tiene 58 tareas sin marcar, no existe código de la feature, las referencias entre tareas son consistentes y la suite pasa 37/37 con .venv. Se señaló que T048 está bloqueada por T047 (coordinación con Pablo) y que no había entrada del analyze en PROMPTS_LLM.md.

## Entrada 108
- **Fecha:** 01/11/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Estamos en la rama 001-terreno-cazador del proyecto Cripta (Parte II, Spec-Driven Development). Antes de hacer nada, lee .specify/memory/constitution.md y specs/001-terreno-cazador/tasks.md. Trabaja siempre bajo esa constitución: estructuras propias (sin dict, set, list ni heapq en cripta/), determinismo, MVC con puertos, la spec precede al código, pruebas antes del código, medir antes de afirmar y registrar cada prompt en PROMPTS_LLM.md. Dime qué tareas de tasks.md están marcadas [x] y cuál es la siguiente. No cambies código todavía."
- **Uso:** leer la constitución y tasks.md completos: ninguna tarea marcada [x]; la siguiente es T001 (línea base con prueba_falso_1_6, se esperan 38). Sin cambios de código.

## Entrada 109
- **Fecha:** 01/11/2026
- **Herramienta:** Claude Code (Claude Opus 5.5), comando de spec-kit `/speckit-analyze`
- **Prompt:** "Sí. Orden: 1) Revisa git log y dime si /speckit-analyze corrió y se commiteó. Si no, córrelo ahora y espera mi revisión antes de seguir. 2) Agrega a PROMPTS_LLM.md las entradas faltantes (desde la 107, con el texto real de cada prompt) y haz un commit solo con eso. 3) Después empieza T001. Cuando la línea base quede en 38, actualiza en tasks.md el checkpoint de la Fase 2 ("38/38") y T051 (el total final será 47, no 46), en un commit aparte. Haz un commit por fase, como pide la constitución, y no pases a la fase siguiente sin avisarme."
- **Uso:** confirmar en git log y reflog que /speckit-analyze no había corrido (el último commit era "ajustes antes de analyze") y correrlo. Informe sin problemas críticos y con 100 % de cobertura de FR y SC; hallazgos D1 (prueba_reglas no detecta set, collections ni bibliotecas de grafos), U1 (desempate entre dos salidas a la misma vecina), I1 (T051 no tiene total), I2, I3, I4, U2 y C1. Se detuvo a esperar la revisión.

## Entrada 110
Fecha: 01/11/2026
Herramienta: Claude
Prompt: “[informe de /speckit-analyze de 001-terreno-cazador adjunto]”
Uso: revisar el informe de analyze, decidir qué hallazgos corregir, mover la regla de desempate a la spec y fijar dónde va el total de 47 pruebas.

## Entrada 111
- **Fecha:** 01/11/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Sí. Corrige D1, U1, U2 (el de T013), I2, I3, I4 y C1, en este orden de commits: 1) Un commit que toque SOLO spec.md: agrega a FR-014 que si dos salidas de u llevan a la misma vecina v con el mismo costo, gana la primera en el orden N, S, E, O, y agrega ese caso a los casos borde (no como escenario de aceptación nuevo, para que SC-001 siga en 21). 2) Un commit con los cambios en tasks.md y plan.md: - D1: tarea nueva en la Fase 1, justo después de T001: ampliar prueba_reglas para detectar set, frozenset, {a, b}, comprensiones de conjunto, set(), import heapq, bisect, collections (cualquiera), networkx y otras bibliotecas de grafos, con autopruebas. T057 queda con "sin dict, set, list, heapq, bisect ni sorted". - U1: T005, T028 y el generador de T021 siguen la regla de FR-014 (id de la vecina, luego orden N, S, E, O); agrega un caso con dos salidas a la misma vecina. - U2: en T013, _registro = None se asigna antes que cerrada. - C1: agrega a T020 (prueba_cazador) los casos de jugador muerto, varios cazadores en la misma sala y primer costo del cazador, con la marca BORDE. - I2, I3, I4 como los propones. - El total: "47/47" en T053 y T057; en T001, corregir README.md:27 a 38; en la tarea de README final, a 47. 3) Un commit con las entradas faltantes de PROMPTS_LLM.md (analyze y esta revisión). No empieces T001 hasta que yo confirme los tres commits." Seguido de "Agrega este prompt antes del tuyo" con el texto de la entrada 110.
- **Uso:** tres commits. (1) spec.md: desempate N, S, E, O en FR-014 y su caso borde; SC-001 sigue en 21. (2) tasks.md y plan.md: nueva T002 (ampliar prueba_reglas), así que las tareas se renumeran a T001–T059 (las citadas como T005, T013, T020, T021, T028, T053 y T057 ahora son T006, T014, T021, T022, T029, T054 y T058); desempate en el oráculo, el Cazador y el generador; _registro antes que cerrada; casos BORDE; totales 38 y 47/47; I2, I3 e I4 en plan.md. (3) Estas entradas 107 a 111.

## Entrada 112
- **Fecha:** 01/11/2026
- **Herramienta:** Claude Code (Claude Opus 5.5), comando de spec-kit `/speckit-implement` (solo la Fase 1)
- **Prompt:** "Primero haz el push de los commits y lo confirmas, luego empezamos con T001, haz un commi por fase terminada. En esta sección es clave que hagas las pruebas de cada fase priemro para ver si fallan y corregir en el momento. Si el error se ve relacionado con algo del spec.md se detiene y pregunta antes de corregir por si solo. Ah y me mandas el resultado de la fase para verificar antes de empezar la siguiente." Durante T001 se respondió "Dejarla fuera (Recomendado)" a la pregunta de qué hacer con prueba_falso_1_6.
- **Uso:** push de la rama y Fase 1 (T001 a T006). T001: prueba_falso_1_6 queda fuera porque es el módulo de ServidorFalso, sin asserts; línea base 37/37 y README a 37 (los totales de tasks.md pasaron a 37 y 46 en un commit aparte). T002: prueba_reglas detecta conjuntos, collections y bibliotecas de grafos; sus autopruebas fallaron antes del cambio. T003: fixture del formato 1 con un script reproducible. T004: paquete pruebas/datos/terreno_cazador. T005: apoyo_terreno.py. T006: oráculo Bellman-Ford, validado contra Dijkstra en 6000 pares.

## Entrada 113
Fecha: 01/11/2026
Herramienta: Claude
Prompt: “La Fase 1 está terminada y confirmada en fa09957. Las pruebas pasan 37/37. ... yo loveo muy bien, pensaria que se puede hacerr el push y empozar com la 2”
Uso: revisar el informe de la Fase 1, aprobar el push, señalar tres ajustes previos a la Fase 2 y marcar la duda sobre la activación del cazador.

## Entrada 114
- **Fecha:** 01/11/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Sí, haz push y antes de la Fase 2: 1) Baja la probabilidad de salidas repetidas hacia la misma vecina en las criptas al azar de apoyo_terreno para que solo una minoría (alrededor de 20 a 30 %) tenga alguna sala con duplicadas, y deja un caso fijo con duplicadas. Commit propio.2)Agrega a la sección Assumptions de spec.md, en un commit propio que solo toque spec.md: "El cazador usa la misma regla de activación que los demás enemigos (Parte I §2.4): está dormido y no actúa hasta que el jugador entra a su sala; una vez activo permanece activo aunque cambie de sala. Su primera acción se programa con costo base 100. La decisión de la ruta (FR-011 a FR-017) solo aplica a cazadores activos." Registra el prompt en PROMPTS_LLM.md. No cambies nada más." Seguido de "Agrega este prompt" con el texto de la entrada 113.
- **Uso:** push de la Fase 1 (a2b02b8..fa09957). (1) apoyo_terreno: dos salas se conectan una sola vez y la duplicada se agrega solo a propósito (PROB_DUPLICADA = 0.04, 23,9 % de 1000 criptas), con el caso fijo duplicadas_misma_vecina() comprobado con el oráculo. (2) spec.md: la regla de activación del cazador en Assumptions. (3) Estas entradas.

## Entrada 115
- **Fecha:** 01/11/2026
- **Herramienta:** Claude Code (Claude Opus 5.5), `/speckit-implement` (Fase 2)
- **Prompt:** "Haz push y empieza la Fase 2"
- **Uso:** push de los ajustes previos (fa09957..702fc12) y Fase 2 (T007 a T009). Primero se escribió una verificación del contrato en el scratchpad (no entra en la suite, para no cambiar los totales) y fallaron sus 4 casos. Después: DatosInvalidos(ErrorCripta), SalidaDTO.costo y FichaEnemigoDTO.rango al final y con valor por omisión, y RegistroPuertas. Los 4 casos pasan, prueba_reglas sigue en verde y la suite queda en 37/37.

## Entrada 116
- **Fecha:** 01/11/2026
- **Herramienta:** Claude Code (Claude Opus 5.5), `/speckit-implement` (Fase 3, US1)
- **Prompt:** "Haz push y empieza la Fase 3"
- **Uso:** push de la Fase 2 (702fc12..5772804) y escritura de las pruebas de US1 antes del código: prueba_costo_salidas (10 casos), prueba_datos_costo (9) y prueba_fuentes_costos. Fallaron todas por la razón esperada; se corrigieron dos defectos de las propias pruebas (un pasillo de 2 salas que termina la partida al llegar a la salida, y la propiedad ultimo_estado de VistaRegistradora, que tapaba el atributo de VistaNula). Después, T013 (convertidor), T014 (Salida) y T015 (Sala).

## Entrada 117
- **Fecha:** 01/11/2026
- **Herramienta:** Claude Code (Claude Opus 5.5), `/speckit-implement` (Fase 3, US1)
- **Prompt:** "retoma donde qudaste, antes verifica que los T anteriores de la fase si hayan quedado implementados"
- **Uso:** comprobar que T010 a T015 estaban en el árbol de trabajo y funcionaban (prueba_reglas en verde y una comprobación directa de Salida y Sala), y terminar T016 (Mundo.enlazar), T017 (Partida.costo_de), T018 (EventoAccionActor), T019 (ControladorMenu sin cambios) y T020: las tres pruebas de US1 en verde, prueba_reglas OK, suite 37/37 y main.py --bench --rapido sin errores.

## Entrada 118
Fecha: 01/11/2026
Herramienta: Claude
Prompt: “[informe de la Fase 3 de Claude Code] lo que veo es lo del null del json pero realmente no lo veo tan mal, auqnue nose si es mejor no declarado para evitar errorres de no haber inicializado parametors, y lo demas lo veo bien trabajado”
Uso: decidir que un costo null equivale a no declarado, registrar la aclaración en la spec antes del código y dar el prompt para cerrar la Fase 3.

## Entrada 119
- **Fecha:** 01/11/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "Sí: un "costo": null equivale a no declarado (100), igual que llave y cierre_automatico, que ya usan datos.get. Orden: 1) Un commit que toque SOLO spec.md: en FR-003 y en los casos borde, aclara que costo null equivale a ausente (100) y que cualquier otro valor que no sea entero ≥ 1 sigue siendo error. rango null o ausente en un cazador sigue siendo error (FR-009). 2) Ajusta el convertidor (T013) y prueba_datos_costo: null vale 100; "100", true, 0, -5 y 2.5 siguen fallando. Corre la suite. 3) Commit de la Fase 3 (US1) con las tareas marcadas en tasks.md y los prompts en PROMPTS_LLM.md. Avísame al terminar, con el resultado de la suite." Seguido de "y agrega" con el texto de la entrada 118.
- **Uso:** (1) spec.md: FR-003 y casos borde (costo null = no declarado; rango null o ausente de un cazador sigue siendo error), commit e6106f2. (2) Primero se ajustó prueba_datos_costo (sacar null de los inválidos y un caso nuevo, que falló), después el convertidor con datos.get("costo"). Las tres pruebas de US1 pasan, prueba_reglas OK y la suite 37/37. T013 y contracts/datos-entrada.md dicen ahora "ausente o null". La Fase 3 ya estaba confirmada en 8bdd138, así que el ajuste va en un commit propio encima.

## Entrada 120
- **Fecha:** 01/11/2026
- **Herramienta:** Claude Code (Claude Opus 5.5), `/speckit-implement` (Fase 4, US2)
- **Prompt:** "listo haz el push y empiezas con la fase 4"
- **Uso:** push (5772804..ff88865) y Fase 4 (T021 a T032). Pruebas primero, y fallaron todas por lo que faltaba: prueba_cazador (18 casos: H2.E1 a H2.E9, rango 0, misma vecina por dos salidas, sentido del recorrido, casos BORDE y la regla de activación), prueba_cazador_equivalencia (1000 situaciones con turnos encadenados), casos de rango en prueba_datos_costo y rango por las dos fuentes y la caché en prueba_fuentes_costos. Se corrigieron defectos de las pruebas (comparar fichas con ListaEnlazada, activar enemigos con el Diario conectado) y se optimizó el oráculo sin cambiar su algoritmo, validado otra vez contra Dijkstra. Implementación: rango en convertidor y caché, sello en Sala, MapaDistancias (P1), Cazador, fábrica y Partida. Resultado: 4492 decisiones idénticas al oráculo, tres errores introducidos a propósito detectados, suite 37/37 y bench rápido sin errores.

## Entrada 121
- **Fecha:** 01/11/2026
- **Herramienta:** Claude Code (Claude Opus 5.5)
- **Prompt:** "actualiza data-model.md y haces el push para que inicies Fase 5"
- **Uso:** alinear data-model.md con la implementación de la Fase 4: asegurar() recibe el id del objetivo, el contador de sellos vive en el Mundo (sello_mapa, nuevo_sello_mapa), las propiedades y anotar_distancia de Sala, _cota_reutilizable y examinadas_ultimo_calculo del mapa. Push y comienzo de la Fase 5.

## Entrada 122
- **Fecha:** 01/11/2026
- **Herramienta:** Claude Code (Claude Opus 5.5), `/speckit-implement` (Fase 5, US3)
- **Prompt:** "actualiza data-model.md y haces el push para que inicies Fase 5" (la parte de la Fase 5).
- **Uso:** Fase 5 (T033 a T037). Prueba primero: prueba_vista_costos (H3.E1, H3.E2 y compatibilidad de los DTOs), que falló en sus 3 casos. Después: SalidaVisible.costo y ActorVisible.es_cazador; el Controlador los llena; dibujoSala muestra el costo bajo la letra de cada puerta y un anillo y el prefijo «» » en el cazador; hudJuego pone el costo en la brújula y el prefijo en "En la sala" y en el selector de ataque; pantallaJuego, en sus textos. Se renderizó una sala real con una ventana invisible de arcade para revisar el dibujo, y el anillo se movió encima de la capa de oscuridad. Suite 37/37. T038 queda pendiente de la revisión manual de quickstart §3.

## Entrada 123
- **Fecha:** 01/11/2026
- **Herramienta:** Claude Code (Claude Opus 5.5), `/speckit-implement` (Fase 6, US4)
- **Prompt:** "ya lo revisé, marca T038, haz push y empieza la Fase 6"
- **Uso:** marcar T038 (el usuario hizo la revisión manual de quickstart §3), push de la Fase 5 y comienzo de la Fase 6.

## Entrada 124
- **Fecha:** 01/11/2026
- **Herramienta:** Claude Code (Claude Opus 5.5), `/speckit-implement` (Fase 6, US4)
- **Prompt:** respuestas a dos preguntas de la Fase 6: "¿Apruebas esta enmienda [de FR-026(b): R es el mayor rango entre los cazadores activos (los únicos que deciden) en el momento del cálculo]?" → "Sí, con este texto (Recomendado)"; "P3 necesita R_activos [...] ¿Cómo lo calcula la Partida?" → "Recorrer cazadores (Recomendado)".
- **Uso:** Fase 6 (T039 a T046). Pruebas primero: prueba_conteo_cazador (pasó desde el inicio porque el mapa acotado ya existía; se comprobó que un mapa sin cota la hace fallar) y prueba_rendimiento_cazador (falló: no existía el bench, y después P1 dio 45 y 50 ms con 100 rangos distintos en la malla de 1024 salas). Se escribieron alternativasCazador (P1, P2 y BusquedaPorCazador, validada contra el oráculo en 4500 decisiones) y benchCazador, registrado en benchTodo. T044: solo P3 pasaba los 20 ms (P1 40,8 y 41,4 ms; P2 21,6 ms; P3 18,0 ms). T045: enmienda de FR-026(b) en su propio commit (859cf55), P3 en MapaDistancias y R_activos en la Partida. P3 quedaba en el límite (17,9 a 21,6 ms) por la búsqueda lineal de salas por id, repetida en cada turno de enemigo: Mundo.sala() recuerda la última sala y el movimiento de enemigos usa salida.sala_destino. Bench final: P3 15,8 ms como máximo en la malla. prueba_4_4 cuenta las 5 tablas nuevas de benchTodo. Suite 37/37.

## Entrada 125
- **Fecha:** 01/11/2026
- **Herramienta:** Claude Code (Claude Opus 5.5), `/speckit-implement` (Fase 7, persistencia)
- **Prompt:** "haz el push y para la Fase 7 useamos el FORMATO_VERSION=2, provisional segun el orden de merge al main."
- **Uso:** push de la Fase 6 (bd9fd2e..d4f44ac) y Fase 7 (T047 a T052). Prueba primero: prueba_persistencia_cazador; (a) y (b) fallaron (el formato seguía en 1, y una partida con cazador ni se podía cargar porque faltaba el rango); (c) y (d) ya pasaban, lo que confirma T050: modoReplay ya reporta DatosInvalidos y sale con 1. T048: el acuerdo (2, provisional según el orden de merge) en el contrato, en T048 y en plan.md. T049: el costo efectivo en el archivo, el rango del enemigo al cargar, RegistroPuertas, enlazar() y Partida.reconstruir_tras_cargar(). T051: la equivalencia guarda y carga entre turnos (917 veces) con las 4492 decisiones idénticas; una carga sin enlazar la hace fallar. Suite 37/37 y bench rápido sin errores.

## Entrada 126
- **Fecha:** 01/11/2026
- **Herramienta:** Claude Code (Claude Opus 5.5), `/speckit-implement` (Fase 8, cierre)
- **Prompt:** "opción 2, haz push y sigue con la Fase 8"
- **Uso:** sacar del índice la salida de prueba_6_3 (paquete_prueba_6_3/ a .gitignore, commit f334303) y push. Fase 8: T053, las 9 pruebas nuevas en ejecutar_pruebas.py (46/46); T054, README (46 pruebas, sección de terreno y cazador, formato 2 incompatible con los guardados anteriores); T055, D71 a D74 en DECISIONES.md (después de D70; origin/main no agregó decisiones), con las cifras del bench; T056, numeración de PROMPTS_LLM.md continua de la 16 a la 126 (la 1 repetida y la 4, 6, 14 y 15 faltantes son de la Parte I y no se renumeran); T057, las 21 marcas de escenario en su prueba y los 28 FR citados; T058, suite 46/46, prueba_reglas, --bench --rapido y quickstart §4 con las tres partidas reales del usuario (mismo final que en puntajes.jsonl).
