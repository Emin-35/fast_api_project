# To run FastAPI application, you can use the command: uvicorn app.main:app --reload
    # app.main refers to the file main.py in the app directory, and app refers to the FastAPI instance created in that file.
# To stop the server, you can use Ctrl+C in the terminal where the server is running.

from fastapi import FastAPI, Request, HTTPException, status # HTTPException is used to raise HTTP errors with specific status codes and messages, and status is a module that provides constants for common HTTP status codes.
from fastapi import Depends # For dependency injection, figurers out how we will inject the database session into our route

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
#from fastapi.responses import JSONResponse no need for async
from fastapi.exceptions import RequestValidationError # This exception is raised when the request data fails validation, such as when a required parameter is missing or has an invalid type.

from starlette.exceptions import HTTPException as StarletteHTTPException 
# FastAPI uses Starlette under the hood, and StarletteHTTPException is the base class for HTTP exceptions in Starlette.
# If the user goes to a URL that doesn't exist, Starlette will raise error. 
# If we only catch HTTPException, it won't catch the StarletteHTTPException, and the user will see a default error page instead of our custom error page.
# To handle this, we need to catch both HTTPException and StarletteHTTPException in our custom error handler.


from typing import Annotated # For type hinting with FastAPI's dependency injection system, it allows us to specify that a parameter is a dependency that should be injected by FastAPI.
from sqlalchemy import select
#from sqlalchemy.orm import Session -> No need for async # For IDE to know what our DB parameter is, basically a type hint

import app.database_models as models # For database_models.py file
from app.database import Base, engine, get_db # Base and engine for creating tables and get_db is a dependency function that provides a database session.

from app.schemas import PostCreate, PostResponse, UserCreate, UserResponse

from app.schemas import PostUpdate, UserUpdate # Import the PostUpdate schema for updating posts

# For Async functionality
from contextlib import asynccontextmanager
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload # For eager loading relationships, super important for async
# Eager loading is the opposite of lazy loading. It's a technique where when you retrieve an object from the database, all other data associated with that object is loaded simultaneously and all at once.


"""
200 OK - Successful GET, PUT, or PATCH
201 Created - Successful POST for users and posts
204 No Content - Successful DELETE
400 Bad Request - Duplicate username/email when creating user
404 Not Found - Resource doesn't exist (user or post)
422 Unprocessable Entity - Validation error (automatic from Pydantic)*
"""

# ------------------------ app.post is for creating a new resource and app.get is for retrieving a resource

## ------------------------------------- SYNC and ASYNC Functions ep7 -------------------------------------

# Async is allows the program to handle multiple tasks concurrently.
# Synchronous code execution which is what we normally do, is one thing happens after another.

# What we're looking to avoid by switching to asynchronous is waiting for something EXTERNAL
# IO-Bound tasks are the situations where we would look to Async to improve performance.
# IO-Bound tasks are EXTERNAL taks such as database response (Querry calls), network request (API calls) or a file to read (Disk) because we can do other work during that time.

# Async does not help with computing or CPU bound operations. (Heavy calculations, image processing, data crunching).

# !!! Async isn't always faster. For small fast querries, async overhead machinery might even slow things down.
# Real benefits show up when you have concurrent load meaning lots of request happening at the same time.

"""
When you define a route with just a regular function

@app.get(...)
def foo(...)

FastAPI automatically runs it in a seperate thread pool. This prevents the function from blocking the main event loop
Even with a regular 'def' function, other quests can be still be process and this is automatic

If we define an async function

@app.get(...)
async def foo(...)

FastAPI runs it directly in the main event loop. This is efficint yes, but we must wait any IO operations
If we do blocking IO without 'await', then we'll block the entire event loop which is terrible.

@app.get("/")
async def read_data():
    data = requests.get("https://api.example.com") 
    return data

    Really bad, async without 'await'
    requests.get is a synchronous library and performs "blocking".
    When the event loop reaches this line, it locks the ENTIRE API until a response comes from the internet.
    Other users cannot access the site.

@app.get("/")
async def read_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")
    return response.json()

    Good, we use 'await'
    We tell the Event Loop: "Until this data arrives, you go and attend to the other requests, I'll wait."

An Event Loop is a single loop that continuously checks which task is ready and then executes it.

"""

# We need to create our tables in a lifespan function
# The Lifespan function is a modern mechanism that allows you to manage the tasks that need to be performed at the start-up and shutdown of a FastAPI application from a single location.

