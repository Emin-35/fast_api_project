# To run FastAPI application, you can use the command: uvicorn app.main:app --reload
    # app.main refers to the file main.py in the app directory, and app refers to the FastAPI instance created in that file.
# To stop the server, you can use Ctrl+C in the terminal where the server is running.
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json

app = FastAPI()

# Define a simple route
# Routes are defined using decorators, and the function below will be called when a GET request is made to the root URL.
# And routes are used to define the endpoints of your API, allowing you to specify how the application should respond to different HTTP requests (GET, POST, etc.) at various paths.

'''
@app.get("/") # This route will be accessible at the *root* URL ("/") and will return a JSON response with a greeting message.
@app.get("/home") # This is what Stacking Decorators looks like, you can use multiple decorators to define multiple routes for the same function.
def home():
    return HTMLResponse(content="<h1>Hello, welcome to the FastAPI application! This is the home page.</h1>")
'''

# Load posts from the snippet.txt file
with open("app/snippets.json", "r") as file:
    posts = json.load(file)


@app.get("/api/posts", include_in_schema=False) # You can add more routes to handle different paths and HTTP methods as needed.
def get_posts():
    # This route will be accessible at the URL "/api/posts" and will return a list of posts in JSON format.
    return posts


"""
@app.get("/api/html_posts", response_class=HTMLResponse, include_in_schema=False) # This route will be accessible at the URL "/posts" and will return an HTML page displaying the posts.
def display_posts():
    html_content = "<h1>HTML Syntax Posts</h1><ul>"

    for post in posts:
        html_content += f"<li><strong>{post['title']}</strong>: {post['content']}</li>"

    html_content += "</ul>"

    return HTMLResponse(content=html_content, status_code=200)
"""

# !!!! These HTML routes are showing up in our API documentation (localhost:8000/docs), which is not ideal.
# The API documentation is meant for the JSON endpoints, and having HTML routes there can be confusing for users who are looking for API endpoints.
# To prevent this, we can use the `include_in_schema=False` parameter in the route decorators for the HTML routes. 
# This will exclude them from the API documentation but work normally. !!!!





# ---------------------------------------------- TEMPLATES and STATIC FILES ep2 ----------------------------------------------

# When you need full HTML pages including CSS and JavaScript Header Footer, 
# it's better to use templates instead of returning HTML directly from the route functions.
# Because HTML Response needs manually constructed HTML code/string
# FastAPI supports Jinja2 templates, which allow you to create dynamic HTML pages by separating the HTML structure from the data.
# API posts return JSON data which is suitable for API consumption, but it doesn't provide a user-friendly way to display the posts in a web browser.
# We will keep our API routes for JSON responses and create page routes that render HTML templates for a better user experience when viewing the posts in a browser.

# Request is a special object that contains information about the incoming HTTP request
# (URL, headers cookies query params body method client info)
# Think of it as a package that holds everything about what the user sent to your server.
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# To serve static files (like CSS, JavaScript, images), we need to use the StaticFiles middleware provided by FastAPI.
app.mount("/static", StaticFiles(directory="static"), name="static")

# For templates, we need to create a directory named "templates" directory and place our HTML files there.
templates = Jinja2Templates(directory="templates")

# This route will render the "home.html" template when accessed.
@app.get("/", include_in_schema=False)
@app.get("/home")
def get_home(request: Request): # The `request` parameter is required by Jinja2 templates to access request data and render the template correctly.
    # This route will render the "home.html" template when accessed.
    return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Home"}) # posts and title are in HTML file

# If we wanted to create a more pages, we would've to copy the same code and change the template name and title, and want to change a navigation link, we would've to update each page which is not efficient.
# Template Inheritance allows us to create a base template (base.html) that contains the common structure (header, footer, navigation) and then create child templates that extend the base template and only define the unique content for each page.





# ---------------------------------------------- PATH PARAMETERS and ERROR HANDLING ep3 ----------------------------------------------

# Path parameters are used to capture dynamic values from the URL and pass them to the route function.

