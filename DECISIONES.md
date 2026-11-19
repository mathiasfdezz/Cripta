# Documento de Decisiones de Diseño

Proyecto CRIPTA, Estructuras de Datos II, 2026.

Este documento explica, problema por problema (sección 4 del enunciado), qué estructura usamos, qué otras opciones pensamos y por qué las descartamos. Los números salen de nuestras propias mediciones. Para repetirlas:

```
python main.py --bench
```

Todas las mediciones se tomaron en un Intel Core i5-10400 (2.90 GHz), Windows 11 y Python 3.14. Las frecuencias "reales" vienen de una partida completa de cripta-01 en modo offline: 27 comandos, 21 acciones que gastan tiempo, 3 enemigos derrotados y un reloj que terminó en t=1675.

Una nota sobre el formato: cada sección sigue los seis puntos de la sección 8 (problema, alternativas, decisión, complejidad, evidencia y límites).

---

## 4.1 Qué ocurre a continuación (agenda de eventos)

### Problema

El juego no avanza por rondas. Cada actor y cada efecto tiene un evento con su `tiempo_siguiente`, y en cada paso hay que sacar el de menor tiempo (si empatan, el de menor secuencia). Sobre esa misma agenda pasan cosas que la complican: un enemigo que muere deja eventos futuros que no deben ejecutarse, el antídoto cancela el veneno antes del siguiente pulso, una poción de velocidad cambia el tiempo de una acción que ya estaba programada.

Lo que realmente hace nuestro programa en cada evento es: mirar el mínimo, sacarlo y casi siempre volver a programar al mismo actor más adelante. En cripta-01 eso pasa pocas veces (1,4 eventos programados por comando en promedio, 6 como máximo), pero en las criptas sintéticas del bench, con 100 enemigos activos, son 121 eventos por ciclo, y con 900 enemigos llegan a 1086.

### Alternativas consideradas

1. **Lista sin orden.** Programar es agregar al final, O(1). El problema es sacar el siguiente: hay que recorrer toda la lista para encontrar el mínimo. El enunciado prohíbe exactamente eso ("no puede requerir examinar todos los eventos").
2. **Lista ordenada.** Sacar el mínimo es tomar el primero, pero programar obliga a buscar la posición y desplazar elementos, O(n). Como casi cada evento que sale vuelve a entrar, el costo de insertar se paga en cada paso.
3. **Cancelar buscando el evento en la estructura.** Para la muerte de un actor o el antídoto, buscar el evento y sacarlo. En un heap eso es O(n) para encontrarlo.

### Decisión

Un **heap mínimo** propio (`estructuras/min_heap.py`) guardado en una lista, con entradas `(tiempo, secuencia, evento)`. La secuencia la asigna `AgendaEventos`, no el heap, y nunca se repite, así que dos entradas jamás empatan en las dos primeras posiciones y el orden es siempre determinista.

Para cancelar usamos **cancelación perezosa**: el evento se marca como cancelado y se queda en el heap. Cuando llega a la raíz, `_descartar_cancelados` lo saca y sigue con el siguiente. Reprogramar (por ejemplo, por un cambio de velocidad) es cancelar la versión vieja y meter una nueva con secuencia nueva, usando la fórmula de la sección 2.3.

Los efectos también son eventos de esta misma agenda: apagar la antorcha, rearmar una trampa, cerrar una puerta, cada pulso de veneno y cada pulso de regeneración. Cada actor guarda una referencia a su próximo evento, y por eso cancelar nunca necesita buscar.

### Análisis de complejidad

| Operación | Costo | Cuándo pasa |
|---|---|---|
| Programar | O(log n) | En casi todos los eventos (el actor se vuelve a programar) |
| Ver el siguiente | O(1) más los cancelados que haya en la raíz | Una vez por evento |
| Sacar el siguiente | O(log n) | Una vez por evento |
| Cancelar | O(1) | Muertes, antídoto, antorcha nueva, cambios de velocidad |

Cada evento cancelado se saca una sola vez cuando llega a la raíz, así que su costo total se reparte entre las operaciones normales.

### Evidencia empírica

Medimos directamente la alternativa descartada (`bench/agenda_lista.py`): sacar el siguiente y volver a programarlo, en microsegundos por operación.

| Eventos | Heap | Lista sin orden | Lista / heap |
|---|---|---|---|
| 100 | 2,86 | 18,72 | 6,6 veces |
| 300 | 3,09 | 54,66 | 17,7 veces |
| 1000 | 3,25 | 211,73 | 65,1 veces |
| 3000 | 3,68 | 556,98 | 151,4 veces |

El heap casi no cambia al crecer la agenda (de 2,86 a 3,68 µs con 30 veces más eventos). La lista crece de forma lineal. Con los cientos de eventos simultáneos de los que habla el enunciado, la diferencia ya es de más de 60 veces.

Durante el proyecto también mejoramos el heap: `_subir` y `_bajar` mueven un "hueco" y escriben el elemento una sola vez al final, en lugar de intercambiar en cada nivel. Con 3000 eventos bajó de unos 5,1 µs a unos 3,7 µs por operación.

### Límites conocidos

Los eventos cancelados ocupan espacio hasta que llegan a la raíz. Si una partida cancelara muchísimos eventos programados muy lejos en el futuro, el heap crecería con basura. Llevamos la cuenta (`_cancelados_en_heap`) para que `tamano()` sea correcto, pero no reconstruimos el heap. En las partidas que probamos esto no pasa, porque cada actor tiene a lo sumo un evento vivo y los cancelados quedan cerca en el tiempo.

---

## 4.2 Traer el contenido antes de que haga falta (precarga)

### Problema

El jugador no puede entrar a una sala cuyo contenido todavía no conocemos, y pedir el contenido al llegar a cada puerta costaría unos 400 ms por puerta. El servicio de contenido acepta hasta 10 salas por solicitud y cuesta lo mismo pedir 1 que 10, así que lo razonable es pedir por adelantado y por lotes.

En la partida medida de cripta-01, **una sola solicitud de contenido** trajo las 6 salas de la cripta, y el jugador nunca tuvo que esperar al cruzar una puerta.

### Alternativas consideradas

1. **Pedir cada sala al entrar.** Es lo más simple, pero son 6 solicitudes en cripta-01 (una por sala) y una espera de red en cada puerta. Con un presupuesto de 9 solicitudes no alcanza.
2. **Descargar todo el contenido al empezar.** Cumple en criptas pequeñas, pero en una cripta grande gasta presupuesto en salas que el jugador quizás nunca visite, y el presupuesto puede no alcanzar para `salas / 10` solicitudes seguidas.

### Decisión

Un **BFS** desde la sala del jugador (`modelo/precarga.py`) usando nuestra `Fila`, que elige las salas más cercanas que todavía no se pidieron, hasta 10. Primero recorre solo por salidas abiertas. Si no llega a 10, completa atravesando también puertas cerradas, porque el jugador puede abrirlas con una llave. Las salas ya pedidas se guardan en un `VectorOrdenado` y nunca se vuelven a pedir.

Para garantizar que el jugador nunca quede en una sala sin contenido, `ControladorPartida._mover` revisa el destino antes de confirmar el movimiento. Si falta, lo pide en ese momento. Esa espera es de red y no toca el reloj virtual, porque `tiempo` solo cambia cuando la agenda saca un evento.

El cliente es sincrónico: cuando el jugador pide moverse, nunca hay una respuesta a medias. Los contenidos se incorporan en el orden del lote, que es el orden del BFS (cercanía y, a igual distancia, N, S, E, O), así que el resultado es determinista.

### Análisis de complejidad

El BFS visita cada sala y cada salida a lo sumo una vez: O(salas + salidas) en el peor caso, aunque normalmente se detiene en cuanto junta 10 salas. Preguntar si una sala ya se pidió es una búsqueda binaria, O(log n). La precarga solo se dispara cuando alguna vecina de la sala actual todavía no se pidió, no después de cada comando.

### Evidencia empírica

| Estrategia | Solicitudes de contenido en cripta-01 |
|---|---|
| Una sala por solicitud, al entrar | 6 |
| BFS con lotes de 10 (la nuestra) | 1 |

La partida completa de cripta-01 usó 6 de las 9 solicitudes del presupuesto: datos de la cripta, versión del catálogo, una página de salas, un lote de contenido y dos lotes de catálogo. Con las fichas, el esqueleto y el contenido ya guardados en disco (sección 4.4), la segunda partida usó **2**: los datos de la cripta y la versión del catálogo.

También jugamos contra el API las otras criptas publicadas:

| Cripta | Salas | Presupuesto | Solicitudes al arrancar | Solicitudes en una partida |
|---|---|---|---|---|
| cripta-01 | 6 | 9 | 6 | 6 |
| cripta-02 | 20 | 23 | 5 | 7 |
| cripta-03 | 40 | 42 | 5 | 7 |
| cripta-04 | 50 | 52 | 5 | 7 |

### Límites conocidos

Si todas las salas cercanas ya se pidieron, el BFS puede recorrer buena parte del mapa antes de encontrar 10 nuevas. Y una decisión nuestra que tiene su costo: no hicimos solicitudes en segundo plano: la primera vez que se entra a una zona nueva sin precargar todavía hay una espera de red. En la práctica esto pasa muy poco, porque la precarga corre después de cada acción y se adelanta al jugador.

