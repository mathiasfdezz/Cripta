# Documento de Decisiones de Diseño

Proyecto CRIPTA, Estructuras de Datos II, 2026.

Este documento explica, problema por problema (sección 4 del enunciado), qué estructura usamos, qué otras opciones pensamos y por qué las descartamos. Los números salen de nuestras propias mediciones. Para repetirlas:

```
python main.py --bench
```

Todas las mediciones se tomaron en un Intel Core i5-10400 (2.90 GHz), Windows 11 y Python 3.14. Las frecuencias "reales" vienen de una partida completa de cripta-01 en modo offline: 27 comandos, 21 acciones que gastan tiempo, 3 enemigos derrotados y un reloj que terminó en t=1675.

Una nota sobre el formato: cada sección sigue los seis puntos de la sección 8 (problema, alternativas, decisión, complejidad, evidencia y límites).

**Segunda parte.** Las secciones de la segunda parte están al final, bajo «Segunda parte», una por problema de la sección 5 de su enunciado (5.1 a 5.6). Cada una enlaza a la especificación y al plan de spec-kit de los que viene e indica si la decisión final coincide con el plan. Las mediciones de la segunda parte se tomaron en la misma máquina, el 17 de noviembre de 2026, con `python main.py --bench`; la cripta de referencia es la más grande del paquete offline (cripta-06, 300 salas, 760 salidas, 75 enemigos de los cuales 36 son cazadores).

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

# Segunda parte

Cuatro capacidades nuevas, cada una con su especificación, plan, tareas y análisis en `specs/`. La regla editorial no cambió: el enunciado describe operaciones y propiedades, y la estructura la elegimos y la medimos nosotros.

Una idea atraviesa las cuatro: **índices densos**. `GrafoCripta` (capacidad 001) numera las salas de 0 a V−1 en orden de id y las salidas de 0 a E−1, una sola vez y en O(V + E). Desde ahí, las distancias del cazador, el mapa conocido, la verificación de resolubilidad y los puntos de control usan listas indexadas por ese número en vez de buscar por id. Como el orden de los índices es el de los ids, «la vecina de menor id» es «la vecina de menor índice», y el desempate no necesita comparar ids.

---

## P2 5.1 La ruta más barata del cazador

Especificación: [specs/001-terrain-hunter/spec.md](specs/001-terrain-hunter/spec.md) · Plan: [plan.md](specs/001-terrain-hunter/plan.md) · Análisis: [analisis.md](specs/001-terrain-hunter/analisis.md)

### Problema

Cada cazador, en su turno, necesita el costo mínimo d desde su sala hasta la del jugador por salidas abiertas y, si d ≤ rango, el primer paso hacia la vecina de menor id entre las que inician una ruta de costo d. Los costos no son uniformes, así que contar salas no sirve. En la cripta de referencia hay 36 cazadores, y todos persiguen al mismo objetivo.

### Alternativas consideradas

1. **BFS por cantidad de salas.** Es lo que hacía falta en la primera parte. Con costos distintos da rutas equivocadas (el Apéndice B tiene un caso para eso).
2. **Un Dijkstra por cazador, hacia adelante** (`bench/ruta_por_cazador.py`): parte del cazador, se corta en su rango y se detiene al sacar la sala del jugador. Para el desempate, cada sala lleva la menor vecina inicial entre todas sus rutas mínimas.
3. **Un Dijkstra compartido, hacia atrás** desde el jugador por las salidas que entran a cada sala, cortado en el mayor rango de los cazadores. Da la distancia de todas las salas al jugador de una vez.

### Decisión

La alternativa 3 (`modelo/buscador_rutas.py`), con el `MinHeap` propio de la primera parte y **épocas**: cada lista (distancia, vista, asentada) tiene una posición por sala, y una posición solo vale si su época es la del cálculo actual. Así no hay que limpiar V posiciones por cálculo y el costo depende de la región dentro de la cota, no de la cripta.

