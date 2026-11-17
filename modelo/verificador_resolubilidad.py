from estructuras.fila import Fila
from estructuras.ordenamientos import ordenar
from estructuras.pila import Pila
from estructuras.vector_ordenado import VectorOrdenado
from modelo.puerta_bloqueada import PuertaBloqueada
from modelo.reporte_resolubilidad import ReporteResolubilidad

SIN_PUERTA = -1


class VerificadorResolubilidad:
    """Decide si una cripta se puede ganar (§3.5) con el esqueleto y la ubicación de
    las llaves, antes de jugar.

    Un solo recorrido en anchura desde la sala inicial. Una puerta cerrada cuya llave
    aún no se tiene queda pendiente en la lista de esa llave; al obtener la llave se
    liberan todas sus puertas de una vez. Cada salida se mira una vez y cada puerta
    pendiente se libera una vez: no se repite el recorrido por cada llave (§5.4)."""

    def __init__(self, esqueleto, ubicaciones):
        grafo = esqueleto.grafo()
        self._grafo = grafo
        cantidad = grafo.cantidad_salidas()
        # estado inicial de cada salida, tal como lo declara el API
        self._cerrada = [False] * cantidad
        nombres_de_llave = [None] * cantidad
        for salida, (id_sala, direccion) in enumerate(grafo.salida_de):
            dto = esqueleto.salida(id_sala, direccion)
            if dto.cerrada:
                self._cerrada[salida] = True
                nombres_de_llave[salida] = dto.llave
        # llaves con índice denso: las publicadas y las que piden las puertas, por id
        ubicaciones = ordenar(list(ubicaciones), lambda u: (u.id, u.sala))
        todas = [u.id for u in ubicaciones] + [n for n in nombres_de_llave if n is not None]
        self.ids_llave = []
        for nombre in ordenar(todas, lambda n: n):
            if not self.ids_llave or self.ids_llave[-1] != nombre:
                self.ids_llave.append(nombre)
        self._indice_llave = VectorOrdenado()
        for posicion, nombre in enumerate(self.ids_llave):
            self._indice_llave.insertar(nombre, posicion)   # en orden: no desplaza nada
        self._llave_de = [None if n is None else self._indice_llave.buscar(n)
                          for n in nombres_de_llave]
        self._en_sala = [[] for _ in range(grafo.cantidad_salas())]
        self._ubicaciones_de = [[] for _ in self.ids_llave]
        for ubicacion in ubicaciones:
            llave = self._indice_llave.buscar(ubicacion.id)
            self._ubicaciones_de[llave].append(ubicacion)
            sala = grafo.indice(ubicacion.sala)
            if sala is not None:
                self._en_sala[sala].append(llave)

    def verificar(self, sala_inicial, sala_salida, llave_salida):
        grafo = self._grafo
        alcanzada = [False] * grafo.cantidad_salas()
        tengo = [False] * len(self.ids_llave)
        pendientes = [[] for _ in self.ids_llave]
        sin_llave = []
        orden = []
        fila = Fila()

        def alcanzar(sala):
            if not alcanzada[sala]:
                alcanzada[sala] = True
                fila.encolar(sala)

        inicio = grafo.indice(sala_inicial)
        if inicio is not None:
            alcanzar(inicio)
        cerrada, llave_de = self._cerrada, self._llave_de
        while not fila.esta_vacia():
            sala = fila.desencolar()
            for llave in self._en_sala[sala]:
                if tengo[llave]:
                    continue
                tengo[llave] = True
                orden.append(llave)
                # lo que estaba esperando esta llave se libera de una vez
                for salida in pendientes[llave]:
                    alcanzar(grafo.destino_de_salida[salida])
                pendientes[llave] = []
            for destino, _, salida in grafo.salientes[sala]:
                if alcanzada[destino]:
                    continue
                if not cerrada[salida]:
                    alcanzar(destino)
                elif llave_de[salida] is None:
                    sin_llave.append(salida)
                elif tengo[llave_de[salida]]:
                    alcanzar(destino)
                else:
                    pendientes[llave_de[salida]].append(salida)

        resoluble = self._sale(alcanzada, tengo, sala_salida, llave_salida)
        salas, salidas, llaves = (grafo.cantidad_salas(), grafo.cantidad_salidas(),
                                  len(self.ids_llave))
        nombres = [self.ids_llave[k] for k in orden]
        if resoluble:
            return ReporteResolubilidad(True, nombres, salas=salas, salidas=salidas, llaves=llaves)
        bloqueadas = [s for k in range(len(self.ids_llave)) for s in pendientes[k]
                      if not alcanzada[grafo.destino_de_salida[s]]]
        bloqueadas += [s for s in sin_llave if not alcanzada[grafo.destino_de_salida[s]]]
        bloqueadas = ordenar(bloqueadas, lambda s: s)
        frontera = []
        for salida in bloqueadas:
            if not frontera or frontera[-1] != salida:
                frontera.append(salida)
        dependencias = self._dependencias(alcanzada, tengo, frontera)
        ciclo, puertas = self._ciclo(tengo, dependencias)
        no_obtenibles = [self.ids_llave[k] for k in range(len(tengo)) if not tengo[k]]
        sin_ubicacion = [self.ids_llave[k] for k in range(len(tengo))
                         if not self._ubicaciones_de[k]]
        return ReporteResolubilidad(
            False, nombres, no_obtenibles, [self._puerta(s) for s in frontera],
            [self.ids_llave[k] for k in ciclo], [self._puerta(s) for s in puertas],
            sin_ubicacion, salas=salas, salidas=salidas, llaves=llaves)

    def _sale(self, alcanzada, tengo, sala_salida, llave_salida):
        """FR-203: se tiene llave_salida y una salida cerrada que la pide llega a la salida
        desde una sala alcanzable."""
        grafo = self._grafo
        salida_sala = grafo.indice(sala_salida)
        llave = self._indice_llave.buscar(llave_salida) if llave_salida is not None else None
        if salida_sala is None or llave is None or not tengo[llave]:
            return False
        for origen, _, salida in grafo.entrantes[salida_sala]:
            if alcanzada[origen] and self._cerrada[salida] and self._llave_de[salida] == llave:
                return True
        return False

    def _dependencias(self, alcanzada, tengo, frontera):
        """Sigue el recorrido detrás de la frontera, por capas según cuántas puertas
        cerradas se cruzan (0-1 BFS). Para cada llave no obtenible devuelve las
        (llave, salida) de las puertas cerradas de su camino, de la más cercana a ella
        hacia atrás."""
        grafo = self._grafo
        previa = [SIN_PUERTA] * grafo.cantidad_salas()   # última puerta cerrada del camino
        vista = [False] * grafo.cantidad_salas()
        cerrada, llave_de = self._cerrada, self._llave_de
        siguiente = Fila()
        for salida in frontera:
            if llave_de[salida] is not None:
                siguiente.encolar((grafo.destino_de_salida[salida], salida))
        while not siguiente.esta_vacia():
            actual, siguiente = siguiente, Fila()
            while not actual.esta_vacia():
                sala, puerta = actual.desencolar()
                if vista[sala] or alcanzada[sala]:
                    continue
                vista[sala] = True
                previa[sala] = puerta
                for destino, _, salida in grafo.salientes[sala]:
                    if vista[destino] or alcanzada[destino]:
                        continue
                    llave = llave_de[salida]
                    if not cerrada[salida] or (llave is not None and tengo[llave]):
                        actual.encolar((destino, puerta))       # misma capa
                    elif llave is not None:
                        siguiente.encolar((destino, salida))    # una puerta cerrada más
        dependencias = [[] for _ in self.ids_llave]
        for llave in range(len(self.ids_llave)):
            if tengo[llave]:
                continue
            for ubicacion in self._ubicaciones_de[llave]:
                sala = grafo.indice(ubicacion.sala)
                if sala is None or not vista[sala]:
                    continue
                puerta = previa[sala]
                while puerta != SIN_PUERTA:
                    dependencias[llave].append((llave_de[puerta], puerta))
                    origen = grafo.origen_de_salida[puerta]
                    puerta = previa[origen] if vista[origen] else SIN_PUERTA
                break
        return dependencias

    def _ciclo(self, tengo, dependencias):
        """Primer ciclo llave -> dependencia -> ... -> misma llave, recorriendo las
        llaves no obtenibles por id (DFS iterativo). Devuelve (llaves, puertas)."""
        color = [0] * len(self.ids_llave)    # 0 sin visitar, 1 en el camino, 2 terminada
        for inicio in range(len(self.ids_llave)):
            if tengo[inicio] or color[inicio] != 0:
                continue
            pila = Pila()
            pila.apilar((inicio, 0))
            camino = [inicio]
            puertas = []
            color[inicio] = 1
            while not pila.esta_vacia():
                llave, siguiente = pila.desapilar()
                if siguiente < len(dependencias[llave]):
                    pila.apilar((llave, siguiente + 1))
                    otra, puerta = dependencias[llave][siguiente]
                    if color[otra] == 1:
                        desde = camino.index(otra)
                        return camino[desde:] + [otra], puertas[desde:] + [puerta]
                    if color[otra] == 0:
                        color[otra] = 1
                        pila.apilar((otra, 0))
                        camino.append(otra)
                        puertas.append(puerta)
                else:
                    color[llave] = 2
                    camino.pop()
                    if puertas:
                        puertas.pop()
        return [], []

    def _puerta(self, salida):
        grafo = self._grafo
        id_sala, direccion = grafo.salida_de[salida]
        llave = self._llave_de[salida]
        return PuertaBloqueada(id_sala, direccion, grafo.ids[grafo.destino_de_salida[salida]],
                               None if llave is None else self.ids_llave[llave],
                               () if llave is None else self._ubicaciones_de[llave])
