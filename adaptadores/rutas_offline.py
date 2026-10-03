import os


class RutasOffline:
    def __init__(self, carpeta="datos_offline"):
        self._carpeta = carpeta

    def criptas(self):
        return os.path.join(self._carpeta, "criptas.json")

    def datos_cripta(self, cripta_id):
        return os.path.join(self._carpeta, cripta_id, "datos.json")

    def version_cripta(self, cripta_id):
        return os.path.join(self._carpeta, cripta_id, "version.json")

    def pagina_salas(self, cripta_id, pagina):
        return os.path.join(self._carpeta, cripta_id, "salas", f"pagina_{pagina}.json")

    # contenido y fichas van uno por archivo para poder armar cualquier lote
    def contenido_sala(self, cripta_id, sala):
        return os.path.join(self._carpeta, cripta_id, "contenido", f"sala_{sala}.json")

    def version_catalogo(self):
        return os.path.join(self._carpeta, "catalogo", "version.json")

    def ficha(self, ficha_id):
        return os.path.join(self._carpeta, "catalogo", "fichas", f"{ficha_id}.json")