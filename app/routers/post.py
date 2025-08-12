from typing import Annotated, List, Tuple

from fastapi import HTTPException, status, APIRouter, Depends
from sqlalchemy import desc, func
from sqlalchemy.engine.row import Row

from app.core import SessionDep, get_current_active_user
from app.models import User, Post, Vote
from app.schemas import PostCreate, PostResponse, PostWithVote


router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("", response_model=List[PostWithVote])
async def get_posts(
    db: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = 10,
    skip: int = 0,
    search: str | None = "",
):
    posts: List[Row[Tuple[Post, int]]] = (
        db.query(Post, func.count(Vote.type).label("votes"))
        .outerjoin(Vote, Vote.post_id == Post.id)
        .filter(Post.title.contains(search))
        .group_by(Post.id)
        .order_by(desc(Post.created_at))
        .limit(limit)
        .offset(skip)
        .all()
    )
    return posts


@router.get("/me", response_model=List[PostWithVote])
async def get_my_posts(
    db: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    # return current_user.posts
    posts = (
        db.query(Post, func.count(Vote.type).label("votes"))
        .outerjoin(Vote, Vote.post_id == Post.id)
        .filter(Post.owner_id == current_user.id)
        .group_by(Post.id)
        .order_by(desc(Post.created_at))
        .all()
    )
    return posts


@router.get("/latest", response_model=PostWithVote)
async def get_latest_post(
    db: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    # post_query = db.query(Post).order_by(desc(Post.created_at))
    post_query = (
        db.query(Post, func.count(Vote.type).label("votes"))
        .outerjoin(Vote, Vote.post_id == Post.id)
        .group_by(Post.id)
        .order_by(desc(Post.created_at))
    )
    post = post_query.first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="There are no posts yet."
        )
    return post


@router.get("/{post_id}", response_model=PostWithVote)
async def get_post(
    post_id: int,
    db: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    post = (
        db.query(Post, func.count(Vote.type).label("votes"))
        .outerjoin(Vote, Vote.post_id == Post.id)
        .filter(Post.id == post_id)
        .group_by(Post.id)
        .first()
    )
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id: {post_id} was not found",
        )
    return post


@router.get("/user/{user_id}", response_model=List[PostWithVote])
async def get_user_posts(
    user_id: int,
    db: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    # return current_user.posts
    posts = (
        db.query(Post, func.count(Vote.type).label("votes"))
        .outerjoin(Vote, Vote.post_id == Post.id)
        .filter(Post.owner_id == user_id)
        .group_by(Post.id)
        .order_by(desc(Post.created_at))
        .all()
    )
    return posts


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PostResponse)
async def create_post(
    post: PostCreate,
    db: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Post:
    new_post: Post = Post(**post.model_dump(), owner_id=current_user.id)
    try:
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )
    return new_post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    post_query = db.query(Post).filter_by(id=post_id)
    post: Post | None = post_query.first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The post with id: {post_id} wasn't found.",
        )
    if post.owner_id != current_user.id:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this post",
        )
    try:
        post_query.delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database Error {e}",
        )
    return


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    updated_post: PostCreate,
    db: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Post:
    post_query = db.query(Post).filter_by(id=post_id)
    post: Post | None = post_query.first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The post with id: {post_id} wasn't found.",
        )
    if post.owner_id != current_user.id:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this post",
        )
    try:
        post_query.update(updated_post.model_dump(), synchronize_session=False)  # type: ignore
        # for key, value in updated_post.model_dump().items():
        #     setattr(post, key, value)
        db.commit()
        db.refresh(post)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database Error {e}",
        )
    return post