Al arrancar se resuelven las fichas de todo el primer lote, no solo las de la sala inicial. En una cripta sintética de 150 salas y 28 tipos eso son 10 solicitudes antes de la primera acción, cuando el mínimo posible sería 7. Lo dejamos así a propósito: esas fichas se iban a pedir igual unas salas después, así que no cambia el total de la partida, y en las cuatro criptas publicadas el arranque ya usa el mínimo (5) salvo cripta-01 (6). Solo importaría con una cripta muy grande y un presupuesto casi igual al número de páginas.

---

## 4.3 Resolución de referencias del catálogo

### Problema

Cada enemigo, objeto y trampa trae un id de tipo (`ent_rata_gigante`, `itm_antorcha`) que hay que convertir en su ficha antes de usarlo. Los ids llegan en un orden que no controlamos, se repiten entre salas y no se deben pedir dos veces.

Esta búsqueda es de lo que más se repite: cada vez que llega contenido, cada vez que se recoge o se suelta algo, y después de cada comando, cuando el controlador le dice a la caché qué fichas están en uso. En la partida medida la caché recibió 22 consultas de fichas (11 aciertos y 11 fallos).

### Alternativas consideradas

1. **Pedir cada id por separado.** En cripta-01 aparecen 11 ids distintos. Eso serían 11 solicitudes, más que todo el presupuesto (9).
2. **Árbol binario de búsqueda simple** para encontrar la ficha por id. Es el que vimos en clase y en promedio busca en O(log n). Lo descartamos por lo que mostró la medición (abajo): sin balancear, si los ids llegan ordenados se convierte en una lista.
3. **Tabla hash propia.** No la vimos en el curso y `dict` está prohibido. El vector ordenado ya busca en alrededor de 1,5 µs con 2000 fichas, así que no nos pareció que valiera la pena el riesgo.

### Decisión

`CacheCatalogo.resolver(ids)` primero quita los repetidos, después busca cada id en memoria, luego en disco, y lo que falta lo pide a la red en **lotes de hasta 10**. La búsqueda por id usa un **vector ordenado con búsqueda binaria** (`estructuras/vector_ordenado.py`).

Preferimos búsquedas rápidas aunque insertar cueste más: se busca muchísimas veces más de lo que se inserta, y en memoria nunca hay más de unas 25 fichas.

### Análisis de complejidad

| Operación | Vector ordenado | Árbol simple |
|---|---|---|
| Buscar | O(log n) siempre | O(log n) promedio, O(n) si los ids llegan ordenados |
| Insertar | O(n) por el desplazamiento | O(log n) promedio, O(n) peor caso |

Con el tope de 25 fichas, el desplazamiento al insertar mueve como mucho 25 referencias.

### Evidencia empírica

Medimos directamente la alternativa descartada (`bench/arbol_binario.py`), en microsegundos por búsqueda:

| Fichas | Llegada | Vector | Árbol | Altura del árbol |
|---|---|---|---|---|
| 25 | al azar | 0,75 | 0,42 | 8 |
| 25 | ordenada | 0,73 | 0,90 | 25 |
| 250 | al azar | 1,30 | 0,72 | 17 |
| 250 | ordenada | 1,05 | 7,69 | 250 |
| 2000 | al azar | 1,53 | 1,02 | 26 |
| 2000 | ordenada | 1,54 | 60,54 | 2000 |

Siendo honestos con los números: cuando los ids llegan al azar, el árbol es un poco más rápido. Pero los ids del catálogo tienen formato (`itm_...`, `ent_...`) y suelen llegar agrupados y en orden. Ahí el árbol llega a altura 2000 y es 39 veces más lento. El vector da casi el mismo tiempo en los dos casos, y preferimos algo predecible.

Sobre el presupuesto: los 11 ids de cripta-01 se resolvieron con **2 solicitudes** (un lote de 10 y otro de 1) en lugar de 11.

### Límites conocidos

Si el tope de la caché fuera de miles de fichas y entraran muchas fichas nuevas seguidas, el costo O(n) de insertar empezaría a notarse. Para ese caso habría que pensar en un árbol balanceado, que no implementamos.

---

## 4.4 Reutilización y caché persistente

### Problema

En memoria caben como mucho `--cache-size` fichas (25 por defecto). Al pasar el tope hay que liberar alguna, y la que se libere no puede estar en uso: un enemigo vivo, un objeto en el inventario o en el suelo de la sala actual, una trampa de la sala actual. Una ficha liberada se queda en disco, así que volver a necesitarla cuesta una lectura de disco y no una solicitud de red. Todo esto tiene que sobrevivir al cierre del programa y validarse con la versión del catálogo.

### Alternativas consideradas

1. **FIFO** (liberar la que entró primero). Es fácil, pero libera fichas que se siguen usando mucho, por ejemplo la del tipo de enemigo más común de la cripta, solo porque llegó temprano.
2. **No tener tope y guardar todo en memoria.** Va contra el requisito de `--cache-size`.
3. **Liberar una ficha al azar.** Usar el azar del juego aquí afectaría el determinismo, y una caché es infraestructura, no estado de la partida.

### Decisión

**LRU** (se libera la usada hace más tiempo), implementado con una **lista doblemente enlazada**: la cabeza es la usada más recientemente y la cola la más antigua. Cada consulta mueve el nodo al frente en O(1). El vector ordenado de la sección 4.3 guarda, para cada id, el nodo de la lista, así que no hay que recorrerla para encontrarlo.

Para las fichas en uso, cada entrada lleva un **contador de referencias**. Después de cada comando, el controlador (`UsoDeFichas`) le dice a la caché qué fichas están en uso, y al desalojar se salta toda ficha con referencias mayores que cero. Si todas las fichas están en uso, la caché pasa el tope por un rato y se vuelve a ajustar cuando se liberan.

En disco, `AlmacenCatalogoDisco` guarda un archivo por ficha y la versión del catálogo. Al empezar se compara esa versión con la del servidor (una sola solicitud). Si cambió, se borra lo persistido. Si coincide, todo lo de disco sigue valiendo.

El esqueleto y el contenido de cada cripta también se guardan (`ClienteRedConCopia`, en `cache_criptas/`), con la misma organización de archivos que el paquete `--offline`: una página por archivo y un archivo por sala. Se validan con la versión de la cripta, que viene en los datos generales que igual hay que pedir al empezar, así que validar no cuesta una solicitud extra. Si la versión cambió, se borra la copia de esa cripta. Si un archivo está dañado, cuenta como si no estuviera y se vuelve a pedir. Cuando un lote mezcla salas guardadas y nuevas, solo se piden las nuevas.

Elegimos LRU porque el jugador avanza de sala en sala: las fichas de las salas que deja atrás dejan de usarse, y esas son justo las que conviene liberar.

### Análisis de complejidad

| Operación | Costo |
|---|---|
| ¿Está en memoria? | O(log n), búsqueda binaria |
| Marcar como usada | O(1), mover el nodo al frente |
| Liberar | O(1) normalmente; O(k) si las k más antiguas están en uso |
| Recuperar una ficha liberada | una lectura de disco |

### Evidencia empírica

| Medición | Resultado |
|---|---|
| Consulta con acierto (en memoria) | 2,78 µs |
| Consulta con fallo (desaloja y pide) | 11,88 µs |
| Recuperar una ficha liberada desde disco | entre 1 840 y 7 550 µs según la corrida |
| Solicitudes de red al recuperar 100 fichas liberadas | 0 |
| Una solicitud de red (enunciado, sección 3.4) | unos 400 000 µs |

Leer de disco salió más lento de lo que esperábamos (de 1,8 a 7,5 ms), porque cada ficha es un archivo y el sistema operativo y el antivirus revisan cada apertura. Aun así es entre 50 y 200 veces más barato que una solicitud de red y no gasta presupuesto.

| Partida de cripta-02 contra el API | Solicitudes |
|---|---|
| Primera (todo en frío) | 5 |
| Segunda, con fichas, esqueleto y contenido en disco | **2** |
| `--replay` de esa partida | 2 |

### Límites conocidos

- Si hay más fichas en uso que el tope (muchos tipos de enemigos activos a la vez), la caché pasa el tope temporalmente. Lo preferimos a romper la regla de no liberar fichas en uso.
- El tiempo de recuperación depende del disco.
- Un archivo por ficha y por sala es simple y permite armar cualquier lote, pero con miles de salas serían miles de archivos pequeños. Para eso convendría un archivo único con índice, como el del guardado (sección 4.10).

---

## 4.5 Inventario

### Problema

El inventario se recorre hacia adelante y hacia atrás desde el objeto que se está viendo (`sig`, `ant`). Hay que poder soltar ese objeto esté donde esté sin que el costo dependa de la posición, equipar un objeto lo pasa al frente, y la vista ordenada por peso, valor o nombre no puede cambiar el orden real. El tamaño máximo es `inventario_max`, que viene del API.

### Alternativas consideradas

1. **Vector de tamaño `inventario_max`.** Recorrer es fácil, pero soltar del medio obliga a desplazar los elementos siguientes (O(n)), y equipar (pasar al frente) también desplaza. El enunciado pide justo lo contrario.
2. **Lista simplemente enlazada.** Soltar el objeto actual necesita su anterior, y para encontrarlo hay que recorrer desde el inicio. Retroceder (`ant`) tendría el mismo problema.

### Decisión

Una **lista doblemente enlazada** propia (`estructuras/lista_doble.py`) con un cursor (`actual`) que apunta al nodo que se está viendo. Avanzar y retroceder siguen los enlaces. Soltar desenlaza el nodo actual usando sus dos vecinos. Equipar mueve el nodo al frente. La vista ordenada copia los nodos a una lista auxiliar y la ordena con nuestros ordenamientos (sección 4.9), sin tocar la lista real. Con el inventario lleno, `recoger` se rechaza sin gastar tiempo.

