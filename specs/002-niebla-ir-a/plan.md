# Implementation Plan: Niebla de guerra y viaje automático «ir a»

**Branch**: `002-niebla-ir-a` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-niebla-ir-a/spec.md`

## Summary

El conocimiento del jugador se guarda en un `MapaConocido` con una posición por sala y otra por
salida, indexadas con los índices densos de `GrafoCripta` (capacidad 001). Cada cambio se anota en
el historial como (lista, posición, valor anterior), así el pergamino lo revierte y la línea de
tiempo lo copia. «ir a» reutiliza `BuscadorRutas` (capacidad 001) con otros predicados: solo salas
exploradas y salidas recordadas abiertas, recalculado antes de cada paso.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: ninguna nueva (biblioteca estándar y `requests` ya existente)
**Storage**: archivo de partida binario; el formato sube de versión (3 → 4) para incluir el mapa
**Testing**: `unittest` (`python -m unittest`)
**Performance Goals**: un paso de «ir a» < 5 ms con el mapa completo de la cripta de referencia (PR-101); consultas al mapa O(1) (PR-102)
**Constraints**: sin `dict`, `set`, `heapq`, `collections` ni bibliotecas de grafos (Constitución I)

## Constitution Check

- **I. Estructuras propias**: listas indexadas por índice denso (almacenamiento contiguo) y el `MinHeap` propio; ningún `dict` ni `set`.
- **II. Determinismo**: el mapa no usa azar; la ruta desempata por id.
- **III. MVC**: el mapa vive en el modelo; el comando `mapa` y el motivo de detención los muestra la vista; el ciclo del viaje lo coordina el controlador porque necesita traer contenido entre pasos.
- **V. Presupuesto**: la precarga sigue usando el esqueleto completo; el mapa no pide nada a la red.
- **VII. Spec antes que código**: este plan no agrega reglas; todo sale de spec.md.
- **IX. Estado reversible**: cada cambio del mapa se anota en el historial; el guardado sube de versión.

## Estructuras y alternativas

### 1. Estado de sala y memoria de puertas
- **Elegida**: dos listas: `estado[i]` (0 desconocida, 1 avistada, 2 explorada) por índice denso de sala y `recuerdo[s]` (-1 sin observar, 0 abierta, 1 cerrada) por índice de salida. Consultar es O(1). Explorar la sala `i` cuesta O(salidas de i).
- **Alternativa A**: `VectorOrdenado` de ids explorados y otro de salidas observadas. Consulta O(log n) y explorar inserta con desplazamiento O(n): explorar la sala k cuesta proporcional al mapa conocido, lo que §5.3 prohíbe.
- **Alternativa B**: atributos en los objetos `Sala` (DTO congelado): rompe la Constitución X y mezcla datos del API con estado del juego.
- **Reversión**: cada cambio anota (lista, posición, valor anterior). Revertir una entrada con antorcha que exploró 5 salas cuesta O(cambios anotados): las 5 salas, sus avistadas nuevas y sus salidas observadas.

### 2. Ruta de «ir a»
- **Elegida**: la misma clase `BuscadorRutas` del cazador, otra instancia, con `pasable = recuerda_abierta` y `admitida = esta_explorada`. Dijkstra al revés desde el destino, sin cota, y el primer paso con el mismo desempate. Se recalcula antes de cada paso (FR-111), sin caché: el conocimiento cambia en cada paso y el límite (5 ms) lo permite.
- **Por qué compartir la implementación**: el desempate del enunciado es idéntico (§3.4 remite a §3.2) y ya está probado; solo cambian las reglas de qué se puede pasar. **Por qué instancias separadas**: el cazador usa las puertas reales y una caché invalidada por cambios de puertas; «ir a» usa la memoria del jugador y no puede compartir esas distancias.
- **Alternativa medida**: búsqueda hacia adelante desde el jugador que se detiene al sacar el destino (`RutaPorCazador` del bench de 001 con los mismos predicados).

### 3. Coordinación del viaje
- `EstadoPartida.paso_hacia(destino)`: valida el destino (FR-109) y devuelve la dirección del siguiente paso o None. No cambia nada.
- `ControladorPartida`: repite paso → mover (con precarga de contenido) → revisar condiciones de detención (FR-112), y anota cada paso en partida.log con el comentario `# ir a <sala>` antes del primero (FR-113).

## Complejidad

| Operación | Costo |
|-----------|-------|
| estado de una sala, puerta recordada | O(1) |
| explorar una sala (entrar) | O(salidas de la sala + salidas que entran a ella) |
| entrar con antorcha | O(suma de salidas de la sala y de sus vecinas) |
| revertir una acción | O(cambios anotados en ella) |
| un paso de «ir a» | O(R + E_R log R) sobre las salas exploradas |

## Módulos afectados

- `modelo/mapa_conocido.py` (nuevo), `modelo/historial.py` (cambios de una posición de lista), `modelo/estado_partida.py` (exploración, observación, antorcha, `paso_hacia`), `modelo/movimiento.py` (motivos nuevos).
- `controlador/partida.py` (comandos `mapa` e `ir a`, motivo de detención), `adaptadores/bitacora_partida.py` (comentarios).
- `adaptadores/guardado_binario.py`, `adaptadores/guardado_partida.py` (formato 4 con el mapa).
- `vista/consola.py`, `vista/menu_acciones.py` (solo conocimiento del jugador, mapa, viaje).
- `bench/bench_mapa.py` (nuevo).

## Mediciones planificadas (borrador para DECISIONES.md)

- Consultas al mapa: lista indexada frente a `VectorOrdenado`, con 50, 300 y 900 salas exploradas.
- Exploración: costo de explorar una sala nueva según el tamaño del mapa conocido (debe ser constante).
- «ir a»: tiempo por paso con el mapa completo de la cripta de referencia (300 salas) y de una sintética de 900; Dijkstra al revés completo frente a búsqueda hacia adelante con parada en el destino.
- Ciclo del juego con la niebla activa: repetir la medición de 20 ms (§5.6).