from fastapi.responses import JSONResponse
from fastapi import HTTPException, status # HTTPException is used to raise HTTP errors with specific status codes and messages, and status is a module that provides constants for common HTTP status codes.
from fastapi.exceptions import RequestValidationError # This exception is raised when the request data fails validation, such as when a required parameter is missing or has an invalid type.
from starlette.exceptions import HTTPException as StarletteHTTPException
# FastAPI uses Starlette under the hood, and StarletteHTTPException is the base class for HTTP exceptions in Starlette.
# If the user goes to a URL that doesn't exist, Starlette will raise error. 
# If we only catch HTTPException, it won't catch the StarletteHTTPException, and the user will see a default error page instead of our custom error page.
# To handle this, we need to catch both HTTPException and StarletteHTTPException in our custom error handler.

@app.get("/api/posts/{post_id}") # This route will be accessible at the URL "api/posts/{post_id}" where {post_id} is a dynamic value that can be accessed in the route function.
def get_post(post_id: int, request: Request):
    for post in posts:
        if post["id"] == post_id:
            return post
    # If no post is found with the given post_id, we can return a 404 error response.
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@app.get("/posts/{post_id}", include_in_schema=False) # This route will be accessible at the URL "/posts/{post_id}" where {post_id} is a dynamic value that can be accessed in the route function.
def visit_post(post_id: int, request: Request):
    for post in posts:
        if post["id"] == post_id:

            title = post["title"][50:] # This is just to show that we can manipulate the data before sending it to the template
            return templates.TemplateResponse(request, "post.html", {"post": post, "title": title})
        
    # If no post is found with the given post_id, we can return a 404 error response.
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






# ---------------------------------------------- PYDANTIC SCHEMAS ep4----------------------------------------------

# To save our newly created posts.
def save_posts():
    with open("app/snippets.json", "w") as file:
        json.dump(posts, file, indent=4)

# Pydantic is a settings management library that is used by FastAPI to define data models and validate incoming request data.
# Pydantic enforces Python type hints at run-time and is a data validation and gives error messages when something doesn't match up
# These schemas allow us to define the structure of our data, specify types for each field, and perform validation on incoming data 
# to ensure it meets the expected format before processing it in our route functions.

from app.schemas import PostCreate, PostResponse

@app.get("/api/posts", response_model=list[PostResponse]) # You can add more routes to handle different paths and HTTP methods as needed.
def get_posts():
    # This route will be accessible at the URL "/api/posts" and will return a list of posts in JSON format.
    return posts

# Adding response_model=list[PostResponse], FastAPI will automatically convert the list of posts to a list of PostResponse objects, 
# which will ensure that the response data matches the structure defined in the PostResponse schema and also provides automatic validation and documentation for the API endpoint.
# It also act as safeguard, if our data had extra fields that are not defined in the PostResponse schema, those fields would be excluded from the response, ensuring that only the expected data is returned to the client.
# Also if our data is missing any required fields defined in the PostResponse schema, FastAPI would raise a validation error
# Preventing the API from returning incomplete or invalid data to the client.


# app.post request, is what we use to create resources.
@app.post(
    "/api/posts", # create post to /api/posts
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED
)
def create_post(post: PostCreate): # The post parameter is expected to be in the format defined by the PostCreate schema, and FastAPI will automatically validate the incoming request data against this schema.
    new_id = max(p["id"] for p in posts) + 1 if posts else 1 # This is a simple way to generate a new unique ID for the post, by finding the maximum existing ID and adding 1. If there are no posts, it starts with ID 1.
    new_post = {
        "id": new_id,
        "title": post.title,
        "content": post.content,
        "author": post.author,
        "date_posted": "2024-06-01" # This is just a placeholder date, in a real application you would typically use the current date and time.
    }

    posts.append(new_post) # This adds the new post to our list of posts.
    save_posts() # This saves the updated list of posts back to the snippets.json file, ensuring that the new post is persisted.
    return new_post # FastAPI will automatically convert the new_post dictionary to a PostResponse object based on the response_model specified in the route decorator, ensuring that the response data matches the structure defined in the PostResponse schema.








