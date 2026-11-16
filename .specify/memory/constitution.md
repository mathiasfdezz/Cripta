<!--
=== SYNC IMPACT REPORT ===
- Version change: 1.0.0 → 1.1.0 (MINOR: ampliación de directrices de calidad y restricciones técnicas complementarias)
- Modified principles:
  * Principio I (Estructuras de Datos Propias (Implementación Artesanal)):
    - Prohibición de list.sort() y sorted() en los ordenamientos evaluados.
    - Reemplazo de la especificación sobre list: "`list` se permite como almacenamiento contiguo de bajo nivel, sin sustituir a la estructura que resuelve un problema evaluado".
    - Inclusión de regla de gobernanza: cualquier plan o tarea generado que contradiga este principio es un defecto del grupo y se corrige antes de implementar; las dependencias propuestas por un plan se revisan.
  * Principio VI (Rendimiento con Evidencia Empírica y Límites Críticos):
    - Incorporación de umbrales cuantitativos específicos: verificación de resolubilidad 200 ms (cripta publicada más grande), consulta de historia 50 ms (partida de 5000 acciones, K por defecto) y un paso de "ir a" 5 ms (mapa conocido completo de la cripta de referencia).
    - Obligación de documentar en DECISIONES.md cualquier incumplimiento en criptas sintéticas mayores como límite conocido junto con su causa.
  * Principio VII (Especificación antes que Código y Trazabilidad Git):
    - Delimitación estricta de contenidos: spec.md (reglas del juego, historias de usuario, escenarios de aceptación y requisitos numerados; sin nombres de estructuras, algoritmos, clases ni módulos) y plan.md (estructuras, alternativas consideradas, complejidad, módulos afectados y mediciones planificadas; sin reglas nuevas).
    - Inclusión preceptiva de cada caso del Apéndice B del enunciado como escenario de aceptación.
    - Cobertura de cada escenario mediante al menos una prueba automatizada o un partida.log de reproducción citando el FR.
    - Registro obligatorio de cada comando de spec-kit ejecutado con texto propio en PROMPTS_LLM.md.
- Added sections: Ninguna.
- Removed sections: Ninguna.
- Follow-up TODOs: Ninguno. Documento completamente especificado y validado.
==========================
-->

# Constitución del Proyecto CRIPTA (Segunda Parte)

## Core Principles

### I. Estructuras de Datos Propias (Implementación Artesanal)
Todas las estructuras de datos requeridas para resolver los problemas evaluados del juego DEBEN implementarse a mano en el paquete `estructuras/` del proyecto.
- Está terminantemente PROHIBIDO (NO SE DEBE) utilizar las colecciones nativas `dict` o `set` de Python como índice, caché, tabla de símbolos, conjunto de visitados o estructura de búsqueda en el modelo ni en los adaptadores.
- NO SE DEBEN utilizar los módulos estándar `heapq`, `bisect`, ni `collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`), así como tampoco bibliotecas externas de grafos o cálculo de rutas (por ejemplo, `networkx`).
- NO SE DEBEN utilizar `list.sort()` ni `sorted()` en los ordenamientos evaluados.
- Los diccionarios nativos generados por `respuesta.json()` del cliente HTTP solo se DEBEN leer de forma puntual y transitoria en los adaptadores/mapeadores (`adaptadores/mapeadores/`) para deserializar y transformar los datos en DTOs u objetos de dominio. Ningún `dict` DEBE almacenarse en memoria a largo plazo como índice o tabla en el modelo.
- `list` se permite como almacenamiento contiguo de bajo nivel, sin sustituir a la estructura que resuelve un problema evaluado.
- Un plan o tarea generado que contradiga este principio es un defecto del grupo y se corrige antes de implementar; las dependencias que proponga un plan se revisan.
- *Justificación*: El núcleo formativo y técnico del proyecto exige comprender, diseñar, justificar y medir las estructuras de datos algorítmicas sin delegar la complejidad a librerías de alto nivel.

