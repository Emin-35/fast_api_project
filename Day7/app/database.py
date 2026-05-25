# This file is responsible for setting up the database connection and defining the base class for our SQLAlchemy models. 
# It also provides a function to get a database session that can be used in our API endpoints to interact with the database.
#from sqlalchemy import create_engine

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Database URL here tells SQLAlchemy where to connect
# SQLLite will connect to a file called blog.db in the current directory(the dot(.)). If the file doesn't exist, it will be created automatically
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./blog.db"
# +aiosqlite tells SQLAlchemy to which async driver to use for SQLite database

# Engine is the connection to the database.
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}, # SQLLite allows one thread (SQLLite specific rule no need for this in PostgreSQL) to access but FastAPI can handle multiple requests at the same time, 
                                               # so we need to set check_same_thread to False to allow multiple threads to access the database.
)

# Creates database sessions. Session is a transaction with the database, 
# it allows us to interact with the database and perform operations such as querying, inserting, updating, and deleting data.
"""SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)"""
# autocommit and autoflush are set to False to ensure that we have more control over when changes are committed to the database and when the session is flushed.
# bind=engine tells the sessionmaker to use the engine we created earlier to connect to the database.


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False, # This is recommended for async, it prevents issues with expired objects after a commit.
    # When object expires, SQLAlchemy normally try to reload it lazily, but lazy loading doesn't work in async
    # Lazy loading means that data is not loaded until it is needed, i.e., it is delayed.

    # Eager loading is the opposite of lazy loading. It's a technique where when you retrieve an object from the database, all other data associated with that object is loaded simultaneously and all at once.
)

# ----- Dependency Injection is a powerful feature of FastAPI that allows us to define reusable components that can be injected into our API endpoints.
# Basically provides routes for database sessions so they can work.
# Instead of creating the session inside the route, we just ask from FastAPI
class Base(DeclarativeBase):
    pass


# Dependency function provides session to connect our API endpoints to the database.
# It uses a context manager (with statement) to ensure that the database session is properly closed after use, even if an error occurs.
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session # The yield statement allows us to return a database session to the caller while keeping the connection open until the caller is done with it.
                 # FastAPI's dependency injection calls this function for each request and handles clean-up after the request is processed, ensuring that the database session is properly closed.












































