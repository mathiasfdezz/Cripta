class _Nodo:
    def __init__(self, clave, valor):
        self.clave = clave
        self.valor = valor
        self.izquierdo = None
        self.derecho = None


class ArbolBinario:
    """Alternativa descartada para buscar fichas: árbol binario de búsqueda simple,
    sin balancear (es el que se vio en el curso)."""

    def __init__(self):
        self._raiz = None

    def insertar(self, clave, valor):
        nuevo = _Nodo(clave, valor)
        if self._raiz is None:
            self._raiz = nuevo
            return
        actual = self._raiz
        while True:
            if clave < actual.clave:
                if actual.izquierdo is None:
                    actual.izquierdo = nuevo
                    return
                actual = actual.izquierdo
            elif clave > actual.clave:
                if actual.derecho is None:
                    actual.derecho = nuevo
                    return
                actual = actual.derecho
            else:
                actual.valor = valor
                return

    def buscar(self, clave):
        actual = self._raiz
        while actual is not None:
            if clave == actual.clave:
                return actual.valor
            actual = actual.izquierdo if clave < actual.clave else actual.derecho
        return None

    def altura(self):
        # recorrido por niveles con una lista como fila, sin recursión
        if self._raiz is None:
            return 0
        nivel, altura = [self._raiz], 0
        while nivel:
            altura += 1
            siguiente = []
            for nodo in nivel:
                if nodo.izquierdo is not None:
                    siguiente.append(nodo.izquierdo)
                if nodo.derecho is not None:
                    siguiente.append(nodo.derecho)
            nivel = siguiente
        return altura