El desempate se resuelve después del cálculo, no dentro del heap: para el cazador en u se miran sus salidas abiertas u→v y se elige el menor v con costo(u,v) + dist(v) = d. Todas esas v tienen dist(v) < d ≤ cota, así que están asentadas y su distancia es exacta. El resultado no depende del orden en que el heap resuelva empates, que es justo lo que pide §3.2.

**¿Coincide con el plan?** Sí: es la decisión del plan de Abraham (Dijkstra compartido por salidas entrantes con épocas). El análisis cambió dos cosas que no son de algoritmo: el nombre (`RastreadorCazador` chocaba con el rastreador de la primera parte) y que las aristas guarden el número de la salida en vez del objeto `Puerta`, para que la línea de tiempo pudiera copiar el estado.

### Análisis de complejidad

| Operación | Costo |
|---|---|
| Armar `GrafoCripta` | O(V + E), una vez por cripta |
| Cálculo compartido | O(R + E_R log R), R = salas a distancia ≤ cota |
| Decisión de un cazador con el cálculo hecho | O(salidas de su sala) |
| Alternativa: un cálculo por cazador | O(R_i + E_i log R_i) por cazador |

### Evidencia empírica

Cuadrícula sintética de 900 salas con costos de 20 a 300, cazadores cerca del jugador, 25 posiciones del jugador por fila (ms por ronda de decisiones; en cada ronda se verifica que las dos alternativas decidan exactamente lo mismo):

| Cazadores | Rango | Compartido | Uno por cazador | Uno por cazador / compartido |
|---|---|---|---|---|
| 1 | 300 | 0,059 | 0,049 | 0,8 |
| 10 | 300 | 0,071 | 0,563 | 7,9 |
| 30 | 300 | 0,081 | 1,702 | 21,1 |
| 60 | 300 | 0,089 | 3,081 | 34,6 |
| 1 | 2400 | 2,123 | 0,186 | 0,1 |
| 10 | 2400 | 2,492 | 2,072 | 0,8 |
| 30 | 2400 | 2,351 | 5,135 | 2,2 |
| 60 | 2400 | 2,384 | 11,824 | 5,0 |

**Bajo qué condiciones cambia la respuesta.** Con un solo cazador gana el cálculo individual, sobre todo con rango grande: se detiene apenas encuentra al jugador, mientras que el compartido recorre toda la región del rango (792 salas contra 70). Con rango pequeño el compartido gana desde unos pocos cazadores; con rango grande, a partir de unos 10 a 30. En las criptas del juego hay decenas de cazadores (36 en la de referencia), y además el compartido se reutiliza entre turnos (sección siguiente), cosa que el individual no puede hacer porque cada cazador parte de una sala distinta.

### Límites conocidos

La cota es el mayor rango de los cazadores de la partida. Un solo cazador con rango enorme obliga a que el cálculo compartido cubra esa región aunque los demás tengan rango pequeño. Con el catálogo actual (600 y 2400) no es un problema. Si apareciera un rango mucho mayor, convendría agrupar los cálculos por rango.

---

## P2 5.2 Rutas que dejan de ser válidas

Especificación: [specs/001-terrain-hunter/spec.md](specs/001-terrain-hunter/spec.md) (FR-009) · Plan: [research.md](specs/001-terrain-hunter/research.md)

### Problema

Entre dos turnos de un cazador se abren y cierran puertas, el jugador se mueve, otros actores cambian de sala o mueren y cambian velocidades. La decisión tiene que ser siempre la de un cálculo desde cero; reutilizar solo vale si se puede demostrar que no cambia la respuesta.

### Alternativas consideradas

1. **Recalcular siempre**, en cada decisión.
2. **Invalidar con cualquier cambio de puerta** (lo que decía el plan original).
3. **Invalidación selectiva** (elegida).

### Decisión

`BuscadorRutas.asegurar` reutiliza el último cálculo salvo que:

- el jugador cambió de sala (cambia el origen): siempre invalida;
- la cota pedida supera la usada;
- cambió una salida u→x **cuya sala de llegada x quedó asentada** en el último cálculo.

