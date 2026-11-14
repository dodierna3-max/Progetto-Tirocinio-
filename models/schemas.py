from typing import Literal

from pydantic import BaseModel, Field


class ConfigScheduler(BaseModel):
    """Quando creare il report automatico (giorno: 0 = lunedì ... 6 = domenica)."""
    frequenza: Literal["settimana", "giorno", "minuti"]
    giorno: int = Field(ge=0, le=6)
    ora: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    minuti: int = Field(ge=1, le=1440)