### II. Determinismo Absoluto y Reproducibilidad
Dada la misma cripta, la misma semilla y la misma secuencia de acciones, el sistema DEBE producir exactamente la misma partida en cualquier entorno y ejecución.
- Toda aleatoriedad DEBE originarse única y exclusivamente de la instancia `random.Random(semilla)` asociada a la partida activa.
- Queda estrictamente PROHIBIDO (NO SE DEBE) utilizar el generador global pseudoaleatorio de Python (`random.random()`, `random.choice()`, `random.randint()`, etc.).
- La prioridad y resolución de eventos en la agenda DEBE estar definida de manera estricta por el tiempo lógico (`tiempo`) y un número de secuencia monotónico incremental (`secuencia`).
- NO SE DEBE utilizar en ningún caso la hora del reloj del sistema (`time.time()`, `datetime.now()`) ni el orden/latencia de llegada de respuestas de red para desempatar, ordenar o disparar eventos en el modelo de juego.
- *Justificación*: El determinismo estricto garantiza la reproducibilidad completa requerida para auditorías, depuración de errores mediante `--replay`, verificación de puntajes y benchmarking fiable.

### III. Separación Arquitectónica (MVC Estricto)
El sistema DEBE mantener una separación rigurosa de responsabilidades bajo el patrón Modelo-Vista-Controlador.
- El paquete `modelo/` DEBE constituir un núcleo de dominio puro: NO DEBE conocer ni importar conceptos de HTTP, operaciones con el sistema de archivos, formateo de consola ni elementos de la interfaz de usuario.
- Todo acceso a la red (API REST), al disco (archivos offline, cachés, partidas guardadas, bitácoras) y a fuentes externas DEBE ubicarse en el paquete `adaptadores/` y desacoplarse detrás de interfaces abstractas.
- El `controlador/` DEBE orquestar la interacción traduciendo las intenciones del usuario en mutaciones del modelo y coordinando las fuentes de datos.
- Los modos de ejecución no interactivos (`--replay`, `--bench` y `--verificar`) NO DEBEN instanciar la vista interactiva. La suite de pruebas de la vista sí puede importar y verificar los módulos de la vista, pero la ejecución de modos batch opera desacoplada de la interfaz interactiva.
- *Justificación*: El desacoplamiento garantiza que los modos batch, de verificación y de evaluación de rendimiento funcionen de forma desatendida sin depender de terminales interactivas, preservando la independencia del modelo.

### IV. Desacoplamiento Total de Datos de Cripta
Ningún dato particular de una cripta concreta DEBE figurar escrito de forma fija ("hardcodeado") en el código fuente.
- NO SE DEBEN escribir en el código números de sala, identificadores de entidades (enemigos, trampas, llaves, objetos), cantidades de páginas de catálogo, presupuestos de solicitudes ni estadísticas de criptas conocidas.
- Todos los parámetros, topologías de mazmorra, metadatos y entidades DEBEN descubrirse y procesarse dinámicamente en tiempo de ejecución a partir de las respuestas provistas por la fuente de datos.
- Toda lógica y algoritmo DEBE ser genérico y operar de manera homogénea sobre cualquier cripta arbitraria que respete el esquema oficial del API.
- *Justificación*: Evita soluciones ad-hoc sesgadas a las mazmorras de muestra y garantiza que el motor resuelva el problema general.

### V. Presupuesto de Red y Consumo Eficiente
El sistema DEBE monitorear, respetar y no superar bajo ninguna circunstancia el `presupuesto_solicitudes` definido por la cripta.
- Toda solicitud HTTP enviada a la red DEBE contabilizarse dentro del presupuesto consumido, incluyendo de forma expresa los reintentos provocados por saturación o límites de tasa (código HTTP 429).
- El cliente de red DEBE emplear técnicas de optimización obligatorias:
  1. Solicitudes por lotes (`batch`) cuando el API admita consultar múltiples elementos en una única petición (por ejemplo, contenido de salas contiguas).
  2. Algoritmos de precarga inteligente (BFS de salas adyacentes a la posición actual).
  3. Persistencia y almacenamiento en caché en disco validado estrictamente por versiones (`version.json` o cabeceras de versión del API), evitando peticiones redundantes si la versión coincide.
