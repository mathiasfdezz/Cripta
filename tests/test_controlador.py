import unittest

from controlador.controlador import Controlador
from modelo.bitacora import Bitacora
from modelo.inventario import Inventario


class Obj:
    def __init__(self, id, nombre, clase, peso=1, valor=1):
        self.id, self.nombre, self.clase, self.peso, self.valor = id, nombre, clase, peso, valor


class VistaFalsa:
    def __init__(self):
        self.mensajes = []
        self.detallado = None
    def mostrar_mensaje(self, t): self.mensajes.append(t)
    def mostrar_objeto_actual(self, o): pass
    def mostrar_objeto_soltado(self, o): self.mensajes.append("soltado " + o.nombre)
    def mostrar_objeto_equipado(self, o): self.mensajes.append("equipado " + o.nombre)
    def mostrar_inventario_detallado(self, items): self.detallado = items
    def mostrar_bitacora(self, m): self.mensajes.extend(m)


def armar(capacidad=2):
    vista, bit = VistaFalsa(), Bitacora()
    return Controlador(Inventario(capacidad), vista, bit), vista, bit


class PruebasControlador(unittest.TestCase):

    def test_recoger_lleno_no_consume_tiempo(self):
        c, vista, _ = armar(1)
        assert c.recoger_objeto(Obj("a", "A", "pocion")) is True
        assert c.recoger_objeto(Obj("b", "B", "pocion")) is False
        assert "Inventario lleno" in vista.mensajes[-1]

    def test_equipar_valida_clase_y_vacio(self):
        c, vista, _ = armar()
        assert c.equipar_objeto() is False and "vacio" in vista.mensajes[-1]
        c.recoger_objeto(Obj("p", "Pocion", "pocion"))
        assert c.equipar_objeto() is False and "armas y armaduras" in vista.mensajes[-1]
        c.recoger_objeto(Obj("d", "Daga", "arma"))
        c.inventario.avanzar()
        assert c.equipar_objeto() is True and "equipado Daga" in vista.mensajes[-1]

    def test_soltar_devuelve_objeto_o_none(self):
        c, _, _ = armar()
        assert c.soltar_objeto() is None
        daga = Obj("d", "Daga", "arma")
        c.recoger_objeto(daga)
        assert c.soltar_objeto() is daga

    def test_vista_marca_equipado_y_bitacora(self):
        c, vista, bit = armar(3)
        c.recoger_objeto(Obj("d", "Daga", "arma", 2, 15))
        c.recoger_objeto(Obj("p", "Pocion", "pocion", 1, 5))
        c.equipar_objeto()
        c.mostrar_inventario_por_peso()
        assert [(o.nombre, e) for o, e in vista.detallado] == [("Pocion", False), ("Daga", True)]
        c.mostrar_bitacora()
        assert len(bit) >= 2


if __name__ == "__main__":
    unittest.main()
