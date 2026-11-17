# Análisis de consistencia: Niebla de guerra e «ir a»

Salida de `/speckit-analyze` (Claude Code, 2026-11-17) sobre `spec.md`, `plan.md` y `tasks.md`.

| ID | Categoría | Severidad | Ubicación | Hallazgo | Corrección |
|----|-----------|-----------|-----------|----------|------------|
| B1 | Cobertura | MEDIA | tasks.md | SC-103 (replay de bitácoras con viajes) solo estaba implícito en T115. | T115 ya reproduce la bitácora y compara; se deja explícito en su nombre. Sin cambio de tareas. |
| B2 | Inconsistencia | BAJA | data-model.md | Listaba un campo `explorada_por_turno` que ningún requisito pide. | Eliminado. |
| B3 | Cobertura | MEDIA | tasks.md | FR-105 (la precarga sigue usando el esqueleto completo) no tenía prueba. | T120 incluye que la precarga trae vecinas no exploradas. |
| B4 | Constitución IX | — | plan.md | El cambio de formato de guardado sube la versión y el archivo viejo se rechaza (T107). | Conforme. |
| B5 | Constitución I | — | plan.md | Sin `dict`, `set`, `heapq` ni bibliotecas de grafos. | Conforme. |

**Cobertura**: FR-101 a FR-114, PR-101 y PR-102 tienen tarea. Los 6 casos del Apéndice B (niebla e ir a)
tienen prueba asignada: T110 (no explorada), T112 (puerta recordada), T113 (dormidos), T105 (antorcha),
T106 (pergamino con antorcha), T114 (pergamino durante viaje).
