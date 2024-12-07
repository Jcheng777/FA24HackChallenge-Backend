import json
from db import db, user_story_association_table, user_event_association_table, user_recipe_association_table, recipe_ingredient_association_table, user_event_attendance_association_table
from flask import Flask, request 
from db import User, Story, Event, Recipe, Ingredient, Asset 
from datetime import datetime
from pydantic import BaseModel
from typing import List
from openai import OpenAI
from dotenv import load_dotenv
import os
import users_dao

app = Flask(__name__)
db_filename = "cook_app.db"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.create_all()

# Authentication helper functions
def extract_token(request):
    """
    Helper function that extracts the token from the header of a request
    """
    auth_header = request.headers.get("Authorization")
    if auth_header is None:
        return False, failure_response("Missing authorization header", 401)
    
    #Bearer <token>
    bearer_token = auth_header.replace("Bearer ", "").strip()
    if not bearer_token:
        return False, failure_response("Invalid authorization header", 401)
    return True, bearer_token


# Generalized response formats
def success_response(data, code=200):
    return json.dumps({"success": True, "data": data}), code

def failure_response(message, code=404):
    return json.dumps({"success": False, "error": message}), code

# Set up OpenAI API key 
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define schema for recipe
class Recipe_Gen(BaseModel):
    title: str
    description: str 
    instructions: List[str]
    servings: int
    time: int # Time in minutes
    rating: int

# -- ROUTES ------------------------------------------------------------

@app.route("/")
def base():
    return "hello world"


# -- AUTHENTICATION ROUTES ----------------------------------------------

@app.route("/register/", methods=["POST"])
def register_account():
    """
    Endpoint for registering a new user
    """
    body = json.loads(request.data)
    username = body.get("username")
    password = body.get("password")
    if username is None or password is None:
        return failure_response("Missing required fields", 400)
    created, user = users_dao.create_user(username, password)
    if not created: 
        return failure_response("User already exists", 409) 
    return success_response({"session_token": user.session_token,
                             "session_expiration": str(user.session_expiration),
                             "refresh_token": user.refresh_token }, 201)

@app.route("/login/", methods=["POST"])
def login():
    """
    Endpoint for logging in a user
    """
    body = json.loads(request.data)
    username = body.get("username")
    password = body.get("password")
    if username is None or password is None:
        return failure_response("Missing required fields", 400)  
    success, user = users_dao.verify_credentials(username, password)
    if not success: 
        return failure_response("Invalid credentials", 401)
    user.renew_session()
    db.session.commit()
    return success_response({"session_token": user.session_token,
                             "session_expiration": str(user.session_expiration),
                             "refresh_token": user.refresh_token }, 200)

@app.route("/logout/", methods=["POST"])
def logout():
    """
    Endpoint for logging out a user
    """
    success, response = extract_token(request)
    if not success:
        return response
    session_token = response
    user = users_dao.get_user_by_session_token(session_token)
    if not user or not user.verify_session_token(session_token):
        return failure_response("Invalid session token", 401)
    user.session_expiration = datetime.now()
    return success_response("Successfully logged out", 200)

@app.route("/session/", methods=["POST"])
def refresh_session():
    """
    Endpoint for refreshing a user's session
    """
    success, response = extract_token(request)
    if not success:
        return response
    refresh_token = response
    try:
        user = users_dao.renew_session(refresh_token)
    except Exception as e:
        return failure_response("Invalid refresh token", 401)
    return success_response({"session_token": user.session_token,
                             "session_expiration": str(user.session_expiration),
                             "refresh_token": user.refresh_token }, 200)


# -- USER ROUTES -------------------------------------------------------

@app.route("/users/")
def get_users():
    """
    Endpoint for getting all users
    """
    return success_response({"users": [u.serialize() for u in User.query.all()]})

@app.route("/users/<int:user_id>/")
def get_user(user_id):
    """
    Endpoint for getting a user by id
    """
    # Check if user exists
    user = User.query.filter_by(id=user_id).first()
    if user is None: 
        return failure_response("User not found!")
    
    return success_response(user.serialize())

@app.route("/users/<int:user_id>/", methods=["DELETE"])
def delete_user(user_id):
    """
    Endpoint for deleting a user by id
    """
    # Check if user exists
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    
    db.session.delete(user)
    db.session.commit()
    return success_response(user.serialize())

