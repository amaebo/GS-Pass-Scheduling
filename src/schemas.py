from pydantic import BaseModel, Field, ConfigDict

GS_CODE_REGEX = r"^[A-Z][A-Z0-9_]{2,49}$"  # 3–50 chars, all caps, with numbers or underscores allowed.


class Satellite(BaseModel):
    norad_id: int = Field(..., ge=1)  # must be >= 1
    s_name: str = Field(..., min_length=1)


class GroundStation(BaseModel):
    gs_code: str = Field(min_length=3, max_length=50, pattern=GS_CODE_REGEX)
    lon: float
    lat: float
    alt: float
    status: str = Field("ACTIVE")


class Mission(BaseModel):
    mission_name: str = Field(..., min_length=1)
    owner: str | None = None
    priority: str | None = None


class MissionUpdate(BaseModel):
    mission_name: str | None = Field(None, min_length=1)
    owner: str | None = None
    priority: str | None = None
class GSUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gs_code: str | None = Field(None, min_length=3, max_length=50, pattern=GS_CODE_REGEX) 
    status: str | None = None
class ReservationCreate(BaseModel):
    pass_id: int = Field(..., gt=0)
    mission_id: int | None = Field(None, gt=0)
    commands: list[str] = Field(default_factory=list)
