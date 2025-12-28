from sqlalchemy import Column, ForeignKey, Integer

from . import Base


class Vote(Base):
    __tablename__ = "votes"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    post_id = Column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    type = Column(
        Integer,  # 1 = upvote, 2 = downvote
        nullable=False,
    )
