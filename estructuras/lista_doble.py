class Nodo:

    def __init__(self, dato):
        self.dato = dato
        self.anterior = None
        self.siguiente = None


class ListaDoble:

    def __init__(self):
        self.cabeza = None
        self.cola = None
        self.tamano = 0

    def esta_vacia(self):
        return self.cabeza is None

    def agregar_final(self, dato):
        nuevo = Nodo(dato)

        if self.esta_vacia():
            self.cabeza = nuevo
            self.cola = nuevo
        else:
            nuevo.anterior = self.cola
            self.cola.siguiente = nuevo
            self.cola = nuevo

        self.tamano += 1
        return nuevo

    def agregar_frente(self, dato):
        nuevo = Nodo(dato)

        if self.esta_vacia():
            self.cabeza = nuevo
            self.cola = nuevo
        else:
            nuevo.siguiente = self.cabeza
            self.cabeza.anterior = nuevo
            self.cabeza = nuevo

        self.tamano += 1
        return nuevo

    def insertar_despues(self, referencia, dato):
        if referencia is None:
            return self.agregar_frente(dato)

        nuevo = Nodo(dato)
        nuevo.anterior = referencia
        nuevo.siguiente = referencia.siguiente

        if referencia.siguiente is not None:
            referencia.siguiente.anterior = nuevo
        else:
            self.cola = nuevo

        referencia.siguiente = nuevo
        self.tamano += 1
        return nuevo

    def insertar_antes(self, referencia, dato):
        if referencia is None:
            return self.agregar_final(dato)

        if referencia.anterior is None:
            return self.agregar_frente(dato)

        return self.insertar_despues(referencia.anterior, dato)

    # ---------- eliminacion y reordenamiento (O(1)) ----------

    def eliminar_nodo(self, nodo):
        if nodo is None:
            return None

        if nodo.anterior is not None:
            nodo.anterior.siguiente = nodo.siguiente
        else:
            self.cabeza = nodo.siguiente

        if nodo.siguiente is not None:
            nodo.siguiente.anterior = nodo.anterior
        else:
            self.cola = nodo.anterior

        nodo.anterior = None
        nodo.siguiente = None

        self.tamano -= 1

        return nodo.dato

    def mover_al_frente(self, nodo):
        if nodo is None or self.cabeza is None or nodo is self.cabeza:
            return

        if nodo.anterior is not None:
            nodo.anterior.siguiente = nodo.siguiente

        if nodo.siguiente is not None:
            nodo.siguiente.anterior = nodo.anterior

        if nodo is self.cola:
            self.cola = nodo.anterior

        nodo.anterior = None
        nodo.siguiente = self.cabeza

        self.cabeza.anterior = nodo
        self.cabeza = nodo

    def obtener_primero(self):
        if self.cabeza is None:
            return None
        return self.cabeza.dato

    def obtener_ultimo(self):
        if self.cola is None:
            return None
        return self.cola.dato

    def __len__(self):
        return self.tamano

    def recorrer(self):
        actual = self.cabeza

        while actual is not None:
            yield actual
            actual = actual.siguiente