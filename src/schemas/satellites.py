from pydantic import BaseModel, Field


class Satellite(BaseModel):
    norad_id: int = Field(..., ge=1)  # must be >= 1
    s_name: str = Field(..., min_length=1)
