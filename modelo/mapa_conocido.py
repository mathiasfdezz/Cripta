DESCONOCIDA = 0
AVISTADA = 1
EXPLORADA = 2

SIN_OBSERVAR = -1
ABIERTA = 0
CERRADA = 1


class MapaConocido:
    """Lo que el jugador sabe de la cripta (niebla de guerra).

    Una posición por sala y otra por salida, con los índices densos de GrafoCripta:
    preguntar por una sala o por una puerta recordada es O(1) y explorar una sala
    cuesta lo que tienen sus salidas, no lo que mide el mapa conocido.

    Cada cambio se anota en el historial como (lista, posición, valor anterior), así
    el pergamino lo revierte sin copiar el mapa. 'registrar' es
    Historial.registrar_elemento."""

    def __init__(self, grafo, registrar=None):
        self._grafo = grafo
        self.registrar = registrar
        self.estado = [DESCONOCIDA] * grafo.cantidad_salas()
        self.recuerdo = [SIN_OBSERVAR] * grafo.cantidad_salidas()

    # ------------------------------------------------------------ consultas

    def estado_de(self, id_sala):
        indice = self._grafo.indice(id_sala)
        return DESCONOCIDA if indice is None else self.estado[indice]

    def esta_explorada(self, indice):
        return self.estado[indice] == EXPLORADA

    def recuerda_abierta(self, salida):
        return self.recuerdo[salida] == ABIERTA

    def recuerdo_de(self, salida):
        return self.recuerdo[salida]

    def salas_exploradas(self):
        """Ids de las salas exploradas, en orden creciente."""
        ids = self._grafo.ids
        return [ids[i] for i, valor in enumerate(self.estado) if valor == EXPLORADA]

    def salas_avistadas(self):
        ids = self._grafo.ids
        return [ids[i] for i, valor in enumerate(self.estado) if valor == AVISTADA]

    # ------------------------------------------------------------ cambios

    def explorar(self, indice, esta_cerrada):
        """La sala queda explorada; se observan todas sus salidas y sus destinos
        desconocidos pasan a avistados. esta_cerrada(salida) da el estado real."""
        self._poner(self.estado, indice, EXPLORADA)
        for destino, _, salida in self._grafo.salientes[indice]:
            self._poner(self.recuerdo, salida, CERRADA if esta_cerrada(salida) else ABIERTA)
            if self.estado[destino] == DESCONOCIDA:
                self._poner(self.estado, destino, AVISTADA)

    def observar_sala(self, indice, esta_cerrada):
        """El jugador está en esta sala: ve sus salidas y las que llegan a ella."""
        for _, _, salida in self._grafo.salientes[indice]:
            self._poner(self.recuerdo, salida, CERRADA if esta_cerrada(salida) else ABIERTA)
        for _, _, salida in self._grafo.entrantes[indice]:
            self._poner(self.recuerdo, salida, CERRADA if esta_cerrada(salida) else ABIERTA)

    def observar_salida(self, salida, esta_cerrada):
        self._poner(self.recuerdo, salida, CERRADA if esta_cerrada(salida) else ABIERTA)

    def explorar_vecinas(self, indice, esta_cerrada):
        """Antorcha: las vecinas por cualquier salida, abierta o cerrada."""
        for destino, _, _ in self._grafo.salientes[indice]:
            if self.estado[destino] != EXPLORADA:
                self.explorar(destino, esta_cerrada)

    def restaurar(self, estados, recuerdos):
        """Al cargar una partida guardada."""
        if len(estados) != len(self.estado) or len(recuerdos) != len(self.recuerdo):
            raise ValueError("el mapa guardado no corresponde a este esqueleto")
        self.estado = list(estados)
        self.recuerdo = list(recuerdos)

    def _poner(self, lista, posicion, valor):
        anterior = lista[posicion]
        if anterior == valor:
            return
        if self.registrar is not None:
            self.registrar(lista, posicion, anterior)
        lista[posicion] = valor
