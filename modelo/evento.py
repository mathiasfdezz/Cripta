class Evento:
    def __init__(self, tipo, objetivo, dato=None):
        # tipo: qué va a pasar ("accion", "veneno", "rearme_trampa", ...)
        # objetivo: a quién le pasa ("jugador", "e-201", "t-17", ...)
        self.tipo = tipo
        self.objetivo = objetivo
        # dato: lo que el evento necesita al ejecutarse (por ejemplo, cuánta velocidad devolver)
        self.dato = dato
        # los llena la agenda al programar el evento
        self.tiempo_siguiente = None
        self.secuencia = None
        # cancelado: la agenda lo ignora cuando llega a la raíz del heap
        self.cancelado = False
        # en_agenda: sigue dentro del heap (aún no se ha sacado ni descartado)
        self.en_agenda = False

    def __deepcopy__(self, memo):
        # solo tiene datos simples: copia directa, sin el camino genérico de deepcopy
        copia = Evento.__new__(Evento)
        memo[id(self)] = copia
        copia.tipo = self.tipo
        copia.objetivo = self.objetivo
        copia.dato = self.dato
        copia.tiempo_siguiente = self.tiempo_siguiente
        copia.secuencia = self.secuencia
        copia.cancelado = self.cancelado
        copia.en_agenda = self.en_agenda
        return copia

    def __repr__(self):
        return f"Evento({self.tipo}, {self.objetivo})"