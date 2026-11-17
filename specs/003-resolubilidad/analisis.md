# Análisis de consistencia: Verificación de resolubilidad

Salida de `/speckit-analyze` (Claude Code, 2026-11-17).

| ID | Categoría | Severidad | Ubicación | Hallazgo | Corrección |
|----|-----------|-----------|-----------|----------|------------|
| C1 | Cobertura | MEDIA | tasks.md | FR-209 (reporte en pantalla al iniciar) solo tenía implementación (T212), sin prueba. | T214 verifica que la consola muestre el reporte antes del primer turno. |
| C2 | Ambigüedad | BAJA | spec.md FR-208 | El código de salida de `--verificar` estaba definido; el de una partida que no inicia por no ser resoluble, no. | Se usa 1, igual que cualquier partida que no se puede iniciar (sin cambio de spec: FR-207 no fija código). |
| C3 | Constitución III | — | plan.md | `--verificar` imprime con un formateador de la vista que no lee entrada y no instancia `Consola`. | Conforme; T214 lo comprueba. |
| C4 | Constitución I | — | plan.md | `Fila` y pila propias, sin `collections.deque`. | Conforme. |

**Cobertura**: FR-201 a FR-210 y PR-201, PR-202 con tareas. Apéndice B: T206 (ciclo de llave_salida),
T205 (errante), T204 (orden determinista), T214 (no inicia sin --forzar).