@app.route("/users/<int:user_id>/", methods=["POST"])
def update_user(user_id):
    """
    Endpoint for updating a user by id
    """
    # Check if user exists
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    
    body = json.loads(request.data)
    user.username = body.get("username")
    user.email = body.get("email")
    user.password = body.get("password")

    db.session.commit()
    return success_response(user.serialize())

@app.route("/users/<int:user_id>/stories/<int:story_id>/save", methods=["POST"])
def save_story(user_id, story_id):
    """
    Endpoint for saving a story for a user
    """
    # Check if user exists
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    
    #Check if story exists
    story = Story.query.filter_by(id=story_id).first()
    if story is None:
        return failure_response("Story not found!")

    # Add story to user's saved stories
    insert_statement = user_story_association_table.insert().values(user_id = user_id, story_id = story_id)
    db.session.execute(insert_statement)
    user.saved_stories.append(story)
    db.session.commit()
    return success_response(user.serialize())

@app.route("/users/<int:user_id>/events/<int:event_id>/save", methods=["POST"])
def save_event(user_id, event_id):
    """
    Endpoint for saving an event for a user
    """
    # Check if user exists
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    
    #Check if event exists
    event = Event.query.filter_by(id=event_id).first()
    if event is None:
        return failure_response("Event not found!")

    # Add event to user's saved events
    insert_statement = user_event_association_table.insert().values(user_id = user_id, event_id = event_id)
    db.session.execute(insert_statement)
    user.saved_events.append(event)
    db.session.commit()
    return success_response(user.serialize())

@app.route("/users/<int:user_id>/recipes/<int:recipe_id>/save", methods=["POST"])
def save_recipe(user_id, recipe_id):
    """
    Endpoint for saving a recipe for a user
    """
    # Check if user exists
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    
    #Check if recipe exists
    recipe = Recipe.query.filter_by(id=recipe_id).first()
    if recipe is None:
        return failure_response("Recipe not found!")

    # Add recipe to user's saved recipes
    insert_statement = user_recipe_association_table.insert().values(user_id = user_id, recipe_id = recipe_id)
    db.session.execute(insert_statement)
    user.saved_recipes.append(recipe)
    db.session.commit()
    return success_response(user.serialize())

@app.route("/users/<int:user_id>/events/<int:event_id>/attend", methods=["POST"])
def attend_event(user_id, event_id):
    """
    Endpoint for a user to attend an event
    """
    # Check if user exists
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    
    #Check if event exists
    event = Event.query.filter_by(id=event_id).first()
    if event is None:
        return failure_response("Event not found!")

    # Add event to user's attending events
    insert_statement = user_event_attendance_association_table.insert().values(user_id = user_id, event_id = event_id)
    db.session.execute(insert_statement)
    user.events_attending.append(event)
    db.session.commit()
    event.number_going += 1
    return success_response(user.serialize())
    
@app.route("/users/<int:user_id>/events/<int:event_id>/unattend", methods=["POST"])
def unattend_event(user_id, event_id):
    """
    Endpoint for a user to unattend an event
    """
    # Check if user exists
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    
    #Check if event exists
    event = Event.query.filter_by(id=event_id).first()
    if event is None:
        return failure_response("Event not found!")
    
    # Remove event from user's attending events
    delete_statement = user_event_attendance_association_table.delete().where(user_event_attendance_association_table.c.user_id == user_id).where(user_event_attendance_association_table.c.event_id == event_id)
    db.session.execute(delete_statement)
    if event in user.events_attending:
        user.events_attending.remove(event)
    db.session.commit()
    event.number_going -= 1
    return success_response(user.serialize())

# -- ASSET ROUTES ------------------------------------------------------

@app.route("/upload/", methods=["POST"])
def upload():
    """
    Endpoint for uploading an image to AWS given its base 64 form, then
    storing/returning the URL of that image
    """
    body = json.loads(request.data)
    image_data = body.get("image_data")

    if image_data is None:
        return failure_response("No base64 image found")
    
    asset = Asset(image_data = image_data)
    db.session.add(asset)
    db.session.commit()

    return success_response(asset.serialize(), 201)

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

@app.route("/stories/")
def get_all_stories(): 
    """
    Endpoint for getting all stories for a user 
    """
    # Retrieve all stories for a user 
    stories = Story.query.all()

    return success_response({"stories": [story.serialize() for story in stories]})

@app.route("/users/<int:user_id>/stories/")
def get_stories(user_id): 
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
    Endpoint for getting a specific story for a user by id
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
    Endpoint updating specific story for a user by id
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

