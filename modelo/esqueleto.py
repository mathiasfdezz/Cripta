from estructuras.vector_ordenado import VectorOrdenado

# Orden fijo de direcciones: hace deterministas el BFS y las solicitudes.
DIRECCIONES = ("N", "S", "E", "O")


class Salida:
    """Una salida dirigida de una sala (estado inicial de la definicion)."""

    def __init__(self, direccion, destino, cerrada=False, llave=None,
                 cierre_automatico=None):
        self.direccion = direccion
        self.destino = destino
        self.cerrada = bool(cerrada)          # el API puede mandar null
        self.llave = llave
        self.cierre_automatico = cierre_automatico


class Sala:
    def __init__(self, id_sala, nombre, salidas):
        self.id = id_sala
        self.nombre = nombre
        self.salidas = salidas                # lista en orden N, S, E, O


class Esqueleto:
    """Salas y conexiones de la cripta. Indice por id: VectorOrdenado."""

    def __init__(self):
        self._salas = VectorOrdenado()

    def agregar_pagina(self, pagina):
        """Incorpora la respuesta de GET /criptas/<id>/salas?pagina=n."""
        for datos in pagina["salas"]:
            salidas = []
            for direccion in DIRECCIONES:
                if direccion in datos.get("salidas", {}):
                    s = datos["salidas"][direccion]
                    salidas.append(Salida(direccion, s["sala"], s.get("cerrada"),
                                          s.get("llave"), s.get("cierre_automatico")))
            self._salas.insertar(datos["id"], Sala(datos["id"], datos["nombre"], salidas))

    def obtener(self, id_sala):
        return self._salas.buscar(id_sala)

    def __len__(self):
        return len(self._salas)
