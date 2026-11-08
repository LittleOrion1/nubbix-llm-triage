
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class ClasificacionTriage(BaseModel):

    model_config = ConfigDict(extra="forbid")#- extra="forbid": rechaza campos adicionales que no estén definidos.
    #Literal: restringe la categoría a cuatro valores posibles.
    category: Literal[
        "billing",
        "technical",
        "account",
        "other"
    ]

    confidence: float = Field(
        ge=0,
        le=1,
        description="Nivel de confianza de la clasificación"
    )
