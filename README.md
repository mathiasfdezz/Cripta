# Cripta

Juego de mazmorra por consola para el proyecto de Estructuras de Datos II.

La segunda parte agrega terreno con costo y cazadores, niebla de guerra con viaje automático
(«ir a»), verificación de resolubilidad y línea de tiempo con puntos de control. Se desarrolló con
especificaciones ejecutables (SDD).

## Desarrollo con spec-kit

- **spec-kit**: versión **1.1.0**, instalada con
  `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v1.1.0`.
- **Agente**: **Claude Code** (integración `claude`, la que usa el proyecto por defecto). La
  constitución se escribió con Gemini CLI, cuya integración sigue instalada.
- Constitución: `.specify/memory/constitution.md`. Especificaciones, planes, tareas y análisis de
  cada capacidad: `specs/001-terrain-hunter`, `specs/002-niebla-ir-a`, `specs/003-resolubilidad` y
  `specs/004-linea-de-tiempo`.
- Cada requisito tiene un identificador único en el proyecto (FR-001…, FR-101…, FR-201…, FR-301…)
  y cada prueba de aceptación cita el suyo.

## Requisitos

- Python 3.11 o superior
- Dependencias: `pip install -r requirements.txt` (solo `requests`)

## Ejecutar

```bash
python main.py
```

Sin argumentos muestra las criptas disponibles y pide elegir una (por número o por id). También se puede indicar directamente: `python main.py cripta-02`.

Antes de empezar se verifica si la cripta se puede ganar y se muestra el reporte. Si no es
resoluble, la partida no inicia salvo con `--forzar`.

Banderas:

- `--offline`: lee los datos de `datos_offline/` en vez del API. No gasta solicitudes.
- `--cache-size N`: fichas del catalogo en memoria (por defecto 25, minimo 1).
- `--semilla N`: semilla del azar. Sin ella se elige una y se muestra al empezar.
- `--replay partidas/ARCHIVO.log`: reproduce una partida sin interaccion. Si la version de la cripta o del catalogo ya no coincide, lo informa y no la reproduce.
- `--bench`: corre las mediciones de rendimiento y termina.
- `--verificar CRIPTA`: solo verifica si la cripta se puede ganar e imprime el reporte (orden de
  llaves, o llaves que faltan, puertas que bloquean y ciclo de llaves). No abre la interfaz.
  Código de salida 0 si es resoluble y 1 si no. Ejemplo: `python main.py --verificar cripta-05 --offline`.
- `--forzar`: juega aunque la cripta no sea resoluble.
- `--checkpoint-cada K`: acciones del jugador entre puntos de control de la línea de tiempo
  (por defecto 25; la elección está medida en `DECISIONES.md`).
- `--replay partidas/ARCHIVO.log --hasta T`: reproduce la partida hasta el instante T e imprime el
  mismo resumen que `historia T`, sin la interfaz. Si T es posterior al final, muestra el estado
  final y lo indica.

## Cómo se juega

Después de cada pantalla aparece el menú **¿Qué haces?** con lo que se puede hacer en ese momento (moverse, abrir una puerta si tienes su llave, atacar, recoger, usar o equipar objetos, esperar, deshacer). Basta con escribir el número de la opción. Atajos que funcionan siempre: `i` inventario, `g` guardar, `c` cargar, `?` ayuda y `q` salir.

También se pueden escribir los comandos: `n`/`s`/`e`/`o` (o `norte`, `sur`...), `abrir <dir>`, `atacar <número>`, `esperar`, `recoger <número>`, `soltar`, `equipar`, `usar`, `sig`/`ant` (recorrer el inventario), `inv [peso|valor|nombre]`, `deshacer`, `guardar [nombre]`, `cargar [nombre]` y `salir`.

Comandos de la segunda parte:

- `mapa` (o `m`): las salas exploradas con sus salidas, costos y puertas como las recuerdas, y
  cuántas salas avistadas hay. Las salas que no exploraste no muestran nombre.
- `ir a <sala>`: viaja a una sala explorada paso a paso, por la ruta conocida más barata. Se
  detiene al llegar, al entrar a una sala con enemigos, al recibir daño o si ya no hay ruta, y
  dice por qué. No abre puertas.