- Si el presupuesto de solicitudes se agota, el programa NO DEBE caerse: DEBE avisar una sola vez de dicha condición y NUNCA DEBE dejar al jugador en una sala cuyo contenido no conozca (impidiendo transiciones hacia salas sin datos).
- *Justificación*: El acceso al API es un recurso escaso; una gestión resiliente del agotamiento protege la consistencia del juego sin comprometer la integridad visual ni la navegación.

### VI. Rendimiento con Evidencia Empírica y Límites Críticos
Toda afirmación, optimización o decisión de diseño relativa a la complejidad y rendimiento DEBE estar respaldada por mediciones empíricas reproducibles mediante la bandera `--bench`.
- Los límites temporales fijados por el enunciado del proyecto DEBEN medirse y cumplirse sobre la cripta de referencia:
  - Ciclo completo de eventos entre dos decisiones del jugador: máximo 20 ms.
  - Verificación de resolubilidad: máximo 200 ms (cripta publicada más grande).
  - Consulta de historia: máximo 50 ms (partida de 5000 acciones, K por defecto).
  - Un paso de "ir a": máximo 5 ms (mapa conocido completo de la cripta de referencia).
- Las pruebas de estrés con criptas sintéticas más grandes (con escalas de cientos o miles de salas, actores y eventos) se utilizan para documentar límites conocidos y comportamiento asintótico, y NO DEBEN considerarse una condición de aceptación o fallo. Un incumplimiento medido en una cripta sintética mayor se documenta como límite conocido en `DECISIONES.md` con su causa.
- Cada estructura de datos o algoritmo clave DEBE documentar en `DECISIONES.md` en la raíz del repositorio la comparación frente a alternativas descartadas con evidencia empírica cuantitativa.
- *Justificación*: El rendimiento en tiempo real exige comprobación científica sobre la cripta de referencia y honestidad técnica documentando los límites asintóticos del sistema frente a cargas mayores.

### VII. Especificación antes que Código y Trazabilidad Git
NINGUNA capacidad, algoritmo o módulo DEBE implementarse en el código sin contar previamente con su especificación formal, plan de implementación y lista de tareas aprobados y confirmados en el historial de Git.
- `spec.md` DEBE contener reglas del juego, historias de usuario, escenarios de aceptación y requisitos numerados, y NO DEBE contener nombres de estructuras de datos, algoritmos, clases ni módulos.
- `plan.md` DEBE contener estructuras, alternativas consideradas, complejidad, módulos afectados y mediciones planificadas, y NO DEBE contener reglas nuevas.
- Cada requisito funcional DEBE identificarse de forma estable y unívoca (e.g., `FR-001`, `FR-002`, ...).
- Cada caso del Apéndice B del enunciado DEBE aparecer como escenario de aceptación.
- Cada escenario de aceptación DEBE contar con al menos una prueba automatizada o un archivo `partida.log` de reproducción que cite explícitamente el requisito funcional (`FR-xxx`) correspondiente.
- Cada tarea técnica del plan DEBE explicitar los requisitos funcionales a los que da cumplimiento.
- Cada comando de spec-kit ejecutado con texto propio DEBE registrarse en `PROMPTS_LLM.md`.
- Si durante la implementación se detecta un error, inconsistencia o inviabilidad en la especificación, se DEBE enmendar primero el documento de especificación en una confirmación (`commit`) de Git independiente antes de alterar el código productivo.
- *Justificación*: La disciplina de diseño previo previene el retrabajo, evita la desviación de alcance y proporciona una auditoría rigurosa de cada decisión tomada.

### VIII. Calidad y Pruebas Automatizadas con unittest
La calidad y corrección del sistema DEBEN validarse mediante pruebas automatizadas exhaustivas utilizando exclusivamente la biblioteca estándar `unittest`.
- La totalidad de las pruebas del proyecto DEBE ejecutarse con éxito desde la raíz mediante el comando estándar: `python -m unittest`.
- Una tarea o funcionalidad NO DEBE considerarse terminada hasta que todas las pruebas (existentes y nuevas) pasen limpiamente con cero errores y cero fallos.
- Las pruebas DEBEN cubrir casos nominales, condiciones de borde (límites de presupuesto, inventario colmado, reversión al inicio, cola vacía) y recuperación ante fallos de datos o red.
- *Justificación*: Asegura una red de seguridad continua para prevenir regresiones y garantizar la estabilidad integral del juego ante refactorizaciones.

