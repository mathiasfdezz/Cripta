# Cripta

Juego de mazmorra por consola para el proyecto de Estructuras de Datos II.

## Requisitos

- Python 3.11 o superior
- Dependencias: `pip install -r requirements.txt`

## Ejecutar

```bash
python main.py cripta-01
```

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
`inv [peso|valor|nombre]`, `deshacer` (pergamino de retroceso) y `salir`.

## Archivos

- `datos_offline/`: respuestas del API guardadas. Para regenerarlas: `python -m scripts.descargar_offline`
- `cache_catalogo/`: fichas del catalogo guardadas en disco. Se regenera sola.
- `partidas/`: bitacora de cada partida (`partida-FECHA.log`), sirve para `--replay`.
- `puntajes.txt`: tabla local de puntajes.

## Pruebas

```bash
python -m unittest
```

## Mediciones

```bash
python -m bench.bench
```

## Documentacion

- `docs/`: Documento de Decisiones de Diseno.
- Bitacora de prompts: documento de Word del grupo.