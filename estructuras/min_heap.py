class MinHeap:
    def __init__(self):
        self._datos = []

    def tamano(self):
        return len(self._datos)

    def esta_vacio(self):
        return len(self._datos) == 0

    def minimo_o_nada(self):
        """Como ver_minimo, pero devuelve None si está vacío (sin lanzar error)."""
        return self._datos[0] if self._datos else None

    def ver_minimo(self):
        if self.esta_vacio():
            raise IndexError("el heap está vacío")
        return self._datos[0]

    def insertar(self, elemento):
        self._datos.append(elemento)
        self._subir(len(self._datos) - 1)

    def extraer_minimo(self):
        if self.esta_vacio():
            raise IndexError("el heap está vacío")
        minimo = self._datos[0]
        ultimo = self._datos.pop()
        if not self.esta_vacio():
            self._datos[0] = ultimo
            self._bajar(0)
        return minimo

    # subir y bajar mueven un "hueco" en lugar de intercambiar en cada nivel:
    # el elemento se escribe una sola vez, al llegar a su lugar

    def _subir(self, i):
        datos = self._datos
        elemento = datos[i]
        while i > 0:
            padre = (i - 1) // 2
            if elemento < datos[padre]:
                datos[i] = datos[padre]
                i = padre
            else:
                break
        datos[i] = elemento

    def _bajar(self, i):
        datos = self._datos
        n = len(datos)
        elemento = datos[i]
        while True:
            hijo = 2 * i + 1
            if hijo >= n:
                break
            derecho = hijo + 1
            if derecho < n and datos[derecho] < datos[hijo]:
                hijo = derecho
            if datos[hijo] < elemento:
                datos[i] = datos[hijo]
                i = hijo
            else:
                break
        datos[i] = elemento