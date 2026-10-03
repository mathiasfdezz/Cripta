from modelo.esqueleto import Esqueleto
from modelo.precarga import salas_a_precargar


def sala(id_sala, **salidas):
    """sala(1, N=2, E=(7, True)) -> dict con la forma del API."""
    d = {}
    for dir_, v in salidas.items():
        if isinstance(v, tuple):
            d[dir_] = {"sala": v[0], "cerrada": v[1], "llave": "itm_llave"}
        else:
            d[dir_] = {"sala": v}
    return {"id": id_sala, "nombre": "S" + str(id_sala), "salidas": d}


def esqueleto(*salas):
    e = Esqueleto()
    e.agregar_pagina({"pagina": 1, "total_paginas": 1, "salas": list(salas)})
    return e


def nada(_):
    return False


def test_orden_por_cercania_y_direccion():
    e = esqueleto(sala(1, N=2, S=3), sala(2, S=1, N=4), sala(3, N=1, S=5),
                  sala(4, S=2), sala(5, N=3))
    assert salas_a_precargar(e, 1, nada) == [1, 2, 3, 4, 5]


def test_limite_de_10():
    salas = [sala(i, E=i + 1, O=i - 1) for i in range(2, 40)]
    salas.append(sala(1, E=2))
    e = esqueleto(*salas)
    r = salas_a_precargar(e, 1, nada)
    assert r == list(range(1, 11)) and len(r) == 10


def test_salta_las_ya_pedidas_pero_las_atraviesa():
    e = esqueleto(sala(1, N=2), sala(2, S=1, N=3), sala(3, S=2, N=4), sala(4, S=3))
    pedidas = {1, 2}
    r = salas_a_precargar(e, 1, lambda i: i in pedidas)
    assert r == [3, 4]                     # llega a 3 y 4 pasando por 1 y 2


def test_nada_que_pedir():
    e = esqueleto(sala(1, N=2), sala(2, S=1))
    assert salas_a_precargar(e, 1, lambda i: True) == []


def test_abiertas_primero_y_cerradas_despues():
    # 1 --(cerrada)--> 2 ; 1 --abierta--> 3 --abierta--> 4
    e = esqueleto(sala(1, N=(2, True), E=3), sala(2, S=1), sala(3, O=1, E=4), sala(4, O=3))
    assert salas_a_precargar(e, 1, nada) == [1, 3, 4, 2]
    # con limite 3 la sala tras la puerta cerrada queda fuera
    assert salas_a_precargar(e, 1, nada, limite=3) == [1, 3, 4]


def test_ids_no_contiguos_y_ciclos():
    e = esqueleto(sala(100, E=7), sala(7, O=100, E=42), sala(42, O=7, E=100))
    assert salas_a_precargar(e, 100, nada) == [100, 7, 42]


def test_sala_desconectada_no_aparece():
    e = esqueleto(sala(1, N=2), sala(2, S=1), sala(9))
    assert 9 not in salas_a_precargar(e, 1, nada)


def test_determinista():
    e = esqueleto(sala(1, N=2, S=3, E=4, O=5), sala(2, S=1), sala(3, N=1),
                  sala(4, O=1), sala(5, E=1))
    a = salas_a_precargar(e, 1, nada)
    assert a == salas_a_precargar(e, 1, nada) == [1, 2, 3, 4, 5]


def test_salida_con_cerrada_null():
    e = Esqueleto()
    e.agregar_pagina({"pagina": 1, "total_paginas": 1, "salas": [
        {"id": 1, "nombre": "A", "salidas": {"N": {"sala": 2, "cerrada": None,
                                                    "llave": None,
                                                    "cierre_automatico": None}}},
        {"id": 2, "nombre": "B", "salidas": {}}]})
    assert salas_a_precargar(e, 1, nada, limite=2) == [1, 2]
    assert e.obtener(1).salidas[0].cerrada is False


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_"):
            fn()
            print("OK ", nombre)
    print("Todas las pruebas pasaron")