### Análisis de complejidad

| Operación | Costo |
|---|---|
| Avanzar / retroceder | O(1) |
| Soltar el actual | O(1) |
| Equipar (al frente) | O(1) |
| Recoger | O(1) |
| Vista ordenada | O(n log n) o O(n²) según el algoritmo que elija la sección 4.9, sobre una copia |

### Evidencia empírica

Soltar según la posición, en microsegundos:

| Tamaño | Frente | Medio | Fondo |
|---|---|---|---|
| 10 | 0,53 | 0,54 | 0,50 |
| 1000 | 2,21 | 2,06 | 1,93 |

Con 10 objetos el tiempo es prácticamente el mismo en las tres posiciones. Con 1000 sube un poco en total (es la medición completa, incluida la preparación), pero sigue sin depender de la posición: el fondo incluso sale un poco más barato que el frente.

### Límites conocidos

Cada nodo usa más memoria que una casilla de un vector, por los dos enlaces. Con `inventario_max` de unas decenas de objetos no importa.

---

## 4.6 Pergaminos de retroceso e historial reversible

### Problema

Un pergamino devuelve la partida a como estaba antes de la última acción del jugador, incluido todo lo que pasó hasta su siguiente decisión: ataques de enemigos, efectos, reloj, eventos programados o cancelados, rastro, vida, inventario, puertas y trampas. No se puede copiar el estado completo, el historial guarda como mucho 5 acciones, y los pergaminos mismos no entran en el retroceso.

En cripta-01 una acción cambia en promedio 13 cosas (25 como máximo). Con 100 enemigos activos son unas 265, y con 400, unas 964.

### Alternativas consideradas

1. **Copiar el estado antes de cada acción.** Está prohibido, y con 100 enemigos sería copiar cientos de objetos en cada turno, aunque solo cambien unos pocos.
2. **Volver a jugar desde el inicio** con la semilla y todos los comandos menos el último. No guarda nada extra, pero deshacer costaría cada vez más a medida que la partida avanza.

### Decisión

Un `Historial` (`modelo/historial.py`) que es una **lista doblemente enlazada de pilas**. Cada acción del jugador abre un intervalo nuevo (una `Pila`). Cada cambio se apila de una de dos formas:

- `(objeto, atributo, valor_anterior)`, que es lo más común y lo más barato;
- una función que sabe deshacer el cambio, para lo que no es un atributo simple (sacar un objeto del suelo, enlazar un nodo del inventario, un cambio en la agenda).

Deshacer desapila en orden inverso, así que lo último que cambió es lo primero que se revierte. Al pasar de 5 intervalos se descarta el más viejo (la cabeza de la lista) en O(1).

Hay algunos detalles que importan:

- Se guarda el estado del `random.Random` de la partida al empezar cada acción, y repetir la acción después de deshacer da exactamente el mismo resultado.
- La agenda avisa al historial de cada cosa que hace (programar, cancelar, sacar), y deshacer la deja como estaba.
- El contador de secuencia **no** se rebobina: los eventos restaurados conservan su número y los nuevos siguen recibiendo números mayores. Así nunca se repiten.
- El reloj cambia en cada evento, pero para deshacer solo importa cuánto valía al empezar el intervalo. Lo anotamos **una sola vez por intervalo**. Antes de este cambio, con 100 enemigos se guardaban 332 cambios por acción. Ahora son 265.
- Recoger, soltar o usar un pergamino se hace con el historial apagado (`sin_registrar`), y su cantidad nunca se revierte.

### Análisis de complejidad

Anotar un cambio es O(1). Deshacer es O(k), donde k es la cantidad de cambios del intervalo, no el tamaño del estado. La memoria está acotada por 5 intervalos.

### Evidencia empírica

| Escenario | Acción (µs) | Deshacer (µs) | Cambios guardados |
|---|---|---|---|
| cripta-01 (partida real) | n/a | n/a | 13 de promedio, 25 máximo |
| 100 salas, 100 enemigos | 703,5 | 225,1 | 265,5 |
| 400 salas, 400 enemigos | 3222,1 | 838,7 | 964,5 |

Deshacer siempre cuesta bastante menos que la acción que revierte, y crece con los cambios del intervalo, no con el tamaño de la cripta.

### Límites conocidos

Lo que se guarda por intervalo crece de forma lineal con la cantidad de enemigos que actúan entre dos decisiones. Con miles de enemigos activos, cada intervalo ocuparía bastante memoria, aunque nunca más de 5 intervalos.

---

## 4.7 El rastro del jugador

### Problema

El rastreador sigue el rastro más fresco de las salas vecinas por las que puede pasar. Su decisión tiene que costar según la cantidad de salidas de su sala, no según el tamaño de la cripta ni lo largo del recorrido del jugador. Un rastro de 400 o más unidades ya no sirve, y a igual frescura gana la sala de menor id.

### Alternativas consideradas

1. **Buscar un camino hacia el jugador** (BFS por todo el mapa) en cada decisión. Cuesta según el tamaño de la cripta, que es lo que el enunciado prohíbe.
2. **Borrar los rastros viejos de forma activa** con un evento cada vez que un rastro cumple 400. Eso mete eventos extra en la agenda por cada sala que el jugador pisa, y el heap trabajaría más en cada ciclo sin necesidad.

### Decisión

`Rastro` (`modelo/rastro.py`) guarda, en un `VectorOrdenado`, un registro por sala con la última vez que el jugador estuvo ahí. La primera vez que se consulta una sala se **enlazan sus vecinas**: cada registro guarda su lista de `(dirección, puerta, registro_vecino)`. Desde ahí, decidir es una búsqueda binaria para encontrar el registro de la sala y un recorrido por esa lista.

La caducidad **se detecta al consultar**: si `ahora - tiempo >= 400`, ese vecino no cuenta. No se borra nada. Comparar cuesta una resta, mientras que borrar activamente costaría eventos.

El rastro se refresca en cada acción del jugador (no solo al moverse), y cada refresco pasa por el historial para que el pergamino lo revierta.

### Análisis de complejidad

Decidir cuesta O(log n + salidas): la búsqueda binaria del registro de la sala y luego solo sus salidas (a lo sumo 4). No depende del recorrido del jugador. Enlazar la vecindad la primera vez puede costar O(salidas · n), porque los registros nuevos se insertan en el vector ordenado y eso desplaza elementos, pero pasa una sola vez por sala en toda la partida. Con k rastreadores que actúan, el trabajo por ciclo es O(k · (log n + salidas)), lineal en los enemigos que realmente actúan.

### Evidencia empírica

Medimos directamente la alternativa descartada (`bench/bench_rastro.py` y `bench/rastreo_por_bfs.py`): el jugador camina al azar 300 pasos por una cuadrícula y después se mide la decisión de un rastreador desde salas al azar. En microsegundos por decisión:

| Salas | Primera vez en la sala | Sala ya vista | BFS por la cripta | BFS / sala ya vista |
|---|---|---|---|---|
| 100 | 15,62 | 1,29 | 1 328,65 | 1 027 veces |
| 900 | 43,83 | 1,81 | 38 396,88 | 21 223 veces |
| 2 500 | 110,75 | 2,33 | 231 028,93 | 99 156 veces |

Con 25 veces más salas, la decisión normal pasa de 1,3 a 2,3 µs (es la búsqueda binaria, O(log n)), mientras que el BFS crece con el mapa entero. La columna "primera vez" sí crece, porque incluye enlazar la vecindad; eso pasa una vez por sala en toda la partida.

El bench del ciclo (sección 5.2) también lo mide dentro del motor, donde un tercio de los enemigos sintéticos son rastreadores. El costo por evento casi no cambia al multiplicar los enemigos por 9:

| Enemigos | Eventos por ciclo | µs por evento |
|---|---|---|
| 100 | 121 | 9,2 |
| 400 | 483 | 10,8 |
| 900 | 1086 | 12,2 |

Si la decisión del rastreador dependiera del tamaño de la cripta, el costo por evento crecería junto con el mapa (de 100 a 900 salas). Sube un poco, pero mucho menos que el mapa.

### Límites conocidos

Los rastros viejos nunca se borran, así que la memoria del rastro crece con las salas que el jugador visitó (un registro por sala). Como mucho es una entrada por sala de la cripta.

---

## 4.8 Bitácora en pantalla

### Problema

La interfaz muestra solo los últimos 20 mensajes. La memoria tiene que quedarse constante durante toda la partida, y agregar un mensaje no puede desplazar los 19 anteriores.

### Alternativas consideradas

1. **Lista que crece** y mostrar solo los últimos 20. Cumple lo visual, pero la memoria crece toda la partida.
2. **Lista con `append` y `pop(0)` al pasar de 20.** La memoria queda fija, pero `pop(0)` desplaza los 19 mensajes restantes cada vez, que es justo lo que prohíbe el enunciado.

### Decisión

Una **fila circular** propia (`estructuras/fila.py`) de capacidad 20 con sobrescritura. Cuando está llena, el mensaje nuevo se escribe encima del más viejo y el índice de inicio avanza una posición (módulo 20). Nada se mueve.

### Análisis de complejidad

Agregar es O(1) y la memoria es siempre de 20 casillas. Mostrar los mensajes es O(20), del más viejo al más nuevo.

### Evidencia empírica

Medimos las dos alternativas descartadas (`bench/bench_bitacora.py`) agregando 100 000 mensajes:

