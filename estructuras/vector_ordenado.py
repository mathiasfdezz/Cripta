class VectorOrdenado:
    def __init__(self):
        self._claves = []
        self._valores = []

    def _indice(self, clave):
        bajo, alto = 0, len(self._claves)
        while bajo < alto:
            medio = (bajo + alto) // 2
            if self._claves[medio] < clave:
                bajo = medio + 1
            else:
                alto = medio
        return bajo

    def _encontrado(self, i, clave):
        return i < len(self._claves) and self._claves[i] == clave

    def buscar(self, clave):
        i = self._indice(clave)
        return self._valores[i] if self._encontrado(i, clave) else None

    def contiene(self, clave):
        return self._encontrado(self._indice(clave), clave)

    def insertar(self, clave, valor):
        i = self._indice(clave)
        if self._encontrado(i, clave):
            self._valores[i] = valor
            return False
        self._claves.append(None)
        self._valores.append(None)
        j = len(self._claves) - 1
        while j > i:
            self._claves[j] = self._claves[j - 1]
            self._valores[j] = self._valores[j - 1]
            j -= 1
        self._claves[i] = clave
        self._valores[i] = valor
        return True

    def eliminar(self, clave):
        i = self._indice(clave)
        if not self._encontrado(i, clave):
            return None
        valor = self._valores[i]
        for j in range(i, len(self._claves) - 1):
            self._claves[j] = self._claves[j + 1]
            self._valores[j] = self._valores[j + 1]
        self._claves.pop()
        self._valores.pop()
        return valor

    def __len__(self):
        return len(self._claves)

    def __iter__(self):
        for i in range(len(self._claves)):
            yield self._claves[i], self._valores[i]