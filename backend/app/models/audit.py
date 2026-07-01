from datetime import datetime

from sqlmodel import Field, SQLModel


class AuditLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int | None = Field(default=None, foreign_key="project.id")
    action: str
    actor: str
    details_json: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExportRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    export_type: str
    file_path: str | None = None
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)
