import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.models.audit import AuditLog, ExportRecord  # noqa: F401
from app.models.candidate import (  # noqa: F401
    DuplicateResult,
    EligibleCandidate,
    ExtractionResult,
    Final3Selection,
    RawCandidate,
    ScoringResult,
    Top10Recommendation,
)
from app.models.project import Project, SubjectAsset


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def project(session):
    proj = Project(name="Test Project", description="Phase 2 test project")
    session.add(proj)
    session.commit()
    session.refresh(proj)
    return proj


@pytest.fixture()
def subject_asset(session, project):
    subject = SubjectAsset(
        project_id=project.id,
        address="123 Test St",
        market_area="District 2",
        land_type="ODT",
        planning_segment="residential",
        size_sqm=100.0,
    )
    session.add(subject)
    session.commit()
    session.refresh(subject)
    return subject
