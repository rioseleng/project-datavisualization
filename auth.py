from database import add_user, authenticate_user

def register_user(username, password):
    """Register a new user."""
    return add_user(username, password)

def login_user(username, password):
    """Authenticate user and return admin status if successful."""
    return authenticate_user(username, password)
