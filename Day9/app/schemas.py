# In Python type hints are not compulsory, but with Pydantic, we make them mandotory.

# The code we write ensures that the application doesn't trust data coming from the outside world (the user) and checks whether each piece of incoming data complies with your rules.

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
    password:str = Field(min_length=8)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True) # With this pydantic will read from our SQLAlchemy model, turn into JSON file and return it to the client.

    id: int
    username: str
    image_file: str | None
    image_path: str # When Pydantic converts an object to JSON, it only considers the fields defined in the schema.
    # Since we have @property on image_path function in database_models/table users this acts like an value instead of a function.

    # Since UserResponse inherits from UserBase, and UserBase has email field and sharing user email on a public API is really bad
    # In the future we will have public and private schemas for UserCreate to fix this problem.

# This is going to be what is shared between the PostCreate and PostResponse schemas, so we can avoid repeating ourselves.
# It defines the common fields that both schemas will have, such as title, content, and published.

# We need to create 2 different (public/private) schemas for user informations
# For security reasons, we can't publicly return user emails so we return it in priavete schema.
class UserPrivate(UserPublic):
    email: EmailStr


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
    author: UserPublic # This is a nested schema (Relationship Loading) that represents the author of the post, it will include the fields defined in the UserResponse schema. 
    # This allows us to include information about the author of the post in the response when retrieving a post.
    # When SQLAlchemy loads a post, now it can also load the related user. 
    # Pydantic sees that author field, validates the user object and includes the full user data in our API response. (username, email, image_file, image_path)


## --------------- UPDATE DELETE FUNCTIONALITYS -----------------

# We generally have 2 update methods, put and patch.
# The put method is used to update an entire resource, which means that all fields must be provided in the request body, even if they are not being updated. If a field is not provided, it will be set to null or its default value.
# The patch method is used to update a resource partially, which means that only the fields that are being updated need to be provided in the request body. If a field is not provided, it will not be updated and will retain its current value.

# We want a scheme where all the fields are optional, because users might want to patch instead of put.
# This why we cant inherit from PostBase because PostBase has (...) areas which are MANDATORY!, since we use patch to update we can't expect users to fill all the information
class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=10)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=120)
    image_file: str | None = Field(default=None, min_length=1, max_length=200) # To update profile picture


# Token schema for login responses
class Token(BaseModel):
    access_token: str
    token_type: str