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


"""
200 OK - Successful GET, PUT, or PATCH
201 Created - Successful POST for users and posts
204 No Content - Successful DELETE
400 Bad Request - Duplicate username/email when creating user
404 Not Found - Resource doesn't exist (user or post)
422 Unprocessable Entity - Validation error (automatic from Pydantic)*
"""

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

# app.post is for creating a new resource and app.get is for retrieving a resource

## User Routes
@app.post( 
    "/api/users", 
    response_model=UserResponse, # What will be returned after calling create_user
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
# response_model = UserResponse filters what goes outside and turns into a JSON. Mandatory for data safety
@app.get("/api/users/{user_id}", response_model = UserResponse) # This route will be accessible at the URL "api/users/{user_id}" where {user_id} is a dynamic value that can be accessed in the route function.
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    
    result_id_search = db.execute(select(models.User).where(models.User.id == user_id))

    existing_id = result_id_search.scalars().first()

    if existing_id:
        return existing_id
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

## Get all the users
@app.get("/api/users", response_model=list[UserResponse])
def get_all_users(db: Annotated[Session, Depends(get_db)]):

    users = db.execute(select(models.User))

    all_users = users.scalars().all()

    return all_users


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






# ---------------------------------------------- CRUD OPERATIONS (Update, Delete) ep6 ----------------------------------------------


from app.schemas import PostUpdate, UserUpdate # Import the PostUpdate schema for updating posts

# put is for full update
# Since we're OVERWRIDING, we need to use PostCreate
@app.put("/api/posts/{post_id}", response_model=PostResponse)
def update_post_full(
    post_id: int,
    post_data:PostCreate,
    db: Annotated[Session, Depends(get_db)],
    ):

    post_id_result = db.execute(select(models.Post).where(models.Post.id == post_id))
    update_post = post_id_result.scalars().first()

    if not update_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, details="Post not found")

    # Updating user_id in PostCreate
    # If client sent an user that is not same as it is on the database
    if post_data.user_id != update_post.user_id:
        user_id_result = db.execute(select(models.User).where(models.User.id == post_data.user_id))

        user = user_id_result.scalars().first()

        if not user:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
    
    # Ovewrite on old data
    update_post.title = post_data.title
    update_post.content = post_data.content
    update_post.user_id = post_data.user_id

    db.commit()
    db.refresh(update_post)
    return update_post


# patch is for partial update
@app.patch("/api/posts/{post_id}", response_model=PostResponse)
def update_post_partial(
    post_id: int,
    post_data:PostUpdate,
    db: Annotated[Session, Depends(get_db)],
    ):

    post_id_result = db.execute(select(models.Post).where(models.Post.id == post_id))
    update_post = post_id_result.scalars().first()

    if not update_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, details="Post not found")
    
    # Model dump will provide us a dict that have old data and new data by user
    update_data = post_data.model_dump(exclude_unset=True) # Since patch partially updates and non-given datas will be None, this exclude_unset will make sure they won't be change

    # Iterate over the dict and change update the data.
    for field, value in update_data.items():
        setattr(update_post, field, value)

    db.commit()
    db.refresh(update_post)
    return update_post


# No need for response, all we need is an status code No Content
@app.delete("/api/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_posts(post_id:int, db: Annotated[Session, Depends(get_db)]):

    post_id_result = db.execute(select(models.Post).where(models.Post.id == post_id))
    delete_post = post_id_result.scalars().first()

    if not delete_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )


    db.delete(delete_post)
    db.commit()


## Update User

@app.patch("/api/users/{user_id}", response_model= UserResponse)
def update_user(
    user_id: int,
    user_data:UserUpdate, # Validating the given data by the user
    db: Annotated[Session, Depends(get_db)],
    ):

    user_id_result = db.execute(select(models.User).where(models.User.id == user_id))

    update_user = user_id_result.scalars().first()

    # If there is no user to be updated
    if not update_user:
        raise HTTPException (status_code=status.HTTP_404_NOT_FOUND, details="User not found")
    

    # If username is already exist in our database
    if user_data.username is not None and user_data.username != update_user.username:
        result_username = db.execute(select(models.User).where(models.User.username == user_data.username))

        existing_user = result_username.scalars().first()

        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    
    # If email is already exist in our database
    if user_data.email is not None and user_data.email != update_user.email:
        result_email = db.execute(select(models.User).where(models.User.email == user_data.email))

        existing_email = result_email.scalars().first()

        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

        # The reason why we dont use model_dump and setattr just like in update_post_partial
        # If we iterate through everything using `setattr` inside `update_data.items()`, it becomes difficult to trigger uniqueness checks (Username/Email exist?) separately for each field.
        # In post updates, there's usually no such concern about uniqueness (two posts can have the same title), so using setattr for "bulk updates" is much more practical.

    if user_data.username is not None:
        update_user.username = user_data.username

    if user_data.email is not None:
        update_user.email = user_data.email

    if user_data.image_file is not None:
        update_user.image_file = user_data.image_file


    db.commit()
    db.refresh(update_user)

    print(f"Nesne Durumu: file={update_user.image_file}, path={update_user.image_path}")

    return update_user


## Delete User
# We need to also think about user's posts when we delete an user.
# We can either leave posts or cascate delete the user's posts

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id:int, db: Annotated[Session, Depends(get_db)]):
    
    user_id_result = db.execute(select(models.User).where(models.User.id == user_id))

    deleted_user = user_id_result.scalars().first()

    if not deleted_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


    db.delete(deleted_user)
    db.commit()