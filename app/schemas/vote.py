from pydantic import BaseModel
from enum import IntEnum


class VoteAction(IntEnum):
    UPVOTE = 1
    DOWNVOTE = 2
    REMOVE = 0


class VoteCreate(BaseModel):
    post_id: int
    action: VoteAction


class VoteResponse(BaseModel):
    message: str