La demostración del tercer punto: el resultado solo depende de las salidas que entran a salas asentadas. Si x no quedó asentada, dist(x) > cota, y cualquier ruta que use u→x cuesta más que la cota; abrir o cerrar esa salida no cambia ninguna distancia ≤ cota. Las muertes, los cambios de sala de otros actores y los cambios de velocidad no tocan el esqueleto: no invalidan.

Para saber qué cambió sin buscar, cada `Puerta` avisa a su esqueleto al cambiar de estado, también cuando el cambio viene del pergamino o de cargar una partida (la propiedad `cerrada` lo hace en el setter). El esqueleto guarda los números de salida cambiados, y con más de 64 pendientes da todo por cambiado.

La prueba `test_reutilizar_equivale_a_calcular_desde_cero` juega 60 rondas con 8 cazadores, puertas que se abren y cierran al azar y un jugador que se mueve, y compara cada decisión con un cálculo hecho aparte por relajación repetida, sin heap ni cachés.

**¿Coincide con el plan?** No del todo. El plan original invalidaba con cualquier cambio de puerta. El análisis (hallazgo A3) señaló que eso no responde la pregunta de §5.2 («qué eventos invalidan qué información»), y la medición de abajo muestra cuándo importa la diferencia.

### Análisis de complejidad

Revisar si el cálculo sigue valiendo cuesta O(salidas cambiadas desde la última consulta). Recalcular cuesta lo de la sección anterior.

### Evidencia empírica

30 cazadores en la cuadrícula de 900 salas, 300 rondas; el jugador se mueve cada 4 rondas. «Estables»: una puerta cambia cada 50 rondas. «Inestables»: 8 puertas al azar por ronda. Las tres estrategias deciden exactamente lo mismo en todas las rondas (se verifica).

| Rango | Puertas | Estrategia | ms por ronda | Cálculos |
|---|---|---|---|---|
| 2400 | estables | selectiva | 0,703 | 79 |
| 2400 | estables | cualquier puerta | 0,695 | 80 |
| 2400 | estables | recalcular siempre | 70,037 | 9000 |
| 2400 | inestables | selectiva | 1,665 | 300 |
| 2400 | inestables | cualquier puerta | 1,644 | 300 |
| 2400 | inestables | recalcular siempre | 49,655 | 9000 |
| 300 | estables | selectiva | 0,049 | 75 |
| 300 | estables | cualquier puerta | 0,045 | 80 |
| 300 | estables | recalcular siempre | 1,851 | 9000 |
| 300 | inestables | selectiva | 0,052 | 110 |
| 300 | inestables | cualquier puerta | 0,076 | 300 |
| 300 | inestables | recalcular siempre | 1,443 | 9000 |

Reutilizar ahorra entre 25 y 100 veces frente a recalcular siempre. La invalidación selectiva solo se nota cuando la región del rango es chica frente a la cripta: con rango 300 y puertas inestables hace 110 cálculos en vez de 300, porque la mayoría de las puertas que cambian están lejos. Con rango 2400 casi toda la cuadrícula queda asentada y cualquier cambio cuenta. Es la respuesta a la pregunta de §8: una puerta que se cierra sola lejos de todos los cazadores no invalida nada si su sala de llegada está fuera de la región calculada.

### Límites conocidos

El jugador moviéndose invalida siempre, y cada paso suyo cuesta un cálculo completo. En la cripta de referencia eso está dentro del presupuesto (sección P2 5.6), pero es lo que domina cuando el jugador se mueve sin parar.

---

## P2 5.3 El mapa conocido

Especificación: [specs/002-niebla-ir-a/spec.md](specs/002-niebla-ir-a/spec.md) · Plan: [plan.md](specs/002-niebla-ir-a/plan.md) · Análisis: [analisis.md](specs/002-niebla-ir-a/analisis.md)

### Problema