@app.route("/events/")
def get_all_events(): 
    """
    Endpoint for getting all events for a user 
    """
    # Retrieve all events for a user 
    events = Event.query.all()

    return success_response({"events": [event.serialize() for event in events]})

@app.route("/users/<int:user_id>/events/", methods=["POST"])
def create_event(user_id):
    """
    Endpoint for creating an event
    """
    # Check if user exists
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    body = json.loads(request.data)

    # Create new event 
    new_event = Event(
        user_id = user_id,
        image_url = body.get("image_url"),
        title = body.get("title"),
        caption = body.get("caption"),
        number_going = body.get("number_going"),
        # time = datetime.fromisoformat(body.get("time")),
        location = body.get("location"),
        created_at = datetime.now()
    )

    # Add and commit to database 
    db.session.add(new_event)
    db.session.commit()

    return success_response(new_event.serialize(), 201)

@app.route("/users/<int:user_id>/events/")
def get_events(user_id):
    """
    Endpoint for getting all events for a user
    """
    # Check if user exists 
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    # Retrieve all events for a user 
    events = Event.query.filter_by(user_id=user_id).all()
    return success_response({"events": [event.serialize() for event in events]})

@app.route("/users/<int:user_id>/events/<int:event_id>/")
def get_event(event_id, user_id):
    """Endpoint for getting a specific event for a user by id"""
    # Check if user exists 
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    # Check if event exists
    event = Event.query.filter_by(id=event_id, user_id=user_id).first()
    if event is None:
        return failure_response("Event not found!")
    
    return success_response(event.serialize())

@app.route("/users/<int:user_id>/events/<int:event_id>/", methods=["DELETE"])
def delete_event(event_id, user_id):
    """Endpoint for deleting a specific event for a user by id"""
    # Check if user exists 
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    # Check if event exists
    event = Event.query.filter_by(id=event_id, user_id=user_id).first()
    if event is None:
        return failure_response("Event not found!")
    
    db.session.delete(event)
    db.session.commit()
    return success_response(event.serialize())

