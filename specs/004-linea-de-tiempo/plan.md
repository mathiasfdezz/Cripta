# Implementation Plan: Línea de tiempo con puntos de control

**Branch**: `004-linea-de-tiempo` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-linea-de-tiempo/spec.md`

## Summary

Reconstrucción **hacia adelante**: la línea guarda la lista de operaciones que cambian la partida
(acciones del jugador con su argumento, avances del reloj, llegada de contenido, movimientos del
cursor) y, cada K acciones, un punto de control: una copia completa del estado justo antes de la
acción, con el estado del `random.Random`. Para consultar se copia el punto de control más cercano
anterior y se re-aplican como máximo K acciones. El punto de control se ubica en O(1) por
aritmética (la acción k está después del punto ⌊(k−1)/K⌋) y el instante t con una búsqueda binaria
propia sobre los tiempos de decisión. Un pergamino recorta la cola de la línea en O(cambios de la
acción revertida).

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: ninguna nueva (`copy.deepcopy` de la biblioteca estándar para las copias)
**Storage**: archivo de partida formato 5 con la línea (K y operaciones)
**Testing**: `unittest`
**Performance Goals**: consulta < 50 ms con 5000 acciones y K por defecto (PR-301)
**Constraints**: una copia como máximo cada K acciones; sin `dict`/`set`/`bisect` (Constitución I y IX)

## Constitution Check

- **I**: listas como almacenamiento contiguo, búsqueda binaria propia (sin `bisect`); el `memo` de `deepcopy` es interno de la biblioteca, no un índice del modelo.
- **II**: la re-simulación parte de una copia que incluye el `random.Random` de la partida; misma entrada, misma salida.
- **III**: la línea vive en el modelo; el resumen lo arma la vista; `--replay --hasta` no instancia la vista interactiva.
- **IX**: la excepción de la constitución: copias completas solo como puntos de control, una cada K acciones; fuera de ellos, solo operaciones.

## Estructuras y alternativas

### 1. Reconstrucción hacia adelante (elegida) frente a hacia atrás
- **Hacia adelante**: punto de control + re-simular ≤ K acciones. Costo de consulta acotado por K; memoria = operaciones + V/K copias. Reutiliza el motor tal cual: la re-simulación es la partida misma.
- **Hacia atrás**: invertir cambios desde el estado actual. El historial de retroceso guarda funciones que apuntan a los objetos vivos: para no tocar la partida habría que copiar el estado actual en cada consulta y volver a enlazar cada cambio a la copia; además, consultar el inicio de una partida de 5000 acciones invierte 5000 acciones (no acotado por K) salvo que también haya puntos de control. Se descarta; el bench mide el costo de la copia y de la re-simulación para respaldarlo.

### 2. Ubicar el punto de control
- Puntos de control en una lista, uno por cada K acciones: el de la acción k está en la posición ⌊(k−1)/K⌋, O(1).
- Para `historia t`: lista de tiempos de decisión (no decreciente) y búsqueda binaria propia, O(log n).
- **Alternativa**: recorrer la lista de puntos de control: O(n/K) por consulta.

### 3. Recorte al usar un pergamino
- Se quitan de la cola las operaciones de la acción revertida (conservando la llegada de contenido, que el pergamino no deshace), su tiempo de decisión y, si lo hubiera, el punto de control tomado al iniciarla. O(operaciones de esa acción).

### 4. Copia del estado
- `copy.deepcopy` con un memo inicial que comparte lo inmutable (grafo, salas del esqueleto, caché del catálogo), da un historial vacío a la copia y descarta las cachés de búsqueda. `Puerta` y `Evento` tienen copia propia (sin el camino genérico), lo que baja la copia de la cripta de referencia de 17 ms a 6 ms.

### 5. Persistencia
- El archivo pasa a formato 5 y agrega un registro con K y las operaciones (el contenido de sala se serializa completo). Al cargar se re-simula desde el inicio para rearmar los puntos de control; el estado reconstruido se compara con el guardado y, si coincide, es el estado de la partida cargada.

### 6. Valor de K
- Se mide memoria y tiempo de consulta con K = 10, 50, 200 y sin puntos de control en una partida sintética de 5000 acciones; se elige el menor K cuyo costo de memoria sea razonable y que cumpla 50 ms con holgura.

## Complejidad

| Operación | Costo |
|-----------|-------|
| anotar una operación | O(1) |
| punto de control | O(tamaño del estado), una vez cada K acciones |
| `historia #k` | O(1) ubicar + O(copia) + O(≤ K acciones) |
| `historia t` | O(log n) ubicar + lo anterior |
| recorte por pergamino | O(operaciones de la acción revertida) |
| memoria | O(operaciones) + ⌈n/K⌉ copias |

## Módulos afectados

- Nuevos: `modelo/linea_tiempo.py`, `modelo/punto_de_control.py`, `modelo/copia_estado.py`, `vista/texto_historia.py`, `bench/bench_linea_tiempo.py`.
- Cambian: `modelo/estado_partida.py` (anotar operaciones, cursor por el modelo, avanzar hasta un instante), `modelo/puerta.py` y `modelo/evento.py` (copia propia), `controlador/partida.py` (`historia`, cursor), `adaptadores/guardado_binario.py` y `guardado_partida.py` (formato 5), `main.py` (`--checkpoint-cada`, `--replay --hasta`), `vista/consola.py`.

## Mediciones planificadas

- Memoria (tracemalloc) y tiempo de consulta (promedio y máximo) con K = 10, 50, 200 y sin puntos de control, partida de 5000 acciones.
- Costo de un punto de control en la cripta de referencia y su efecto en el ciclo de 20 ms.
- Repetir el bench del historial de retroceso con la carga nueva (§5.6).
