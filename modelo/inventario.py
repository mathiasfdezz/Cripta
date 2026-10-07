from estructuras.lista_doble import ListaDoble
from estructuras.ordenamientos import ordenar


CLASE_ARMA = "arma"
CLASE_ARMADURA = "armadura"
CLASE_PERGAMINO = "pergamino_retroceso"


CLASES_CONSUMIBLES = ("pocion", "antidoto", "antorcha", CLASE_PERGAMINO)


class Inventario:

    def __init__(self, capacidad):
        if capacidad < 0:
            raise ValueError("capacidad no puede ser negativa")
        self.capacidad = capacidad
        self.lista = ListaDoble()
        self.actual = None
        self._nodo_arma = None
        self._nodo_armadura = None


    def esta_lleno(self):
        return len(self.lista) >= self.capacidad

    def esta_vacio(self):
        return self.lista.esta_vacia()

    def __len__(self):
        return len(self.lista)


    def recoger(self, objeto):
        if self.esta_lleno():
            return False

        nodo = self.lista.agregar_final(objeto)

        if self.actual is None:
            self.actual = nodo

        return True

    def avanzar(self):
        if self.actual is None:
            return None

        if self.actual.siguiente is not None:
            self.actual = self.actual.siguiente

        return self.actual.dato

    def retroceder(self):
        if self.actual is None:
            return None

        if self.actual.anterior is not None:
            self.actual = self.actual.anterior

        return self.actual.dato

    def obtener_actual(self):
        if self.actual is None:
            return None
        return self.actual.dato

    def _quitar_nodo(self, nodo):
        if nodo is self._nodo_arma:
            self._nodo_arma = None
        if nodo is self._nodo_armadura:
            self._nodo_armadura = None

        if nodo is self.actual:
            if nodo.siguiente is not None:
                self.actual = nodo.siguiente
            else:
                self.actual = nodo.anterior

        return self.lista.eliminar_nodo(nodo)

    def soltar_actual(self):
        if self.actual is None:
            return None
        return self._quitar_nodo(self.actual)

    def puede_equipar_actual(self):
        if self.actual is None:
            return False
        return self.actual.dato.clase in (CLASE_ARMA, CLASE_ARMADURA)

    def equipar_actual(self):
        if not self.puede_equipar_actual():
            return None

        nodo = self.actual

        if nodo.dato.clase == CLASE_ARMA:
            self._nodo_arma = nodo
        else:
            self._nodo_armadura = nodo

        self.lista.mover_al_frente(nodo)

        return nodo.dato

    def marcar_equipado(self, nodo):
        # al cargar una partida: el orden ya viene guardado, solo se recuerda qué estaba equipado
        if nodo.dato.clase == CLASE_ARMA:
            self._nodo_arma = nodo
        elif nodo.dato.clase == CLASE_ARMADURA:
            self._nodo_armadura = nodo

    def arma_equipada(self):
        return None if self._nodo_arma is None else self._nodo_arma.dato

    def armadura_equipada(self):
        return None if self._nodo_armadura is None else self._nodo_armadura.dato

    def bonus_ataque(self):
        arma = self.arma_equipada()
        return 0 if arma is None else getattr(arma, "ataque_bonus", 0)

    def bonus_defensa(self):
        armadura = self.armadura_equipada()
        return 0 if armadura is None else getattr(armadura, "defensa_bonus", 0)

    def esta_equipado(self, nodo):
        return nodo is self._nodo_arma or nodo is self._nodo_armadura

    def consumir_actual(self):
        if self.actual is None:
            return None
        if self.actual.dato.clase not in CLASES_CONSUMIBLES:
            return None
        return self._quitar_nodo(self.actual)

    def consumir_primero_de_clase(self, clase):
        if clase not in CLASES_CONSUMIBLES:
            return None
        for nodo in self.lista.recorrer():
            if nodo.dato.clase == clase:
                return self._quitar_nodo(nodo)
        return None

    def cantidad_de_clase(self, clase):
        total = 0
        for nodo in self.lista.recorrer():
            if nodo.dato.clase == clase:
                total += 1
        return total

    def cantidad_pergaminos(self):
        return self.cantidad_de_clase(CLASE_PERGAMINO)

    def tiene_objeto_id(self, id_objeto):
        for nodo in self.lista.recorrer():
            if nodo.dato.id == id_objeto:
                return True
        return False

    def obtener_elementos(self):
        elementos = []
        for nodo in self.lista.recorrer():
            elementos.append(nodo.dato)
        return elementos

    def _nodos(self):
        nodos = []
        for nodo in self.lista.recorrer():
            nodos.append(nodo)
        return nodos

    def _vista(self, clave, reverso=False):
        nodos = ordenar(self._nodos(), lambda n: clave(n.dato), reverso)
        return nodos

    def vista_por_peso(self):
        return [n.dato for n in self._vista(lambda o: o.peso)]

    def vista_por_valor(self):
        # Descendente a proposito: lo mas valioso primero.
        return [n.dato for n in self._vista(lambda o: o.valor, reverso=True)]

    def vista_por_nombre(self):
        return [n.dato for n in self._vista(lambda o: o.nombre.lower())]

    def vista_detallada(self, criterio=None):
        if criterio is None:
            nodos = self._nodos()
        elif criterio == "peso":
            nodos = self._vista(lambda o: o.peso)
        elif criterio == "valor":
            nodos = self._vista(lambda o: o.valor, reverso=True)
        elif criterio == "nombre":
            nodos = self._vista(lambda o: o.nombre.lower())
        else:
            raise ValueError("criterio desconocido: " + str(criterio))
        return [(n.dato, self.esta_equipado(n)) for n in nodos]