@app.route("/users/<int:user_id>/events/<int:event_id>/", methods=["POST"])
def update_event(event_id, user_id):
    """Endpoint for updating a specific event for a user by id"""
    # Check if user exists
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    
    # Check if event exists
    event = Event.query.filter_by(id=event_id, user_id=user_id).first()
    if event is None:
        return failure_response("Event not found!")
    
    body = json.loads(request.data)
    event.image_url = body.get("image_url")
    event.title = body.get("title")
    event.caption = body.get("caption")
    event.time = datetime.fromisoformat(body.get("time"))
    event.location = body.get("location")

    db.session.commit()
    return success_response(event.serialize())


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
            - Step-by-step instructions (a list of strings e.g. [""Boil the spaghetti.", "Prepare the Bolognese sauce.", "Serve the sauce on top of the spaghetti."])
            - Number of servings (as an integer)
            - Estimated preparation time in minutes 
            - Rating (from 1-10 the level of difficulty of making the recipe)
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

@app.route("/recipes/")
def get_all_recipes():
    """
    Endpoint for getting all recipes for all users
    """
    # Retrieve all recipes from the database
    recipes = Recipe.query.all()

    # Serialize the recipes and their associated ingredients
    recipes_data = []
    for recipe in recipes:
        # Fetch ingredients for this recipe along with their quantities and units
        ingredients = db.session.query(
            recipe_ingredient_association_table.c.ingredient_id,
            recipe_ingredient_association_table.c.quantity,
            recipe_ingredient_association_table.c.unit,
            Ingredient.name,
            Ingredient.image_url
        ).join(Ingredient, recipe_ingredient_association_table.c.ingredient_id == Ingredient.id).filter(
            recipe_ingredient_association_table.c.recipe_id == recipe.id
        ).all()

        formatted_ingredients = [
            {
                "id": ingredient.ingredient_id,
                "name": ingredient.name,
                "quantity": ingredient.quantity,
                "unit": ingredient.unit,
                "image_url": ingredient.image_url
            }
            for ingredient in ingredients
        ]

        recipe_data = recipe.serialize()
        recipe_data["ingredients"] = formatted_ingredients
        recipes_data.append(recipe_data)

    return success_response({"recipes": recipes_data})

@app.route("/users/<int:user_id>/recipes/")
def get_recipes(user_id):
    """
    Endpoint for getting all recipes (both custom and AI-generated) for a user 
    """
    # Check if user exists 
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    # Retrieve all recipes for a user (both custom and AI-generated)
    recipes = Recipe.query.filter_by(user_id=user_id).all()

    recipes_data = []
    for recipe in recipes:
        # Fetch ingredients for this recipe along with their quantities and units
        ingredients = db.session.query(
            recipe_ingredient_association_table.c.ingredient_id,
            recipe_ingredient_association_table.c.quantity,
            recipe_ingredient_association_table.c.unit,
            Ingredient.name,
            Ingredient.image_url
        ).join(Ingredient, recipe_ingredient_association_table.c.ingredient_id == Ingredient.id).filter(
            recipe_ingredient_association_table.c.recipe_id == recipe.id
        ).all()

        # Debugging: Print ingredients to check if they are being fetched correctly
        print(f"Recipe ID {recipe.id} Ingredients: {ingredients}")

        formatted_ingredients = []
        for ingredient in ingredients:
            formatted_ingredients.append({
                "id": ingredient.ingredient_id,
                "name": ingredient.name,
                "quantity": ingredient.quantity,
                "unit": ingredient.unit,
                "image_url": ingredient.image_url
            })

        recipe_data = recipe.serialize()
        recipe_data["ingredients"] = formatted_ingredients
        recipes_data.append(recipe_data)

    return success_response({"recipes": recipes_data})

@app.route("/users/<int:user_id>/recipes-custom/")
def get_custom_recipes(user_id):
    """
    Endpoint for getting all custom recipes for a user 
    """
    # Check if user exists 
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    # Retrieve all recipes for a user 
    recipes = Recipe.query.filter_by(user_id=user_id, ai_generated=False).all()

    recipes_data = []
    for recipe in recipes:
        # Fetch ingredients for this recipe along with their quantities and units
        ingredients = db.session.query(
            recipe_ingredient_association_table.c.ingredient_id,
            recipe_ingredient_association_table.c.quantity,
            recipe_ingredient_association_table.c.unit,
            Ingredient.name,
            Ingredient.image_url
        ).join(Ingredient, recipe_ingredient_association_table.c.ingredient_id == Ingredient.id).filter(
            recipe_ingredient_association_table.c.recipe_id == recipe.id
        ).all()

        print(f"Recipe ID {recipe.id} Ingredients: {ingredients}")

        formatted_ingredients = []
        for ingredient in ingredients:
            # Format the ingredients to include quantity and unit
            formatted_ingredients.append({
                    "id": ingredient.ingredient_id,
                    "name": ingredient.name,
                    "quantity": ingredient.quantity,
                    "unit": ingredient.unit,
                    "image_url": ingredient.image_url
                })

        recipe_data = recipe.serialize()
        recipe_data["ingredients"] = formatted_ingredients
        recipes_data.append(recipe_data)
    
    return success_response({"recipes": recipes_data})

@app.route("/users/<int:user_id>/recipes-ai/")
def get_generated_recipes(user_id):
    """
    Endpoint for getting al generated recipes for a user 
    """
    # Check if user exists 
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    # Retrieve all recipes for a user 
    recipes = Recipe.query.filter_by(user_id=user_id, ai_generated=True).all()

    recipes_data = []
    for recipe in recipes:
        # Fetch ingredients for this recipe along with their quantities and units
        ingredients = db.session.query(
            recipe_ingredient_association_table.c.ingredient_id,
            recipe_ingredient_association_table.c.quantity,
            recipe_ingredient_association_table.c.unit,
            Ingredient.name,
            Ingredient.image_url
        ).join(Ingredient, recipe_ingredient_association_table.c.ingredient_id == Ingredient.id).filter(
            recipe_ingredient_association_table.c.recipe_id == recipe.id
        ).all()

        formatted_ingredients = []
        for ingredient in ingredients:
            # Format the ingredients to include quantity and unit
            formatted_ingredients.append({
                    "id": ingredient.ingredient_id,
                    "name": ingredient.name,
                    "quantity": ingredient.quantity,
                    "unit": ingredient.unit,
                    "image_url": ingredient.image_url
                })

        recipe_data = recipe.serialize()
        recipe_data["ingredients"] = formatted_ingredients
        recipes_data.append(recipe_data)
    
    return success_response({"recipes": recipes_data})

@app.route("/users/<int:user_id>/recipes/<int:recipe_id>/")
def get_recipe(user_id, recipe_id):
    """
    Endpoint for getting a specific recipe for a user by id
    """
    # Check if user exists 
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    
    # Retrieve specific story
    recipe = Recipe.query.filter_by(id=recipe_id, user_id=user_id).first()

    # Check if story exists for a given user
    if recipe is None:
        return failure_response("Recipe not found for this user!")
    
    # Fetch ingredients for this recipe along with their quantities and units
    ingredients = db.session.query(
        recipe_ingredient_association_table.c.ingredient_id,
        recipe_ingredient_association_table.c.quantity,
        recipe_ingredient_association_table.c.unit,
        Ingredient.name,
        Ingredient.image_url
    ).join(Ingredient, recipe_ingredient_association_table.c.ingredient_id == Ingredient.id).filter(
        recipe_ingredient_association_table.c.recipe_id == recipe.id
    ).all()

    # Format the ingredients to include quantity and unit
    formatted_ingredients = [
        {
            "id": ingredient.ingredient_id,
            "name": ingredient.name,
            "quantity": ingredient.quantity,
            "unit": ingredient.unit,
            "image_url": ingredient.image_url
        }
        for ingredient in ingredients
    ]

    # Serialize the recipe and include formatted ingredients
    recipe_data = recipe.serialize()
    recipe_data["ingredients"] = formatted_ingredients

    return success_response(recipe_data)

@app.route("/users/<int:user_id>/recipes/", methods=["POST"])
def create_recipe(user_id):
    """
    Endpoint for creating a recipe
    """
    # Check if user exists 
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")

    # Load data 
    body = json.loads(request.data)

    # Ensure instructions is a list (array) of strings
    instructions = body.get("instructions", [])
    if not isinstance(instructions, list):
        return failure_response("Instructions must be a list of strings", 400)

    # Create new recipe
    new_recipe = Recipe(
        title = body.get("title"),
        description = body.get("description"),
        instructions = instructions,
        user_id = user_id,
        rating = body.get("rating"),
        time = body.get("time"),
        servings = body.get("servings"),
        image_url = body.get("image_url"),
        created_at = datetime.now(),
        ai_generated = False
    )

    db.session.add(new_recipe)
    db.session.flush()

    # Get additional data
    ingredients_data = body.get("ingredients")

    # associate ingredient(s) to recipe
    for ingredient in ingredients_data:
        ingredient_id = ingredient.get("ingredient_id")
        quantity = ingredient.get("quantity")
        unit = ingredient.get("unit")

        db.session.execute(recipe_ingredient_association_table.insert(), {
        "recipe_id": new_recipe.id,
        "ingredient_id": ingredient_id,
        "quantity": quantity,
        "unit": unit
        })
    
    db.session.commit()

    associated_ingredients = db.session.query(recipe_ingredient_association_table).filter_by(recipe_id=new_recipe.id).all()
    print(f"Associated ingredients for recipe {new_recipe.id}: {associated_ingredients}")


    return success_response(new_recipe.serialize(), 201)

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
    ingredients = user.ingredients
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
        created_at = datetime.now(),
        ai_generated = True
    )
    db.session.add(new_recipe)
    db.session.flush()

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
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    
    new_ingredient = Ingredient(
        user_id = user_id, 
        name = body.get("name"),
        image_url = body.get("image_url")
    )

    # Add the new ingredient to the user's ingredient list via the relationship
    user.ingredients.append(new_ingredient)

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

    # Use the relationship to retrieve all ingredients for the user
    ingredients = user.ingredients

    return success_response({"ingredients": [ingredient.simple_serialize() for ingredient in ingredients]})

@app.route("/users/<int:user_id>/ingredients/<int:ingredient_id>")
def get_ingredient(user_id, ingredient_id):
    """
    Endpoint for getting a specific ingredient for a user by id
    """
    # Check if user exists
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return failure_response("User not found!")
    
    # Retrieve the specific ingredient for the user
    ingredient = next((ing for ing in user.ingredients if ing.id == ingredient_id), None)
    if ingredient is None: 
        return failure_response("Ingredient not found for this user!")

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

    # Check if ingredient exists in the user's ingredient list
    ingredient = next((ing for ing in user.ingredients if ing.id == ingredient_id), None)
    if ingredient is None:
        return failure_response("Ingredient not found for this user!")

    # Remove the ingredient from the user's list
    user.ingredients.remove(ingredient)

    # Commit the changes to the database
    db.session.commit()
    
    return success_response(ingredient.simple_serialize())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
