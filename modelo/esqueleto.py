from estructuras.vector_ordenado import VectorOrdenado


class Esqueleto:
    """Salas y conexiones de la cripta. Indice por id: VectorOrdenado."""

    def __init__(self):
        self._salas = VectorOrdenado()

    def agregar_pagina(self, pagina):
        """Incorpora un PaginaSalas (las salidas ya vienen en orden N, S, E, O)."""
        for sala in pagina.salas:
            self._salas.insertar(sala.id, sala)

    def obtener(self, id_sala):
        return self._salas.buscar(id_sala)

    def __len__(self):
        return len(self._salas)
