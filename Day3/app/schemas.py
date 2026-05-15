# Pydantic Schemas are a structured blueprint that defines the shape, types, and validation rules for your data.
# Basically classes that defines what we accept and return from our API endpoints.


# BaseModel if the base class that all of the pydantic models will inherit from.
# ConfigDict is a class that allows us to configure the behavior and configuration of our pydantic models, such as how they handle extra fields, whether they allow population by field name, and how they handle JSON serialization.
# Field is a function that allows us to define additional metadata for our model fields, such as default values, validation rules, and descriptions Max-Min length.
from pydantic import BaseModel, ConfigDict, Field, EmailStr

from datetime import datetime

# No need for userpassword or infortmation. This is what we expect when we create a new user.
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="The username of the user") # The ... means that this field is required and must be provided when creating a new user. 
    email: EmailStr = Field(..., max_length=120, description="The email address of the user") # The EmailStr type is a special type provided by Pydantic that validates that the value is a valid email address or it's an empty string.


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True) # With this pydantic will read from our SQLAlchemy model.

    id: int
    image_file: str | None
    image_path: str
    # Since UserResponse inherits from UserBase, and UserBase has email field and sharing user email on a public API is really bad
    # In the future we will have public and private schemas for UserCreate to fix this problem.

# This is going to be what is shared between the PostCreate and PostResponse schemas, so we can avoid repeating ourselves.
# It defines the common fields that both schemas will have, such as title, content, and published.

class PostBase(BaseModel): # This defines a base schema for a post
    title: str = Field(..., min_length=1, max_length=100, description="The title of the post") # The ... means that this field is required and must be provided when creating a new post. 
    content: str = Field(..., min_length=10, description="The content of the post") # The min_length and max_length parameters must be between 1 and 100 characters long. The description parameter provides a description of the field that will be included in the API documentation.
    

class PostCreate(PostBase): # This defines a schema for creating a new post, which inherits from the PostBase schema and adds any additional fields or validation rules that are specific to creating a post.
    user_id: int # Temporary! When we get authentication, we will get the user_id from the session token automatically anyway.

# PostResponds inherits from PostBase, (title, content, author) with additional fields defined in PostResponse (id, date_posted).
class PostResponse(PostBase): # This defines a schema for the response when retrieving a post, it includes fields that client doens't provide.
    model_config = ConfigDict(from_attributes=True) # This allows us to create a PostResponse object from a dictionary that has keys that match the field names of the PostResponse schema, even if the keys are not exactly the same as the field names.
                                                    # from_attributes=True It tells Pydantic to read data from the attributes of the object such as from database instead of post["title"] it can also reach to same data with post.title, rather than from a dictionary. 
                                                    # This is useful when we want to create a PostResponse object from a SQLAlchemy model instance, which has attributes that match the field names of the PostResponse schema.
    id: int = Field(..., description="The unique identifier of the post") # The id field is required and must be provided when returning a post in the response. It is an integer that serves as a unique identifier for the post.
    user_id: int
    date_posted: datetime
    author: UserResponse # This is a nested schema that represents the author of the post, it will include the fields defined in the UserResponse schema. This allows us to include information about the author of the post in the response when retrieving a post.
    # When SQLAlchemy loads a post, now it can also load the related user. Pydantic sees that author field, validates the user object and includes the full user data in our API response. (username, email, image_file, image_path)










