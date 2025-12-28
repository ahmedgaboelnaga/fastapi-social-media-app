from typing import Any, List
import pytest
from fastapi.testclient import TestClient
from app import models, schemas


def test_get_all_posts(
    authorized_client: TestClient, test_posts: List[models.Post]
) -> None:
    res = authorized_client.get("/posts")
    assert res.status_code == 200
    res_posts = [schemas.PostWithVote(**post) for post in res.json()]
    assert len(res_posts) == len(test_posts)


def test_unauthorized_user_get_all_posts(client: TestClient) -> None:
    res = client.get("/posts")
    assert res.status_code == 401


def test_unauthorized_user_get_post_by_id(
    client: TestClient, test_posts: List[models.Post]
) -> None:
    res = client.get(f"/posts/{test_posts[0].id}")
    assert res.status_code == 401


def test_get_non_existent_post_by_id(
    authorized_client: TestClient, test_posts: List[models.Post]
) -> None:
    res = authorized_client.get("/posts/9999")
    assert res.status_code == 404


def test_get_post_by_id(
    authorized_client: TestClient, test_posts: List[models.Post]
) -> None:
    res = authorized_client.get(f"/posts/{test_posts[0].id}")
    assert res.status_code == 200
    post = schemas.PostWithVote(**res.json())
    assert post.Post.id == test_posts[0].id


@pytest.mark.parametrize(
    "title, content, published",
    [
        ("test_create_post_1", "test_content_for_post_1", True),
        ("test_create_post_2", "test_content_for_post_2", False),
    ],
)
def test_create_post(
    authorized_client: TestClient,
    test_user: dict[str, Any],
    title: str,
    content: str,
    published: bool,
) -> None:
    res = authorized_client.post(
        "/posts", json={"title": title, "content": content, "published": published}
    )
    assert res.status_code == 201
    post = schemas.PostResponse(**res.json())
    assert post.owner_id == test_user["id"]
    assert post.title == title
    assert post.content == content
    assert post.published == published


def test_create_post_default_published(
    authorized_client: TestClient, test_user: dict[str, Any]
) -> None:
    res = authorized_client.post(
        "/posts",
        json={
            "title": "test_create_post_published",
            "content": "test_content_for_post_published",
        },
    )
    assert res.status_code == 201
    post = schemas.PostResponse(**res.json())
    assert post.owner_id == test_user["id"]
    assert post.title == "test_create_post_published"
    assert post.content == "test_content_for_post_published"
    assert post.published is True


def test_create_post_with_invalid_token(
    client: TestClient, test_user: dict[str, Any]
) -> None:
    res = client.post(
        "/posts",
        json={
            "title": "test_create_post_invalid_token",
            "content": "test_content_for_post_invalid_token",
            "published": True,
        },
    )
    assert res.status_code == 401


def test_create_post_with_missing_fields(
    authorized_client: TestClient, test_user: dict[str, Any]
) -> None:
    res = authorized_client.post(
        "/posts",
        json={
            "title": "test_create_post_missing_fields",
        },
    )
    assert res.status_code == 422


def test_unauthorized_user_delete_post(
    client: TestClient, test_posts: List[models.Post]
) -> None:
    res = client.delete(f"/posts/{test_posts[0].id}")
    assert res.status_code == 401


def test_delete_post_successful(
    authorized_client: TestClient,
    test_posts: List[models.Post],
) -> None:
    res = authorized_client.delete(f"/posts/{test_posts[0].id}")
    assert res.status_code == 204


def test_delete_non_existent_post(
    authorized_client: TestClient, test_posts: List[models.Post]
) -> None:
    res = authorized_client.delete(f"/posts/{99999}")
    assert res.status_code == 404


def test_delete_other_people_post(
    authorized_client: TestClient,
    test_posts: List[models.Post],
) -> None:
    res = authorized_client.delete(f"/posts/{test_posts[4].id}")
    assert res.status_code == 403
    assert res.json()["detail"] == "Not authorized to delete this post"


def test_unauthorized_user_update_post(
    client: TestClient, test_posts: List[models.Post]
) -> None:
    data: dict[str, Any] = {
        "title": "updated title",
        "content": "updated content",
        "published": False,
    }
    res = client.put(f"/posts/{test_posts[0].id}", json=data)
    assert res.status_code == 401


def test_update_post_successful(
    authorized_client: TestClient,
    test_user: dict[str, Any],
    test_posts: List[models.Post],
) -> None:
    data: dict[str, Any] = {
        "title": "updated title",
        "content": "updated content",
        "published": False,
    }
    res = authorized_client.put(f"/posts/{test_posts[0].id}", json=data)
    updated_post = schemas.PostResponse(**res.json())
    assert updated_post.title == data["title"]
    assert updated_post.content == data["content"]
    assert updated_post.published == data["published"]
    assert res.status_code == 200


def test_update_other_user_post(
    authorized_client: TestClient,
    test_posts: List[models.Post],
) -> None:
    data: dict[str, Any] = {
        "title": "updated title",
        "content": "updated content",
        "published": False,
    }
    res = authorized_client.put(f"/posts/{test_posts[4].id}", json=data)
    assert res.status_code == 403
    assert res.json()["detail"] == "Not authorized to update this post"


def test_update_non_existent_post(
    authorized_client: TestClient, test_posts: List[models.Post]
) -> None:
    data: dict[str, Any] = {
        "title": "updated title",
        "content": "updated content",
        "published": False,
    }
    res = authorized_client.put(f"/posts/{99999}", json=data)
    assert res.status_code == 404
