from estructuras.min_heap import MinHeap


class BuscadorRutas:
    """Costo mínimo de llegar desde cada sala hasta una sala objetivo.

    Es Dijkstra al revés: parte del objetivo y avanza por las salidas que ENTRAN a
    cada sala, así un solo cálculo sirve a todos los que persiguen al mismo objetivo.
    Se detiene al pasar la cota: lo que queda más lejos no se visita.

    Las listas tienen una posición por sala y una época: una posición solo vale si
    su época es la del cálculo actual, así no hay que limpiar V posiciones cada vez.

    pasable(salida) dice si hoy se puede atravesar esa salida; admitida(sala), si la
    búsqueda puede usar esa sala (None = todas). Deben ser métodos de objetos del
    estado y no funciones sueltas: así una copia del estado sigue funcionando."""

    def __init__(self, grafo, pasable, admitida=None):
        n = grafo.cantidad_salas()
        self._grafo = grafo
        self._pasable = pasable
        self._admitida = admitida
        self._distancia = [0] * n
        self._vista = [0] * n       # época en que se le puso una distancia provisional
        self._asentada = [0] * n    # época en que su distancia quedó definitiva
        self._epoca = 0
        self.objetivo = None
        self.cota = None
        # para el bench
        self.calculos = 0
        self.reutilizados = 0
        self.salas_asentadas = 0

    def calcular(self, objetivo, cota):
        """Distancias exactas hasta 'objetivo' (índice denso) de todas las salas que
        están a lo sumo a 'cota'. O(R + E_R log R), R = salas dentro de la cota."""
        self._epoca += 1
        epoca = self._epoca
        distancia, vista, asentada = self._distancia, self._vista, self._asentada
        entrantes = self._grafo.entrantes
        pasable, admitida = self._pasable, self._admitida
        self.objetivo = objetivo
        self.cota = cota
        self.calculos += 1
        heap = MinHeap()
        distancia[objetivo] = 0
        vista[objetivo] = epoca
        heap.insertar((0, objetivo))
        while not heap.esta_vacio():
            d, sala = heap.extraer_minimo()
            if asentada[sala] == epoca:
                continue   # entrada vieja: ya salió con una distancia menor
            if d > cota:
                break
            asentada[sala] = epoca
            self.salas_asentadas += 1
            for origen, costo, salida in entrantes[sala]:
                if asentada[origen] == epoca or not pasable(salida):
                    continue
                if admitida is not None and not admitida(origen):
                    continue
                nueva = d + costo
                if vista[origen] != epoca or nueva < distancia[origen]:
                    vista[origen] = epoca
                    distancia[origen] = nueva
                    heap.insertar((nueva, origen))

    def asegurar(self, objetivo, cota, salidas_cambiadas=(), desbordado=False):
        """Recalcula solo si el resultado anterior pudo cambiar; True si recalculó.

        Basta con mirar las salidas cambiadas que entran a una sala asentada: una ruta
        que pasa por una sala no asentada cuesta más que la cota y no cambia ninguna
        distancia dentro de ella, esté su puerta abierta o cerrada."""
        if (not desbordado and self.objetivo == objetivo and self.cota is not None
                and self.cota >= cota):
            destino_de = self._grafo.destino_de_salida
            asentada, epoca = self._asentada, self._epoca
            if not any(asentada[destino_de[s]] == epoca for s in salidas_cambiadas):
                self.reutilizados += 1
                return False
        self.calcular(objetivo, cota)
        return True

    def distancia(self, sala):
        """Costo mínimo desde 'sala' hasta el objetivo, o None si pasa de la cota o no
        hay ruta."""
        return self._distancia[sala] if self._asentada[sala] == self._epoca else None

    def primer_paso(self, desde, d):
        """(sala vecina, costo, índice de la salida) del primer paso de una ruta de
        costo d. Entre varias vecinas posibles, la de menor id (= menor índice)."""
        mejor = None
        for destino, costo, salida in self._grafo.salientes[desde]:
            if mejor is not None and destino >= mejor[0]:
                continue
            if not self._pasable(salida):
                continue
            if self._admitida is not None and not self._admitida(destino):
                continue
            resto = self.distancia(destino)
            if resto is not None and costo + resto == d:
                mejor = (destino, costo, salida)
        return mejor