## Lifespan function (Liteal heart-beat of our async FastAPI app)

#async: This indicates that asynchronous operations will be performed within the function, requiring a "wait" (await) period.
#contextmanager: This structure transforms the function into a context manager. It establishes a logic of "start a job, allow something to happen in between (yield), then finish the job."

@asynccontextmanager
async def lifespan(_app: FastAPI): # When calling this function, FastAPI sends the application itself (app) as a parameter. The underscore (_) used if a function receives a parameter but you never use that parameter within the function, you put an underscore before its name.
    # startup

    # `async with`: Opens an asynchronous "block". When this block is finished, resources (connections) are automatically cleared.
    async with engine.begin() as conn: # engine.begin() as conn: Tells the database engine: "Open a connection to me and start a Transaction. We name this active database connection "conn".
        await conn.run_sync(Base.metadata.create_all) # await tells Event Loop to look for other tasks till this job is done. Creates our tables async, item potent can run multiple times if tables are already created

        # conn.run_sync(...): This is the most critical part. SQLAlchemy's create_all function is actually a synchronous function (not asynchronous). 
        # However, we are in an asynchronous environment. run_sync allows us to safely run this synchronous function over the asynchronous connection (conn).
    yield # The function is paused here. The line above this one runs when the application starts. As soon as `yield` is called, control passes to FastAPI and the application starts accepting requests. The code remains "on hold" at this line until the application closes.
    # shutdown
    await engine.dispose() # Wait for the shutdown, close/clean all the connection pools. (If we don't do this, after shutdown there might be a ghost connection to our database)


# app = FastAPI() sync version
app = FastAPI(lifespan=lifespan) # async version

# To serve static files (like CSS, JavaScript, images), we need to use the StaticFiles middleware provided by FastAPI.
app.mount("/static", StaticFiles(directory="static"), name="static")
# This is for serving media files, such as profile pictures uploaded by users. We will store these files in a directory called "media" and serve them at the URL path "/media".
app.mount("/media", StaticFiles(directory="media"), name="media") 

# For templates, we need to create a directory named "templates" directory and place our HTML files there.
templates = Jinja2Templates(directory="templates")



# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

"""
If we didn't use `selectinload`: The moment you typed `post.author.username` somewhere in your code (e.g., in an HTML template or Pydantic model), 
SQLAlchemy would say, "Wait a minute, I don't have the author information, let me go to the database and get it." 
But this requires `await`, and you're not in a place where you can use `await` at that moment.

Result: Your code will crash, and we'll get a `MissingGreenlet` or `GreenletError`.

Also yes, technically, .option part comes right after select part in db.execute 
We specify what to select with `select`, and `.options` tells you how that selected item will be loaded (how the relationships will be retrieved).

select(...): Which table?
.options(...): Should related data be retrieved? (Eager loading)
"""

## ---------------------------- Async Home Route ----------------------------
@app.get("/", include_in_schema=False)
@app.get("/home", include_in_schema=False, name="get_home") # Usually FastAPI will use the function name as the default name for the route, but we can specify a custom name using the name parameter in the route decorator. This is useful for generating URLs in templates and for documentation purposes.
async def get_home(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    ):
    
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author)),
        ) # Eager loading, when we iterate over post and access post.auther that will work because we already loaded post table
    
    posts = result.scalars().all()
    
    return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Home"})



## ---------------------------- Async Post Page (for a single post) ----------------------------
@app.get("/posts/{post_id}", include_in_schema=False, name="post_page")
async def post_page(
    post_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    ):
    
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id == post_id),
        )
    
    existing_post = result.scalars().first()

    if existing_post:
        return templates.TemplateResponse(request, "post.html", {"post": existing_post, "title": existing_post.title[:50]})

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")



## ---------------------------- Async HTLM version for the User Post Page ----------------------------
@app.get("/users/{user_id}/posts", include_in_schema=False, name = "user_posts_page") # This route will be accessible at the URL "/users/{user_id}/posts" where {user_id} is a dynamic value that can be accessed in the route function.
async def user_posts_page(
    user_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    ):

    result_user = await db.execute(select(models.User).where(models.User.id == user_id)) # No need to .select because we're not accessing any releationship on the user object
    existing_user = result_user.scalars().first()

    if not existing_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    result_user_posts = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author)) # .select is needed because our template accesses post.author
        .where(models.Post.user_id == user_id),
        )
    
    existing_posts = result_user_posts.scalars().all() # Get all the posts

    return templates.TemplateResponse(request, "user_posts.html", {"posts": existing_posts, "user": existing_user, "title": f"{existing_user.username}'s Posts"})



