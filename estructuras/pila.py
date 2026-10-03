class Pila:
    def __init__(self):
        self._datos = []

    def esta_vacia(self):
        return len(self._datos) == 0

    def apilar(self, dato):
        self._datos.append(dato)

    def desapilar(self):
        return None if not self._datos else self._datos.pop()

    def tope(self):
        return None if not self._datos else self._datos[-1]

    def __len__(self):
        return len(self._datos)