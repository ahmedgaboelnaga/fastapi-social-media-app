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


# Absolutely—let’s turn your offset pagination into **cursor-based (keyset) pagination** step by step, using your current `Post` + votes query and keeping search support.

# ---

# # 1) Why switch to cursor pagination?

# * **Offset (`skip/limit`)** gets slow for big offsets (`OFFSET 100000`) because the DB still scans/marks those rows.
# * **Cursor (keyset)** uses your sort keys to jump *directly* to the next page → stable & fast for infinite scroll feeds.

# ---

# # 2) Pick deterministic sort keys

# You’re sorting by `created_at DESC`. Add a **tiebreaker** for equal timestamps, e.g. `id DESC`.

# ```python
# .order_by(Post.created_at.desc(), Post.id.desc())
# ```

# > Cursor will carry (`created_at`, `id`) of the last (or first) item on the page.

# ---

# # 3) (Recommended) Add an index

# For Postgres, a composite index helps:

# ```python
# # in your models file
# from sqlalchemy import Index

# Index(
#     "ix_posts_created_id_desc",
#     Post.created_at.desc(),
#     Post.id.desc()
# )
# ```

# (If your DB doesn’t support DESC indexes, a normal `(created_at, id)` index still helps.)

# ---

# # 4) Create opaque cursor helpers

# Encode/decode (`created_at`, `id`) as a URL-safe base64 string so clients never depend on internal details.

# ```python
# # app/core/cursor.py
# import base64, json
# from datetime import datetime, timezone

# def encode_cursor(created_at: datetime, id_: int) -> str:
#     # store UTC ISO string; ensure tz-aware
#     if created_at.tzinfo is None:
#         created_at = created_at.replace(tzinfo=timezone.utc)
#     payload = {"created_at": created_at.isoformat(), "id": id_}
#     raw = json.dumps(payload).encode("utf-8")
#     return base64.urlsafe_b64encode(raw).decode("utf-8")

# def decode_cursor(cursor: str) -> tuple[datetime, int]:
#     raw = base64.urlsafe_b64decode(cursor.encode("utf-8"))
#     payload = json.loads(raw.decode("utf-8"))
#     created_at = datetime.fromisoformat(payload["created_at"])
#     return created_at, int(payload["id"])
# ```

# ---

# # 5) Inequalities for keyset filters (very important)

# With order **DESC, DESC**:

# * **Next page (older items)**
#   `created_at < last_created_at  OR  (created_at = last_created_at AND id < last_id)`

# * **Previous page (newer items)**
#   `created_at > first_created_at  OR  (created_at = first_created_at AND id > first_id)`

# We’ll support both `next` and `prev`. (If you only need infinite scroll forward, you can omit `prev`.)

# ---

# # 6) Response shape (example)

# Return items plus cursors so the client can keep paginating.

# ```python
# # app/schemas/pagination.py
# from pydantic import BaseModel
# from typing import Optional, List

# class PageMeta(BaseModel):
#     limit: int
#     next_cursor: Optional[str] = None
#     prev_cursor: Optional[str] = None

# class PaginatedPosts(BaseModel):
#     items: List[PostWithVote]   # your existing schema
#     meta: PageMeta
# ```

# ---

# # 7) The FastAPI endpoint (keyset version)

# ```python
# from fastapi import APIRouter, Depends, Query
# from typing import List, Tuple, Optional, Annotated, Literal
# from sqlalchemy.orm import Session
# from sqlalchemy import func, and_, or_
# from sqlalchemy.sql import Row
# from datetime import datetime

# from app.core.cursor import encode_cursor, decode_cursor
# from app.models import Post, Vote, User
# from app.deps import get_db, get_current_active_user
# from app.schemas.pagination import PaginatedPosts, PageMeta
# from app.schemas.posts import PostWithVote  # your existing schema

# router = APIRouter()

# Direction = Literal["next", "prev"]

# @router.get("", response_model=PaginatedPosts)
# async def get_posts(
#     db: Session = Depends(get_db),
#     current_user: Annotated[User, Depends(get_current_active_user)],
#     limit: int = Query(10, ge=1, le=100),
#     search: Optional[str] = Query("", description="Filter by title substring"),
#     cursor: Optional[str] = Query(None, description="Opaque pagination cursor"),
#     direction: Direction = Query("next", description="'next' (older) or 'prev' (newer)"),
# ):
#     # Base query: posts + vote count, filtered & grouped
#     base_q = (
#         db.query(Post, func.count(Vote.type).label("votes"))
#         .outerjoin(Vote, Vote.post_id == Post.id)
#         .filter(Post.title.contains(search))
#         .group_by(Post.id)
#     )