El jugador conoce cada sala como explorada, avistada o desconocida, y recuerda cada puerta como estaba la última vez que la vio. Esas consultas ocurren en cada pantalla, en cada paso de «ir a» y en cada exploración con antorcha. Explorar tiene que costar lo que se revela, no lo que mide el mapa conocido. Todo cambio se revierte con el pergamino y entra en la línea de tiempo. «ir a» busca la ruta más barata sobre ese conocimiento, en menos de 5 ms por paso.

### Alternativas consideradas

1. **Vectores ordenados** de ids explorados y avistados: consulta O(log n) e inserción con desplazamiento, O(n), así que explorar la sala k cuesta proporcional a lo ya explorado.
2. **Atributos en las salas** del esqueleto: mezcla el DTO del API (inmutable) con el estado del juego.
3. **Una lista por sala y otra por salida** con los índices densos (elegida).

Para «ir a»: compartir la implementación con el cazador o escribir otra búsqueda.

### Decisión

`MapaConocido` (`modelo/mapa_conocido.py`) guarda `estado[i]` (0, 1, 2) por sala y `recuerdo[s]` (−1 sin observar, 0 abierta, 1 cerrada) por salida. Cada cambio se anota en el historial como `(lista, posición, valor anterior)` con `registrar_elemento`, un tercer tipo de anotación agregado al `Historial` de la primera parte.

Respuesta a la pregunta de §8 sobre la antorcha: para revertir la exploración de cinco salas basta guardar, por cada posición que cambió, la lista, la posición y el valor anterior. Son las salas que pasaron a exploradas o avistadas y las salidas observadas que cambiaron. No se copia el mapa.

«ir a» usa **la misma clase** `BuscadorRutas` que el cazador, en otra instancia y con otras reglas: `pasable` = la salida se recuerda abierta, `admitida` = la sala está explorada. Compartir la clase asegura el mismo desempate (§3.4 remite a §3.2) con el código ya probado. Compartir la instancia o las distancias no sirve: el cazador usa las puertas reales y «ir a» la memoria del jugador.

**¿Coincide con el plan?** Sí, con una mejora que salió de medir: el plan calculaba las distancias desde el destino a todo lo explorado. En la versión final el cálculo se detiene apenas queda asentada la sala del jugador. Su distancia ya es definitiva, y también la de cualquier vecina que pueda ser su primer paso, porque está más cerca del destino. El paso no cambia (el bench lo compara en cada viaje) y el trabajo baja a la mitad.

### Análisis de complejidad

| Operación | Costo |
|---|---|
| Estado de una sala o puerta recordada | O(1) |
| Explorar una sala | O(salidas de la sala + salidas que llegan a ella) |
| Entrar con antorcha | O(salidas de la sala y de sus vecinas) |
| Revertir | O(cambios anotados) |
| Un paso de «ir a» | O(R + E_R log R) sobre lo explorado, cortado al llegar a la sala del jugador |

### Evidencia empírica

Consultar el estado de una sala (ns por consulta):

| Salas exploradas | Lista por índice | Vector ordenado de ids |
|---|---|---|
| 50 | 59 | 632 |
| 300 | 61 | 872 |
| 900 | 59 | 1104 |

Explorar una sala nueva según cuántas hay exploradas (µs por sala, 900 salas en orden aleatorio):

| Tramo | Lista por índice | Vector ordenado de ids |
|---|---|---|
| salas 0 a 90 | 2,20 | 44,12 |
| salas 405 a 495 | 2,27 | 62,58 |
| salas 810 a 900 | 2,27 | 62,80 |

Un paso de «ir a» con todo el mapa explorado, 300 viajes al azar (ms):

| Mapa | Promedio | p95 | Máximo | Sin cortar al llegar | Búsqueda hacia adelante | ¿Cumple 5 ms? |
|---|---|---|---|---|---|---|
| cripta-06 (300 salas) | 0,132 | 0,271 | 0,315 | 0,155 | 0,125 | sí |
| sintética de 900 salas | 1,300 | 2,552 | 4,487 | 2,746 | 1,231 | sí |

Las consultas no dependen del tamaño del mapa conocido y explorar cuesta lo mismo al principio que al final, como pide §5.3. En la cripta de referencia un paso de «ir a» tarda unas 15 veces menos que el límite en el peor viaje.

