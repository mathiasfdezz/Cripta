# Implementation Plan: Verificación de resolubilidad

**Branch**: `003-resolubilidad` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-resolubilidad/spec.md`

## Summary

Un único recorrido en anchura desde la sala inicial que, al encontrar una puerta cerrada cuya
llave todavía no se tiene, la deja **pendiente en la lista de esa llave**. Cuando se obtiene una
llave se liberan de una vez todas sus puertas pendientes y sus destinos entran a la fila. Cada
salida se examina una vez y cada puerta pendiente se libera una vez: O(V + E + L log L).
Si no es resoluble, el mismo recorrido continúa por detrás de la frontera (0-1 BFS por cantidad
de puertas cerradas) para saber de qué llaves depende cada llave no obtenible, y un DFS iterativo
en orden de id encuentra el ciclo.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: ninguna nueva
**Storage**: `llaves.json` junto a los datos de cada cripta (copia en disco y paquete offline)
**Testing**: `unittest`
**Performance Goals**: < 200 ms en la cripta publicada más grande (PR-201); crecimiento lineal (PR-202)
**Constraints**: sin `dict`, `set`, `collections` ni bibliotecas de grafos (Constitución I)

## Constitution Check

- **I**: `Fila` propia (circular) para el recorrido, listas por índice denso (`GrafoCripta` de 001), `VectorOrdenado` para el índice de llaves por id.
- **II**: orden de la fila (salidas N, S, E, O; llaves de una sala por id) y DFS por id: determinista.
- **III**: el verificador vive en el modelo y no sabe de HTTP; la consulta de llaves está en los adaptadores; `--verificar` imprime con un formateador de texto sin la vista interactiva.
- **IV**: nada de la cripta está en el código; todo sale del esqueleto y de `/llaves`.
- **V**: `/llaves` cuenta en el presupuesto y se guarda en disco validado por versión.
- **VI**: bench del recorrido incremental frente al repetido por llave.

## Estructuras y alternativas

### 1. Recorrido incremental con puertas pendientes por llave (elegido)
- `alcanzada[i]` por índice denso, `Fila` de salas por procesar.
- `pendientes[k]`: lista de salidas bloqueadas por la llave k (índice denso de llave).
- Al obtener k: cada salida de `pendientes[k]` encola su destino si no estaba alcanzado. La lista queda vacía: nunca se vuelve a mirar.
- **Costo**: O(V + E) del recorrido + O(L log L) para indexar las llaves + O(puertas cerradas · log L) para buscar el índice de su llave.

### 2. Alternativa medida: repetir el recorrido por llave
- Un BFS completo con las llaves actuales; si encontró llaves nuevas, otro BFS desde cero. O(L · (V + E)) en una cadena de L llaves. Es la «alternativa ingenua» que §5.4 pide medir.

### 3. Reporte de una cripta no resoluble
- **Frontera**: las salidas que quedaron en `pendientes` (o cerradas sin llave) con destino no alcanzado. Sale del recorrido, sin trabajo extra.
- **Dependencias**: se continúa el recorrido desde esas salidas por las salas no alcanzadas, por capas según cuántas puertas cerradas se cruzaron (0-1 BFS con dos `Fila`). Cada sala guarda la última puerta cerrada de su camino y cada puerta la anterior; las llaves de esa cadena son las dependencias de la llave que está en la sala. Un solo recorrido más: O(V + E).
- **Ciclo**: DFS iterativo (pila propia) sobre el grafo llave → dependencias, en orden de id; el primer arco a una llave en la pila actual da el ciclo concreto. O(L + dependencias).

### 4. Integración
- `VerificacionCripta` (controlador) carga el esqueleto y las llaves, ejecuta el verificador y entrega el esqueleto al `ControladorPartida` para no pedir las páginas dos veces.
- `main.py`: `--verificar <cripta>` y `--forzar`; en una partida normal se verifica antes de crear el controlador.

## Complejidad

| Paso | Costo |
|------|-------|
| indexar llaves | O(L log L) |
| recorrido incremental | O(V + E + C log L), C = salidas cerradas |
| frontera | O(C) |
| dependencias (solo si no es resoluble) | O(V + E) |
| ciclo | O(L + D), D = dependencias |

## Módulos afectados

- Nuevos: `dtos/ubicacion_llave.py`, `adaptadores/mapeadores/mapeador_llaves.py`, `modelo/verificador_resolubilidad.py`, `modelo/reporte_resolubilidad.py`, `modelo/puerta_bloqueada.py`, `controlador/verificacion_cripta.py`, `vista/texto_resolubilidad.py`, `bench/bench_resolubilidad.py`, `bench/resolubilidad_repetida.py`.
- Cambian: `adaptadores/fuente_datos.py`, `cliente_red.py`, `cliente_red_con_copia.py`, `cliente_offline.py`, `rutas_offline.py`, `descargador_offline.py` (consulta `/llaves`); `controlador/partida.py` (esqueleto ya cargado); `vista/consola.py` (reporte al iniciar); `main.py`.

## Mediciones planificadas (borrador para DECISIONES.md)

- Tiempo de verificación de cada cripta publicada (la mayor debe quedar bajo 200 ms).
- Criptas sintéticas con 50, 200 y 800 llaves encadenadas: incremental frente a repetido por llave.
