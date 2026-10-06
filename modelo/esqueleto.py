from estructuras.vector_ordenado import VectorOrdenado
from modelo.puerta import OPUESTA, Puerta


class Esqueleto:
    """Salas y conexiones de la cripta. Indice por id: VectorOrdenado.

    Cada conexion entre dos salas es una sola Puerta compartida: la sala 2 por
    E y la sala 5 por O usan el mismo objeto, asi que su estado es el mismo
    desde ambos lados. (Salida.cerrada es solo lo que declaro el API.)"""

    def __init__(self):
        self._salas = VectorOrdenado()
        self._puertas = VectorOrdenado()   # clave de la conexion -> Puerta

    def agregar_pagina(self, pagina):
        """Incorpora un PaginaSalas (las salidas ya vienen en orden N, S, E, O).
        Las dos salas de una puerta pueden venir en paginas distintas."""
        for sala in pagina.salas:
            es_nueva = self._salas.insertar(sala.id, sala)
            if es_nueva:   # volver a agregar una sala no reinicia sus puertas
                for salida in sala.salidas:
                    self._puerta_de(sala.id, salida).incorporar(sala.id, salida)

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
        """La Puerta compartida de esa salida, o None si no hay salida."""
        salida = self.salida(id_sala, direccion)
        if salida is None:
            return None
        return self._puertas.buscar(self._clave(id_sala, salida))

    def puede_atravesar(self, id_sala, direccion):
        """True si hay salida en esa direccion y su puerta esta abierta."""
        puerta = self.puerta(id_sala, direccion)
        return puerta is not None and puerta.esta_abierta()

    def _puerta_de(self, id_sala, salida):
        clave = self._clave(id_sala, salida)
        puerta = self._puertas.buscar(clave)
        if puerta is None:
            puerta = Puerta()
            self._puertas.insertar(clave, puerta)
        return puerta

    @staticmethod
    def _clave(id_sala, salida):
        # los dos lados de una conexion: (sala, direccion) y (destino, direccion opuesta);
        # ordenados, ambos lados dan la misma clave
        lado = (id_sala, salida.direccion)
        otro = (salida.sala_destino, OPUESTA.get(salida.direccion, salida.direccion))
        return (lado, otro) if lado <= otro else (otro, lado)