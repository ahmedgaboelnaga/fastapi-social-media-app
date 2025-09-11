from sqlalchemy import Column, ForeignKey, Integer, Enum
import enum

from . import Base


class VoteType(str, enum.Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"


class Vote(Base):
    __tablename__ = "votes"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    post_id = Column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    type = Column(
        Enum(
            VoteType,
            name="votetype",
            values_callable=lambda obj: [e.value for e in obj],  # type: ignore
        ),
        nullable=False,
    )
