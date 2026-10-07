from estructuras.ordenamientos import ordenar


class UsoDeFichas:
    """Mantiene al día qué fichas tiene retenidas la caché. Después de cada comando
    recibe las que están en uso y solo retiene o libera la diferencia."""

    def __init__(self, cache):
        self._cache = cache
        self._retenidas = []   # ids distintos, ordenados

    def actualizar(self, ids_en_uso):
        nuevas = _distintos(ids_en_uso)
        # primero se retiene lo nuevo y después se suelta lo viejo: así ninguna
        # ficha que sigue en uso queda un instante sin protección
        for id_ficha in _diferencia(nuevas, self._retenidas):
            if not self._cache.esta_en_memoria(id_ficha):
                self._cache.resolver([id_ficha])
            self._cache.retener(id_ficha)
        for id_ficha in _diferencia(self._retenidas, nuevas):
            self._cache.liberar(id_ficha)
        self._retenidas = nuevas

    def retenidas(self):
        return list(self._retenidas)


def _distintos(ids):
    ordenados = ordenar(list(ids), lambda x: x)
    distintos = []
    for id_ficha in ordenados:
        if not distintos or distintos[-1] != id_ficha:
            distintos.append(id_ficha)
    return distintos


def _diferencia(a, b):
    """Elementos de a que no están en b. Las dos listas vienen ordenadas y sin
    repetidos, así que se recorren juntas una sola vez."""
    resultado = []
    j = 0
    for elemento in a:
        while j < len(b) and b[j] < elemento:
            j += 1
        if j == len(b) or b[j] != elemento:
            resultado.append(elemento)
    return resultado