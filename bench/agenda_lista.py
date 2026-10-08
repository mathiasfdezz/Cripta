class AgendaLista:
    """Alternativa descartada para la agenda: una lista sin orden. Programar es
    agregar al final; sacar el siguiente obliga a recorrer todos los eventos."""

    def __init__(self):
        self._eventos = []
        self._secuencia = 1

    def programar(self, tiempo, evento):
        self._eventos.append((tiempo, self._secuencia, evento))
        self._secuencia += 1

    def sacar_siguiente(self):
        menor = 0
        for i in range(1, len(self._eventos)):
            if self._eventos[i][:2] < self._eventos[menor][:2]:
                menor = i
        return self._eventos.pop(menor)