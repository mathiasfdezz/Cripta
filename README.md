# Cripta

Juego de mazmorra por consola para el proyecto de Estructuras de Datos II.

## Requisitos

- Python 3.11 o superior
- Dependencias: `pip install -r requirements.txt` (solo `requests`)

## Ejecutar

```bash
python main.py
```

Sin argumentos muestra las criptas disponibles y pide elegir una (por número o por id). También se puede indicar directamente: `python main.py cripta-01`.

Banderas:

- `--offline`: lee los datos de `datos_offline/` en vez del API. No gasta solicitudes.
- `--cache-size N`: fichas del catalogo en memoria (por defecto 25, minimo 1).
- `--semilla N`: semilla del azar. Sin ella se elige una y se muestra al empezar.
- `--replay partidas/ARCHIVO.log`: reproduce una partida sin interaccion. Si la version de la cripta o del catalogo ya no coincide, lo informa y no la reproduce.
- `--bench`: corre las mediciones de rendimiento y termina.

## Comandos en el juego

Escribe `ayuda` dentro del juego para ver la lista. Los principales:
`n`/`s`/`e`/`o` (moverse), `abrir <dir>`, `atacar [instancia]`, `esperar`,
`recoger [id]`, `soltar`, `equipar`, `usar`, `sig`/`ant` (recorrer el inventario),
`inv [peso|valor|nombre]`, `deshacer` (pergamino de retroceso),
`guardar [nombre]`, `cargar [nombre]` y `salir`.

## Archivos generados

- `datos_offline/`: respuestas del API guardadas para `--offline`. Para regenerarlas (gasta solicitudes): `python -m scripts.descargar_offline`
- `cache_catalogo/`: fichas del catalogo guardadas en disco. Se regenera sola si cambia la version del catalogo.
- `partidas/partida-FECHA.log`: bitacora de cada partida, sirve para `--replay`.
- `partidas/partida-FECHA-cargada.log`: bitacora nueva que se crea al cargar una partida guardada.
- `partidas/NOMBRE.sav`: partidas guardadas en formato binario con `guardar`.
- `puntajes.txt`: tabla local de puntajes.

## Pruebas

```bash
python -m unittest
```

## Mediciones

```bash
python main.py --bench
```

Tarda unos 15 segundos y no usa la red. Mide la agenda (heap contra lista), la busqueda en la cache (vector ordenado contra arbol binario), la recuperacion de fichas liberadas, el inventario, el historial de retroceso, los ordenamientos y su umbral, el guardado binario contra JSON y el ciclo completo entre dos decisiones del jugador (limite de 20 ms). La fila de la cripta de referencia (la primera del paquete offline) necesita datos_offline/.

## Estructura del proyecto

- `modelo/`: reglas del juego (no sabe nada de red, archivos ni pantalla).
- `estructuras/`: estructuras propias (heap, lista doble, pila, fila circular, vector ordenado, ordenamientos).
- `controlador/`: traduce los comandos del jugador a operaciones del modelo.
- `vista/`: consola y reproduccion.
- `adaptadores/`: API, modo offline, guardado binario y archivos.
- `dtos/`: datos que llegan del API, sin logica.
- `bench/`: mediciones y alternativas descartadas.
- `tests/`: pruebas con unittest.

## Documentacion

- `docs/decisiones.md`: Documento de Decisiones de Diseno.
- `docs/bitacora_prompts.pdf`: bitacora de prompts enviados a LLMs (herramienta, prompt y uso de cada respuesta).