| Estructura | µs por mensaje | Memoria al final | ¿Desplaza mensajes? |
|---|---|---|---|
| Fila circular (la nuestra) | 0,35 | 216 bytes | no |
| Lista con `pop(0)` | 0,23 | 248 bytes | sí, 19 por mensaje |
| Lista que crece | 0,09 | 800 984 bytes | no |

En tiempo, nuestra fila es la más lenta de las tres: está escrita en Python y las listas usan código en C. Pero la diferencia es de una décima de microsegundo por mensaje, y en una partida entran unos pocos mensajes por comando. Lo que el enunciado pide es memoria constante y sin desplazar, y la fila circular es la única de las tres que cumple las dos cosas. La lista que crece ya ocupa casi 800 KB después de 100 000 mensajes, y la lista con `pop(0)` mueve los 19 anteriores cada vez.

La prueba `test_fila_sobrescribe_mas_antiguo` (en `tests/test_estructuras.py`) revisa que al pasar de la capacidad se pierda el más viejo y que el orden siga siendo el correcto.

### Límites conocidos

Si se quisiera ver un historial largo de mensajes, esta estructura no sirve, porque lo viejo se pierde. Para eso está la bitácora de partida de la sección 4.11, que sí guarda todo en disco.

---

## 4.9 Ordenamiento

### Problema

Ordenamos en varios lugares: la vista del inventario (pocos elementos, a lo sumo `inventario_max`), la tabla de puntajes, el índice del archivo de guardado (las salas casi siempre llegan ya ordenadas por id) y la lista de fichas en uso. No se permite `sort()` ni `sorted()`, hay que implementar al menos dos algoritmos y el programa tiene que elegir solo, según los datos.

### Alternativas consideradas

1. **Un solo algoritmo, merge sort, para todo.** Siempre es O(n log n), pero en listas pequeñas o casi ordenadas pierde contra inserción por el trabajo extra de partir y mezclar.
2. **Un solo algoritmo, inserción, para todo.** Es muy bueno en listas cortas y casi ordenadas, pero cuadrático en datos al azar: con 1000 elementos tarda 28 ms contra 2,5 ms de merge.

### Decisión

Implementamos **inserción** y **merge sort** (los dos estables) en `estructuras/ordenamientos.py`, y `elegir_algoritmo` decide así:

1. Si hay 50 elementos o menos, inserción.
2. Si no, se mide el desorden: la proporción de pares vecinos que están al revés (una pasada, O(n)). Si es 5 % o menos, inserción.
3. En cualquier otro caso, merge sort.

El umbral de tamaño al principio lo pusimos en 100 "a ojo". La medición de abajo mostró que entre 50 y 75 elementos merge ya gana con datos al azar, y lo bajamos a 50.

### Análisis de complejidad

| Algoritmo | Mejor caso | Peor caso | Memoria extra |
|---|---|---|---|
| Inserción | O(n), datos ordenados | O(n²) | O(1) aparte de la copia |
| Merge sort | O(n log n) | O(n log n) | O(n) |
| Medir el desorden | O(n) | O(n) | O(1) |

### Evidencia empírica

Alrededor del umbral, en microsegundos por ordenamiento:

| Datos | n | Inserción | Merge | Gana | Elegimos |
|---|---|---|---|---|---|
| aleatorio | 50 | 65,66 | 80,15 | inserción | inserción |
| aleatorio | 75 | 277,35 | 129,30 | merge | merge |
| aleatorio | 150 | 709,81 | 493,53 | merge | merge |
| casi ordenado (2 %) | 75 | 13,84 | 106,04 | inserción | inserción |
| casi ordenado (2 %) | 150 | 34,63 | 230,54 | inserción | inserción |

Con comparaciones costosas (clave lenta, n = 200), en milisegundos:

| Datos | Inserción | Merge |
|---|---|---|
| aleatorio | 15,589 | 3,830 |
| casi ordenado (2 %) | 0,969 | 2,569 |
| ordenado | 0,561 | 2,296 |

Y cuántas veces se llama a la clave con n = 1000 (sirve para estimar el costo cuando comparar es caro):

| Datos | Inserción | Merge |
|---|---|---|
| aleatorio | 253 101 | 17 440 |
| ordenado | 1 998 | 9 864 |
| casi ordenado (2 %) | 13 202 | 13 670 |

La regla acierta en los casos que más nos importan: los datos casi ordenados (como el índice del guardado) van a inserción, que ahí es varias veces más rápida, y los datos grandes y desordenados van a merge.

### Límites conocidos

La regla se equivoca con datos **al revés** de 50 elementos o menos: ahí merge gana (121,54 µs contra 66,88 µs con 50 elementos) y nosotros elegimos inserción, porque por debajo de 50 no medimos el desorden. Son unos 55 µs de diferencia y en el juego no aparecen listas invertidas, así que lo dejamos así. Con 1000 elementos y 10 % de desorden merge gana claramente (6,6 ms contra 2,3 ms), y como 10 % pasa del umbral, la regla elige bien merge.

---

## 4.10 Guardado binario de la partida

### Problema

La partida se guarda en un archivo binario de formato propio. Al cargar debe poder leerse una sala específica sin leer todo el archivo, el programa tiene que detectar un archivo de otra versión del formato, y hay que compararlo con guardar lo mismo en JSON.

### Alternativas consideradas

1. **JSON.** Es fácil de leer y depurar, pero ocupa más y, para sacar una sola sala, hay que parsear el archivo entero.
2. **Índice de salas sin ordenar.** Encontrar una sala obligaría a recorrer todo el índice, O(n).
3. **pickle.** No es un formato propio (lo pide el enunciado) y cargar un pickle de origen desconocido puede ejecutar código.

### Decisión

Un formato propio con `struct` (`adaptadores/guardado_binario.py`):

1. Un prefijo fijo con la marca `CRPT`, la **versión del formato** (hoy 3), la semilla, el reloj, la cantidad de salas y dónde empiezan el jugador y el índice.
2. Los ids y versiones de la cripta y del catálogo.
3. El registro del jugador (vida, inventario, agenda pendiente, estado del azar, veneno), con CRC32.
4. Un registro por sala, cada uno con su CRC32.
5. Al final, un **índice ordenado por id de sala** con `(id, posición, largo)`.

Para leer una sala se hace búsqueda binaria **sobre el índice en disco**: cada paso lee una sola entrada con `seek`, y al final se lee solo el registro de esa sala. Si la versión del formato no coincide, se lanza `GuardadoIncompatible` con un mensaje claro y el juego no se cae. También se valida que el guardado sea de la misma cripta y del mismo catálogo.

El índice se ordena con nuestro `ordenar`. Las salas casi siempre llegan ya en orden, y ahí la regla de la sección 4.9 usa inserción en tiempo casi lineal.

### Análisis de complejidad

| Operación | Binario | JSON |
|---|---|---|
| Leer una sala | O(log n) lecturas del índice y una de la sala | O(tamaño del archivo) |
| Cargar todo | O(tamaño) | O(tamaño) |

### Evidencia empírica

| Salas | Binario (B) | JSON (B) | Carga completa bin (ms) | Carga completa JSON (ms) | 1 sala bin (ms) | 1 sala JSON (ms) |
|---|---|---|---|---|---|---|
| 20 | 2 823 | 4 683 | 0,20 | 0,15 | 0,09 | 0,15 |
| 200 | 26 914 | 44 815 | 0,97 | 0,55 | 0,09 | 0,56 |
| 2 000 | 273 067 | 453 472 | 9,75 | 5,80 | 0,10 | 5,69 |
| 20 000 | 2 811 835 | 4 642 818 | 114,24 | 87,77 | 0,11 | 88,32 |

Lo que muestran los números:

- El binario ocupa **un 40 % menos** en todos los tamaños.
- Leer una sala cuesta **lo mismo (0,1 ms)** con 20 salas que con 20 000. En JSON crece con el archivo: con 20 000 salas tarda 87 ms, unas 790 veces más.
- La carga completa la **gana JSON**: con 20 000 salas, 88 ms contra 114 ms. El módulo `json` de Python está escrito en C, y nuestro desempaquetado es Python puro. Al principio la diferencia era casi del doble (147 ms). Medimos dónde se iba el tiempo y era el desempaquetado de cada sala, con unas 15 llamadas a funciones auxiliares por sala. Lo reescribimos leyendo byte a byte con los formatos de `struct` ya compilados, sin cambiar el formato del archivo, y bajó un 22 %. Igualar a JSON exigiría cambiar el formato, y no vale la pena: lo que pide el enunciado es poder leer una sala sin leer todo, y ahí el binario gana por mucho.

### Límites conocidos

- La carga completa sigue siendo más lenta que JSON (unas 1,3 veces con 20 000 salas).
- Cada cambio de formato invalida los guardados viejos. Nos pasó al agregar el veneno (de la versión 2 a la 3): los archivos v2 ya no cargan y el juego lo avisa.

---

## 4.11 Bitácora de partida y reproducción

### Problema

Cada acción del jugador va a un archivo de texto de solo anexado, con un encabezado que tiene, como mínimo, el id de la cripta, la versión de la cripta, la del catálogo y la semilla. `--replay` reproduce la partida completa sin interacción, y si las versiones ya no coinciden tiene que avisar en lugar de reproducir contra datos distintos.

### Alternativas consideradas

1. **Guardar el estado completo después de cada acción.** Haría la reproducción trivial, pero el archivo crecería muchísimo y no sería un registro de acciones.
2. **Guardar solo la semilla.** No alcanza: sin los comandos no hay forma de saber qué hizo el jugador.

