from typing import Any, List
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker, Session
from app import schemas
from app import models
from app.core import settings
from app.core.database import get_db
from app.models import Base
from app.main import app
from app.core import create_access_token


SQLALCHEMY_TEST_DATABASE_URL = f"postgresql+psycopg://{settings.database_username}:{settings.database_password}@localhost:{settings.database_port}/{settings.database_name}_test"


@pytest.fixture(scope="session")
def test_engine():
    engine: Engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)

    try:
        yield engine
    finally:
        # Cleanup
        engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine: Engine):
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    db: Session = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_session: Session):
    # Run code before we run our test
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Run code after we run our test
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(client: TestClient) -> dict[str, Any]:
    user_data = {"email": "test@example.com", "password": "password123"}
    res = client.post("/users", json=user_data)
    assert res.status_code == 201
    new_user = res.json()
    new_user["password"] = user_data["password"]
    return new_user


@pytest.fixture(scope="function")
def test_user2(client: TestClient) -> dict[str, Any]:
    user_data = {"email": "second@example.com", "password": "password123"}
    res = client.post("/users", json=user_data)
    assert res.status_code == 201
    new_user = res.json()
    new_user["password"] = user_data["password"]
    return new_user


@pytest.fixture(scope="function")
def token(test_user: dict[str, Any]) -> schemas.Token:
    access_token = create_access_token(data={"sub": test_user["email"]})
    return schemas.Token(access_token=access_token, token_type="bearer")


@pytest.fixture(scope="function")
def authorized_client(client: TestClient, token: schemas.Token) -> TestClient:
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token.access_token}",
    }
    return client


@pytest.fixture(scope="function")
def test_posts(
    test_user: dict[str, Any], test_user2: dict[str, str], db_session: Session
) -> List[models.Post]:
    posts_data: list[dict[str, Any]] = [
        {
            "title": "first post",
            "content": "content of first post",
            "owner_id": test_user["id"],
        },
        {
            "title": "second post",
            "content": "content of second post",
            "owner_id": test_user["id"],
        },
        {
            "title": "third post",
            "content": "content of third post",
            "owner_id": test_user["id"],
        },
        {
            "title": "fourth post",
            "content": "content of fourth post",
            "owner_id": test_user["id"],
        },
        {
            "title": "fifth post by a different user",
            "content": "this post is created by second user",
            "owner_id": test_user2["id"],
        },
    ]
    db_session.add_all([models.Post(**post_data) for post_data in posts_data])
    db_session.commit()

    posts: List[models.Post] = db_session.query(models.Post).all()
    return posts