### IX. Estado Reversible y Persistencia Incremental
Cualquier cambio de estado introducido en el juego DEBE soportar reversibilidad mediante el pergamino de retroceso y guardarse en el archivo de partida sin recurrir a duplicaciones completas indiscriminadas del estado.
- Queda prohibido (NO SE DEBE) clonar el estado completo (`deepcopy`) en cada turno o evento. Se permiten copias completas del estado EXCLUSIVAMENTE como puntos de control (*checkpoints*) de la línea de tiempo, como máximo uno cada K acciones del jugador (donde K es configurable con la bandera `--checkpoint-cada`). Fuera de dichos puntos de control, solo se DEBE guardar lo estrictamente necesario para reconstruir los cambios (deltas).
- Las partidas guardadas (`.sav`) DEBEN incluir una cabecera con el número de versión del formato de guardado.
- Si el esquema o la codificación del guardado se modifica, se DEBE incrementar su versión; el sistema DEBE identificar y reportar los archivos antiguos incompatibles de manera explícita y amigable sin corromper la ejecución.
- *Justificación*: La duplicación masiva continua del estado degrada el uso de memoria y excede el presupuesto de tiempo por ciclo; el balance entre checkpoints periódicos controlados y almacenamiento diferencial protege tanto los recursos como la experiencia de juego.

### X. Simplicidad, Legibilidad y Cero Dependencias Innecesarias
El código DEBE guiarse por la claridad, la sencillez arquitectónica y el respeto a las directrices de estilo del proyecto.
- El proyecto DEBE ejecutarse en Python 3.11 o superior.
- Modularidad: Se DEBE mantener la convención de una clase por archivo, agrupando componentes en sus paquetes respectivos.
- Los Objetos de Transferencia de Datos (DTOs) en `dtos/` DEBEN ser inmutables (e.g., congelados) y carecer de métodos de lógica o reglas del juego.
- Idioma y estilo: Los nombres de clases, métodos, funciones, variables, rutas y mensajes DEBEN estar expresados en español correcto y consistente.
- Los comentarios DEBEN ser breves y de alto valor, explicando el *porqué* de una decisión o algoritmo complejo y nunca reiterando lo evidente.
- NO SE DEBEN añadir dependencias externas adicionales en `requirements.txt` a menos que se justifique fehacientemente y se apruebe en el plan técnico.
- Ante múltiples alternativas de diseño válidas que satisfagan la especificación, se DEBE escoger siempre la opción más simple y directa (KISS / YAGNI).
- *Justificación*: Un código legible, modular y minimalista reduce la tasa de errores, minimiza la fricción de mantenimiento y asegura que el foco resida en la lógica algorítmica.

## Restricciones Técnicas y Estándares del Sistema

### Entorno y Dependencias
- **Versión de Python**: Python 3.11 o superior (con soporte para tipado estático y mejoras en manejo de excepciones).
- **Dependencias autorizadas**: Exclusivamente las listadas en `requirements.txt` (`requests`). Cualquier otra adición requiere un proceso formal de enmienda justificado en el plan de arquitectura.
- **Entorno de consola**: La interfaz de usuario opera en modo texto en terminal estándar (ANSI/UTF-8), abstrayéndose completamente del modelo mediante adaptadores de vista.
- **Registro de Decisiones**: Toda justificación de estructuras elegidas frente a alternativas descartadas se documenta formalmente en `DECISIONES.md` en la raíz del proyecto.

