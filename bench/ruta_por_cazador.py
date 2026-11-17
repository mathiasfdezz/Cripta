from estructuras.min_heap import MinHeap


class RutaPorCazador:
    """Alternativa medida en el bench (no la usa el juego): un Dijkstra hacia adelante
    por cada cazador, cortado en su rango, que se detiene al sacar la sala del jugador.

    Para cumplir el desempate cada sala lleva la menor vecina inicial entre todas
    las rutas mínimas que llegan a ella: con costos >= 1, todas esas rutas pasan por
    salas que salen del heap antes, así que la etiqueta ya es final al sacarla."""

    def __init__(self, grafo, pasable):
        n = grafo.cantidad_salas()
        self._grafo = grafo
        self._pasable = pasable
        self._distancia = [0] * n
        self._primero = [0] * n
        self._vista = [0] * n
        self._asentada = [0] * n
        self._epoca = 0
        self.salas_asentadas = 0

    def decidir(self, desde, objetivo, rango):
        """(sala vecina, costo de la salida) del paso a dar, o None si espera."""
        self._epoca += 1
        epoca = self._epoca
        distancia, primero = self._distancia, self._primero
        vista, asentada = self._vista, self._asentada
        salientes, pasable = self._grafo.salientes, self._pasable
        heap = MinHeap()
        distancia[desde] = 0
        vista[desde] = epoca
        heap.insertar((0, desde))
        while not heap.esta_vacio():
            d, sala = heap.extraer_minimo()
            if asentada[sala] == epoca:
                continue
            if d > rango:
                return None
            asentada[sala] = epoca
            self.salas_asentadas += 1
            if sala == objetivo:
                break
            for destino, costo, salida in salientes[sala]:
                if asentada[destino] == epoca or not pasable(salida):
                    continue
                nueva = d + costo
                etiqueta = destino if sala == desde else primero[sala]
                if vista[destino] != epoca or nueva < distancia[destino]:
                    vista[destino] = epoca
                    distancia[destino] = nueva
                    primero[destino] = etiqueta
                    heap.insertar((nueva, destino))
                elif nueva == distancia[destino] and etiqueta < primero[destino]:
                    primero[destino] = etiqueta
        if asentada[objetivo] != epoca or desde == objetivo:
            return None
        paso = primero[objetivo]
        for destino, costo, salida in salientes[desde]:
            if destino == paso and pasable(salida):
                return destino, costo
        return None
