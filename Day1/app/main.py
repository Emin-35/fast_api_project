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
with open("app/snippets.txt", "r") as file:
    posts = json.load(file)

@app.get("/api/posts") # You can add more routes to handle different paths and HTTP methods as needed.
def get_posts():
    # This route will be accessible at the URL "/api/posts" and will return a list of posts in JSON format.
    return posts

@app.get("/api/html_posts", response_class=HTMLResponse, include_in_schema=False) # This route will be accessible at the URL "/posts" and will return an HTML page displaying the posts.
def display_posts():
    html_content = "<h1>HTML Syntax Posts</h1><ul>"

    for post in posts:
        html_content += f"<li><strong>{post['title']}</strong>: {post['content']}</li>"

    html_content += "</ul>"

    return HTMLResponse(content=html_content, status_code=200)


# !!!! These HTML routes are showing up in our API documentation (localhost:8000/docs), which is not ideal.
# The API documentation is meant for the JSON endpoints, and having HTML routes there can be confusing for users who are looking for API endpoints.
# To prevent this, we can use the `include_in_schema=False` parameter in the route decorators for the HTML routes. 
# This will exclude them from the API documentation but work normally. !!!!





# ---------------------------------------------- TEMPLATES and STATIC FILES ----------------------------------------------

# When you need full HTML pages including CSS and JavaScript Header Footer, 
# it's better to use templates instead of returning HTML directly from the route functions.
# FastAPI supports Jinja2 templates, which allow you to create dynamic HTML pages by separating the HTML structure from the data.
# API posts return JSON data which is suitable for API consumption, but it doesn't provide a user-friendly way to display the posts in a web browser.
# We will keep our API routes for JSON responses and create page routes that render HTML templates for a better user experience when viewing the posts in a browser.

# Request is a special object that contains information about the incoming HTTP request
# (URL, headers cookies query params body method client info)
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# To serve static files (like CSS, JavaScript, images), we need to use the StaticFiles middleware provided by FastAPI.
app.mount("/static", StaticFiles(directory="static"), name="static")

# For templates, we need to create a directory named "templates" directory and place our HTML files there.
templates = Jinja2Templates(directory="templates")

# This route will render the "home.html" template when accessed.
@app.get("/")
@app.get("/home")
def get_home(request: Request): # The `request` parameter is required by Jinja2 templates to access request data and render the template correctly.
    # This route will render the "home.html" template when accessed.
    return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Home"}) # posts and title are in HTML file

# If we wanted to create a more pages, we would've to copy the same code and change the template name and title, and want to change a navigation link, we would've to update each page which is not efficient.
# Template Inheritance allows us to create a base template (base.html) that contains the common structure (header, footer, navigation) and then create child templates that extend the base template and only define the unique content for each page.