### Decisión

`BitacoraPartida` escribe el encabezado y después un comando por línea, con `append`. Solo se anotan los comandos que **se ejecutaron y cambian algo**: un comando rechazado no se anota, y tampoco `guardar`, `cargar`, `inv` ni `ayuda` (el replay no debe tocar archivos). `sig` y `ant` sí se anotan, porque mueven el cursor del inventario y cambian sobre qué objeto actúan `soltar`, `equipar` y `usar`. Este caso lo encontramos como bug durante la integración: el replay soltaba otro objeto, y ahora hay una prueba para que no vuelva a pasar.

La reproducción funciona porque el juego es determinista: un solo `random.Random(semilla)` que pertenece a la partida y una secuencia en la agenda que nunca se repite. Antes de reproducir, `main.py` compara la versión de la cripta y la del catálogo con las del encabezado, y si no coinciden lo reporta y no reproduce. El replay usa `VistaReplay`, sin la vista interactiva.

Si se carga una partida guardada, se crea una bitácora nueva que copia los comandos jugados hasta el guardado, así el archivo nuevo sigue siendo reproducible desde el inicio. Si la bitácora original ya no existe, la nueva queda marcada como no reproducible y `--replay` lo dice.

### Análisis de complejidad

Anotar un comando es O(1) (una línea al final del archivo). Reproducir cuesta lo mismo que jugar esos comandos.

### Evidencia empírica

Las pruebas `test_misma_semilla_y_comandos_dan_la_misma_partida`, `test_el_replay_suelta_el_mismo_objeto_despues_de_mover_el_cursor` y `test_la_bitacora_de_la_partida_cargada_reproduce_lo_mismo` comparan el estado completo (tiempo, vida, enemigos, inventario, suelo, rastro, agenda y estado del azar) entre la partida original y la reproducida, y dan exactamente lo mismo.

### Límites conocidos

Una bitácora solo se puede reproducir mientras sigan disponibles esas versiones de la cripta y del catálogo, en el API o en el paquete `--offline`. Si el profesor cambia la versión de una cripta, los logs viejos dejan de ser reproducibles, y el programa lo dice.

---

## 5.2 Presupuesto de procesamiento (20 ms por ciclo)

### Problema

Con la cripta ya cargada, y sin contar red ni pantalla, resolver todos los eventos entre dos decisiones del jugador tiene que tomar menos de 20 ms.

### Decisión

El ciclo es `avanzar_hasta_turno_jugador`: saca eventos hasta que el siguiente es el turno del jugador. Para que alcanzara con muchos enemigos hicimos tres cambios, después de medir:

1. **El reloj se anota una vez por intervalo** en el historial, y no en cada evento (sección 4.6).
2. **El heap mueve un hueco** en lugar de intercambiar en cada nivel (sección 4.1).
3. **`gc.freeze()` en el controlador** después de cargar la cripta y después de cargar una partida. Le pide al recolector de basura de Python que deje de revisar los objetos que viven toda la partida (mapa, fichas, enemigos). No lo apaga: solo evita que, en medio de un ciclo, el recolector se ponga a recorrer miles de objetos que nunca van a ser basura. Está en el controlador y no en el modelo, porque el modelo no debe saber nada del entorno de ejecución, y el bench hace exactamente lo mismo para medir lo que corre en el juego.

### Evidencia empírica

| Escenario | Promedio (ms) | p95 (ms) | Máximo (ms) | Eventos por ciclo | ¿Cumple? |
|---|---|---|---|---|---|
| cripta-01 (con el controlador) | 0,03 | 0,04 | 0,09 | 1 | sí |
| 100 salas, 100 enemigos | 1,11 | 2,15 | 4,18 | 121 | sí |
| 400 salas, 400 enemigos | 5,19 | 9,85 | 14,69 | 483 | sí |
| 625 salas, 600 enemigos | 8,28 | 12,70 | 27,88 | 724 | en el 95 % de los ciclos |
| 900 salas, 900 enemigos | 13,24 | 19,94 | 41,49 | 1086 | depende de la corrida (el p95 queda cerca de 20) |

Con la cripta de referencia el ciclo tarda 0,03 ms, unas 600 veces por debajo del límite. Con 400 enemigos activos a la vez cumple incluso en el peor ciclo.

### Límites conocidos

El costo es de unos 11 a 12 µs por evento, así que en el peor caso el límite se alcanza alrededor de los 500 eventos por ciclo (unos 400 enemigos activos a la vez). Con 600 o 900 el promedio sigue por debajo de 20 ms, pero algunos ciclos se pasan. Con 900 el p95 queda justo en el borde: en esta corrida dio 19,94 ms y en otra dio 23,41 ms, así que al repetir el bench puede salir "NO" en esa fila. Probamos apagando el recolector por completo y los picos seguían apareciendo, así que una parte viene del sistema operativo y no de nuestro código.

La mejora siguiente sería no programar acciones para los enemigos que no tienen nada que hacer (un guardián lejos del jugador, por ejemplo) y despertarlos solo cuando el jugador se acerca. No la implementamos: cambia cuándo actúa cada enemigo y habría que revisar el determinismo y el retroceso con calma. Queda como trabajo futuro.

---

## Veneno y regeneración

El enunciado (sección 2.10) define las reglas: el veneno hace su daño cada 80 unidades durante 400, el antídoto lo cancela antes del siguiente pulso, y la regeneración cura cada 200 sin pasar de `vida_max`. Pero el contrato del API (`additionalProperties: false`) no trae ningún campo que diga **cuánto** daño, **cuánto** cura ni **qué** enemigo lo aplica. Se lo consultamos al profesor. Primero nos dijo que debería estar en la documentación del API y que lo iba a revisar, y el 15 de octubre nos confirmó que los campos están en el catálogo y aparecen en los últimos niveles. Ese mismo día revisamos el Swagger, las cuatro criptas publicadas y su catálogo completo (11 fichas), y todavía no aparecían, así que suponemos que llegarán con la cripta de la revisión.

En vez de inventar valores, que sería escribir estadísticas de una cripta dentro del código (la sección 9 lo prohíbe), hicimos lo siguiente:

- La ficha de un enemigo puede traer `veneno` (daño por pulso) y `regeneracion` (vida por pulso). El mapeador los lee si vienen. Si no vienen, quedan en `None` y el efecto nunca ocurre. Hoy, en las criptas publicadas, no ocurre.
- Como no conocemos el formato exacto, el mapeador acepta un número entero o un objeto con un número adentro (por ejemplo `{"daño": 2}` o `{"cantidad": 3}`). Cualquier otra cosa (un texto, un negativo, un objeto con dos números) es un error de datos con un mensaje que dice qué ficha y qué campo fallaron. Así un formato inesperado no hace caer la partida en medio de un combate.
- Un enemigo con `veneno` envenena al jugador cuando lo golpea. Hay un solo evento de pulso a la vez en la agenda, y cada pulso programa el siguiente hasta completar los 400. Un veneno nuevo reemplaza al anterior y vuelve a durar 400 desde ese momento (decisión nuestra).
- El antídoto **cancela el pulso pendiente sin buscarlo** en la agenda, con la misma cancelación perezosa de la sección 4.1.
- Un enemigo con `regeneracion` empieza a regenerarse cuando se activa. Si muere, su evento se cancela.
- Todo pasa por el historial (el pergamino lo revierte) y por el guardado (formato versión 3). Al cargar, `enlazar_evento_restaurado` vuelve a conectar cada evento con su dueño, para poder cancelarlo después sin buscarlo.

Las pruebas (`tests/test_efectos.py`) usan fichas de prueba con esos campos y revisan los 5 pulsos, el antídoto, la muerte por veneno, el retroceso, la regeneración con tope y que guardar, cargar y seguir con veneno activo dé exactamente lo mismo que no haber guardado.

---

## Pruebas con las criptas publicadas y con una cripta grande

La sección 9 dice que la revisión usa una cripta que no hemos visto, que puede ser más grande y tener más tipos y efectos. Para no llegar a ciegas hicimos dos cosas.

Primero, jugamos contra el API las cuatro criptas publicadas (6, 20, 40 y 50 salas) y reprodujimos esas partidas con `--replay`. Ninguna se cayó y todas usaron muy por debajo del presupuesto (tabla de la sección 4.2).

Segundo, armamos una cripta sintética en el mismo formato del API: 150 salas en 3 páginas, 12 tipos de enemigos (algunos con veneno y regeneración), todas las clases de objetos, puertas con llave y cierre automático, y trampas con y sin rearme. Sobre ella y sobre las criptas publicadas jugamos partidas con comandos al azar, incluidos comandos inválidos, guardar y cargar a mitad de partida, y cachés de 1, 3 y 25 fichas. Cada partida se reprodujo después con su bitácora:

| Prueba | Partidas | Caídas | Replays distintos |
|---|---|---|---|
| Cripta grande, comandos al azar | 60 de 400 comandos | 0 | 0 |
| Cripta grande, jugador casi inmortal (llega a 139 de 150 salas) | 45 de 700 comandos | 0 | 0 |
| Cripta grande, llaves, puertas, antídoto, retroceso, guardar y cargar | 30 | 0 | 0 |
| cripta-02, 03 y 04, jugador normal y casi inmortal | 126 | 0 | 0 |

Explorar toda la cripta grande costó entre 25 y 26 solicitudes, de ellas 15 de contenido (150 salas en lotes de 10). También simulamos que el presupuesto se acaba a mitad de partida: el juego no se cae, avisa una sola vez y nunca deja al jugador en una sala cuyo contenido no conoce.

