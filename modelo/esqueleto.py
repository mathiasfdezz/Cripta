from copy import deepcopy

from estructuras.vector_ordenado import VectorOrdenado
from modelo.grafo_cripta import GrafoCripta
from modelo.puerta import Puerta

# más cambios de puertas sin consultar que esto: se da todo por cambiado
MAX_CAMBIOS_ANOTADOS = 64


class Esqueleto:
    """Salas y conexiones de la cripta. Indice por id: VectorOrdenado.

    Cada salida tiene su propia Puerta, con el estado que declara el API para ese
    lado: la sala 2 por E y la sala 5 por O son puertas distintas."""

    def __init__(self):
        self._salas = VectorOrdenado()
        self._puertas = VectorOrdenado()   # (sala, direccion) -> Puerta
        self._grafo = None
        self._puertas_por_salida = []      # índice de salida del grafo -> Puerta
        self._cambios = []                 # salidas cuya puerta cambió desde la última consulta
        self._desbordado = False

    def __deepcopy__(self, memo):
        """Las salas y el grafo no cambian: se comparten. Las puertas sí: se copian."""
        copia = Esqueleto.__new__(Esqueleto)
        memo[id(self)] = copia
        copia._salas = self._salas
        copia._grafo = self._grafo
        copia._puertas = VectorOrdenado()
        for clave, puerta in self._puertas:
            copia._puertas.insertar(clave, deepcopy(puerta, memo))
        copia._puertas_por_salida = [deepcopy(p, memo) for p in self._puertas_por_salida]
        copia._cambios = list(self._cambios)
        copia._desbordado = self._desbordado
        return copia

    def agregar_pagina(self, pagina):
        """Incorpora un PaginaSalas (las salidas ya vienen en orden N, S, E, O)."""
        for sala in pagina.salas:
            es_nueva = self._salas.insertar(sala.id, sala)
            if es_nueva:   # volver a agregar una sala no reinicia sus puertas
                for salida in sala.salidas:
                    self._puertas.insertar((sala.id, salida.direccion), Puerta(salida))
                self._grafo = None

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

    # --------------------------------------------------------- grafo y rutas

    def grafo(self):
        """El GrafoCripta de las salas cargadas. Se arma una vez, en O(V + E)."""
        if self._grafo is None:
            self._grafo = GrafoCripta([sala for _, sala in self._salas])
            self._puertas_por_salida = []
            for id_sala, direccion in self._grafo.salida_de:
                puerta = self.puerta(id_sala, direccion)
                puerta.indice = len(self._puertas_por_salida)
                puerta.al_cambiar = self._anotar_cambio
                self._puertas_por_salida.append(puerta)
            self._cambios = []
            self._desbordado = False
        return self._grafo

    def puerta_de_salida(self, indice):
        return self._puertas_por_salida[indice]

    def salida_abierta(self, indice):
        return not self._puertas_por_salida[indice].cerrada

    def salida_cerrada(self, indice):
        return self._puertas_por_salida[indice].cerrada

    def tomar_cambios(self):
        """(salidas cuya puerta cambió, desbordado) desde la última llamada. Si
        desbordado es True se anotaron demasiados y hay que suponer que cambió todo."""
        cambios, desbordado = self._cambios, self._desbordado
        self._cambios = []
        self._desbordado = False
        return cambios, desbordado

    def _anotar_cambio(self, indice):
        if self._desbordado or indice is None:
            return
        if len(self._cambios) >= MAX_CAMBIOS_ANOTADOS:
            self._cambios = []
            self._desbordado = True
            return
        self._cambios.append(indice)