### Límites conocidos

En la cripta sintética de 900 salas el peor viaje queda cerca del límite (4,5 ms en la corrida final; en otra corrida llegó a 5,4 ms), que se mide en la cripta de referencia. Cortar al asentar la sala del jugador dejó el cálculo igual de rápido que una búsqueda hacia adelante desde el jugador. Para mapas mucho más grandes, la mejora siguiente sería guardar las distancias del último destino y reutilizarlas mientras el conocimiento no cambie, igual que con el cazador.

---

## P2 5.4 Resolubilidad

Especificación: [specs/003-resolubilidad/spec.md](specs/003-resolubilidad/spec.md) · Plan: [plan.md](specs/003-resolubilidad/plan.md) · Análisis: [analisis.md](specs/003-resolubilidad/analisis.md)

### Problema

Antes de jugar, decidir si se puede obtener `llave_salida` y llegar a la salida por una puerta que la pide, con las llaves de `/llaves`. Obtener una llave puede abrir una región entera: repetir el recorrido por cada llave no cumple. Si no es resoluble, el reporte necesita la frontera bloqueada y las dependencias entre llaves, y tienen que salir del mismo recorrido. El ciclo se reporta de forma determinista.

### Alternativas consideradas

1. **Repetir el recorrido por llave** (`bench/resolubilidad_repetida.py`): un BFS con las llaves actuales; si encontró llaves nuevas, otro desde cero. O(L·(V + E)).
2. **Recorrido incremental con puertas pendientes por llave** (elegido).

### Decisión

`VerificadorResolubilidad` (`modelo/verificador_resolubilidad.py`) hace un solo BFS con la `Fila` circular propia. Una salida cerrada cuya llave no se tiene queda en `pendientes[llave]`. Al obtener una llave se recorre su lista una vez y se encolan los destinos, y la lista queda vacía. Respuesta a la pregunta de §8: las puertas que el recorrido encontró cerradas antes de tener la llave están anotadas en la lista de esa llave, así que al obtenerla se liberan de una vez, sin volver a recorrer lo ya alcanzado.

Si no es resoluble, el mismo recorrido sigue por detrás de la frontera, por capas según cuántas puertas cerradas se cruzan (0-1 BFS con dos `Fila`). Cada sala guarda la última puerta cerrada de su camino y cada puerta la anterior, así que las dependencias de una llave son las llaves de esa cadena. Un DFS iterativo con `Pila`, en orden de id, encuentra el primer ciclo. En cripta-05, la cripta sellada, informa `llave hierro → llave negra → llave hierro` con las dos puertas involucradas.

El orden de las llaves es determinista: el BFS sigue N, S, E, O, y las llaves de una misma sala se toman en orden de id.

**¿Coincide con el plan?** Sí.

### Análisis de complejidad

O(V + E + L log L): indexar las llaves (ordenadas con el merge sort propio), un recorrido y cada puerta pendiente liberada una vez. El reporte de una cripta no resoluble agrega otro O(V + E) y O(L + dependencias) para el ciclo.

### Evidencia empírica

Criptas publicadas (ms, solo el verificador; entre paréntesis, con la lectura de los archivos):

| Cripta | Salas | Salidas | Llaves | Resoluble | ms |
|---|---|---|---|---|---|
| cripta-02 | 20 | 40 | 2 | sí | 0,08 (0,7) |
| cripta-03 | 40 | 80 | 3 | sí | 0,13 (1,0) |
| cripta-04 | 50 | 100 | 3 | sí | 0,15 (1,2) |
| cripta-05 | 24 | 48 | 3 | no | 0,11 (0,9) |
| cripta-06 | 300 | 760 | 4 | sí | 1,23 (9,2) |

Llaves encadenadas: tramos de 6 salas, cada tramo detrás de una puerta que pide la llave que está al principio del anterior, más un desvío por sala para que el mapa sea ancho (ms):

