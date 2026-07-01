from datetime import datetime

from sqlmodel import Field, SQLModel


class Project(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SubjectAsset(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    address: str
    market_area: str
    land_type: str
    planning_segment: str | None = None
    size_sqm: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
