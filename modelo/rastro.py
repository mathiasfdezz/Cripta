from estructuras.vector_ordenado import VectorOrdenado

ANTIGUEDAD_MAXIMA = 400   # un rastro de 400 o más ya no sirve


class _RegistroSala:
    def __init__(self, id_sala):
        self.id = id_sala
        self.tiempo = None    # última vez que el jugador estuvo aquí
        self.vecinos = None   # [(direccion, puerta, registro_destino)], se enlaza al primer uso


class Rastro:
    """Rastro del jugador por sala y vecindad enlazada de cada sala.

    La primera vez que se consulta una sala se enlazan sus vecinas (una búsqueda
    por salida). Desde ahí, decidir a dónde va un enemigo recorre solo las
    salidas de su sala: no depende del tamaño de la cripta."""

    def __init__(self, esqueleto):
        self._esqueleto = esqueleto
        self._salas = VectorOrdenado()   # id de sala -> _RegistroSala

    def marcar(self, id_sala, tiempo):
        self._registro(id_sala).tiempo = tiempo

    def tiempo_en(self, id_sala):
        registro = self._salas.buscar(id_sala)
        return None if registro is None else registro.tiempo

    def salidas_abiertas(self, id_sala):
        """Salas vecinas a las que se puede pasar ahora, en orden N, S, E, O."""
        return [destino.id for _, puerta, destino in self._vecinos(id_sala)
                if puerta.esta_abierta()]

    def sala_mas_fresca(self, id_sala, ahora):
        """Vecina por salida abierta con el rastro más reciente y de menos de 400
        unidades. Si dos empatan gana el menor id. None si ninguna sirve."""
        mejor = None
        for _, puerta, destino in self._vecinos(id_sala):
            if not puerta.esta_abierta() or destino.tiempo is None:
                continue
            # la caducidad se detecta al consultar, no se borra nada
            if ahora - destino.tiempo >= ANTIGUEDAD_MAXIMA:
                continue
            if (mejor is None or destino.tiempo > mejor.tiempo
                    or (destino.tiempo == mejor.tiempo and destino.id < mejor.id)):
                mejor = destino
        return None if mejor is None else mejor.id

    def _registro(self, id_sala):
        registro = self._salas.buscar(id_sala)
        if registro is None:
            registro = _RegistroSala(id_sala)
            self._salas.insertar(id_sala, registro)
        return registro

    def _vecinos(self, id_sala):
        registro = self._registro(id_sala)
        if registro.vecinos is None:
            registro.vecinos = []
            sala = self._esqueleto.obtener(id_sala)
            for salida in (() if sala is None else sala.salidas):
                # hacia una sala que no está en el mapa no se puede pasar
                if self._esqueleto.obtener(salida.sala_destino) is None:
                    continue
                registro.vecinos.append((salida.direccion,
                                         self._esqueleto.puerta(id_sala, salida.direccion),
                                         self._registro(salida.sala_destino)))
        return registro.vecinos