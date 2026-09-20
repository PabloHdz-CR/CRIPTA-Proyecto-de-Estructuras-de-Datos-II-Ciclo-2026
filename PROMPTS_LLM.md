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