# dirección contraria: lo que sale por N de una sala entra por S en la otra, etc.
OPUESTA = {"N": "S", "S": "N", "E": "O", "O": "E"}


class Puerta:
    """Una puerta entre dos salas. Es un único objeto compartido por ambos lados:
    abrirla o cerrarla desde una sala la abre o la cierra desde la otra."""

    def __init__(self):
        self.lados = []              # [(id_sala, direccion), ...] de las salas que la declaran
        self.cerrada = False
        self.llave = None
        self.cierre_automatico = None
        self._tocada = False         # True si ya se abrió/cerró durante la partida

    def incorporar(self, id_sala, salida):
        """Suma lo que declara uno de los lados. Basta con que un lado la declare
        cerrada para que la puerta (la misma desde los dos lados) esté cerrada."""
        self.lados.append((id_sala, salida.direccion))
        if not self._tocada and salida.cerrada:
            self.cerrada = True
        if self.llave is None:
            self.llave = salida.llave
        if self.cierre_automatico is None:
            self.cierre_automatico = salida.cierre_automatico

    def esta_cerrada(self):
        return self.cerrada

    def esta_abierta(self):
        return not self.cerrada

    def abrir(self):
        self.cerrada = False
        self._tocada = True

    def cerrar(self):
        self.cerrada = True
        self._tocada = True