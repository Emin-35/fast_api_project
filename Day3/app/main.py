# To run FastAPI application, you can use the command: uvicorn app.main:app --reload
    # app.main refers to the file main.py in the app directory, and app refers to the FastAPI instance created in that file.
# To stop the server, you can use Ctrl+C in the terminal where the server is running.

from fastapi import FastAPI, Request, HTTPException, status # HTTPException is used to raise HTTP errors with specific status codes and messages, and status is a module that provides constants for common HTTP status codes.
from fastapi import Depends # For dependency injection, figurers out how we will inject the database session into our route

from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from fastapi.exceptions import RequestValidationError # This exception is raised when the request data fails validation, such as when a required parameter is missing or has an invalid type.

from starlette.exceptions import HTTPException as StarletteHTTPException 
# FastAPI uses Starlette under the hood, and StarletteHTTPException is the base class for HTTP exceptions in Starlette.
# If the user goes to a URL that doesn't exist, Starlette will raise error. 
# If we only catch HTTPException, it won't catch the StarletteHTTPException, and the user will see a default error page instead of our custom error page.
# To handle this, we need to catch both HTTPException and StarletteHTTPException in our custom error handler.


from typing import Annotated # For type hinting with FastAPI's dependency injection system, it allows us to specify that a parameter is a dependency that should be injected by FastAPI.
from sqlalchemy import select
from sqlalchemy.orm import Session # For IDE to know what our DB parameter is, basically a type hint

import app.database_models as models # For database_models.py file
from app.database import Base, engine, get_db # Base and engine for creating tables and get_db is a dependency function that provides a database session.

from app.schemas import PostCreate, PostResponse, UserCreate, UserResponse


# ---------------------------------------------- SQLALCHEMY and RELATIONSHIPS ep5----------------------------------------------

# SQLAlchemy is an Object-Relational Mapping (ORM) library for Python that provides a high-level interface for working with databases.
# ORM is Object-Relational Mapping, which allows us to interact with a database using Python objects and classes instead of writing raw SQL queries.
# We will be using SQLLite as our database, which is a lightweight, file-based database that is easy to set up and use for small applications.

app = FastAPI()

# To serve static files (like CSS, JavaScript, images), we need to use the StaticFiles middleware provided by FastAPI.
app.mount("/static", StaticFiles(directory="static"), name="static")
# This is for serving media files, such as profile pictures uploaded by users. We will store these files in a directory called "media" and serve them at the URL path "/media".
app.mount("/media", StaticFiles(directory="media"), name="media") 

# For templates, we need to create a directory named "templates" directory and place our HTML files there.
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine) # Creates all the tables in the database, and it is item potent meaning you can run multiple time and if the tables already created, nothing will happen.

## User Routes
@app.post(
    "/api/users", 
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
# Annotated metadata that tells FastAPI to inject a database session into the db parameter using the get_db dependency function. Does dependency injection.
# This allows us to interact with the database within our route function without having to manually create and manage the database session.
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]): # For request body validation, we need UserCreate schema.
    result_username_search = db.execute(select(models.User).where(models.User.username == user.username)) # Checks if the user already exists

    existing_user = result_username_search.scalars().first() # Takes the first result from the query, if there is none, returns none. Safer
    # result.result.scalar_one_or_none() This is another way to do the same thing, but it will raise an error if there are multiple users with the same username, which shouldn't happen since we have a unique constraint on the username field in the database.

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    

    result_email_search = db.execute(select(models.User).where(models.User.email == user.email)) # Checks if the user already exists

    existing_email = result_email_search.scalars().first() # Takes the first result from the query, if there is none, returns none. Safer
    
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    # Create new user
    new_user = models.User(
        username=user.username,
        email=user.email,
    )

    db.add(new_user) # Adds the user
    db.commit() # Executes and saves the changes
    db.refresh(new_user) # Reloads the object from the database

    return new_user # FastAPI (pydantic) will automatically convert the new_user SQLAlchemy model instance to a UserResponse object based on the response_model specified in the route decorator, ensuring that the response data matches the structure defined in the UserResponse schema.

## Get User by ID Route
@app.get("/api/users/{user_id}", response_model = UserResponse) # This route will be accessible at the URL "api/users/{user_id}" where {user_id} is a dynamic value that can be accessed in the route function.
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    
    result_id_search = db.execute(select(models.User).where(models.User.id == user_id))

    existing_id = result_id_search.scalars().first()

    if existing_id:
        return existing_id
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


