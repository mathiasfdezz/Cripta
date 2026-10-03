class Fila:
    def __init__(self, capacidad=None, sobrescribir=False):
        if capacidad is not None and capacidad < 1:
            raise ValueError("capacidad debe ser >= 1")
        self.capacidad = capacidad
        self.sobrescribir = sobrescribir
        self._datos = [None] * (capacidad if capacidad is not None else 8)
        self._inicio = 0
        self._tamano = 0

    def esta_vacia(self):
        return self._tamano == 0

    def encolar(self, dato):
        n = len(self._datos)
        if self._tamano == n:
            if self.capacidad is None:
                self._crecer()
                n = len(self._datos)
            elif self.sobrescribir:
                self._datos[self._inicio] = dato
                self._inicio = (self._inicio + 1) % n
                return
            else:
                raise OverflowError("fila llena")
        self._datos[(self._inicio + self._tamano) % n] = dato
        self._tamano += 1

    def desencolar(self):
        if self._tamano == 0:
            return None
        dato = self._datos[self._inicio]
        self._datos[self._inicio] = None
        self._inicio = (self._inicio + 1) % len(self._datos)
        self._tamano -= 1
        return dato

    def frente(self):
        return None if self._tamano == 0 else self._datos[self._inicio]

    def _crecer(self):
        n = len(self._datos)
        nuevos = [None] * (n * 2)
        for i in range(self._tamano):
            nuevos[i] = self._datos[(self._inicio + i) % n]
        self._datos = nuevos
        self._inicio = 0

    def __len__(self):
        return self._tamano

    def __iter__(self):
        """Del mas antiguo al mas reciente."""
        n = len(self._datos)
        for i in range(self._tamano):
            yield self._datos[(self._inicio + i) % n]
