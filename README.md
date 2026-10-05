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
- `--replay PARTIDA.LOG`: reproduce una partida guardada.
- `--bench`: corre las mediciones de rendimiento y termina.

## Archivos

- `datos_offline/`: respuestas del API guardadas. Para regenerarlas: `python -m scripts.descargar_offline`
- `cache_catalogo/`: fichas del catalogo guardadas en disco. Se regenera sola.
- `partidas/`: partidas guardadas.

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