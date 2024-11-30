import json
from db import db
from flask import Flask, request 
from db import User, Post
from datetime import datetime

app = Flask(__name__)
db_filename = "cook_app.db"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.create_all()

# Generalized response formats
def success_response(data, code=200):
    return json.dumps({"success": True, "data": data}), code

def failure_response(message, code=404):
    return json.dumps({"success": False, "error": message}), code

# -- USER ROUTES -------------------------------------------------------

@app.route("/users/")
def get_users():
    """
    Endpoint for getting all users
    """
    return success_response({"users": [u.serialize() for u in User.query.all()]})

@app.route("/users/", methods=["POST"])
def create_user():
    """
    Endpoint for creating a user
    """
    body = json.loads(request.data)

    # Create new user 
    new_user = User(
        username = body.get("username"),
        email = body.get("email"),
        password = body.get("password")
    )

    # Add and commit to database 
    db.session.add(new_user)
    db.session.commit()

    return success_response(new_user.serialize(), 201)

@app.route("/users/<int:user_id>")
def get_user(user_id):
    """
    Endpoint for getting a user by id
    """
    # Check if user exists
    user = User.query.filter_by(id=user_id).first()
    if user is None: 
        return failure_response("User not found!")
    
    return success_response(user.serialize())

# -- POST ROUTES -------------------------------------------------------

@app.route("/users/<int:user_id>/posts/", methods=["POST"])
def create_post(user_id):
    """ 
    Endpoint for creating a post for a user by user id
    """
    # Check if user exists
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    body = json.loads(request.data)

    # Create new post 
    new_post = Post(
        user_id = user_id,
        recipe_id = body.get("recipe_id"),
        image_url = body.get("image_url"),
        title = body.get("title"),
        caption = body.get("caption"),
        created_at = datetime.now()
    )

    # Add and commit to database 
    db.session.add(new_post)
    db.session.commit()

    return success_response(new_post.serialize(), 201)

@app.route("/users/<int:user_id>/posts/")
def get_all_posts(user_id): 
    """
    Get all posts for a user by user id 
    """
    # Check if user exists 
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    # Retrieve all posts for a user 
    posts = Post.query.filter_by(user_id=user_id).all()

    return success_response({"posts": [post.serialize() for post in posts]})

@app.route("/users/<int:user_id>/posts/<int:post_id>/")
def get_post(user_id, post_id): 
    """
    Get specififc post for a user by post id and user id
    """
    # Check if user exists 
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    
    # Retrieve specific post
    post = Post.query.filter_by(id=post_id, user_id=user_id).first()

    # Check if post exists for a given user
    if post is None:
        return failure_response("Post not found for this user!")

    return success_response(post.serialize())

@app.route("/users/<int:user_id>/posts/<int:post_id>/", methods = ["DELETE"])
def delete_post(user_id, post_id): 
    """
    Delete specififc post for a user by post id and user id
    """
    # Check if user exists 
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    # Check if post exists for a given user
    post = Post.query.filter_by(id=post_id, user_id=user_id).first()
    if post is None:
        return failure_response("Post not found for this user!")
    
    # Delete post
    db.session.delete(post)
    db.session.commit()
    return success_response(post.serialize())

@app.route("/users/<int:user_id>/posts/<int:post_id>/", methods = ["POST"])
def update_post(user_id, post_id): 
    """
    Update specififc post for a user by post id and user id
    """
    # Check if user exists 
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    # Check if post exists for a given user
    post = Post.query.filter_by(id=post_id, user_id=user_id).first()
    if post is None:
        return failure_response("Post not found for this user!")
    
    # Update fields 
    body = json.loads(request.data)
    post.recipe_id = body.get("recipe_id")
    post.image_url = body.get("image_url")
    post.title = body.get("title")
    post.caption = body.get("caption")

    db.session.commit()
    return success_response(post.serialize())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
