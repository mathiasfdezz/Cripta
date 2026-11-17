# Quickstart: Validación de Terreno y cazador

Este documento describe cómo validar manualmente la capacidad mediante el modo interactivo y `--bench`.

## Escenarios de Validación

### 1. Costo de Terreno e Intervalo
1. Iniciar una cripta donde la primera salida tenga `costo: 200`.
2. Moverse al Norte (suponiendo esa dirección).
3. **Verificación**: El reloj del juego debe haber avanzado `200 * 100 // velocidad` unidades de tiempo.
4. Comando: `python main.py --offline cripta-01`

### 2. Comportamiento del Cazador (Persecución)
1. Ubicar un cazador a 3 salas de distancia.
2. Pasar el turno (acción `esperar`).
3. **Verificación**: El cazador debe haberse movido hacia la sala del jugador por la ruta de menor costo acumulado.
4. Si hay dos rutas, una más corta en salas pero más cara, verificar que el cazador elige la de más salas pero menor costo.

### 3. Rango del Cazador
1. Alejarse del cazador hasta que el costo mínimo supere su `rango`.
2. Pasar el turno.
3. **Verificación**: El cazador debe permanecer en su sala y su acción registrada en la bitácora debe ser `esperar` (costo 100).

### 4. Desempate por ID
1. Crear un escenario (mediante un test unitario o cripta sintética) donde el cazador tenga dos vecinas que lleven al jugador con el mismo costo mínimo.
2. **Verificación**: El cazador debe moverse a la sala con el ID numérico menor.

### 5. Reescalado por Cambio de Velocidad (FR-013)
1. Hacer que un actor se mueva por una salida de costo 500, de modo que su próxima acción quede programada.
2. Antes de esa acción, aplicar un efecto que duplique la velocidad del actor.
3. **Verificación**: el tiempo restante hasta su próxima acción se reescala como `max(1, (tiempo_siguiente - t) * velocidad_anterior // velocidad_nueva)` y la acción recibe un número de secuencia nuevo (FR-013).

## Pruebas de Rendimiento (--bench)

Ejecutar el benchmark de cazadores:
```bash
python main.py --bench cazadores --num-cazadores 50 --rango 1000
```
- **Éxito**: El tiempo por ciclo de eventos debe ser `< 20ms`.
- **Invalidación**: Probar con `--puertas-inestables` para verificar que el recálculo (cuando la caché falla) sigue dentro del presupuesto.
