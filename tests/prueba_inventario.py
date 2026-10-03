from modelo.inventario import Inventario


class Obj:
    def __init__(self, id, nombre, clase, peso, valor, ataque_bonus=0, defensa_bonus=0):
        self.id = id
        self.nombre = nombre
        self.clase = clase
        self.peso = peso
        self.valor = valor
        self.ataque_bonus = ataque_bonus
        self.defensa_bonus = defensa_bonus


def nombres(inv):
    return [o.nombre for o in inv.obtener_elementos()]


def nuevo():
    inv = Inventario(5)
    inv.espada = Obj("itm_espada", "Espada", "arma", 5, 150, ataque_bonus=4)
    inv.daga = Obj("itm_daga", "daga", "arma", 2, 15, ataque_bonus=3)
    inv.cota = Obj("itm_cota", "Cota", "armadura", 10, 300, defensa_bonus=3)
    inv.pocion = Obj("itm_pocion", "Pocion", "pocion", 1, 50)
    inv.llave = Obj("itm_llave", "Llave negra", "llave", 1, 0)
    for o in (inv.espada, inv.daga, inv.cota, inv.pocion, inv.llave):
        assert inv.recoger(o)
    return inv


def test_capacidad():
    inv = nuevo()
    assert inv.esta_lleno()
    assert inv.recoger(Obj("x", "X", "pocion", 1, 1)) is False
    assert len(inv) == 5
    inv.soltar_actual()
    assert inv.recoger(Obj("x", "X", "pocion", 1, 1)) is True


def test_cursor_y_soltar_en_cualquier_posicion():
    inv = nuevo()
    inv.avanzar(); inv.avanzar()          # sobre Cota
    assert inv.obtener_actual() is inv.cota
    assert inv.soltar_actual() is inv.cota
    assert nombres(inv) == ["Espada", "daga", "Pocion", "Llave negra"]
    assert inv.obtener_actual() is inv.pocion   # cursor pasa al siguiente
    # soltar el ultimo: cursor pasa al anterior
    inv.avanzar()
    inv.soltar_actual()
    assert inv.obtener_actual() is inv.pocion
    # soltar el primero
    inv.retroceder(); inv.retroceder()
    inv.soltar_actual()
    assert nombres(inv) == ["daga", "Pocion"]
    # vaciar
    inv.soltar_actual(); inv.soltar_actual()
    assert inv.soltar_actual() is None and inv.obtener_actual() is None
    assert inv.avanzar() is None


def test_equipar_mueve_al_frente_y_reemplaza():
    inv = nuevo()
    inv.avanzar()                           # daga
    assert inv.equipar_actual() is inv.daga
    assert nombres(inv)[0] == "daga"
    assert inv.bonus_ataque() == 3
    # equipar otra arma sustituye; la anterior sigue en el inventario
    inv.avanzar()                           # desde daga (frente) -> Espada
    assert inv.obtener_actual() is inv.espada
    inv.equipar_actual()
    assert inv.arma_equipada() is inv.espada and inv.bonus_ataque() == 4
    assert inv.daga in inv.obtener_elementos() and len(inv) == 5
    # armadura es independiente del arma
    while inv.obtener_actual() is not inv.cota:
        inv.avanzar()
    inv.equipar_actual()
    assert inv.arma_equipada() is inv.espada
    assert inv.armadura_equipada() is inv.cota and inv.bonus_defensa() == 3


def test_no_equipar_otras_clases():
    inv = nuevo()
    while inv.obtener_actual() is not inv.pocion:
        inv.avanzar()
    assert not inv.puede_equipar_actual()
    antes = nombres(inv)
    assert inv.equipar_actual() is None
    assert nombres(inv) == antes


def test_soltar_equipado_lo_desequipa():
    inv = nuevo()
    inv.equipar_actual()                    # Espada
    assert inv.bonus_ataque() == 4
    inv.soltar_actual()
    assert inv.arma_equipada() is None and inv.bonus_ataque() == 0


def test_misma_ficha_dos_instancias():
    inv = Inventario(3)
    ficha = Obj("itm_daga", "Daga", "arma", 2, 15, ataque_bonus=3)
    inv.recoger(ficha); inv.recoger(ficha)
    inv.avanzar(); inv.equipar_actual()
    vista = inv.vista_detallada()
    assert [e for _, e in vista] == [True, False]


def test_vistas_no_alteran_orden_real():
    inv = nuevo()
    real = nombres(inv)
    assert [o.peso for o in inv.vista_por_peso()] == [1, 1, 2, 5, 10]
    assert [o.valor for o in inv.vista_por_valor()] == [300, 150, 50, 15, 0]
    assert [o.nombre for o in inv.vista_por_nombre()] == \
        ["Cota", "daga", "Espada", "Llave negra", "Pocion"]
    assert nombres(inv) == real


def test_consumibles_y_pergaminos():
    inv = Inventario(6)
    p1 = Obj("itm_perg", "Pergamino", "pergamino_retroceso", 1, 10)
    p2 = Obj("itm_perg", "Pergamino", "pergamino_retroceso", 1, 10)
    llave = Obj("itm_llave", "Llave", "llave", 1, 0)
    pocion = Obj("itm_pocion", "Pocion", "pocion", 1, 5)
    for o in (llave, p1, pocion, p2):
        inv.recoger(o)
    assert inv.cantidad_pergaminos() == 2
    assert inv.consumir_actual() is None        # llave: no se consume
    assert len(inv) == 4
    assert inv.consumir_primero_de_clase("pergamino_retroceso") is p1
    assert inv.cantidad_pergaminos() == 1
    inv.avanzar()
    assert inv.consumir_actual() is pocion
    assert inv.tiene_objeto_id("itm_llave") and not inv.tiene_objeto_id("itm_otra")
    assert inv.consumir_primero_de_clase("arma") is None


def test_lista_doble_reinsercion():
    inv = nuevo()
    lista = inv.lista
    nodo = lista.cabeza.siguiente
    ref = nodo.anterior
    dato = lista.eliminar_nodo(nodo)
    lista.insertar_despues(ref, dato)
    assert nombres(inv) == ["Espada", "daga", "Cota", "Pocion", "Llave negra"]
    lista.insertar_antes(lista.cabeza, Obj("n", "Nuevo", "pocion", 1, 1))
    assert nombres(inv)[0] == "Nuevo"
    lista.insertar_antes(None, Obj("f", "Final", "pocion", 1, 1))
    assert nombres(inv)[-1] == "Final" and len(lista) == 7


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_"):
            fn()
            print("OK ", nombre)
    print("Todas las pruebas pasaron")