| Llaves | Salas | Salidas | Incremental | Repetido por llave | Recorridos del repetido | Repetido / incremental |
|---|---|---|---|---|---|---|
| 50 | 601 | 1199 | 2,6 | 30,2 | 51 | 12 |
| 200 | 2401 | 4799 | 13,2 | 567,0 | 201 | 43 |
| 500 | 6001 | 11999 | 45,9 | 3896,4 | 501 | 85 |

El incremental crece como el tamaño de la cripta (de 4799 a 11999 salidas, 2,5 veces más, el tiempo crece 3,5 veces). El repetido crece como llaves × tamaño. La cripta publicada más grande se verifica en 1,2 ms, muy por debajo de los 200 ms.

### Límites conocidos

Las dependencias del reporte siguen una sola ruta por llave, la que cruza menos puertas cerradas. Si una llave se puede alcanzar por dos rutas que piden llaves distintas, el reporte muestra una de las dos. El ciclo informado es real sobre esa ruta, pero puede no ser el único. Lo dejamos escrito en la aclaración de la especificación.

---

## P2 5.5 Línea de tiempo y puntos de control

Especificación: [specs/004-linea-de-tiempo/spec.md](specs/004-linea-de-tiempo/spec.md) · Plan: [plan.md](specs/004-linea-de-tiempo/plan.md) · Análisis: [analisis.md](specs/004-linea-de-tiempo/analisis.md)

### Problema

Consultar el estado en cualquier instante desde el inicio sin tocar la partida: como mucho una copia completa cada K acciones, una consulta no puede re-aplicar ni deshacer más de K acciones, y fuera de las copias solo se guarda lo necesario para reconstruir. 50 ms por consulta con 5000 acciones y el K por defecto. El pergamino recorta la línea sin recorrer toda la historia.

### Alternativas consideradas

1. **Hacia atrás**, invirtiendo cambios desde el estado actual con el historial de la primera parte. Las funciones del historial apuntan a los objetos vivos: para no tocar la partida habría que copiar el estado actual en cada consulta y volver a enlazar cada cambio a la copia. Además, consultar el principio de una partida de 5000 acciones invertiría 5000 acciones, salvo que también hubiera puntos de control.
2. **Hacia adelante desde un punto de control**, re-simulando (elegida).
3. **Sin puntos de control**: re-simular desde el inicio en cada consulta (se mide).

### Decisión

`LineaTiempo` (`modelo/linea_tiempo.py`) anota cada operación que cambia la partida: acciones del jugador con su argumento, cada avance del reloj, cada llegada de contenido (el DTO, compartido con la partida) y cada movimiento del cursor. Cada K acciones guarda un `PuntoDeControl`: una copia completa justo antes de la acción, incluido el `random.Random`. Para consultar se copia el punto anterior más cercano y se re-aplican a lo sumo K acciones con el mismo motor del juego.

- **Ubicar el punto**: el de la acción k está en la posición ⌊(k−1)/K⌋ de la lista, O(1). Para un instante t, búsqueda binaria propia sobre los tiempos de decisión (no se usa `bisect`).
- **Estado en t**: se re-simula hasta la última decisión ≤ t; si t no es esa decisión, se hace la acción y luego solo los eventos con tiempo ≤ t (`avanzar_hasta_tiempo`). Si varios eventos ocurren en t, se ven todos.
- **Pergamino**: se quitan de la cola las operaciones de la acción revertida (se conserva la llegada de contenido, que el pergamino no deshace), su tiempo de decisión y el punto de control tomado al iniciarla. Cuesta O(operaciones de esa acción). Para que la línea y el pergamino coincidan, el cursor del inventario pasó a anotarse en el historial (supuesto de la especificación).
- **Copia**: `EstadoPartida.copiar()` usa `deepcopy` con copias propias donde importa. El grafo, las salas y la caché del catálogo se comparten (`__deepcopy__` devuelve el mismo objeto); `Puerta` y `Evento` usan `__slots__` y copia directa; la agenda copia solo los eventos vigentes; el rastro copia solo los tiempos (la vecindad enlazada es un atajo que se rearma, y copiarla recursaba hasta el límite de Python en mapas grandes); la copia no lleva historial de retroceso ni cachés de búsqueda.
- **Guardado**: formato 5, con K y las operaciones. Al cargar, la partida se re-simula desde el inicio para rearmar los puntos y el resultado se compara con el estado guardado. Si no coincide (por ejemplo, porque una prueba tocó la vida a mano), se carga el estado y la línea empieza de nuevo desde ese punto, con un aviso. Los formatos 3 (primera parte) y 4 se rechazan con un mensaje.