---

## Retos y dificultades del proyecto

1. **Entender el API y su presupuesto.** Al principio no teníamos claro cómo funcionaba el API ni qué significaba cada endpoint. Tuvimos que aprender a manejar el X-Cripta-Client-Id (uno solo por ejecución), los errores HTTP y sobre todo el 429, leyendo reintentar_en y esperando sin que el programa se cayera. También entendimos que los reintentos cuentan dentro del presupuesto de solicitudes, así que cada solicitud tenía que valer la pena. Por eso agrupamos el contenido y el catálogo en lotes de 10 y precargamos las salas con BFS.

2. **No poder usar dict como estructura.** La regla de no usar dict como índice, caché o tabla de búsqueda nos obligó a implementar nuestras propias estructuras: un vector ordenado con búsqueda binaria para el catálogo, listas doblemente enlazadas para el inventario y el orden de uso de la caché, y un heap mínimo para la agenda. Más de una vez se nos coló un dict o un set (por ejemplo en las direcciones opuestas de las puertas y en el descargador offline), y tuvimos que cambiarlos al revisar el código.

3. **Ordenar el proyecto con MVC.** El primer cliente de red devolvía los diccionarios del JSON tal cual y hacía print desde el adaptador. Tuvimos que separar responsabilidades: DTOs inmutables para los datos del API, mapeadores para convertir el JSON, un contrato FuenteDatos para el modo en línea y el offline, y un modelo que no sabe nada de HTTP, archivos ni pantalla. Decidimos usar una clase por archivo para no terminar con archivos enormes difíciles de cambiar.

4. **Datos del API que no venían como esperábamos.** Las salidas de cada sala venían como un objeto JSON sin orden garantizado, así que las fijamos en el orden N, S, E, O para que el juego fuera determinista. Las trampas traen el campo "daño" con ñ, que no sirve como nombre de atributo. Y el enunciado habla de veneno y regeneración, pero el contrato del API no trae esos campos. Se lo preguntamos al profesor y, como no hubo cambios en el API, los implementamos de forma que se activen solo si la ficha los declara (ver la sección anterior).

5. **Ambigüedades del enunciado.** No sabíamos si una puerta entre dos salas era una sola o si cada lado era independiente. Primero la implementamos compartida, pero el profesor nos aclaró que cada lado es una puerta distinta, y tuvimos que rehacer Puerta, Esqueleto y sus pruebas. También tuvimos que armar nosotros mismos el paquete para el modo --offline a partir de las respuestas del API, guardando un archivo por sala y por ficha (incluyendo lo que sueltan los enemigos) para no depender de cómo se pidieron los lotes.

6. **Integrar el trabajo de todo el equipo.** Al unir el motor con el controlador, la caché y la vista aparecieron errores que no se veían por separado: atacar no gastaba el turno, abrir una puerta costaba 100 en vez de 50 y faltaban los comportamientos y el rastro. Más adelante, un cambio en la bitácora dejó de anotar `sig` y `ant`, y el replay soltaba otro objeto. Tuvimos que corregirlos y actualizar las pruebas sin borrarlas. También aprendimos a revisar siempre cuántas pruebas se ejecutan, porque copiar archivos incompletos o en la versión equivocada hacía que algunas pruebas no corrieran o fallaran.

7. **Determinismo, replay y guardado.** Para que --replay y la carga de partidas funcionaran, el juego tenía que ser completamente determinista: un solo random.Random(semilla) que pertenece a la partida, una secuencia en la agenda que nunca se repite y el estado del generador incluido en el guardado. La prueba más exigente fue que guardar, cargar y seguir jugando diera exactamente lo mismo que no haber guardado nunca.

8. **El retroceso sin copiar el estado.** El pergamino de retroceso tenía que deshacer la última acción del jugador y todo lo que pasó hasta su siguiente decisión, guardando solo lo que cambió y no una copia de la partida. Hubo casos difíciles: el propio pergamino no debe deshacerse, la agenda tiene que restaurar eventos cancelados y sacados, y el contador de secuencia no puede retroceder.

9. **La caché y las fichas en uso.** Al limitar la caché a 25 fichas en memoria nos dimos cuenta de que podía liberar una ficha que se estaba usando (un enemigo vivo, un objeto del inventario o del suelo). Tuvimos que agregar la retención de las fichas en uso y que el controlador se las informe a la caché después de cada comando.

10. **Medir en vez de suponer.** Al principio elegimos el umbral entre inserción y merge sort "a ojo" (100). Las mediciones mostraron que 50 era el valor correcto, y lo cambiamos. Lo mismo pasó con las estructuras: comparamos el heap contra una lista (el heap fue unas 150 veces más rápido con 3000 eventos) y el vector ordenado contra un árbol binario simple, que se degenera cuando los identificadores llegan ordenados.

11. **El límite de 20 ms por ciclo.** Con cientos de enemigos activos, el ciclo entre dos decisiones del jugador pasaba de 20 ms. Optimizamos el motor: el reloj se anota una sola vez por acción en el historial, el heap mueve un "hueco" en vez de intercambiar en cada nivel, y le pedimos al recolector de basura de Python que deje de revisar lo que vive toda la partida (gc.freeze). Con eso cumplimos siempre hasta unos 400 enemigos activos a la vez (alrededor de 500 eventos por ciclo). Con más, los peores casos se ven afectados también por el sistema operativo, y lo dejamos documentado como límite conocido.

12. **El tiempo.** Todo esto se hizo en pocas semanas y en paralelo con otras materias, así que tuvimos que priorizar: primero lo que pide la rúbrica, después las mejoras. Lo que no alcanzamos a implementar (como dormir a los enemigos que no tienen nada que hacer, para bajar más el tiempo por ciclo) quedó anotado como mejora futura.


---

# Parte II · Terreno y cazador

**Especificación:** `specs/001-terrain-hunter/spec.md` (requisitos FR-001 a FR-015 y PR-001) · **Plan:** `specs/001-terrain-hunter/plan.md`, con `research.md` y `data-model.md` · **Tareas:** `specs/001-terrain-hunter/tasks.md` · **Análisis de consistencia:** `specs/001-terrain-hunter/analisis.md`.

**Cómo se hizo.** La capacidad se desarrolló con GitHub Spec Kit: especificación, aclaración, plan, tareas, análisis e implementación, cada fase confirmada en Git antes de la siguiente. Los prompts a las herramientas de IA (Gemini CLI, Claude Code y Claude) están en `PROMPTS_LLM.md`.

**Qué resuelve.** Cada salida puede tener un costo (nulo vale 100) que fija cuánto tarda moverse por ella, y aparece un enemigo nuevo, el cazador, que persigue al jugador por la ruta de menor costo acumulado dentro de su rango. Los tres problemas de diseño son la búsqueda de esa ruta, cuándo se puede reutilizar y cómo se integra el costo en el reloj virtual.

**Resumen de lo medido.** Las cifras de cada comparación están en el Apéndice A al final de este documento: es la salida íntegra de `python main.py --bench` de la corrida de entrega.

---

## 1. Ruta de costo mínimo del cazador

**Problema.** En su turno, el cazador ataca si comparte sala con el jugador. Si no, calcula el costo mínimo `d` de llegar a la sala actual del jugador usando solo salidas abiertas en ese instante; espera si no hay ruta o si `d > rango`; si no, avanza un paso por una ruta de costo `d`, y ante empate elige la sala vecina de menor id (§3.2). La decisión debe ser siempre la que daría un cálculo desde cero, y el ciclo de eventos completo debe quedar bajo 20 ms con decenas de cazadores activos (PR-001).

Las operaciones reales son dos: calcular distancias hacia la sala del jugador (poco frecuente: solo cuando cambia el jugador o las puertas) y consultar la distancia de las vecinas de un cazador (en cada turno de cada cazador, con a lo sumo cuatro salidas por sala). Todos los cazadores persiguen el mismo destino.

**Alternativas consideradas.**

1. *Un recorrido por cazador*, desde la sala de cada uno hasta el jugador. Se descartó porque repite el mismo trabajo: todos los cazadores tienen el mismo destino, así que con N cazadores se hacen N búsquedas por ciclo donde alcanza una. Se midió (`bench/ruta_por_cazador.py`) como alternativa descartada.
2. *Búsqueda por niveles, sin costos.* Se descartó por incorrecta: minimiza el número de salas y no el costo, y el Apéndice B del enunciado pide justamente elegir la ruta de más salas pero menor costo.
3. *Búsqueda dirigida con heurística (A\*).* Se descartó: gana cuando hay un único par origen-destino, pero aquí es un destino común para muchos orígenes, y una sola búsqueda desde el destino los atiende a todos.
4. *Un recorrido compartido desde la sala del jugador* (elegida).

**Decisión.** Un recorrido de costo mínimo (Dijkstra implementado en el proyecto, sin bibliotecas) que parte de la sala del jugador y se propaga hacia afuera, y se detiene cuando supera el rango máximo de los cazadores activos. Una sola corrida deja la distancia al jugador de todas las salas dentro del rango, y cada cazador la consulta.

