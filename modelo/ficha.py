class Ficha:
    def __init__(self, datos):
        if "id" not in datos or "clase" not in datos:
            raise ValueError("una ficha de catalogo requiere 'id' y 'clase'")
        for campo in datos:
            setattr(self, campo, datos[campo])

    def a_dict(self):
        return dict(vars(self))

    def __repr__(self):
        return "Ficha(" + str(self.id) + ")"