**¿Coincide con el plan?** Sí en el método. Lo que cambió fue por medir: la primera copia de la cripta de referencia tardaba 17,1 ms y ocupaba unos 340 KB. Con las copias propias bajó a 4,6 ms y unos 220 KB. Al medir en una cuadrícula grande apareció el problema de recursión del rastro. El K por defecto (10) salió de la tabla de abajo.

### Análisis de complejidad

| Operación | Costo |
|---|---|
| Anotar una operación | O(1) |
| Punto de control | O(tamaño del estado), una vez cada K acciones |
| `historia #k` | O(1) ubicar + copia + ≤ K acciones re-simuladas |
| `historia t` | O(log n) ubicar + lo anterior |
| Pergamino | O(operaciones de la acción revertida) |
| Memoria | O(operaciones) + ⌈n/K⌉ copias |

### Evidencia empírica

Cripta de referencia con **todo** su contenido cargado y sus 75 enemigos activos (el peor caso: en una partida real solo actúan los que el jugador despertó), 5000 acciones del jugador, 40 consultas repartidas por número de acción y por instante:

| K | Puntos | Operaciones | Memoria | Consulta promedio | p95 | Máximo | ¿Cumple 50 ms (p95)? |
|---|---|---|---|---|---|---|---|
| **10** | 500 | 10000 | **97 MB** | **10,2 ms** | **16,7 ms** | **23,7 ms** | **sí** |
| 15 | 334 | 10000 | 65 MB | 14,4 ms | 23,4 ms | 103,4 ms | sí |
| 20 | 250 | 10000 | 49 MB | 17,9 ms | 27,0 ms | 92,4 ms | sí |
| 25 | 200 | 10000 | 40 MB | 18,3 ms | 33,8 ms | 56,1 ms | sí |
| 50 | 100 | 10000 | 21 MB | 33,9 ms | 56,9 ms | 62,2 ms | no |
| 200 | 25 | 10000 | 6,4 MB | 120,5 ms | 216,6 ms | 299,0 ms | no |
| sin puntos | 1 | 10000 | 1,8 MB | 2723 ms | — | 4022 ms | no |

Las filas 15 y 20 son de una corrida aparte con 80 consultas. Un punto de control en esa misma cripta cuesta 4,2 ms de promedio (5,5 ms de máximo), una vez cada K acciones.

**Por qué K = 10.** La memoria baja como 1/K y el tiempo de consulta sube con K (se re-simulan en promedio K/2 acciones). Con K = 25 el p95 quedó bajo 50 ms en la primera medición (33,8 ms), pero en una repetición del bench en otro equipo subió a 107 ms, con máximo de 141 ms. Con K = 10 el máximo quedó bajo 50 ms en todas las corridas (23,7 ms y 19,7 ms), a cambio de duplicar la memoria (unos 100 MB en el peor caso frente a 40 MB). Elegimos K = 10 porque es el único valor que cumple el límite de 50 ms con margen aunque el equipo sea más lento. El máximo no sirve para elegir K: aparecen consultas sueltas de 60 a 100 ms con cualquier K (K = 15 tuvo una de 103 ms), así que no dependen de cuántas acciones se re-simulan. Son pausas del recolector de basura de Python con decenas de MB de copias vivas, el mismo fenómeno que vimos en la sección 5.2 de la primera parte. Respuesta a la pregunta de §8: el punto razonable está donde la consulta más lenta toca el límite, y lo encontramos midiendo esa consulta más lenta para cada K.

### Límites conocidos

