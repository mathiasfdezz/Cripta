from estructuras.vector_ordenado import VectorOrdenado


class GrafoCripta:
    """Las salas con índices densos (0..V-1, en orden de id) y sus salidas numeradas.

    Es estático: solo depende del esqueleto. No guarda puertas, solo el índice de cada
    salida; quien recorre el grafo pregunta por ese índice si se puede pasar. Así las
    copias del estado (puntos de control) pueden compartir el mismo grafo.

    Como los índices siguen el orden de los ids, comparar índices es comparar ids."""

    def __init__(self, salas):
        # salas: las Sala del esqueleto en orden creciente de id
        self.ids = []
        self._indice = VectorOrdenado()
        for sala in salas:
            # llegan ordenadas: cada inserción va al final y no desplaza nada
            self._indice.insertar(sala.id, len(self.ids))
            self.ids.append(sala.id)
        n = len(self.ids)
        self.salientes = [[] for _ in range(n)]   # (destino, costo, salida), en orden N, S, E, O
        self.entrantes = [[] for _ in range(n)]   # (origen, costo, salida)
        self.origen_de_salida = []
        self.destino_de_salida = []
        self.salida_de = []                       # (id de sala, dirección) de cada salida
        for origen, sala in enumerate(salas):
            for salida in sala.salidas:
                destino = self._indice.buscar(salida.sala_destino)
                if destino is None:
                    # hacia una sala que no está en el mapa no se puede pasar
                    continue
                numero = len(self.salida_de)
                self.salida_de.append((sala.id, salida.direccion))
                self.origen_de_salida.append(origen)
                self.destino_de_salida.append(destino)
                self.salientes[origen].append((destino, salida.costo, numero))
                self.entrantes[destino].append((origen, salida.costo, numero))

    def indice(self, id_sala):
        """Índice denso de la sala, o None si no está en el mapa. O(log V)."""
        return self._indice.buscar(id_sala)

    def cantidad_salas(self):
        return len(self.ids)

    def cantidad_salidas(self):
        return len(self.salida_de)
