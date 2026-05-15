from __future__ import annotations # We don't need this in Python 3.10 and above, but it allows us to use forward references in type hints, which is useful for defining relationships between models that reference each other.

from datetime import UTC, datetime # For timezones

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ---- All this written in SQLAlchemy which is an Object-Relational Mapping (ORM) library for Python
# And will automatically convert to the which-ever database (SQLite, PostgreSQL, MySQL) we choose to use in the future without us having to change our code, which is one of the main benefits of using an ORM.

# When we add authentication in the future, we will use this User model to represent the users and posts in our database. 
class User(Base):
    __tablename__ = "users" 

    # If we wrote id: int without Mapped, in run-time for mapped_column function returns a column 
    # but with writing int we would mess up the static analize tools such as Mypy because they expecting column.

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True) # No need to write nullable=True/False because Mapped[str] means nullable=False and Mapped[str | None] means nullable=True
    email: Mapped[str] = mapped_column(String(100), unique=True)
    image_file: Mapped[str | None] = mapped_column(
        String(200),
        default=None,
    )

    # Relationship to the Post model, one to many relationship, one user can have many posts, but each post belongs to only one user.
    # back_populates is used to define the bidirectional relationship between the User and Post models.
    # !!! We need to use list to define one to many relationship, because it will return a list of posts
    posts: Mapped[list[Post]] = relationship(back_populates="author") # Also we forward reference the Post model because it is defined after the User model, so we need to tell Python that it exists before we can use it in the relationship.
    

    # If user uploads an image, the image_path property will return the path to the uploaded image. 
    # If the user does not upload an image, it will return the path to a default profile picture.

    # This is a Python decorator that allows us to define a method that can be accessed like an attribute. 
    # Instead of user.image_path() we can access it like user.image_path
    @property
    def image_path(self) -> str:
        if self.image_file:
            return f"/media/profile_pics/{self.image_file}"
        return "/static/profile_pics/default.jpg"


# Foreign key ALWAYS stays on the "many" side of the relationship, which is the Post model in our case, because one user can have many posts, but each post belongs to only one user.
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    # ForeignKey is used to define a foreign key constraint on the user_id column, which references the id column of the users table
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True, #Since PK gets indexed automatically, but FKs dont. 
        #This kind of like a bookmark for database to quickly find the user_id in the Users table.
    )
    date_posted: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), # SQLLite stores Timestamps as text but when we go to PostgreSQL it will store it as a timestamp with timezone, because of this DateTime(timezone=True)
        default=lambda: datetime.now(UTC), # lambda called each time on creation of a new post, so it will set the default value to the current date and time in UTC timezone.
    )

    # Many to One relationship, many posts can belong to one user, but each post belongs to only one user.
    # back_populates is used to define the bidirectional relationship between the Post and User models
    author: Mapped[User] = relationship(back_populates="posts")

# SQLAlchemy will automatically create the tables in the database based on these models and handle all the join operations