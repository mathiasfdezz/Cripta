from abc import ABC, abstractmethod

MAX_POR_LOTE = 10


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