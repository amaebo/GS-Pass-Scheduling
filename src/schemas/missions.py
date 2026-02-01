from pydantic import BaseModel, Field


class Mission(BaseModel):
    mission_name: str = Field(..., min_length=1)
    owner: str | None = None
    priority: str | None = None


class MissionUpdate(BaseModel):
    mission_name: str | None = Field(None, min_length=1)
    owner: str | None = None
    priority: str | None = None
