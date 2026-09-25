class MinHeap:
    def __init__(self):
        self._datos = []

    def tamano(self):
        return len(self._datos)

    def esta_vacio(self):
        return len(self._datos) == 0

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

    def _subir(self, i):
        while i > 0:
            padre = (i - 1) // 2
            if self._datos[i] < self._datos[padre]:
                self._datos[i], self._datos[padre] = self._datos[padre], self._datos[i]
                i = padre
            else:
                break

    def _bajar(self, i):
        n = len(self._datos)
        while True:
            izq = 2 * i + 1
            der = 2 * i + 2
            menor = i
            if izq < n and self._datos[izq] < self._datos[menor]:
                menor = izq
            if der < n and self._datos[der] < self._datos[menor]:
                menor = der
            if menor == i:
                break
            self._datos[i], self._datos[menor] = self._datos[menor], self._datos[i]
            i = menor
