Retos y dificultades del proyecto

1. Entender el API y su presupuesto
Al principio no teníamos claro cómo funcionaba el API ni qué significaba cada endpoint. Tuvimos que aprender a manejar el X-Cripta-Client-Id (uno solo por ejecución), los errores HTTP y sobre todo el 429, leyendo reintentar_en y esperando sin que el programa se cayera. También entendimos que los reintentos cuentan dentro del presupuesto de solicitudes, así que cada solicitud tenía que valer la pena. Por eso agrupamos el contenido y el catálogo en lotes de 10 y precargamos las salas con BFS.

2. No poder usar dict como estructura
La regla de no usar dict como índice, caché o tabla de búsqueda nos obligó a implementar nuestras propias estructuras: un vector ordenado con búsqueda binaria para el catálogo, listas doblemente enlazadas para el inventario y el orden de uso de la caché, y un heap mínimo para la agenda. Más de una vez se nos coló un dict o un set (por ejemplo en las direcciones opuestas de las puertas y en el descargador offline), y tuvimos que cambiarlos al revisar el código.

3. Ordenar el proyecto con MVC
El primer cliente de red devolvía los diccionarios del JSON tal cual y hacía print desde el adaptador. Tuvimos que separar responsabilidades: DTOs inmutables para los datos del API, mapeadores para convertir el JSON, un contrato FuenteDatos para el modo en línea y el offline, y un modelo que no sabe nada de HTTP, archivos ni pantalla. Decidimos usar una clase por archivo para no terminar con archivos enormes difíciles de cambiar.

4. Datos del API que no venían como esperábamos
Las salidas de cada sala venían como un objeto JSON sin orden garantizado, así que las fijamos en el orden N, S, E, O para que el juego fuera determinista. Las trampas traen el campo "daño" con ñ, que no sirve como nombre de atributo. Y el enunciado habla de veneno y regeneración, pero el contrato del API no trae esos campos. Se lo preguntamos al profesor y quedó en revisarlo.

5. Ambigüedades del enunciado
No sabíamos si una puerta entre dos salas era una sola o si cada lado era independiente. Primero la implementamos compartida, pero el profesor nos aclaró que cada lado es una puerta distinta, y tuvimos que rehacer Puerta, Esqueleto y sus pruebas. También tuvimos que armar nosotros mismos el paquete para el modo --offline a partir de las respuestas del API, guardando un archivo por sala y por ficha (incluyendo lo que sueltan los enemigos) para no depender de cómo se pidieron los lotes.

6. Integrar el trabajo de todo el equipo
Al unir el motor con el controlador, la caché y la vista aparecieron errores que no se veían por separado: atacar no gastaba el turno, abrir una puerta costaba 100 en vez de 50 y faltaban los comportamientos y el rastro. Tuvimos que corregirlos y actualizar las pruebas sin borrarlas. También aprendimos a revisar siempre cuántas pruebas se ejecutan, porque copiar archivos incompletos o en la versión equivocada hacía que algunas pruebas no corrieran o fallaran.

7. Determinismo, replay y guardado
Para que --replay y la carga de partidas funcionaran, el juego tenía que ser completamente determinista: un solo random.Random(semilla) que pertenece a la partida, una secuencia en la agenda que nunca se repite y el estado del generador incluido en el guardado. La prueba más exigente fue que guardar, cargar y seguir jugando diera exactamente lo mismo que no haber guardado nunca.

8. El retroceso sin copiar el estado
El pergamino de retroceso tenía que deshacer la última acción del jugador y todo lo que pasó hasta su siguiente decisión, guardando solo lo que cambió y no una copia de la partida. Hubo casos difíciles: el propio pergamino no debe deshacerse, la agenda tiene que restaurar eventos cancelados y sacados, y el contador de secuencia no puede retroceder.

9. La caché y las fichas en uso
Al limitar la caché a 25 fichas en memoria nos dimos cuenta de que podía liberar una ficha que se estaba usando (un enemigo vivo, un objeto del inventario o del suelo). Tuvimos que agregar la retención de las fichas en uso y que el controlador se las informe a la caché después de cada comando.

10. Medir en vez de suponer
Al principio elegimos el umbral entre inserción y merge sort "a ojo" (100). Las mediciones mostraron que 50 era el valor correcto, y lo cambiamos. Lo mismo pasó con las estructuras: comparamos el heap contra una lista (el heap fue hasta 141 veces más rápido) y el vector ordenado contra un árbol binario simple, que se degenera cuando los identificadores llegan ordenados.

11. El límite de 20 ms por ciclo
Con cientos de enemigos activos, el ciclo entre dos decisiones del jugador pasaba de 20 ms. Optimizamos el motor: el reloj se anota una sola vez por acción en el historial, el heap mueve un "hueco" en vez de intercambiar en cada nivel, y le pedimos al recolector de basura de Python que deje de revisar lo que vive toda la partida (gc.freeze). Con eso cumplimos siempre hasta unos 400 enemigos activos a la vez (alrededor de 500 eventos por ciclo). Con más, los peores casos se ven afectados también por el sistema operativo, y lo dejamos documentado como límite conocido.

12. El tiempo
Todo esto se hizo en pocas semanas y en paralelo con otras materias, así que tuvimos que priorizar: primero lo que pide la rúbrica, después las mejoras. Lo que no alcanzamos a implementar (como dormir a los enemigos que no tienen nada que hacer, para bajar más el tiempo por ciclo) quedó anotado como mejora futura.