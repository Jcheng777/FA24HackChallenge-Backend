import json
from db import db, recipe_ingredient_association_table
from flask import Flask, request 
from db import User, Story, Event, Recipe, Ingredient 
from datetime import datetime
from pydantic import BaseModel
from typing import List
from openai import OpenAI
from dotenv import load_dotenv
import os

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

# Set up OpenAI API key 
load_dotenv()
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

# Define schema for recipe
class Recipe_Gen(BaseModel):
    title: str
    description: str 
    instructions: str
    servings: int
    time: int # Time in minutes
    # rating: int

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
    story.image_url = body.get("image_url")
    story.title = body.get("title")
    story.caption = body.get("caption")

    db.session.commit()
    return success_response(story.serialize())

# -- EVENT ROUTES -------------------------------------------------------

# -- RECIPE ROUTES -------------------------------------------------------

def generate_recipe_with_schema(ingredient_names: List[str]) -> Recipe_Gen: 
    """
    Generate a receipe using OpenAI API with a structured output
    """
    try: 
        prompt = f"""
            Create a recipe using the following ingredients: {', '.join(ingredient_names)}.
            The recipe should include:
            - A title
            - A brief description
            - Step-by-step instructions
            - Number of servings (as an integer)
            - Estimated preparation time in minutes 
            """
        
        # Call the OpenAI API with the structured output format
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": "Extract the recipe information."},
                {"role": "user", "content": prompt},
            ],
            response_format=Recipe_Gen,  # Use the Pydantic Recipe model
        )

        # Log the raw response content for debugging
        print("OpenAI Response (raw):", completion)

        # Access parsed response directly if it maps to Recipe
        recipe = completion.choices[0].message.parsed

        # Ensure recipe is of the expected type
        if isinstance(recipe, Recipe_Gen):
            return recipe
        else:
            raise ValueError("Parsed response is not of type Recipe_Gen")

        return recipe
    
    except Exception as e:
        print(f"Error generating recipe: {e}")
        return None

@app.route("/users/<int:user_id>/generate_recipe/", methods=["POST"])
def generate_recipe(user_id):
    """
    Endpoint for generating a recipe from a user's ingredients
    """
    # Check if user exists
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    # Retrieve ingredients for the user
    ingredients = Ingredient.query.filter_by(user_id=user_id).all()
    if not ingredients:
        return failure_response("No ingredients found for this user!")
        
    ingredient_names = [ingredient.name for ingredient in ingredients]

    recipe = generate_recipe_with_schema(ingredient_names)
    if recipe is None:
        return failure_response("Failed to generate a recipe. Please try again later.")

    new_recipe = Recipe(
        user_id = user_id, 
        title = recipe.title,
        description = recipe.description,
        instructions = recipe.instructions,
        time = recipe.time,
        servings = recipe.servings,
        created_at = datetime.now()
    )
    db.session.add(new_recipe)

    # Associate ingredients with the new recipe
    for ingredient in ingredients:
        db.session.execute(recipe_ingredient_association_table.insert(), {
        "recipe_id": new_recipe.id,
        "ingredient_id": ingredient.id,
        "quantity": "1",  # Default value or dynamic
        "unit": "unit"    # Default value or dynamic
    })

    db.session.commit()

    return success_response(new_recipe.serialize(), 201)

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
        user_id = user_id, 
        name = body.get("name"),
        image_url = body.get("image_url")
    )

    # Add and commit to database 
    db.session.add(new_ingredient)
    db.session.commit()

    return success_response(new_ingredient.simple_serialize(), 201)

@app.route("/users/<int:user_id>/ingredients/")
def get_all_ingredients(user_id):
    """
    Endpoint for getting all ingredients for a user
    """
    # Check if user exists 
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    # Retrieve all stories for a user 
    ingredients = Ingredient.query.filter_by(user_id=user_id).all()

    return success_response({"ingredients": [ingredient.simple_serialize() for ingredient in ingredients]})

@app.route("/users/<int:user_id>/ingredients/<int:ingredient_id>")
def get_ingredient(user_id, ingredient_id):
    """
    Endpoint for getting a specific ingredient for a user by id
    """
    # Check if user exists
    user = User.query.filter_by(id=user_id)
    if user is None:
        return failure_response("User not found!")
    
    # Check if ingredient exists 
    ingredient = Ingredient.query.filter_by(id=ingredient_id, user_id=user_id).first()
    if ingredient is None: 
        return failure_response("Ingredient not found!")

    return success_response(ingredient.simple_serialize())
    
@app.route("/users/<int:user_id>/ingredients/<int:ingredient_id>/", methods=["DELETE"])
def delete_ingredient(user_id, ingredient_id):
    """
    Endpoint for deleting a specific ingredient for a user by id
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
    return success_response(ingredient.simple_serialize())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