## ---------------------------- Async Crerate User Route ----------------------------
@app.post( "/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
# Annotated metadata that tells FastAPI to inject a database session into the db parameter using the get_db dependency function. Does dependency injection.
# This allows us to interact with the database within our route function without having to manually create and manage the database session.
async def create_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    ): # For request body validation, we need UserCreate schema.
    
    result_username_search = await db.execute(select(models.User).where(models.User.username == user.username),) # Checks if the user already exists
    existing_user = result_username_search.scalars().first() # Takes the first result from the query, if there is none, returns none. Safer
    # result.result.scalar_one_or_none() This is another way to do the same thing, but it will raise an error if there are multiple users with the same username, which shouldn't happen since we have a unique constraint on the username field in the database.

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    
    result_email_search = await db.execute(select(models.User).where(models.User.email == user.email),) # Checks if the user already exists
    existing_email = result_email_search.scalars().first() # Takes the first result from the query, if there is none, returns none. Safer
    
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    # Create new user
    new_user = models.User(
        username=user.username,
        email=user.email,
    )

    db.add(new_user) # db.add does not need await, it just adds the object to the sessions pending list in memory. It doesn't actually do any IO
    await db.commit() # Executes and saves the changes
    await db.refresh(new_user) # Reloads the object from the database
    
    return new_user # FastAPI (pydantic) will automatically convert the new_user SQLAlchemy model instance to a UserResponse object based on the response_model specified in the route decorator, ensuring that the response data matches the structure defined in the UserResponse schema.



## ---------------------------- Async Get User by ID Route ----------------------------
# response_model = UserResponse filters what goes outside and turns into a JSON. Mandatory for data safety
@app.get("/api/users/{user_id}", response_model = UserResponse) # This route will be accessible at the URL "api/users/{user_id}" where {user_id} is a dynamic value that can be accessed in the route function.
async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    ):
    
    result_id_search = await db.execute(select(models.User).where(models.User.id == user_id))
    existing_id = result_id_search.scalars().first()

    if existing_id:
        return existing_id
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")



## ---------------------------- Get all the Users ----------------------------
@app.get("/api/users", response_model=list[UserResponse])
async def get_all_users(db: Annotated[AsyncSession, Depends(get_db)]):

    users = await db.execute(select(models.User))
    all_users = users.scalars().all()
    
    return all_users



## ---------------------------- This route will return all the posts for a specific user asynchronously ----------------------------
@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse]) # This route will be accessible at the URL "api/users/{user_id}/posts" where {user_id} is a dynamic value that can be accessed in the route function.
async def get_user_posts(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    ):
    
    result_user = await db.execute(select(models.User).where(models.User.id == user_id))
    existing_user = result_user.scalars().first()

    if not existing_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    result_user_posts = await db.execute(select(
        models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id),
        )
    
    existing_posts = result_user_posts.scalars().all() # Get all the posts
    
    return existing_posts



## ---------------------------- Async Update User CHUD ----------------------------

@app.patch("/api/users/{user_id}", response_model= UserResponse)
async def update_user(
    user_id: int,
    user_data:UserUpdate, # Validating the given data by the user
    db: Annotated[AsyncSession, Depends(get_db)],
    ):

    user_id_result = await db.execute(select(models.User).where(models.User.id == user_id))
    update_user = user_id_result.scalars().first()

    # If there is no user to be updated
    if not update_user:
        raise HTTPException (status_code=status.HTTP_404_NOT_FOUND, details="User not found")
    

    # If username is already exist in our database
    if user_data.username is not None and user_data.username != update_user.username:
        
        result_username = await db.execute(select(models.User).where(models.User.username == user_data.username))
        existing_user = result_username.scalars().first()

        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    
    # If email is already exist in our database
    if user_data.email is not None and user_data.email != update_user.email:
        
        result_email = await db.execute(select(models.User).where(models.User.email == user_data.email))
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


    await db.commit()
    await db.refresh(update_user)
    
    return update_user



