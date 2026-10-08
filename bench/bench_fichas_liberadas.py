import os
import tempfile
import time

from adaptadores.almacen_catalogo import AlmacenCatalogoDisco
from dtos.ficha_catalogo import FichaCatalogo
from modelo.cache_catalogo import CacheCatalogo


class _FuenteContada:
    def __init__(self):
        self.solicitudes = 0

    def catalogo(self, ids):
        self.solicitudes += 1
        return [FichaCatalogo(id=i, nombre=i, clase="arma", peso=1, valor=1, ataque_bonus=1)
                for i in ids]


def principal():
    print("== Recuperar una ficha liberada de memoria (tope 25) ==")
    with tempfile.TemporaryDirectory() as carpeta:
        fuente = _FuenteContada()
        cache = CacheCatalogo(fuente, AlmacenCatalogoDisco(os.path.join(carpeta, "c")), capacidad=25)
        cache.validar_version("cat-1")
        ids = ["itm_%03d" % i for i in range(200)]
        cache.resolver(ids)                    # 200 fichas: solo 25 quedan en memoria
        pedidas = fuente.solicitudes
        liberadas = [i for i in ids if not cache.esta_en_memoria(i)][:100]
        inicio = time.perf_counter()
        for id_ficha in liberadas:
            cache.obtener(id_ficha)
        por_ficha = (time.perf_counter() - inicio) / len(liberadas) * 1e6
        print("desde disco (us por ficha)        %10.1f" % por_ficha)
        print("solicitudes de red al recuperar   %10d" % (fuente.solicitudes - pedidas))
        print("desde la red (enunciado 3.4)      ~400000 us por solicitud")


if __name__ == "__main__":
    principal()