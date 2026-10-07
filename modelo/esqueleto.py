from estructuras.vector_ordenado import VectorOrdenado
from modelo.puerta import Puerta


class Esqueleto:
    """Salas y conexiones de la cripta. Indice por id: VectorOrdenado.

    Cada salida tiene su propia Puerta, con el estado que declara el API para ese
    lado: la sala 2 por E y la sala 5 por O son puertas distintas."""

    def __init__(self):
        self._salas = VectorOrdenado()
        self._puertas = VectorOrdenado()   # (sala, direccion) -> Puerta

    def agregar_pagina(self, pagina):
        """Incorpora un PaginaSalas (las salidas ya vienen en orden N, S, E, O)."""
        for sala in pagina.salas:
            es_nueva = self._salas.insertar(sala.id, sala)
            if es_nueva:   # volver a agregar una sala no reinicia sus puertas
                for salida in sala.salidas:
                    self._puertas.insertar((sala.id, salida.direccion), Puerta(salida))

    def obtener(self, id_sala):
        return self._salas.buscar(id_sala)

    def salida(self, id_sala, direccion):
        """La Salida de esa sala en esa direccion, o None si no existe."""
        sala = self.obtener(id_sala)
        if sala is None:
            return None
        for salida in sala.salidas:
            if salida.direccion == direccion:
                return salida
        return None

    def puerta(self, id_sala, direccion):
        """La Puerta de esa salida, o None si no hay salida."""
        return self._puertas.buscar((id_sala, direccion))

    def reiniciar_puertas(self):
        for _, puerta in self._puertas:
            puerta.reiniciar()

    def puede_atravesar(self, id_sala, direccion):
        """True si hay salida en esa direccion y su puerta esta abierta."""
        puerta = self.puerta(id_sala, direccion)
        return puerta is not None and puerta.esta_abierta()
