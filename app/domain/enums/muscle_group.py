from enum import Enum


class MuscleGroup(str, Enum):
    PECHO = "Pecho"
    ESPALDA = "Espalda"
    HOMBRO = "Hombro"
    BICEPS = "Bíceps"
    TRICEPS = "Tríceps"
    ANTEBRAZO = "Antebrazo"
    ABDOMEN = "Abdomen"
    CUADRICEPS = "Cuádriceps"
    FEMORAL = "Femoral"
    GLUTEO = "Glúteo"
    PANTORRILLA = "Pantorrilla"
