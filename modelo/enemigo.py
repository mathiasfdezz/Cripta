from modelo.actor import Actor

CLASE_ENEMIGO = "enemigo"

GUARDIAN = "guardián"
ERRANTE = "errante"
RASTREADOR = "rastreador"


class Enemigo(Actor):
    def __init__(self, instancia, ficha, sala):
        # instancia: InstanciaEnemigo (el que viene en el contenido de la sala)
        # ficha: FichaCatalogo del tipo de esa instancia
        if ficha.clase != CLASE_ENEMIGO:
            raise ValueError(f"la ficha {ficha.id} no es de un enemigo")
        if ficha.id != instancia.tipo:
            raise ValueError(f"la ficha {ficha.id} no corresponde al tipo {instancia.tipo}")
        # instancia.vida None = empieza con la vida_max del catálogo
        super().__init__(instancia.instancia, sala, ficha.vida_max, ficha.ataque,
                         ficha.defensa, ficha.velocidad, instancia.vida)
        self.instancia = instancia.instancia
        self.tipo = ficha.id
        self.nombre = ficha.nombre
        # guardián / errante / rastreador: lo usa EstadoPartida._comportarse
        self.comportamiento = ficha.comportamiento
        self.suelta = tuple(ficha.suelta)   # ids de catálogo que deja al morir
        # no actúa hasta que el jugador entra a su sala; una vez activo sigue activo
        self.activo = False