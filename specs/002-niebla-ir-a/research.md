# Research: Niebla de guerra y «ir a»

## Preguntas de §8 que responde esta capacidad

**¿Qué información mínima hay que registrar para revertir la exploración de cinco salas con una antorcha encendida?**
Por cada posición que cambió, la lista, la posición y el valor anterior: el estado de cada sala que pasó a explorada o a avistada y el recuerdo de cada salida observada que cambió. Nada más: no se copia el mapa. El historial ya deshace en orden inverso, así que el resultado es exactamente el mapa anterior.

**¿Comparten implementación la ruta de «ir a» y la del cazador?**
Sí la clase, no la instancia ni los datos. Ver plan.md §2.

## Decisiones

1. **Índices densos de 001**: el mapa usa `GrafoCripta`, que ya numera salas y salidas. Así el mapa es una lista de bytes por sala y por salida, y la búsqueda de rutas no traduce ids.
2. **Observación**: las puertas solo cambian por una acción del jugador (abrir) o por su cierre automático. Se observa: al entrar a una sala (sus salidas y las que llegan a ella), al abrir una puerta y cuando un cierre automático ocurre en una salida de la sala del jugador o que llega a ella. Con eso el mapa siempre tiene el estado real de las salidas de la sala actual.
3. **Exploración inicial**: `iniciar()` explora la sala inicial fuera de cualquier intervalo del historial, porque no es una acción del jugador.
4. **Guardado**: el formato pasa a la versión 4 y agrega dos bloques de bytes (estados de sala y recuerdos de salida). Un archivo de versión 3 se rechaza con el mensaje de incompatibilidad ya existente.
5. **Bitácora**: las líneas que empiezan con `#` después de la cabecera son comentarios; el replay las ignora.
