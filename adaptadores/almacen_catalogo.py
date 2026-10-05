import dataclasses
import json
import os

from dtos.ficha_catalogo import FichaCatalogo


class AlmacenCatalogoDisco:

    def __init__(self, carpeta):
        self._carpeta = carpeta
        os.makedirs(carpeta, exist_ok=True)

    def _ruta(self, id_ficha):
        if "/" in id_ficha or "\\" in id_ficha or ".." in id_ficha:
            raise ValueError("id de ficha invalido: " + id_ficha)
        return os.path.join(self._carpeta, id_ficha + ".json")

    def _ruta_version(self):
        return os.path.join(self._carpeta, "version.txt")

    def version(self):
        try:
            with open(self._ruta_version(), "r", encoding="utf-8") as f:
                return f.read().strip()
        except (FileNotFoundError, UnicodeDecodeError):
            return None

    def guardar_version(self, version):
        self._escribir(self._ruta_version(), version)

    def leer(self, id_ficha):
        try:
            ruta = self._ruta(id_ficha)
            with open(ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except (FileNotFoundError, ValueError, OSError):
            return None
        if not isinstance(datos, dict):
            return None
        datos["suelta"] = tuple(datos.get("suelta") or ())
        try:
            return FichaCatalogo(**datos)
        except TypeError:
            return None

    def guardar(self, ficha):
        self._escribir(self._ruta(ficha.id),
                       json.dumps(dataclasses.asdict(ficha), ensure_ascii=False))

    def limpiar(self):
        for nombre in os.listdir(self._carpeta):
            if nombre.endswith(".json"):
                os.remove(os.path.join(self._carpeta, nombre))

    def _escribir(self, ruta, texto):
        temporal = ruta + ".tmp"
        with open(temporal, "w", encoding="utf-8") as f:
            f.write(texto)
        os.replace(temporal, ruta)