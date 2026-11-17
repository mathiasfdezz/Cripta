# Data Model: Línea de tiempo

## LineaTiempo (modelo)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `cada` | int | K: acciones entre puntos de control |
| `operaciones` | lista de tuplas | `("contenido", ContenidoSala)`, `("iniciar",)`, `("accion", nombre, argumento)`, `("avanzar",)`, `("cursor", ±1)`, `("pergamino",)`, `("siguiente",)` |
| `inicio_accion` | lista de int | posición en `operaciones` donde empieza la acción k (k = posición + 1) |
| `decisiones` | lista de int | reloj al decidir la acción k (no decreciente) |
| `puntos` | lista de `PuntoDeControl` | el i-ésimo, justo antes de la acción i·K + 1 |

## PuntoDeControl (modelo)

`accion` (número de la acción siguiente), `operacion` (posición en `operaciones`), `estado`
(copia completa, incluye `random.Random`).

## Archivo de partida, versión 5

Registro adicional con CRC: `K` (uint32), cantidad de operaciones (uint32) y cada operación con
un código de un byte (1 contenido, 2 iniciar, 3 acción, 4 avanzar, 5 cursor, 6 pergamino,
7 siguiente) y sus datos.