- Consultas sueltas pueden pasar los 50 ms por pausas del recolector de basura (ver arriba). El p95 cumple.
- En una cripta sintética más pesada (400 salas, 150 enemigos activos) el p95 con K = 25 es de 70 a 105 ms según la corrida: cada acción re-simulada cuesta más porque actúan más enemigos. Ahí convendría un K menor, y para eso está `--checkpoint-cada`.
- Cargar una partida re-simula todas sus acciones. Con 5000 acciones en el peor caso de la cripta de referencia son unos 15 segundos. La mejora sería guardar también los puntos de control en el archivo.
- La copia usa `copy.deepcopy`, cuyo `memo` interno es un diccionario de la biblioteca estándar. No es un índice del modelo, y las partes que cuentan (ubicar el punto, recortar, re-aplicar) usan estructuras propias.

---

## P2 5.6 Revisión de decisiones de la primera parte

| Decisión de la primera parte | ¿Sigue siendo adecuada? | Antes | Después |
|---|---|---|---|
| Agenda con heap y cancelación perezosa (4.1) | Sí | ver tabla de 4.1 | ver abajo: el ciclo con 36 cazadores en la cripta de referencia sigue muy por debajo de 20 ms |
| Historial de retroceso como lista de pilas (4.6) | Sí, ampliado | anotaba atributos y funciones | también anota posiciones de lista (mapa conocido) y el cursor del inventario |
| Puertas independientes por lado | Sí, ampliado | estado de la puerta | la puerta avisa al esqueleto cuando cambia (invalidación de rutas) y usa `__slots__` (puntos de control) |
| Rastro con vecindad enlazada (4.7) | Sí | vecinas sin costo | cada vecina guarda el costo de su salida; la copia guarda solo los tiempos |
| Movimiento con costo fijo 100 | **No** | todos los movimientos cuestan 100 | cada movimiento cuesta lo que su salida, también para errantes y rastreadores |
| Guardado binario versión 3 (4.10) | Sí, con versión nueva | versión 3 | versión 4 (mapa conocido) y 5 (línea de tiempo); las anteriores se rechazan |
| Precarga por BFS del esqueleto (4.2) | Sí, sin cambios | — | sigue usando el esqueleto completo: es infraestructura, no conocimiento del jugador (FR-105) |

Ciclo completo entre dos decisiones del jugador, repetido con la carga nueva (ms, límite 20):

| Escenario | Promedio | p95 | Máximo | Eventos por ciclo | ¿Cumple? |
|---|---|---|---|---|---|
| Primera parte: cripta-01 con el controlador | 0,03 | 0,04 | 0,09 | 1 | sí |
| cripta-06 con sus 75 enemigos activos, 36 cazadores | 1,21 | 1,66 | 6,23 | 82 | sí |
| cripta-06, el jugador moviéndose en cada ciclo | 1,89 | 4,16 | 16,52 | 120 | sí |
| 900 salas, 900 enemigos (como en la primera parte) | 12,87 | 19,28 | 43,46 | 1086 | p95 sí |
| 900 salas, 60 cazadores de rango 2400, costos variados | 12,77 | 18,41 | 45,70 | 1020 | p95 sí |

Las dos filas de cripta-06 incluyen la línea de tiempo activa (el controlador la lleva siempre), con sus puntos de control cada 25 acciones.

Agenda (sacar el siguiente y reprogramarlo, µs por operación), repetida: con 3000 eventos el heap tarda 3,41 µs y la lista 534,38 (157 veces más), igual que en la primera parte. Historial de retroceso, repetido: 737 µs por acción y 233 µs por deshacer con 100 enemigos (antes 704 y 225).

Con la carga nueva, el heap y el historial siguen siendo la decisión correcta: el ciclo de la cripta de referencia con todos sus cazadores activos y moviéndose cabe con amplitud en 20 ms. El costo por evento sigue en 8 a 16 µs, como en la primera parte, así que los cazadores no cambiaron la escala del problema. Su costo extra es el cálculo compartido, que se hace una vez por movimiento del jugador.