"""
DAO (Data Access Object) file

Helper file containing functions for accessing data in our database
"""

from db import db, User

def get_user_by_username(username):
    """
    Returns a user object from the database given a username
    """
    return User.query.filter(User.username == username).first()

def get_user_by_session_token(session_token):
    """
    Returns a user object from the database given a session token
    """
    return User.query.filter(User.session_token == session_token).first()

def get_user_by_refresh_token(refresh_token):
    """
    Returns  a user object from the database given a refresh token
    """
    return User.query.filter(User.refresh_token == refresh_token).first()

def verify_credentials(username, password):
    """
    Returns if credentials match, and the User object
    """
    possible_user = get_user_by_username(username)
    if possible_user is None:
        return False, None
    return possible_user.verify_password(password), possible_user

def create_user(username, password):
    """
    Creates a User object in the database

    Returns if creation was successful, and the User object
    """
    possible_user = get_user_by_username(username)
    if possible_user is not None:
        return False, possible_user
    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()
    return True, user