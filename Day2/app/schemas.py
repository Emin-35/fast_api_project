# BaseModel if the base class that all of the pydantic models will inherit from.
# ConfigDict is a class that allows us to configure the behavior and configuration of our pydantic models, such as how they handle extra fields, whether they allow population by field name, and how they handle JSON serialization.
# Field is a function that allows us to define additional metadata for our model fields, such as default values, validation rules, and descriptions Max-Min length.
from pydantic import BaseModel, ConfigDict, Field

# This is going to be what is shared between the PostCreate and PostUpdate schemas, so we can avoid repeating ourselves.
# It defines the common fields that both schemas will have, such as title, content, and published.

class PostBase(BaseModel): # This defines a base schema for a post
    title: str = Field(..., min_length=1, max_length=100, description="The title of the post") # The ... means that this field is required and must be provided when creating a new post. 
    content: str = Field(..., min_length=10, description="The content of the post") # The min_length and max_length parameters must be between 1 and 100 characters long. The description parameter provides a description of the field that will be included in the API documentation.
    author: str = Field(default="Anonymous", description="The author of the post") # This field is optional and has a default value of "Anonymous".


class PostCreate(PostBase): # This defines a schema for creating a new post, which inherits from the PostBase schema and adds any additional fields or validation rules that are specific to creating a post.
    pass # Since we don't need to add any additional fields or validation rules for creating a post, we can simply use the pass statement to indicate that this schema is the same as the PostBase schema.
         # If we had authentication, we would've pass the author field here instead of in the PostBase schema, since we would want to set the author field automatically based on the authenticated logged-in user rather than allowing the client to provide it.


# PostResponds inherits from PostBase, (title, content, author) with additional fields defined in PostResponse (id, date_posted).
class PostResponse(PostBase): # This defines a schema for the response when retrieving a post, it includes fields that client doens't provide.
    model_config = ConfigDict(from_attributes=True) # This allows us to create a PostResponse object from a dictionary that has keys that match the field names of the PostResponse schema, even if the keys are not exactly the same as the field names.
                                                    # from_attributes=True It tells Pydantic to read data from the attributes of the object such as from database instead of post["title"] it can also reach to same data with post.title, rather than from a dictionary. 
                                                    # This is useful when we want to create a PostResponse object from a SQLAlchemy model instance, which has attributes that match the field names of the PostResponse schema.
    id: int = Field(..., description="The unique identifier of the post") # The id field is required and must be provided when returning a post in the response. It is an integer that serves as a unique identifier for the post.
    date_posted: str