### Organización de Módulos y Paquetes
- `estructuras/`: Implementaciones artesanales de estructuras de datos (heap, vector ordenado, lista doble, pila, fila, ordenamientos). Sin importaciones de módulos prohibidos.
- `modelo/`: Reglas de negocio del juego, agenda determinista de eventos, cálculo de visibilidad y combate.
- `controlador/`: Coordinación del flujo del juego, despacho de acciones y enlace entre adaptadores y modelo.
- `adaptadores/`: Clientes de red REST, almacenamiento offline, cargador/grabador binario de partidas y bitácoras.
- `dtos/`: Modelos de datos inmutables deserializados de respuestas externas.
- `vista/`: Formateo de visualización por terminal y reproductor de partidas grabadas (`vista_replay.py`).
- `bench/`: Mediciones empíricas de tiempo y memoria sobre la cripta de referencia y criptas sintéticas con semillas reproducibles.
- `tests/`: Suites de pruebas automatizadas con `unittest`.

## Flujo de Trabajo y Puertas de Calidad

### Puertas de Aceptación Obligatorias (Quality Gates)
Antes de fusionar o considerar completada cualquier tarea o funcionalidad en el repositorio, se DEBEN validar las siguientes compuertas:

1. **Gate 1 - Validez Constitucional**: La solución propuesta y su diseño técnico DEBEN respetar sin excepciones los 10 principios fundamentales establecidos en esta constitución.
2. **Gate 2 - Cobertura de Especificación y Trazabilidad**: Todo requisito funcional (`FR-xxx`) DEBE contar con sus correspondientes tareas asociadas y pruebas o registros de reproducción que citen su identificador.
3. **Gate 3 - Aprobación de Pruebas Unitarias**: El comando `python -m unittest` DEBE reportar 100% de éxito en todas las pruebas del repositorio.
4. **Gate 4 - Auditoría de Rendimiento**: En cambios que impacten la agenda, estructuras de datos, navegación o ciclo principal, `python main.py --bench` DEBE ratificar que el ciclo de eventos no excede el umbral de 20 ms sobre la cripta de referencia, así como el cumplimiento de los límites críticos del Principio VI (resolubilidad en 200 ms, consulta de historia en 50 ms e "ir a" en 5 ms). Las pruebas de estrés con criptas sintéticas más grandes documentan límites conocidos en `DECISIONES.md` y no constituyen condición de rechazo o fallo.
5. **Gate 5 - No Infiltración de Datos**: Las pruebas de análisis y revisión de código DEBEN verificar la ausencia total de literales de salas, identificadores fijos o constantes ligadas a criptas específicas.

## Governance

Esta constitución constituye la máxima autoridad técnica y metodológica para el proyecto CRIPTA (Segunda Parte). Sus principios son de observancia obligatoria para todos los desarrolladores y agentes involucrados en el ciclo de vida del software.

### Proceso de Enmiendas
1. Toda propuesta de enmienda o ajuste a los principios o secciones de esta constitución DEBE registrarse directamente en una confirmación (`commit`) de Git dedicada que incluya su debida justificación, sin requerir la creación de *issues* externos.
2. No se permiten enmiendas tácitas o silenciosas. La confirmación dedicada en Git DEBE preceder a la implementación de cualquier código que dependa de la modificación constitucional.
3. El documento DEBE mantener su número de versión actualizado de acuerdo con las reglas de Versionado Semántico y reflejar las fechas de ratificación y última modificación en formato ISO (YYYY-MM-DD).

### Política de Versionado
- **MAJOR (X.0.0)**: Redefinición, adición o eliminación de principios fundamentales que alteren sustancialmente la arquitectura, restricciones de estructuras o políticas de evaluación.
- **MINOR (x.Y.0)**: Inclusión de nuevas directrices de calidad, ampliación de secciones de gobernanza o restricciones técnicas complementarias compatibles con los principios vigentes.
- **PATCH (x.y.Z)**: Ajustes de redacción, corrección de erratas ortográficas o clarificaciones no semánticas.

### Auditoría y Cumplimiento
- En cada ciclo de desarrollo impulsado por especificaciones (`speckit.specify`, `speckit.plan`, `speckit.tasks`, `speckit.implement`), se DEBE ejecutar una auditoría de conformidad constitucional.
- Toda desviación identificada en una revisión técnica es clasificada como un bloqueo crítico que DEBE corregirse de inmediato.

**Version**: 1.1.0 | **Ratified**: 2026-11-03 | **Last Amended**: 2026-11-15
