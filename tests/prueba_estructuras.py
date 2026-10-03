from estructuras.fila import Fila
from estructuras.pila import Pila
from estructuras.vector_ordenado import VectorOrdenado
from modelo.bitacora import Bitacora


def test_fila_fifo_y_crecimiento():
    f = Fila()
    for i in range(100):
        f.encolar(i)
    assert len(f) == 100 and f.frente() == 0
    assert [f.desencolar() for _ in range(100)] == list(range(100))
    assert f.esta_vacia() and f.desencolar() is None and f.frente() is None


def test_fila_circular_intercalada():
    """Compara contra una lista de referencia con encolar/desencolar mezclados
    (fuerza el giro del indice circular y varios crecimientos)."""
    f = Fila()
    modelo = []
    siguiente = 0
    for paso in range(500):
        for _ in range(3):
            f.encolar(siguiente); modelo.append(siguiente); siguiente += 1
        for _ in range(2):
            assert f.desencolar() == modelo.pop(0)
        assert len(f) == len(modelo) and list(f) == modelo


def test_fila_acotada_sin_sobrescribir():
    f = Fila(2)
    f.encolar(1); f.encolar(2)
    try:
        f.encolar(3)
        assert False
    except OverflowError:
        pass


def test_fila_sobrescribe_mas_antiguo():
    f = Fila(3, sobrescribir=True)
    for i in range(1, 8):
        f.encolar(i)
    assert list(f) == [5, 6, 7] and len(f) == 3


def test_pila_lifo():
    p = Pila()
    assert p.desapilar() is None and p.tope() is None
    for i in range(5):
        p.apilar(i)
    assert p.tope() == 4 and len(p) == 5
    assert [p.desapilar() for _ in range(5)] == [4, 3, 2, 1, 0]
    assert p.esta_vacia()


def test_vector_ordenado():
    v = VectorOrdenado()
    for c in [5, 1, 9, 3, 7]:
        assert v.insertar(c, "v" + str(c)) is True
    assert v.insertar(3, "nuevo") is False
    assert [c for c, _ in v] == [1, 3, 5, 7, 9]
    assert v.buscar(3) == "nuevo" and v.buscar(4) is None
    assert v.contiene(9) and not v.contiene(0)
    assert v.eliminar(1) == "v1" and v.eliminar(1) is None
    assert v.eliminar(9) == "v9"
    assert [c for c, _ in v] == [3, 5, 7] and len(v) == 3
    vacio = VectorOrdenado()
    assert vacio.buscar(1) is None and vacio.eliminar(1) is None


def test_bitacora_ultimos_20():
    b = Bitacora()
    for i in range(1, 46):
        b.agregar("m" + str(i))
    u = b.ultimos()
    assert len(u) == 20 and u[0] == "m26" and u[-1] == "m45"
    assert len(b._mensajes._datos) == 20      # memoria constante


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_"):
            fn()
            print("OK ", nombre)
    print("Todas las pruebas pasaron")
