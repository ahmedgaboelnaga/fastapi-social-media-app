# from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import DeclarativeBase


# Base = declarative_base()
class Base(DeclarativeBase):
    pass


from .post import Post
from .user import User
from .vote import Vote

__all__ = ["Base", "Post", "User", "Vote"]