## This route will return all the posts for a specific user
@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse]) # This route will be accessible at the URL "api/users/{user_id}/posts" where {user_id} is a dynamic value that can be accessed in the route function.
def get_user_posts(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result_user = db.execute(select(models.User).where(models.User.id == user_id))

    existing_user = result_user.scalars().first()

    if not existing_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    result_user_posts = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    existing_posts = result_user_posts.scalars().all() # Get all the posts
    return existing_posts


## HTLM version for the user post page
@app.get("/users/{user_id}/posts", include_in_schema=False, name = "user_posts_page") # This route will be accessible at the URL "/users/{user_id}/posts" where {user_id} is a dynamic value that can be accessed in the route function.
def user_posts_page(user_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    result_user = db.execute(select(models.User).where(models.User.id == user_id))

    existing_user = result_user.scalars().first()

    if not existing_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    result_user_posts = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    existing_posts = result_user_posts.scalars().all() # Get all the posts

    return templates.TemplateResponse(request, "user_posts.html", {"posts": existing_posts, "user": existing_user, "title": f"{existing_user.username}'s Posts"})


## Updated Home Route
@app.get("/", include_in_schema=False)
@app.get("/home", include_in_schema=False, name="get_home") # Usually FastAPI will use the function name as the default name for the route, but we can specify a custom name using the name parameter in the route decorator. This is useful for generating URLs in templates and for documentation purposes.
def get_home(request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Home"})


## Updated API Get Posts Route
@app.get("/api/posts", response_model=list[PostResponse]) # You can add more routes to handle different paths and HTTP methods as needed.
def get_posts(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts


## Updated Create Post Route
@app.post(
    "/api/posts", # create post to /api/posts
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED
)
def create_post(post: PostCreate, db: Annotated[Session, Depends(get_db)]):
    # Check if the user exists
    result_user = db.execute(select(models.User).where(models.User.id == post.user_id))
    existing_user = result_user.scalars().first()

    if not existing_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Create new post
    new_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id,
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post

## Updated Get Post by ID Route
@app.get("/api/posts/{post_id}", response_model=PostResponse) # This route will be accessible at the URL "api/posts/{post_id}" where {post_id} is a dynamic value that can be accessed in the route function.
def get_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    existing_post = result.scalars().first()

    if existing_post:
        return existing_post

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


## Updated Post Page Route (for a single post)
@app.get("/posts/{post_id}", include_in_schema=False, name="post_page")
def post_page(post_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    existing_post = result.scalars().first()

    if existing_post:
        return templates.TemplateResponse(request, "post.html", {"post": existing_post, "title": existing_post.title[:50]})

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


# This is a custom error handler that will catch all HTTP exceptions, including 404 errors, and render a custom error page.
@app.exception_handler(StarletteHTTPException) 
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):

    message = (
        exception.detail 
        if exception.detail else "An unexpected error occurred.")

    # If the request is for an API endpoint, return a JSON response with the error message and status code.
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exception.status_code, 
            content={"detail": message}
            )
    
    # If the request is for a regular page, render the error template with the status code and message.
    return templates.TemplateResponse(
        request, "error.html", 
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message
        }, 
        # If we didn't include, it would default to 200 OK, which is not correct for an error page.
        # We want to set the status code of the response to match the error that occurred, so we use the status_code parameter to set it to the exception's status code.
        status_code=exception.status_code if exception.status_code else status.HTTP_500_INTERNAL_SERVER_ERROR)


# This is a custom error handler that will catch all REQUEST validation errors and return a JSON response with the error details and a 422 Unprocessable Entity status code.
@app.exception_handler(RequestValidationError) 
def validation_exception_handler(request: Request, exception: RequestValidationError):

    # Validation errors are typically related to API requests that don't have simple detail string where the client sends data that doesn't match the expected format or schema. 
    # So we can't render an error page for API requests, instead we return a JSON response with the error details and a 422 Unprocessable Entity status code.
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()}
        )
    
    # For non-API requests, we can render a custom error page or return a simple HTML response.
    return templates.TemplateResponse(
        request, "error.html", 
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": "Validation Error",
            "message": "There was an error with your request. Please check the data and try again."
        }, 
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT   
    )