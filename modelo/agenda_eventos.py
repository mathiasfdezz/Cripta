from estructuras.min_heap import MinHeap


class AgendaEventos:
    def __init__(self):
        self._heap = MinHeap()
        self._siguiente_secuencia = 1

    def programar(self, tiempo, evento):
        secuencia = self._siguiente_secuencia
        self._siguiente_secuencia += 1
        # la secuencia nunca se repite, así que nunca se llega a comparar el evento
        self._heap.insertar((tiempo, secuencia, evento))
        return secuencia

    def ver_siguiente(self):
        return self._heap.ver_minimo()

    def sacar_siguiente(self):
        return self._heap.extraer_minimo()

    def esta_vacia(self):
        return self._heap.esta_vacio()

    def tamano(self):
        return self._heap.tamano()
