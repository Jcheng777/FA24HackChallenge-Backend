import json
from db import db
from flask import Flask, request 
from db import User, Story, Event, Recipe, Ingredient 
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

# -- STORY ROUTES -------------------------------------------------------

@app.route("/users/<int:user_id>/stories/", methods=["POST"])
def create_story(user_id):
    """ 
    Endpoint for creating a story 
    """
    # Check if user exists
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    body = json.loads(request.data)

    # Create new story 
    new_story = Story(
        user_id = user_id,
        recipe_id = body.get("recipe_id"),
        image_url = body.get("image_url"),
        title = body.get("title"),
        caption = body.get("caption"),
        created_at = datetime.now()
    )

    # Add and commit to database 
    db.session.add(new_story)
    db.session.commit()

    return success_response(new_story.serialize(), 201)

@app.route("/users/<int:user_id>/stories/")
def get_all_stories(user_id): 
    """
    Endpoint for getting all stories for a user 
    """
    # Check if user exists 
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    # Retrieve all stories for a user 
    stories = Story.query.filter_by(user_id=user_id).all()

    return success_response({"stories": [story.serialize() for story in stories]})

@app.route("/users/<int:user_id>/stories/<int:story_id>/")
def get_story(user_id, story_id): 
    """
    Endpoint for getting a specififc story for a user by id
    """
    # Check if user exists 
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    
    # Retrieve specific story
    story = Story.query.filter_by(id=story_id, user_id=user_id).first()

    # Check if story exists for a given user
    if story is None:
        return failure_response("Story not found for this user!")

    return success_response(story.serialize())

@app.route("/users/<int:user_id>/stories/<int:story_id>/", methods = ["DELETE"])
def delete_story(user_id, story_id): 
    """
    Endpoint for deleting a specififc story for a user by id
    """
    # Check if user exists 
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    # Check if story exists for a given user
    story = Story.query.filter_by(id=story_id, user_id=user_id).first()
    if story is None:
        return failure_response("Story not found for this user!")
    
    # Delete story
    db.session.delete(story)
    db.session.commit()
    return success_response(story.serialize())

@app.route("/users/<int:user_id>/stories/<int:story_id>/", methods = ["POST"])
def update_story(user_id, story_id): 
    """
    Endpoint updating specififc story for a user by id
    """
    # Check if user exists 
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    # Check if story exists for a given user
    story = Story.query.filter_by(id=story_id, user_id=user_id).first()
    if story is None:
        return failure_response("Story not found for this user!")
    
    # Update fields 
    body = json.loads(request.data)
    story.recipe_id = body.get("recipe_id")
    story.image_url = body.get("image_url")
    story.title = body.get("title")
    story.caption = body.get("caption")

    db.session.commit()
    return success_response(story.serialize())

# -- RECIPE ROUTES -------------------------------------------------------
@app.route("/users/<int:user_id>/recipes")

# -- INGREDIENT ROUTES ---------------------------------------------------
@app.route("/users/<int:user_id>/ingredients/", methods=["POST"])
def create_ingredient(user_id):
    """
    Endpoint for creating an ingredient 
    """
    body = json.loads(request.data)

    # Check if user exists
    user = User.query.filter_by(id=user_id)
    if user is None:
        return failure_response("User not found!")
    
    new_ingredient = Ingredient(
        name = body.get("name")
    )

    # Add and commit to database 
    db.session.add(new_ingredient)
    db.session.commit()

    return success_response(new_ingredient.serialize(), 201)

@app.route("/users/<int:user_id>/ingredients/")
def get_all_ingredients(user_id):
    """
    Endpoint for getting all ingredients for a user
    """


@app.route("/users/<int:user_id>/ingredients/")
def get_ingredient(user_id):
    """
    Endpoint for getting all ingredients 
    """

@app.route("/users/<int:user_id>/ingredients/<int:ingredient_id>/", methods=["DELETE"])
def delete_ingredient(user_id, ingredient_id):
    """
    """
    # Check if user exists 
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    # Check if ingredient exists for a given user
    ingredient = Ingredient.query.filter_by(id=ingredient_id, user_id=user_id).first()
    if ingredient is None:
        return failure_response("Ingredient not found for this user!")
    
    # Delete ingredient
    db.session.delete(ingredient)
    db.session.commit()
    return success_response(ingredient.serialize())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
