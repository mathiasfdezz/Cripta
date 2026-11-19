# Cripta

Juego de mazmorra por consola para el proyecto de Estructuras de Datos II.

## Requisitos

- Python 3.11 o superior
- Dependencias: `pip install -r requirements.txt` (solo `requests`)

## Ejecutar

```bash
python main.py
```

Sin argumentos muestra las criptas disponibles y pide elegir una (por número o por id). También se puede indicar directamente el id mostrado en la lista, por ejemplo `python main.py --offline cripta-05`.

Banderas:

- `--offline`: lee los datos de `datos_offline/` en vez del API. No gasta solicitudes.
- `--cache-size N`: fichas del catalogo en memoria (por defecto 25, minimo 1).
- `--semilla N`: semilla del azar. Sin ella se elige una y se muestra al empezar.
- `--replay partidas/ARCHIVO.log`: reproduce una partida sin interaccion. Si la version de la cripta o del catalogo ya no coincide, lo informa y no la reproduce.
- `--bench`: corre las mediciones de rendimiento y termina.

## Cómo se juega

Después de cada pantalla aparece el menú **¿Qué haces?** con lo que se puede hacer en ese momento (moverse, abrir una puerta si tienes su llave, atacar, recoger, usar o equipar objetos, esperar, deshacer). Basta con escribir el número de la opción. Atajos que funcionan siempre: `i` inventario, `g` guardar, `c` cargar, `?` ayuda y `q` salir.

También se pueden escribir los comandos: `n`/`s`/`e`/`o` (o `norte`, `sur`...), `abrir <dir>`, `atacar <número>`, `esperar`, `recoger <número>`, `soltar`, `equipar`, `usar`, `sig`/`ant` (recorrer el inventario), `inv [peso|valor|nombre]`, `deshacer`, `guardar [nombre]`, `cargar [nombre]` y `salir`.

La pantalla de cada sala muestra el **costo de cada salida** (el tiempo de moverse depende de él) y marca a los **cazadores** para distinguirlos de los demás enemigos.

La bitácora de la partida guarda siempre los comandos reales (por ejemplo `sig`, `usar` o `recoger itm_antorcha`), nunca el número del menú, por eso `--replay` no depende de la pantalla.

## Archivos generados

- `datos_offline/`: respuestas del API guardadas para `--offline`. Para regenerarlas (gasta solicitudes): `python -m scripts.descargar_offline`
- `cache_catalogo/`: fichas del catalogo guardadas en disco. Se regenera sola si cambia la version del catalogo.
- `cache_criptas/`: esqueleto y contenido de cada cripta jugada en linea. Se descarta solo si cambia la version de la cripta.
- `partidas/partida-FECHA.log`: bitacora de cada partida, sirve para `--replay`.
- `partidas/partida-FECHA-cargada.log`: bitacora nueva que se crea al cargar una partida guardada.
- `partidas/NOMBRE.sav`: partidas guardadas en formato binario con `guardar`.
- `puntajes.txt`: tabla local de puntajes.

## Pruebas

```bash
python -m unittest
```

Son las pruebas de las dos partes. Las de aceptación de la Parte II citan en un comentario el requisito (`FR-xxx`) que verifican; por ejemplo, `tests/test_cazador.py`, `tests/test_movimiento_terreno.py` y `tests/test_vista_terreno.py` cubren los escenarios de `specs/001-terrain-hunter/spec.md`.

## Mediciones

```bash
python main.py --bench
```

Tarda menos de un minuto y no usa la red. Mide la agenda (heap contra lista), la busqueda en la cache (vector ordenado contra arbol binario), la recuperacion de fichas liberadas, el inventario, el historial de retroceso, la decision del rastreador (contra un BFS por toda la cripta), la bitacora de 20 mensajes (contra listas), los ordenamientos y su umbral, el guardado binario contra JSON y el ciclo completo entre dos decisiones del jugador (limite de 20 ms).

Desde la Parte II también mide la ruta del cazador (cálculo individual contra compartido), la invalidación de rutas (reutilizar contra recalcular siempre, con puertas estables e inestables) y el ciclo de eventos con cazadores. Las mediciones de la Parte I se repiten con esa carga. La fila de la cripta de referencia necesita `datos_offline/`.

## Estructura del proyecto

- `modelo/`: reglas del juego (no sabe nada de red, archivos ni pantalla).
- `estructuras/`: estructuras propias (heap, lista doble, pila, fila circular, vector ordenado, ordenamientos).
- `controlador/`: traduce los comandos del jugador a operaciones del modelo.
- `vista/`: consola y reproduccion.
- `adaptadores/`: API, modo offline, guardado binario y archivos.
- `dtos/`: datos que llegan del API, sin logica.
- `bench/`: mediciones y alternativas descartadas.
- `tests/`: pruebas con unittest.
- `.specify/`: constitución del proyecto (`.specify/memory/constitution.md`), plantillas y scripts de Spec Kit.
- `specs/`: una carpeta por capacidad de la Parte II con su `spec.md`, `plan.md` y `tasks.md`.

## Documentación

- `DECISIONES.md`: Documento de Decisiones de Diseño (Parte I y Parte II).
- `PROMPTS_LLM.md`: bitácora de todos los prompts enviados a LLMs (herramienta, prompt textual y uso de cada respuesta), incluidos los comandos de Spec Kit.
- `docs/enunciado_parte2.md`: enunciado de la Parte II, usado como referencia por los comandos de Spec Kit.
- `docs/bitacora_prompts.pdf`: bitácora de prompts de la Parte I.

## Parte II: desarrollo dirigido por especificaciones

- **Spec Kit:** CLI versión 1.2.3 (`uv tool list`). El repositorio se inicializó con `specify init` en otra máquina del grupo, cuya bitácora menciona la 1.1.0.
- **Agentes:** Gemini CLI (`.gemini/`) y Claude Code (`.claude/`) ejecutan los comandos de Spec Kit; Claude (claude.ai) se usó como asistente de revisión. Todo prompt está en `PROMPTS_LLM.md`.
- **Flujo por capacidad:** `/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.analyze` e `/speckit.implement`, con la constitución en `.specify/memory/constitution.md` (versión 1.1.0). El historial de Git conserva el orden: especificación, aclaraciones, plan, tareas y, después, el código.

### Estado de las capacidades

| Capacidad | Estado |
|---|---|
| Terreno y cazador (`specs/001-terrain-hunter`) | Especificada, aclarada, planificada, analizada e **implementada**, con pruebas y mediciones |
| Niebla de guerra e «ir a» | **No implementada** |
| Resolubilidad | **No implementada** |
| Línea de tiempo | **No implementada** |

Para las capacidades no implementadas, lo que exista de ellas está en `specs/`: una carpeta con `spec.md` (y `plan.md` y `tasks.md` si se llegó a esa fase). Una capacidad sin carpeta en `specs/` no fue especificada. Comprobación: `dir specs`.

### Comandos nuevos

Esta entrega no agrega banderas nuevas: `--verificar`, `--forzar`, `--checkpoint-cada` y `--replay … --hasta` pertenecen a capacidades no implementadas. Lo nuevo en la Parte II es el comportamiento del cazador, el costo de las salidas en la partida y las secciones de cazadores de `--bench`.

### Pruebas de aceptación

`python -m unittest` ejecuta todas las pruebas. Para ver la trazabilidad de un requisito, por ejemplo FR-014: `findstr /n /c:"FR-014" tests\test_cazador.py`.
