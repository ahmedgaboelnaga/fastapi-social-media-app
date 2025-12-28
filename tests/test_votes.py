import pytest
from typing import List, Any
from fastapi.testclient import TestClient
from app import models
from sqlalchemy.orm import Session


@pytest.fixture(scope="function")
def test_vote(
    db_session: Session,
    test_user: dict[str, Any],
    test_posts: List[models.Post],
) -> None:
    new_upvote = models.Vote(
        post_id=test_posts[0].id,
        user_id=test_user["id"],
        type=1,  # 1 = UPVOTE
    )
    new_downvote = models.Vote(
        post_id=test_posts[1].id,
        user_id=test_user["id"],
        type=2,  # 2 = DOWNVOTE
    )
    db_session.add_all([new_upvote, new_downvote])
    db_session.commit()


def test_unauthorized_vote_attempt(
    client: TestClient, test_posts: List[models.Post]
) -> None:
    res = client.post("/vote", json={"post_id": test_posts[0].id, "action": 1})
    assert res.status_code == 401


def test_vote_on_non_existent_post(
    authorized_client: TestClient, test_posts: List[models.Post]
) -> None:
    res = authorized_client.post("/vote", json={"post_id": 9999, "action": 1})
    assert res.status_code == 404


def test_already_upvoted(
    authorized_client: TestClient,
    test_posts: List[models.Post],
    test_vote: None,
) -> None:
    res = authorized_client.post(
        "/vote",
        json={"post_id": test_posts[0].id, "action": 1},
    )
    assert res.status_code == 409


def test_upvote_on_downvoted(
    authorized_client: TestClient,
    test_posts: List[models.Post],
    test_vote: None,
) -> None:
    res = authorized_client.post(
        "/vote", json={"post_id": test_posts[1].id, "action": 1}
    )
    assert res.status_code == 201


def test_new_upvote(
    authorized_client: TestClient, test_posts: List[models.Post], test_vote: None
) -> None:
    res = authorized_client.post(
        "/vote",
        json={
            "post_id": test_posts[2].id,
            "action": 1,
        },
    )
    assert res.status_code == 201


def test_already_downvoted(
    authorized_client: TestClient, test_posts: List[models.Post], test_vote: None
) -> None:
    res = authorized_client.post(
        "/vote",
        json={"post_id": test_posts[1].id, "action": 2},
    )
    assert res.status_code == 409


def test_downvote_on_upvote(
    authorized_client: TestClient, test_posts: List[models.Post], test_vote: None
) -> None:
    res = authorized_client.post(
        "/vote", json={"post_id": test_posts[0].id, "action": 2}
    )
    assert res.status_code == 201


def test_new_downvote(
    authorized_client: TestClient, test_posts: List[models.Post], test_vote: None
) -> None:
    res = authorized_client.post(
        "/vote", json={"post_id": test_posts[2].id, "action": 2}
    )
    assert res.status_code == 201


def test_remove_vote_successful(
    authorized_client: TestClient, test_posts: List[models.Post], test_vote: None
) -> None:
    res = authorized_client.post(
        "/vote", json={"post_id": test_posts[0].id, "action": 0}
    )
    assert res.status_code == 201


def test_remove_non_existent_vote(
    authorized_client: TestClient, test_posts: List[models.Post], test_vote: None
) -> None:
    res = authorized_client.post(
        "/vote", json={"post_id": test_posts[2].id, "action": 0}
    )
    assert res.status_code == 404
