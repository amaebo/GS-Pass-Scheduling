from pydantic import BaseModel, Field

GS_CODE_REGEX = r"^[A-Z][A-Z0-9_]{2,49}$"  # 3–50 chars, all caps, with numbers or underscores allowed.


class GroundStation(BaseModel):
    gs_code: str = Field(min_length=3, max_length=50, pattern=GS_CODE_REGEX)
    lon: float
    lat: float