- **Cola de prioridad:** el `MinHeap` de `estructuras/` de la Parte I, reutilizado.
- **Salas por índice denso:** los ids de sala no son contiguos ni empiezan en 1, así que al cargar la cripta, una sola vez, se construye una correspondencia de id a un índice entero de 0 a V-1 con el `VectorOrdenado` de la Parte I (sin `dict`). Cada salida guarda ya resueltos los índices de su origen y su destino, y el recorrido trabaja con listas indexadas por ese entero: no consulta la correspondencia por cada arista.
- **Reinicio sin recorrer la cripta:** un contador de época por sala indica si su distancia pertenece a la corrida actual, así preparar una corrida nueva cuesta O(1) y no O(V).
- **Salidas dirigidas, sin suponer simetría:** §3.1 iguala el costo en ambos sentidos, pero no garantiza que exista la salida inversa ni que su puerta esté en el mismo estado (el API describe cada salida como dirigida, con su propio estado). Por eso, al cargar la cripta se construye, para cada sala, la lista de salidas *entrantes* (origen, costo y referencia a la puerta, para leer su estado actual), y el recorrido que parte del jugador propaga por ellas.
- **Desempate:** terminado el recorrido, un cazador en la sala `u` examina sus salidas y elige la sala vecina `v` con `costo(u,v) + dist(v) = dist(u)` y menor id.

Módulos principales: `modelo/grafo_cripta.py` (índices densos y salidas entrantes) y `modelo/buscador_rutas.py` (búsqueda).

**Complejidad.** Construcción de salidas entrantes e índices: O(V + E), una vez por cripta. Recorrido: O(R + E_R log R), con R las salas dentro del rango máximo y E_R sus salidas entrantes; no depende del tamaño total de la cripta. Preparar la corrida: O(1). Decisión de un cazador: O(1), porque examina a lo sumo cuatro salidas.

**Evidencia empírica.** Apéndice A, secciones de la ruta del cazador: un cazador frente a muchos, y cálculo individual (alternativa descartada) frente a compartido. Las pruebas `tests/test_cazador.py` verifican la corrección sobre los casos del Apéndice B (ruta de menos salas y mayor costo, desempate por id, rejilla con muchísimas rutas mínimas, salidas de un solo sentido, puertas cerradas en un solo sentido, sala intermedia sin contenido cargado).

**Límites conocidos.** Si el rango máximo cubre casi toda la cripta, R se acerca a V y cada recorrido cuesta como recorrer la cripta completa. La correspondencia de ids supone un esqueleto que no cambia durante la partida, como en el servicio actual. El cálculo compartido supone un único objetivo: con varios jugadores habría un mapa por jugador.

**¿Coincide con el plan original?** La decisión coincide con el plan vigente. El primer borrador del plan tenía dos errores que se corrigieron antes de implementar, por revisión contra el enunciado y por el informe de consistencia, no por una medición: suponía simetría del esqueleto (solo el costo es simétrico) y expresaba la complejidad en función de todas las salas y no de la región dentro del rango.

---

## 2. Invalidación de rutas

**Problema.** Calcular el mapa de distancias en cada turno de cada cazador es correcto pero caro. Se quiere reutilizarlo entre turnos sin cambiar nunca la decisión (§3.2, equivalencia observable): reutilizar un cálculo anterior solo es válido si se puede demostrar que el resultado es idéntico al de calcular desde cero.

**Alternativas consideradas.**

1. *Recalcular siempre*, en cada decisión. Es trivialmente correcto y es la alternativa descartada; se midió contra la reutilización (Apéndice A).
2. *Reutilizar con invalidación por eventos* (elegida).

**Decisión.** El mapa se marca como *sucio* cuando ocurre algo que puede cambiar la respuesta, y se recalcula bajo demanda en la siguiente consulta.

**Argumento de equivalencia.** La decisión de un cazador depende solo del esqueleto (estático), del estado actual de las puertas, de la sala del jugador y del rango máximo de los cazadores activos (que acota la búsqueda). Si ninguna de esas variables cambió desde el último cálculo, el resultado es idéntico por construcción. Eventos entre dos turnos de un cazador:

| Evento | ¿Invalida? | Razón |
|---|---|---|
| Se abre o se cierra una puerta | Sí | cambia la conectividad. Un refinamiento no invalida si la salida queda fuera de la región ya asentada, porque no puede cambiar ninguna distancia calculada |
| El jugador cambia de sala | Sí | cambia el origen del recorrido |
| Aparece o muere un cazador con rango distinto del máximo vigente | Sí | cambia el umbral que acota la búsqueda |
| Otro actor cambia de sala | No | no altera costos, puertas ni destino |
| Cambio de velocidad de un actor | No | no altera costos, puertas ni destino |
| Daño, muerte u otras acciones sin cambio de rango máximo | No | no alteran la topología ni el destino |

**Complejidad.** Marcar el mapa como sucio: O(1). Cada recálculo cuesta lo mismo que la búsqueda de la sección 1; en un tramo sin invalidaciones, el costo de las decisiones es el de consultar las vecinas.

**Evidencia empírica.** Apéndice A, sección de invalidación: reutilización contra recálculo siempre, con puertas estables y con puertas inestables (que cambian cada pocos turnos). Verificación de corrección: `tests/test_cazador.py` compara la decisión con el cálculo desde cero en una rejilla con costos variados, ocho cazadores y puertas que se abren y se cierran, y comprueba que una puerta fuera de la región asentada no obliga a recalcular.

**Límites conocidos.** Con puertas que cambian en casi cada turno la reutilización no ahorra nada y cuesta lo mismo que recalcular siempre. Si una regla futura hiciera que otros actores afectaran el costo o la transitabilidad de las salidas (por ejemplo, enemigos que bloquean), habría que ampliar la tabla de eventos que invalidan.

**¿Coincide con el plan original?** Sí. El plan inicial era enumerar los eventos con una justificación; se completó con la tabla y la cláusula del rango máximo tras el análisis de consistencia, no por una medición.

---

## 3. Costo de las salidas y reescalado de la velocidad

**Problema.** El costo de moverse es el de la salida (nulo vale 100, entero mayor o igual que 1) y el intervalo hasta la próxima acción es `max(1, costo_salida * 100 // velocidad)` para todos los actores; las demás acciones conservan su costo (FR-012). Si un efecto cambia la velocidad de un actor con una acción ya programada, el tiempo restante se reescala según P1 §2.3 (FR-013).

**Alternativas consideradas.**

1. *Calcular el costo en la vista o en el controlador.* Se descartó porque rompe la separación MVC: el costo es una regla del juego y vive en el modelo.
2. *Guardar el costo de la salida en el evento y recalcular el tiempo restante con él.* Se descartó: la fórmula de P1 §2.3 conserva el progreso a partir del tiempo restante, que ya incluye el costo del terreno; agregarlo no cambia el resultado observable y obligaría a modificar un método ya probado de la agenda.
3. *Guardar el costo en la salida, centralizar la fórmula en el modelo de movimiento y reutilizar la agenda de la Parte I sin modificarla* (elegida).

**Decisión.** La salida guarda su costo (valor 100 si el servicio no lo declara o es nulo). La fórmula del intervalo está en un solo lugar del modelo. `AgendaEventos.cambiar_velocidad` ya implementa `max(1, (tiempo_siguiente - t) * velocidad_anterior // velocidad_nueva)`; se reutiliza sin cambios y esta capacidad solo agrega la prueba que lo verifica tras un movimiento costoso. La vista muestra el costo de cada salida y marca a los cazadores.

**Complejidad.** Calcular un intervalo: O(1). Reescalar: el costo de reprogramar un evento en la agenda de la Parte I; no depende del costo de la salida.

**Evidencia empírica.** `tests/test_movimiento_terreno.py` (intervalos con velocidades altas y bajas, intervalo mínimo 1, reescalado tras un movimiento por una salida costosa, costos de las demás acciones sin cambios) y `tests/test_vista_terreno.py` (costos visibles, cazadores distinguibles). Las mediciones de la agenda con la carga nueva están en el Apéndice A.

**Límites conocidos.** El costo es entero y no varía durante la partida: si una regla futura lo hiciera depender del tiempo o de otros actores, la fórmula del intervalo tendría que recibirlo en el momento de moverse.

**¿Coincide con el plan original?** No exactamente. El primer borrador del plan proponía pasar el costo de la salida como `costo_base` a `cambiar_velocidad`. Se corrigió antes de implementar, por revisión contra la fórmula de P1 §2.3 y no por una medición, y el plan vigente reutiliza el método sin modificarlo.

---

## 4. Mediciones de la Parte I repetidas con la carga nueva (§5.6)

Se repitieron con cazadores las mediciones de la agenda de eventos y del ciclo completo entre dos decisiones del jugador (límite de 20 ms), junto con el resto de las secciones de la Parte I; el resultado completo está en el Apéndice A. Esta capacidad no modificó ninguna estructura de la Parte I (`estructuras/` no cambió) y reutiliza el `MinHeap` y el `VectorOrdenado`, por lo que las decisiones de la Parte I siguen vigentes. Las mediciones anteriores de cada sección están en los apartados de la Parte I de este documento: el "antes" es esa tabla y el "después" es el Apéndice A.

**Límite conocido.** Las pruebas de estrés con criptas sintéticas mayores que la de referencia pueden superar los 20 ms por ciclo; como establece el Principio VI de la constitución, esos casos se documentan como límite conocido y no como condición de aceptación. La causa es que el costo del ciclo crece con el número de eventos programados por ciclo (acciones de todos los enemigos activos).

---

## 5. Trazabilidad de la capacidad

