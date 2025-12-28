from typing import Annotated

from fastapi import HTTPException, status, APIRouter, Depends

from app.core import SessionDep, get_current_active_user
from app.models import User, Vote, Post
from app.schemas import VoteAction, VoteCreate, VoteResponse

router = APIRouter(prefix="/vote", tags=["Voting"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=VoteResponse)
async def vote(
    vote: VoteCreate,
    db: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> VoteResponse:
    post_query = db.query(Post).filter(Post.id == vote.post_id)
    post = post_query.first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {vote.post_id} does not exist",
        )

    vote_query = db.query(Vote).filter_by(post_id=vote.post_id, user_id=current_user.id)
    found_vote = vote_query.first()

    if vote.action == VoteAction.UPVOTE:
        # Check if already upvoted
        if found_vote and found_vote.type == 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User {current_user.id} already upvoted on post with id {vote.post_id}.",
            )
        if found_vote:
            # Update existing vote (was downvote, now upvote)
            vote_query.update(
                {"type": 1},
                synchronize_session="evaluate",
            )
        else:
            # Create new upvote
            new_vote: Vote = Vote(
                user_id=current_user.id,
                post_id=vote.post_id,
                type=1,
            )
            db.add(new_vote)

    elif vote.action == VoteAction.DOWNVOTE:
        # Check if already downvoted
        if found_vote and found_vote.type == 2:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User {current_user.id} already downvoted on post with id {vote.post_id}.",
            )
        if found_vote:
            # Update existing vote (was upvote, now downvote)
            vote_query.update(
                {"type": 2},
                synchronize_session="evaluate",
            )
        else:
            # Create new downvote
            new_downvote: Vote = Vote(
                user_id=current_user.id,
                post_id=vote.post_id,
                type=2,
            )
            db.add(new_downvote)

    elif vote.action == VoteAction.REMOVE:
        if not found_vote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Vote doesn't exist"
            )
        vote_query.delete(synchronize_session=False)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    action_messages = {1: "upvote", 2: "downvote", 0: "remove"}
    return VoteResponse(
        message=f"Vote {action_messages.get(vote.action, 'action')} successful"
    )
