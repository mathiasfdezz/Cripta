from dataclasses import dataclass


@dataclass(frozen=True)
class FichaCatalogo:
    id: str
    nombre: str
    clase: str
    # enemigos
    vida_max: int | None = None
    ataque: int | None = None
    defensa: int | None = None
    velocidad: int | None = None
    comportamiento: str | None = None
    suelta: tuple = ()
    # efectos que el contrato del API todavía no trae: si la ficha no los declara, no pasan
    veneno: int | None = None          # daño por pulso al jugador que golpea
    regeneracion: int | None = None    # vida que recupera en cada pulso
    # objetos
    peso: int | None = None
    valor: int | None = None
    ataque_bonus: int | None = None
    defensa_bonus: int | None = None
    cura: int | None = None
    modificador_velocidad: int | None = None
    duracion: int | None = None
    abre: str | int | None = None
    # trampas
    dano: int | None = None
    rearme: int | None = None