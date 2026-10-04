from abc import ABC, abstractmethod

MAX_POR_LOTE = 10


def validar_lote(elementos, nombre):
    if len(elementos) == 0 or len(elementos) > MAX_POR_LOTE:
        raise ValueError(f"{nombre} acepta de 1 a {MAX_POR_LOTE} elementos, "
                         f"se pidieron {len(elementos)}")


class FuenteDatos(ABC):

    @abstractmethod
    def listar_criptas(self):
        pass

    @abstractmethod
    def datos_cripta(self, cripta_id):
        pass

    @abstractmethod
    def version_cripta(self, cripta_id):
        pass

    @abstractmethod
    def pagina_salas(self, cripta_id, pagina):
        pass

    @abstractmethod
    def contenido(self, cripta_id, salas):
        pass

    @abstractmethod
    def version_catalogo(self):
        pass

    @abstractmethod
    def catalogo(self, ids):
        pass

    @abstractmethod
    def fijar_presupuesto(self, presupuesto):
        pass

    @abstractmethod
    def solicitudes_realizadas(self):
        pass