from typing import Annotated # For type hinting with FastAPI's dependency injection system, it allows us to specify that a parameter is a dependency that should be injected by FastAPI.

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import app.database_models as models
from app.database import get_db
from app.schemas import PostCreate, PostResponse, PostUpdate # Import the PostUpdate schema for updating posts


## ------------------------------------- API Routers and Organization ep8 -------------------------------------

# To add more features, and maintaine the code base at the same time, we need to organize our code
# We can use API Routers to organize our routes into separate files and then include them in our main application.

# APIRouter is FastAPI's tools for organizing routes into modules. So instead of defining all of our routes on the main file, we will define them on seperate file.
# Main idea is, in a seperate file, we create a router with 'router = APIRouter()' and we define our routes using 'router.get', 'router.post' intead of app.get or app.post
# Then we import that router into our main file and include/connect it in our FastAPI app with 'app.include_router(router)'.

# We can also apply common prefixes to group of routes, apply tags for documentation, and even apply dependencies to a group of routes using APIRouter. This helps us keep our code organized and maintainable as our application grows in complexity.
# Another good thing about siplitting our routes that we can only import the routers we need in a specific file, instead of importing everything in the main file, which can lead to circular imports and other issues. 


router = APIRouter()



## ---------------------------- Async Get Posts Route ----------------------------
@router.get("", response_model=list[PostResponse]) # You can add more routes to handle different paths and HTTP methods as needed.
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(select(
        models.Post)
        .options(selectinload(models.Post.author)),
        )
    
    posts = result.scalars().all()
    return posts



## ---------------------------- Async Create Post Route ----------------------------
@router.post(
    "", # create post to /api/posts
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
@router.get("/{post_id}", response_model=PostResponse) # This route will be accessible at the URL "api/posts/{post_id}" where {post_id} is a dynamic value that can be accessed in the route function.
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
@router.put("/{post_id}", response_model=PostResponse)
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
@router.patch("/{post_id}", response_model=PostResponse)
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
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_posts(post_id:int, db: Annotated[AsyncSession, Depends(get_db)]):

    post_id_result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    delete_post = post_id_result.scalars().first()

    if not delete_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )


    await db.delete(delete_post)
    await db.commit()

