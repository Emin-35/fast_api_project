# In Python, the `__init__.py` file transforms a simple directory into a "package" that Python can infiltrate, calling functions and classes from.

# Accessing routers from within main.py 
# While inside the app/main.py file, you need to jump to the routers folder, which is outside of its own folder. Since Python uses the root directory, you can perform the import operation in main.py as follows:
# Python looks in the root directory, sees the routers folder. Because it contains __init__.py, it accepts it as a valid package and successfully links the users.py and posts.py files inside it to main.py.

# This file is used to import all the routers from the different modules in the app.
# It allows us to keep our code organized and modular.