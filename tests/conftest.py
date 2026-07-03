"""Shared test fixtures.

An isolated in-memory SQLite database (shared across connections via StaticPool), the same
`create_app` factory the process uses, and seeded consultants with ready-made bearer tokens.
No live network, no external services — CI runs fully offline (CLAUDE.md quality standard).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import pytest
from bcap_contracts.common import AssessorLevel, ConsultantTier, Role
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from grassmarket.auth.security import create_access_token, hash_password
from grassmarket.config import Settings
from grassmarket.data.database import create_all
from grassmarket.data.repository import Principal, Repository, StoredConsultant
from grassmarket.web.app import create_app

TEST_JWT_SECRET = "test-secret-that-is-more-than-thirty-two-characters-long-xxxxx"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        env="ci",
        jwt_secret=TEST_JWT_SECRET,
        database_url="sqlite+pysqlite:///:memory:",
    )


@pytest.fixture
def engine() -> Iterator[Engine]:
    # StaticPool + shared in-memory DB so every connection sees the same schema and rows.
    eng = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


@pytest.fixture
def repo(session_factory: sessionmaker[Session]) -> Iterator[Repository]:
    session = session_factory()
    try:
        yield Repository(session)
        session.commit()
    finally:
        session.close()


@dataclass(frozen=True)
class SeededConsultant:
    stored: StoredConsultant
    principal: Principal
    token: str


def _seed(
    session_factory: sessionmaker[Session],
    settings: Settings,
    *,
    email: str,
    role: Role = Role.CONSULTANT,
    tier: ConsultantTier = ConsultantTier.VENTURE_ASSOCIATE,
) -> SeededConsultant:
    session = session_factory()
    try:
        repo = Repository(session)
        stored = repo.create_consultant(
            email=email,
            full_name=email.split("@")[0].title(),
            hashed_password=hash_password("correct-horse-battery-staple"),
            role=role,
            tier=tier,
            assessor_level=AssessorLevel.TRAINED,
        )
        session.commit()
    finally:
        session.close()
    token = create_access_token(
        settings,
        consultant_id=stored.id,
        email=stored.email,
        role=stored.role,
        tier=stored.tier,
        assessor_level=stored.assessor_level,
    )
    return SeededConsultant(
        stored=stored, principal=Principal(consultant_id=stored.id, role=stored.role), token=token
    )


@pytest.fixture
def alice(session_factory: sessionmaker[Session], settings: Settings) -> SeededConsultant:
    return _seed(session_factory, settings, email="alice@bruntsfieldcapital.com")


@pytest.fixture
def bob(session_factory: sessionmaker[Session], settings: Settings) -> SeededConsultant:
    return _seed(session_factory, settings, email="bob@bruntsfieldcapital.com")


@pytest.fixture
def admin(session_factory: sessionmaker[Session], settings: Settings) -> SeededConsultant:
    return _seed(session_factory, settings, email="admin@bruntsfieldcapital.com", role=Role.ADMIN)


@pytest.fixture
def app(settings: Settings, engine: Engine) -> FastAPI:
    return create_app(settings=settings, engine=engine)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


def auth_header(seeded: SeededConsultant) -> dict[str, str]:
    return {"Authorization": f"Bearer {seeded.token}"}