- `historia <t>` o `historia #k`: cómo estaba la partida en el instante t o justo antes de tu
  acción número k (reloj, sala, vida, inventario, efectos, enemigos de esa sala y mapa). No gasta
  tiempo ni cambia nada.

Cada salida muestra su costo (moverse tarda lo que cuesta la salida) y los cazadores aparecen
marcados como `[CAZADOR, rango N]`.

La bitácora de la partida guarda siempre los comandos reales (por ejemplo `sig`, `usar` o `recoger itm_antorcha`), nunca el número del menú, por eso `--replay` no depende de la pantalla.

## Archivos generados

- `datos_offline/`: respuestas del API guardadas para `--offline` (criptas 02 a 06 de la segunda parte, con la ubicación de las llaves). Para regenerarlas (gasta solicitudes): `python -m scripts.descargar_offline`. Los datos de la primera parte quedaron en `tests/datos_p1/` porque las pruebas viejas los usan.
- `cache_catalogo/`: fichas del catalogo guardadas en disco. Se regenera sola si cambia la version del catalogo.
- `cache_criptas/`: esqueleto y contenido de cada cripta jugada en linea. Se descarta solo si cambia la version de la cripta.
- `partidas/partida-FECHA.log`: bitacora de cada partida, sirve para `--replay`.
- `partidas/partida-FECHA-cargada.log`: bitacora nueva que se crea al cargar una partida guardada.
- `partidas/NOMBRE.sav`: partidas guardadas en formato binario con `guardar` (versión 5: incluye el mapa conocido y la línea de tiempo; los archivos de la primera parte se rechazan con un aviso).
- `puntajes.txt`: tabla local de puntajes.

## Pruebas

```bash
python -m unittest
```

Pruebas de aceptación de cada capacidad (cada una cita el FR que verifica):

```bash
python -m unittest tests.test_movimiento_terreno tests.test_cazador tests.test_vista_terreno
python -m unittest tests.test_niebla tests.test_ir_a tests.test_vista_niebla
python -m unittest tests.test_resolubilidad tests.test_verificar_main tests.test_mapeador_llaves
python -m unittest tests.test_linea_tiempo tests.test_replay_hasta
```

## Mediciones

```bash
python main.py --bench
```

No usa la red y tarda unos minutos. De la primera parte mide la agenda (heap contra lista), la busqueda en la cache (vector ordenado contra arbol binario), la recuperacion de fichas liberadas, el inventario, el historial de retroceso, la decision del rastreador (contra un BFS por toda la cripta), la bitacora de 20 mensajes (contra listas), los ordenamientos y su umbral, el guardado binario contra JSON y el ciclo completo entre dos decisiones del jugador (limite de 20 ms), ahora también en la cripta de referencia con todos sus cazadores activos.

De la segunda parte: la ruta del cazador (un cálculo compartido contra uno por cazador, rango pequeño y grande), la invalidación (reutilizar contra recalcular siempre, con puertas estables e inestables), el mapa conocido y el paso de «ir a», la resolubilidad (recorrido incremental contra repetirlo por llave, con criptas de muchas llaves encadenadas) y la línea de tiempo (memoria y consulta con K = 10, 25, 50 y 200 y sin puntos de control). La cripta de referencia es la más grande del paquete offline.

## Estructura del proyecto

- `modelo/`: reglas del juego (no sabe nada de red, archivos ni pantalla).
- `estructuras/`: estructuras propias (heap, lista doble, pila, fila circular, vector ordenado, ordenamientos).
- `specs/` y `.specify/`: especificaciones y artefactos de spec-kit.
- `controlador/`: traduce los comandos del jugador a operaciones del modelo.
- `vista/`: consola y reproduccion.
- `adaptadores/`: API, modo offline, guardado binario y archivos.
- `dtos/`: datos que llegan del API, sin logica.
- `bench/`: mediciones y alternativas descartadas.
- `tests/`: pruebas con unittest.

## Documentacion

- `DECISIONES.md`: Documento de Decisiones de Diseño (primera y segunda parte).
- `PROMPTS_LLM.md`: bitácora de prompts de la segunda parte, incluidos los comandos de spec-kit.
- `docs/bitacora_prompts.pdf`: bitácora de prompts de la primera parte.
- `docs/enunciado_parte2.md`: enunciado de la segunda parte, como referencia de las especificaciones.