from typing import Annotated # For type hinting with FastAPI's dependency injection system, it allows us to specify that a parameter is a dependency that should be injected by FastAPI.

# APIRouter is important 
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func # func for case sensitive queries
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import app.database_models as models
from app.database import get_db
from app.schemas import PostResponse, UserCreate, Token, UserPublic, UserPrivate, UserUpdate # Import the UserUpdate schema for updating users

from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm

from auth import (
    create_access_token, 
    hash_password, 
    oauth2_scheme, 
    verify_access_token, 
    verify_password,
)

from app.config import settings

## ------------------------------------- API Routers and Organization ep8 -------------------------------------

# To add more features, and maintaine the code base at the same time, we need to organize our code
# We can use API Routers to organize our routes into separate files and then include them in our main application.

# APIRouter is FastAPI's tools for organizing routes into modules. So instead of defining all of our routes on the main file, we will define them on seperate file.
# Main idea is, in a seperate file, we create a router with 'router = APIRouter()' and we define our routes using 'router.get', 'router.post' intead of app.get or app.post
# Then we import that router into our main file and include/connect it in our FastAPI app with 'app.include_router(router)'.

# We can also apply common prefixes to group of routes, apply tags for documentation, and even apply dependencies to a group of routes using APIRouter. This helps us keep our code organized and maintainable as our application grows in complexity.
# Another good thing about siplitting our routes that we can only import the routers we need in a specific file, instead of importing everything in the main file, which can lead to circular imports and other issues. 



# This is what we decorate our routes with, instead of our app
router = APIRouter()



# Since this is an API router, we need to include only the API routes which are the 'path = /api/..' for user API end-points.
# After moving the api routes, two things will change (mainly). 
# First, intead of 'app.post' it will be 'router.post' and second, the path is going to change
# Instead of '/api/users' it will be just " " empty string because routes are relative. So when we include this router we will specify the prefix as '/api/users' and then all the routes in this file will be relative to that prefix. 
# So we can just use empty string for the path in the route decorator and it will work correctly when we include the router in our main application with the specified prefix. This way we can keep our code organized and modular, and we can easily manage our routes as our application grows.



## ---------------------------- Async Crerate User Route ----------------------------
@router.post(
        "",
        response_model=UserPrivate,
        status_code=status.HTTP_201_CREATED,
        )
# Annotated metadata that tells FastAPI to inject a database session into the db parameter using the get_db dependency function. Does dependency injection.
# This allows us to interact with the database within our route function without having to manually create and manage the database session.
async def create_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    ): # For request body validation, we need UserCreate schema.
    
    result_username_search = await db.execute(select(models.User).where(func.lower(models.User.username) == user.username.lower()),) # Checks if the user already exists

    existing_user = result_username_search.scalars().first() # Takes the first result from the query, if there is none, returns none. Safer
    # result.result.scalar_one_or_none() This is another way to do the same thing, but it will raise an error if there are multiple users with the same username, which shouldn't happen since we have a unique constraint on the username field in the database.

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    
    result_email_search = await db.execute(select(models.User).where(func.lower(models.User.email) == user.email.lower()),) # Checks if the user already exists
    existing_email = result_email_search.scalars().first() # Takes the first result from the query, if there is none, returns none. Safer
    
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    # Create new user
    new_user = models.User(
        username=user.username,
        email=user.email.lower(),
        password_hash = hash_password(user.password),
    )

    db.add(new_user) # db.add does not need await, it just adds the object to the sessions pending list in memory. It doesn't actually do any IO
    await db.commit() # Executes and saves the changes
    await db.refresh(new_user) # Reloads the object from the database
    
    return new_user # FastAPI (pydantic) will automatically convert the new_user SQLAlchemy model instance to a UserResponse object based on the response_model specified in the route decorator, ensuring that the response data matches the structure defined in the UserResponse schema.



# login_for_access_token
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Look up user by email (case-insensitive)
    # Note: OAuth2PasswordRequestForm uses "username" field, but we treat it as email
    result = await db.execute(
        select(models.User).where(
            func.lower(models.User.email) == form_data.username.lower(),
        ),
    )
    user = result.scalars().first()

    # Verify user exists and password is correct
    # Don't reveal which one failed (security best practice)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token with user id as subject
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")



# get_current_user
@router.get("/me", response_model=UserPrivate)
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get the currently authenticated user."""
    user_id = verify_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate user_id is a valid integer (defense against malformed JWT)
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(models.User).where(models.User.id == user_id_int),
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user



## ---------------------------- Async Get User by ID Route ----------------------------
# response_model = UserResponse filters what goes outside and turns into a JSON. Mandatory for data safety
@router.get("/{user_id}", response_model = UserPublic) # This route will be accessible at the URL "api/users/{user_id}" where {user_id} is a dynamic value that can be accessed in the route function.
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
@router.get("", response_model=list[UserPublic])
async def get_all_users(db: Annotated[AsyncSession, Depends(get_db)]):

    users = await db.execute(select(models.User))
    all_users = users.scalars().all()
    
    return all_users



## ---------------------------- This route will return all the posts for a specific user asynchronously ----------------------------
@router.get("/{user_id}/posts", response_model=list[PostResponse]) # This route will be accessible at the URL "api/users/{user_id}/posts" where {user_id} is a dynamic value that can be accessed in the route function.
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
        .where(models.Post.user_id == user_id)
        .order_by(models.Post.date_posted.desc()),
        )
    
    existing_posts = result_user_posts.scalars().all() # Get all the posts
    
    return existing_posts



## ---------------------------- Async Update User CHUD ----------------------------

@router.patch("/{user_id}", response_model= UserPrivate)
async def update_user(
    user_id: int,
    user_data:UserUpdate, # Validating the given data by the user
    db: Annotated[AsyncSession, Depends(get_db)],
    ):

    user_id_result = await db.execute(select(models.User).where(models.User.id == user_id))
    update_user = user_id_result.scalars().first()

    # If there is no user to be updated
    if not update_user:
        raise HTTPException (status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    

    # If username is already exist in our database
    if user_data.username is not None and user_data.username.lower() != update_user.username.lower():
        
        result_username = await db.execute(select(models.User).where(func.lower(models.User.username) == user_data.username.lower()))
        existing_user = result_username.scalars().first()

        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    
    # If email is already exist in our database
    if user_data.email is not None and user_data.email.lower() != update_user.email.lower():
        
        result_email = await db.execute(select(models.User).where(func.lower(models.User.email) == user_data.email.lower()))
        existing_email = result_email.scalars().first()

        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

        # The reason why we dont use model_dump and setattr just like in update_post_partial
        # If we iterate through everything using `setattr` inside `update_data.items()`, it becomes difficult to trigger uniqueness checks (Username/Email exist?) separately for each field.
        # In post updates, there's usually no such concern about uniqueness (two posts can have the same title), so using setattr for "bulk updates" is much more practical.

    if user_data.username is not None:
        update_user.username = user_data.username

    if user_data.email is not None:
        update_user.email = user_data.email.lower()

    if user_data.image_file is not None:
        update_user.image_file = user_data.image_file


    await db.commit()
    await db.refresh(update_user)
    
    return update_user



## ---------------------------- Async Delete User CHUD ----------------------------
# We need to also think about user's posts when we delete an user.
# We can either leave posts or cascate delete the user's posts

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
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