#     # Sorting:
#     # - For 'next' we fetch older items; keep DESC so the response is already newest->oldest
#     # - For 'prev' we fetch newer items by applying opposite inequalities, but we’ll query in ASC
#     #   then reverse results so the response is still newest->oldest.
#     if cursor:
#         c_created_at, c_id = decode_cursor(cursor)

#         if direction == "next":
#             # older than the cursor (DESC pagination)
#             base_q = base_q.filter(
#                 or_(
#                     Post.created_at < c_created_at,
#                     and_(Post.created_at == c_created_at, Post.id < c_id),
#                 )
#             ).order_by(Post.created_at.desc(), Post.id.desc())
#         else:
#             # newer than the cursor; fetch ASC so we can easily reverse later
#             base_q = base_q.filter(
#                 or_(
#                     Post.created_at > c_created_at,
#                     and_(Post.created_at == c_created_at, Post.id > c_id),
#                 )
#             ).order_by(Post.created_at.asc(), Post.id.asc())
#     else:
#         # first page
#         base_q = base_q.order_by(Post.created_at.desc(), Post.id.desc())

#     rows: List[Row[Tuple[Post, int]]] = base_q.limit(limit + 1).all()  # fetch one extra to detect "has more"

#     # If we queried ASC for 'prev', reverse to keep the response in DESC order (newest->oldest)
#     reversed_for_prev = False
#     if cursor and direction == "prev":
#         rows.reverse()
#         reversed_for_prev = True

#     items_rows = rows[:limit]
#     has_more = len(rows) > limit

#     # Build response items in your existing shape (PostWithVote)
#     items: List[PostWithVote] = []
#     for post, votes in items_rows:
#         items.append(PostWithVote.from_orm_with_votes(post, votes))  # implement as you already do

#     # Cursors
#     next_cursor = None
#     prev_cursor = None

#     if items_rows:
#         first_post, first_votes = items_rows[0]
#         last_post, last_votes = items_rows[-1]

#         # next_cursor always points to the **last** item in the returned page
#         next_cursor = encode_cursor(last_post.created_at, last_post.id) if has_more else None

#         # prev_cursor always points to the **first** item in the returned page
#         # It allows the client to go "newer" than the first item they just got.
#         prev_cursor = encode_cursor(first_post.created_at, first_post.id)

#         # Special case: when we used 'prev' direction and reversed, we *did* move newer,
#         # so there may or may not be a further 'prev' page. We still provide prev_cursor
#         # based on the first item; clients can probe and get empty or more.
#         # (Optionally you could pre-check by an extra EXISTS query.)

#     return PaginatedPosts(
#         items=items,
#         meta=PageMeta(limit=limit, next_cursor=next_cursor, prev_cursor=prev_cursor),
#     )
# ```

# > Notes
# >
# > * We pull `limit + 1` rows to know if there’s another page (`has_more`).
# > * For `prev`, we query **ASC** to apply “newer than cursor” cleanly, then reverse to keep response in descending order.

# ---

# # 8) Client usage examples

# * **First page (newest)**
#   `GET /posts?limit=10`

# * **Next page (older)**
#   `GET /posts?limit=10&cursor=<next_cursor_from_previous>&direction=next`

# * **Previous page (newer)**
#   `GET /posts?limit=10&cursor=<prev_cursor_from_previous>&direction=prev`

# Make sure the client keeps `search` (and any other filters) identical between pages; a cursor is only valid for the same filter/sort.

# ---

# # 9) Handling votes without GROUP BY (optional)

# If you want to avoid `GROUP BY`, you can use a correlated subquery:

# ```python
# from sqlalchemy.orm import aliased

# votes_subq = (
#     db.query(func.count(Vote.type))
#     .filter(Vote.post_id == Post.id)
#     .correlate(Post)
#     .as_scalar()
# )

# base_q = db.query(Post, votes_subq.label("votes"))
# # no .group_by(Post.id) needed
# ```

# Both patterns are fine with Postgres since grouping by primary key allows selecting the whole row.

# ---

# # 10) Gotchas & best practices

# * **Stable order**: Always use the same `ORDER BY (created_at DESC, id DESC)`.
# * **Timezones**: Store/compare `created_at` in UTC; cursors encode ISO8601 with timezone.
# * **Invalidated cursors**: If filters change (e.g., `search`), treat the cursor as invalid and start fresh.
# * **Inserts/deletes during paging**: Keyset is robust; you might “miss” or “re-see” a newly inserted item at the boundary, which is usually acceptable for feeds.
# * **Indexing**: Composite index on `(created_at, id)` massively speeds keyset scans.

# ---

# If you want, I can adapt the snippet to your exact `PostWithVote.from_orm_with_votes` (or give you that helper) and show quick tests with sample data.


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
