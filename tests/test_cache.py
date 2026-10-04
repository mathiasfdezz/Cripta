import shutil
import tempfile
import unittest

from adaptadores.almacen_catalogo import AlmacenCatalogoDisco
from adaptadores.mapeadores.mapeador_catalogo import ficha_catalogo_desde_json
from dtos.ficha_catalogo import FichaCatalogo
from modelo.cache_catalogo import CacheCatalogo


class ProveedorFalso:
    def __init__(self):
        self.pedidos = []   # lista de lotes pedidos

    def catalogo(self, ids):
        self.pedidos.append(list(ids))
        return [FichaCatalogo(id=i, nombre=i, clase="arma", peso=1, valor=1) for i in ids]


def ids(n, prefijo="itm_"):
    return [prefijo + str(k).zfill(2) for k in range(n)]


class ProveedorFormaReal:
    """Devuelve fichas con la forma exacta del esquema OpenAPI."""

    def catalogo(self, ids):
        datos = {
            "ent_rata": {"id": "ent_rata", "nombre": "Rata gigante", "clase": "enemigo",
                         "vida_max": 12, "ataque": 5, "defensa": 1, "velocidad": 150,
                         "comportamiento": "guardi\u00e1n", "suelta": None},
            "trp_dardos": {"id": "trp_dardos", "nombre": "Dardos", "clase": "trampa",
                           "da\u00f1o": 4, "rearme": None},
            "itm_llave": {"id": "itm_llave", "nombre": "Llave", "clase": "llave",
                          "peso": 1, "valor": 0, "abre": None},
            "itm_pocion": {"id": "itm_pocion", "nombre": "Poci\u00f3n", "clase": "pocion",
                           "peso": 1, "valor": 5, "cura": 10,
                           "modificador_velocidad": None, "duracion": None},
        }
        return [ficha_catalogo_desde_json(datos[i]) for i in ids]


class PruebasCacheCatalogo(unittest.TestCase):

    def test_lotes_de_10_y_sin_repetidos(self):
        prov = ProveedorFalso()
        cache = CacheCatalogo(prov, capacidad=50)
        cache.resolver(ids(25) + ids(5))             # 25 distintos, 5 repetidos
        assert [len(l) for l in prov.pedidos] == [10, 10, 5]
        assert cache.fallos == 25 and cache.aciertos == 0
        cache.resolver(ids(25))
        assert len(prov.pedidos) == 3                # nada nuevo a la red
        assert cache.aciertos == 25

    def test_orden_de_resultado(self):
        cache = CacheCatalogo(ProveedorFalso(), capacidad=50)
        r = cache.resolver(["itm_b", "itm_a", "itm_b"])
        assert [f.id for f in r] == ["itm_b", "itm_a", "itm_b"]

    def test_desaloja_el_menos_recientemente_usado(self):
        prov = ProveedorFalso()
        cache = CacheCatalogo(prov, capacidad=3)
        cache.resolver(["a", "b", "c"])
        cache.resolver(["a"])                        # a pasa a ser la mas reciente
        cache.resolver(["d"])                        # sale b (la mas antigua)
        assert cache.esta_en_memoria("a") and cache.esta_en_memoria("c")
        assert cache.esta_en_memoria("d") and not cache.esta_en_memoria("b")
        assert len(cache) == 3 and cache.desalojos == 1

    def test_fichas_en_uso_no_se_desalojan(self):
        cache = CacheCatalogo(ProveedorFalso(), capacidad=2)
        cache.resolver(["a", "b"])
        cache.retener("a")                           # a es la mas antigua pero en uso
        cache.resolver(["c"])
        assert cache.esta_en_memoria("a") and not cache.esta_en_memoria("b")
        cache.retener("a"); cache.liberar("a")
        assert cache.referencias("a") == 1           # contador, no booleano
        cache.liberar("a")
        assert cache.referencias("a") == 0

    def test_todo_en_uso_excede_tope_y_se_reajusta(self):
        cache = CacheCatalogo(ProveedorFalso(), capacidad=2)
        cache.resolver(["a", "b"])
        cache.retener("a"); cache.retener("b")
        cache.resolver(["c"])
        cache.retener("c")
        assert len(cache) == 3                       # excede: nada desalojable
        cache.liberar("a")                           # al liberar se reajusta
        assert len(cache) == 2 and not cache.esta_en_memoria("a")

    def test_disco_evita_la_red(self):
        carpeta = tempfile.mkdtemp()
        try:
            prov = ProveedorFalso()
            cache = CacheCatalogo(prov, AlmacenCatalogoDisco(carpeta), capacidad=2)
            cache.validar_version("cat-1")
            cache.resolver(["a", "b", "c"])          # a se desaloja de memoria
            assert len(prov.pedidos) == 1
            assert not cache.esta_en_memoria("a")
            cache.resolver(["a"])                    # vuelve desde disco
            assert len(prov.pedidos) == 1 and cache.lecturas_disco == 1

            # "cierre del programa": otra cache sobre la misma carpeta
            prov2 = ProveedorFalso()
            cache2 = CacheCatalogo(prov2, AlmacenCatalogoDisco(carpeta), capacidad=5)
            assert cache2.validar_version("cat-1") is True
            cache2.resolver(["a", "b", "c"])
            assert prov2.pedidos == []               # 0 solicitudes de red
        finally:
            shutil.rmtree(carpeta)

    def test_version_distinta_invalida_el_disco(self):
        carpeta = tempfile.mkdtemp()
        try:
            c1 = CacheCatalogo(ProveedorFalso(), AlmacenCatalogoDisco(carpeta))
            c1.validar_version("cat-1")
            c1.resolver(["a"])
            prov = ProveedorFalso()
            c2 = CacheCatalogo(prov, AlmacenCatalogoDisco(carpeta))
            assert c2.validar_version("cat-2") is False
            c2.resolver(["a"])
            assert prov.pedidos == [["a"]]           # hubo que pedirla de nuevo
        finally:
            shutil.rmtree(carpeta)

    def test_ids_mas_que_la_capacidad_en_un_lote(self):
        carpeta = tempfile.mkdtemp()
        try:
            cache = CacheCatalogo(ProveedorFalso(), AlmacenCatalogoDisco(carpeta),
                                  capacidad=3)
            r = cache.resolver(ids(8))
            assert [f.id for f in r] == ids(8) and len(cache) == 3
        finally:
            shutil.rmtree(carpeta)

    def test_formas_reales_sobreviven_al_disco(self):
        carpeta = tempfile.mkdtemp()
        try:
            todos = ["ent_rata", "trp_dardos", "itm_llave", "itm_pocion"]
            c1 = CacheCatalogo(ProveedorFormaReal(), AlmacenCatalogoDisco(carpeta))
            c1.validar_version("cat-1")
            c1.resolver(todos)

            prov = ProveedorFalso()
            c2 = CacheCatalogo(prov, AlmacenCatalogoDisco(carpeta))
            c2.validar_version("cat-1")
            rata, trampa, llave, pocion = c2.resolver(todos)
            assert prov.pedidos == []
            assert rata.comportamiento == "guardi\u00e1n" and rata.suelta == ()
            assert trampa.dano == 4 and trampa.rearme is None
            assert llave.abre is None
            assert pocion.nombre == "Poci\u00f3n" and pocion.cura == 10
            assert pocion.duracion is None
        finally:
            shutil.rmtree(carpeta)


if __name__ == "__main__":
    unittest.main()
