# Research: Línea de tiempo

## Medición previa al plan (2026-11-17)

Copia completa del estado de la cripta de referencia (300 salas, 75 enemigos activos, 760 puertas,
unos 500 eventos en la agenda) con `copy.deepcopy`:

| Variante | ms por copia | memoria |
|----------|--------------|---------|
| genérica | 17,1 | 344 KB |
| memo con lo inmutable compartido + copia propia de `Puerta` y `Evento` | 5,8 | menos |

Con la variante optimizada un punto de control cabe en el ciclo de 20 ms.

## Preguntas de §8

**Con K = 1 la consulta histórica es instantánea y con K infinito no hay copias. ¿Dónde está el punto razonable y cómo lo van a medir?**
El bench juega 5000 acciones deterministas y mide memoria total y tiempo de consulta (promedio y
máximo sobre consultas repartidas en toda la partida) con K = 10, 50, 200 y sin puntos de control.
La consulta cuesta una copia más hasta K acciones re-simuladas; la memoria, n/K copias.

## Decisiones

1. **Qué se anota**: acciones del jugador (nombre y argumento), cada avance del reloj hasta su
   turno, cada llegada de contenido (el DTO, compartido con la partida) y cada movimiento del
   cursor. Es lo mínimo para que la re-simulación pase por los mismos estados.
2. **Pergamino y cursor**: el cursor pasa a registrarse en el historial (spec, supuesto) para que
   lo revertido por el pergamino coincida con lo que se recorta de la línea.
3. **Contenido**: el pergamino no deshace la llegada de contenido; al recortar se conservan esas
   operaciones.
4. **Secuencia de la agenda**: el pergamino no rebobina el contador de secuencia; la re-simulación
   sí empieza desde el del punto de control. Los eventos existentes conservan su secuencia y los
   nuevos siempre reciben números mayores en los dos casos, así que el orden relativo es el mismo.