| Requisitos | Pruebas | Medición |
|---|---|---|
| FR-001, FR-004 (costo de la salida, rango del cazador) | `tests/test_mapeador_salas.py`, `tests/test_mapeador_catalogo.py` | |
| FR-002, FR-003, FR-012, FR-013 (costo, intervalo, reescalado) | `tests/test_movimiento_terreno.py` | |
| FR-005 a FR-009, FR-014, FR-015 (comportamiento del cazador) | `tests/test_cazador.py` | `bench/bench_cazadores.py`, `bench/ruta_por_cazador.py` |
| FR-010, FR-011 (vista) | `tests/test_vista_terreno.py` | |
| PR-001 (ciclo de 20 ms) | | `bench/bench_cazadores.py` |

Para recorrer un requisito: `findstr /n /c:"FR-014" tests\test_cazador.py` muestra el escenario y la prueba que lo cita.

## Apéndice A - Salida de python main.py --bench (corrida del 18/11/2026)
```text
### Agenda de eventos (4.1)
== Agenda: sacar el siguiente y reprogramarlo (us por operacion) ==
 eventos         heap        lista lista/heap
     100         3.16        19.35        6.1
     300         3.37        59.94       17.8
    1000         5.34       152.37       28.5
    3000         3.93       699.17      177.9

### Busqueda en la cache (4.3 y 4.4)
== Buscar una ficha: vector ordenado vs arbol binario simple (us por busqueda) ==
fichas llegada          vector        arbol   altura arbol
    25 al azar            2.01         1.25              8
    25 ordenada           2.39         2.93             25
   250 al azar            3.22         2.16             17
   250 ordenada           3.35        24.53            250
  2000 al azar            4.65         3.34             26
  2000 ordenada           4.87       195.81           2000

== Recuperar una ficha liberada de memoria (tope 25) ==
desde disco (us por ficha)           19097.7
solicitudes de red al recuperar            0
desde la red (enunciado 3.4)      ~400000 us por solicitud

### Estructuras (cache, inventario, agenda)
== Cache de catalogo (us por consulta, tope 25) ==
acierto (en memoria)          10.07
fallo (desaloja y pide)       49.20

== Inventario: soltar (us) segun la posicion ==
n=   10  frente        5.28
n=   10  medio         2.30
n=   10  fondo         2.42
n= 1000  frente       10.10
n= 1000  medio         7.44
n= 1000  fondo         2.69

== Agenda de eventos (us por programar + sacar) ==
n=  300        4.74
n= 3000        5.75

### Retroceso (4.6)
== Historial de retroceso (por accion del jugador) ==
escenario                    accion (us)   deshacer (us)  cambios guardados
100 salas, 100 enemigos            966.9           255.1              265.5
400 salas, 400 enemigos           3860.1           977.0              964.5
(se guarda solo lo que cambio en cada intervalo, nunca una copia del estado)

### Rastro (4.7)
== Decision de un rastreador: vecinas de su sala vs BFS por la cripta (us) ==
   salas   1a vez en sala    sala ya vista            BFS  BFS/vista
     100            16.12             1.66        1335.24        805
     900            42.28             1.85       38328.18      20749
    2500           100.81             2.61      225784.96      86632

### Bitacora en pantalla (4.8)
== Bitacora de 20 mensajes: costo de agregar y memoria tras 100000 mensajes ==
estructura                     us/agregar          bytes         desplaza
fila circular (la nuestra)          0.212            216               no
lista con pop(0)                    0.165            248   19 por mensaje
lista que crece                     0.109         800984               no

### Ordenamientos (4.9)
== Tiempo (ms) por tamano y tipo de dato, clave barata ==
datos           n    insercion        merge  gana
aleatorio       5       0.0016       0.0041  insercion
ordenado        5       0.0009       0.0037  insercion
inverso         5       0.0019       0.0042  insercion
casi 2%         5       0.0009       0.0036  insercion
casi 10%        5       0.0009       0.0037  insercion
aleatorio      10       0.0041       0.0088  insercion
ordenado       10       0.0014       0.0078  insercion
inverso        10       0.0059       0.0088  insercion
casi 2%        10       0.0015       0.0077  insercion
casi 10%       10       0.0015       0.0077  insercion
aleatorio      20       0.0141       0.0214  insercion
ordenado       20       0.0028       0.0180  insercion
inverso        20       0.0204       0.0192  merge
casi 2%        20       0.0029       0.0180  insercion
casi 10%       20       0.0036       0.0186  insercion
aleatorio      50       0.0614       0.0649  insercion
ordenado       50       0.0067       0.0530  insercion
inverso        50       0.1255       0.0676  merge
casi 2%        50       0.0136       0.0565  insercion
casi 10%       50       0.0159       0.0573  insercion
aleatorio     200       0.9649       0.3381  merge
ordenado      200       0.0278       0.3047  insercion
inverso       200       2.0501       0.2815  merge
casi 2%       200       0.1062       0.2912  insercion
casi 10%      200       0.2665       0.3038  insercion
aleatorio    1000      29.5374       2.3581  merge
ordenado     1000       0.1555       1.6485  insercion
inverso      1000      55.4893       1.6936  merge
casi 2%      1000       1.6618       1.9100  insercion
casi 10%     1000       6.5190       2.1703  merge

== Llamadas a clave() (proxy de comparaciones costosas), n=1000 ==
aleatorio  insercion=  253101  merge=   17440
ordenado   insercion=    1998  merge=    9864
inverso    insercion=  500499  merge=   10088
casi 2%    insercion=   13202  merge=   13670
casi 10%   insercion=   60062  merge=   16190

== Tiempo (ms) con clave COSTOSA, n=200 ==
aleatorio  insercion=   15.346  merge=    3.581
ordenado   insercion=    0.538  merge=    2.121
inverso    insercion=   27.702  merge=    2.346
casi 2%    insercion=    0.931  merge=    2.409
casi 10%   insercion=    3.576  merge=    3.218

== Alrededor del umbral de tamano (50) y de desorden (5%): us por ordenamiento ==
datos           n    insercion        merge       gana      elige
aleatorio      25        22.40        29.63  insercion  insercion
aleatorio      50        71.50        70.10      merge  insercion
aleatorio      75       202.43       129.98      merge      merge
aleatorio     100       262.56       200.22      merge      merge
aleatorio     125       513.63       247.59      merge      merge
aleatorio     150       700.98       284.35      merge      merge
inverso        25        37.53        26.19      merge  insercion
inverso        50       132.17        60.43      merge  insercion
inverso        75       330.20       103.71      merge      merge
inverso       100       585.85       137.19      merge      merge
inverso       125       885.23       176.53      merge      merge
inverso       150      1297.28       363.07      merge      merge
casi 2%        25         6.43        32.09  insercion  insercion
casi 2%        50        17.35        95.52  insercion  insercion
casi 2%        75        14.00        89.72  insercion  insercion
casi 2%       100        30.68       134.40  insercion  insercion
casi 2%       125        55.37       187.66  insercion  insercion
casi 2%       150        37.88       205.14  insercion  insercion

### Guardado binario vs JSON (4.10)
   salas |    bin (B)   json (B) | carga bin ms carga json ms |  1 sala bin ms 1 sala json ms
      20 |       2823       4683 |        0.194        0.115 |         0.0601          0.104
     200 |      26914      44815 |        0.992        0.565 |         0.0579          0.527
    2000 |     273067     453472 |        9.976        5.522 |         0.0708          5.627
   20000 |    2811835    4642818 |      156.478       83.422 |         0.1418         75.626

### Presupuesto de procesamiento (P1 5.2 y P2 6.1, con la carga nueva)
== Ciclo completo entre dos decisiones del jugador (ms, limite 20) ==
escenario                       promedio       p95    maximo    eventos  us/evento  cumple
cripta-06 (36 cazadores)            3.20      4.91      7.03         82       38.9      si
cripta-06 moviÚndose                4.36      6.19     10.84        120       36.4      si
100 salas, 100 enemigos             3.75      5.28     15.88        121       31.0      si
400 salas, 400 enemigos             6.42     10.79     32.11        483       13.3     p95
625 salas, 600 enemigos             9.20     12.96     28.77        724       12.7     p95
900 salas, 900 enemigos            15.76     23.98     55.74       1086       14.5      NO
900 salas, 60 cazadores            23.73     53.57     67.05       1020       23.3      NO
(eventos = eventos programados por ciclo; 'p95': cumple en el 95% de los ciclos)

### Segunda parte: ruta del cazador e invalidaci¾n (P2 5.1 y 5.2)
== Ruta del cazador: un cßlculo compartido frente a uno por cazador (ms por ronda de decisiones, 900 salas) ==
cazadores  rango     compartido   individual      raz¾n salas/compart.   salas/indiv.
1          300            0.200        0.165        0.8             24             19
10         300            0.237        1.843        7.8             25            217
30         300            0.269        5.709       21.2             26            653
60         300            0.263       10.053       38.2             23           1216
1          2400           4.776        0.431        0.1            792             70
10         2400           4.720        4.009        0.8            851            748
30         2400           6.867       14.712        2.1            836           2030
60         2400           7.232       36.308        5.0            843           4611
(las dos alternativas deciden exactamente lo mismo; se verifica en cada ronda)

== Invalidaci¾n: reutilizar el cßlculo frente a recalcular siempre (30 cazadores, rango 2400, 300 rondas) ==
puertas                estrategia         ms/ronda   cßlculos reutilizados
estables (1 c/50)      reutilizar            2.093         79         8921
estables (1 c/50)      recalcular          149.152       9000            0
inestables (8/ronda)   reutilizar            2.146        300         8700
inestables (8/ronda)   recalcular           94.988       9000            0
(en los dos casos las decisiones de todas las rondas son idÚnticas)
```
