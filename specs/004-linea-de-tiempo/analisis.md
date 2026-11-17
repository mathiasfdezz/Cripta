# Análisis de consistencia: Línea de tiempo

Salida de `/speckit-analyze` (Claude Code, 2026-11-17).

| ID | Categoría | Severidad | Ubicación | Hallazgo | Corrección |
|----|-----------|-----------|-----------|----------|------------|
| D1 | Constitución IX | ALTA | spec.md, plan.md | La constitución permite copias completas solo como puntos de control, una cada K acciones. El plan cumple: la consulta copia el punto de control (copia temporal, se descarta), no lo guarda. | Se deja explícito en T309: el número de puntos guardados nunca supera ⌈acciones/K⌉. |
| D2 | Inconsistencia | MEDIA | spec.md supuestos / P1 §2.11 | El supuesto de que el pergamino revierte el cursor cambia un detalle de la primera parte. | Es una precisión compatible (P1 dice «estado anterior a la última acción»); la prueba de P1 que corresponda se revisa en T302. |
| D3 | Cobertura | MEDIA | tasks.md | PR-301 se mide en el bench, pero no hay prueba automática de tiempo. | T309 incluye una partida larga con K por defecto y un tope holgado de tiempo por consulta. |
| D4 | Constitución I | — | plan.md | Búsqueda binaria propia; sin `bisect`. | Conforme. |

**Cobertura**: FR-301 a FR-310 con tareas. Apéndice B: T306 (t mayor), T308 (pergamino), T305
(mismo instante), T307 (no altera), T311 (--hasta posterior), T313 (archivo de la primera parte).