## ---------------------------- Async Delete User CHUD ----------------------------
# We need to also think about user's posts when we delete an user.
# We can either leave posts or cascate delete the user's posts

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id:int,
    db: Annotated[AsyncSession, Depends(get_db)]):
    
    user_id_result = await db.execute(select(models.User).where(models.User.id == user_id))
    deleted_user = user_id_result.scalars().first()

    if not deleted_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    await db.delete(deleted_user)
    await db.commit()



## ---------------------------- Async Get Posts Route ----------------------------
@app.get("/api/posts", response_model=list[PostResponse]) # You can add more routes to handle different paths and HTTP methods as needed.
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(
        models.Post)
        .options(selectinload(models.Post.author)),
        )
    
    posts = result.scalars().all()
    return posts



## ---------------------------- Async Create Post Route ----------------------------
@app.post(
    "/api/posts", # create post to /api/posts
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_post(
    post: PostCreate,
    db: Annotated[AsyncSession, Depends(get_db)]):
    
    # Check if the user exists
    result_user = await db.execute(select(models.User).where(models.User.id == post.user_id))
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
    await db.commit()
    await db.refresh(new_post, attribute_names=["author"]) # When we create a new post and retun it, we need the author to be loaded for PostReponse
    # Instead of doing a seperate query with 'selectinload' we can tell to 'db.refresh' to load specific relationships using the 'attribute_names' parameter
    return new_post



## ---------------------------- Async Get Post by ID Route ----------------------------
@app.get("/api/posts/{post_id}", response_model=PostResponse) # This route will be accessible at the URL "api/posts/{post_id}" where {post_id} is a dynamic value that can be accessed in the route function.
async def get_post(
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]):
    
    result = await db.execute(
        select(models.Post)
        .option(selectinload(models.Post.author))
        .where(models.Post.id == post_id),
        )
    existing_post = result.scalars().first()

    if existing_post:
        return existing_post

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")



## ---------------------------- Async Update Post Fully CHUD ----------------------------
# put is for full update
# Since we're OVERWRIDING, we need to use PostCreate
@app.put("/api/posts/{post_id}", response_model=PostResponse)
async def update_post_full(
    post_id: int,
    post_data:PostCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    ):

    post_id_result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    update_post = post_id_result.scalars().first()

    if not update_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, details="Post not found")

    # Updating user_id in PostCreate
    # If client sent an user that is not same as it is on the database
    if post_data.user_id != update_post.user_id:

        user_id_result = await db.execute(select(models.User).where(models.User.id == post_data.user_id))
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

    await db.commit()
    await db.refresh(update_post, attribute_names=["author"])
    return update_post



## ---------------------------- Async Update Post Partial CHUD ----------------------------
# patch is for partial update
@app.patch("/api/posts/{post_id}", response_model=PostResponse)
async def update_post_partial(
    post_id: int,
    post_data:PostUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    ):

    post_id_result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    update_post = post_id_result.scalars().first()

    if not update_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, details="Post not found")
    
    # Model dump will provide us a dict that have old data and new data by user
    update_data = post_data.model_dump(exclude_unset=True) # Since patch partially updates and non-given datas will be None, this exclude_unset will make sure they won't be change

    # Iterate over the dict and change update the data.
    for field, value in update_data.items():
        setattr(update_post, field, value)

    await db.commit()
    await db.refresh(update_post, attribute_names=["author"])
    return update_post



## ---------------------------- Async Delete Post CHUD ----------------------------
# No need for response, all we need is an status code No Content
@app.delete("/api/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_posts(post_id:int, db: Annotated[AsyncSession, Depends(get_db)]):

    post_id_result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    delete_post = post_id_result.scalars().first()

    if not delete_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )


    await db.delete(delete_post)
    await db.commit()




"""
Our current handlers are synchronous and we're creating an JSON response manually.
Better approach is to use FastAPI's default handlers which are async
This gives us consistent behavior with the rest of FastAPI and less code to maintain
"""
# This is a custom error handler that will catch all HTTP exceptions, including 404 errors, and render a custom error page.
@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):

    if request.url.path.startswith("/api/"):
        return await http_exception_handler(request, exception) # Default async handler

    message = (
    exception.detail
    if exception.detail else "An unexpected error occurred. Please try again."
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
async def validation_exception_handler(request: Request, exception: RequestValidationError):

    # Validation errors are typically related to API requests that don't have simple detail string where the client sends data that doesn't match the expected format or schema.
    if request.url.path.startswith("/api/"):
        return await request_validation_exception_handler(request, exception)
    
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