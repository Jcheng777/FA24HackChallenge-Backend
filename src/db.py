from flask_sqlalchemy import SQLAlchemy
import base64
import boto3
import datetime 
import io 
from io import BytesIO
from mimetypes import guess_type, guess_extension
import os 
from PIL import Image 
import random
import re 
import string
from dotenv import load_dotenv

import datetime
import bcrypt
import hashlib
import os
import json

db = SQLAlchemy()

load_dotenv()

EXTENSIONS = ["png", "gif", "jpg", "jpeg"]
BASE_DIR = os.getcwd()
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")

S3_BASE_URL = f"https://{S3_BUCKET_NAME}.s3.us-east-1.amazonaws.com"

# association tables

""" 
Association table between Recipes and Ingredients
"""
recipe_ingredient_association_table = db.Table(
  "recipe_ingredient_association",
  db.Model.metadata,
  db.Column("recipe_id", db.Integer, db.ForeignKey("recipes.id")),
  db.Column("ingredient_id", db.Integer, db.ForeignKey("ingredients.id")),
  db.Column("quantity", db.String, nullable=True),
  db.Column("unit", db.String, nullable=True)
)

""" 
Association table between Users and Ingredients
"""
user_ingredient_association_table = db.Table(
  "user_ingredient_association",
  db.Model.metadata,
  db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
  db.Column("ingredient_id", db.Integer, db.ForeignKey("ingredients.id"))
)

""" 
Association table between Users and Recipes
"""
user_recipe_association_table = db.Table(
  "users_recipes_association",
  db.Model.metadata,
  db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
  db.Column("recipe_id", db.Integer, db.ForeignKey("recipes.id")),
  db.UniqueConstraint("user_id", "recipe_id", name="unique_user_recipe")
)

""" 
Association table between Users and Events
"""
user_event_association_table = db.Table(
  "users_events_association",
  db.Model.metadata,
  db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
  db.Column("event_id", db.Integer, db.ForeignKey("events.id")),
  db.UniqueConstraint("user_id", "event_id", name="unique_user_event")
)

""" 
Association table between Users and Stories
"""
user_story_association_table = db.Table(
  "users_stories_association",
  db.Model.metadata,
  db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
  db.Column("story_id", db.Integer, db.ForeignKey("stories.id")),
  db.UniqueConstraint("user_id", "story_id", name="unique_user_story")
)

""" 
Association table between Users and Events (for event attendance purposes)
"""
user_event_attendance_association_table = db.Table(
  "users_events_attendance_association",
  db.Model.metadata,
  db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
  db.Column("event_id", db.Integer, db.ForeignKey("events.id")),
  db.UniqueConstraint("user_id", "event_id", name="unique_user_event_attendance")
)



# database model classes

class Asset(db.Model):
  """
  Asset Model
  """
  __tablename__ = "asset"
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  base_url = db.Column(db.String, nullable=False)
  salt = db.Column(db.String, nullable=False)
  extension = db.Column(db.String, nullable=False)
  width = db.Column(db.Integer, nullable=False)
  height = db.Column(db.Integer, nullable=False)
  created_at = db.Column(db.DateTime, nullable=False)

  def __init__(self, **kwargs):
    """
    Initializes an Asset object
    """
    self.create(kwargs.get("image_data"))

  def serialize(self):
    """ 
    Serializes an Asset Object
    """
    return {
      "id": self.id,
      "url": f"{self.base_url}/{self.salt}.{self.extension}",
      "created_at": str(self.created_at)
    }
  
  def create(self, image_data):
    """
    Given an image in base64 encoding, does the following:
    1. Rejects th image if it is not a supported filename
    2. Generate a random string for the image filename
    3. Decodes the image and attepts to upload to AWS
    """

    try:
      # Ensure image_data is properly passed
      if not image_data:
        raise ValueError("No image data provided")

      ext = guess_extension(guess_type(image_data)[0])[1:]

      if ext not in EXTENSIONS:
        raise Exception(f"Exception {ext} is not valid!")
      
      salt = "".join(
        random.SystemRandom().choice(
          string.ascii_uppercase + string.digits
        )
        for _ in range(16)
      )

      img_str = re.sub("^data:image/.+;base64,", "", image_data)
      img_data = base64.b64decode(img_str)
      img = Image.open(BytesIO(img_data))

      self.base_url = S3_BASE_URL
      self.salt = salt
      self.extension = ext 
      self.width = img.width 
      self.height = img.height
      self.created_at = datetime.datetime.now()
 
      img_filename = f"{self.salt}.{self.extension}"

      self.upload(img, img_filename)

    except Exception as e:
      print(f"Error when creating image: {e}")
    

  def upload(self, img, img_filename):
    """
    Attempts to upload the image into the specified s3 bucket
    """
    try:
      # save image into temporary
      img_temp_loc = f"{BASE_DIR}/{img_filename}"
      img.save(img_temp_loc)

      #upload image into S3 bucket
      s3_client = boto3.client("s3")
      s3_client.upload_file(img_temp_loc, S3_BUCKET_NAME, img_filename)

      s3_resource = boto3.resource("s3")
      object_acl = s3_resource.ObjectAcl(S3_BUCKET_NAME, img_filename)
      object_acl.put(ACL="public-read")

      # remove image from temp location 
      os.remove(img_temp_loc)
    except Exception as e:
      print(f"Error when uploading an image: {e}") 

class User(db.Model): 
  """ 
  User Model
  """
  __tablename__ = "users"
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  username = db.Column(db.String, nullable=False, unique=True)
  password_digest = db.Column(db.String, nullable=False)
  session_token = db.Column(db.String, nullable=True)
  session_expiration = db.Column(db.DateTime, nullable=True)
  refresh_token = db.Column(db.String, nullable=True)
  recipes = db.relationship("Recipe", cascade="delete")
  stories = db.relationship("Story", cascade="delete")
  events = db.relationship("Event", cascade="delete")
  ingredients = db.relationship("Ingredient", secondary="user_ingredient_association", back_populates="users")
  saved_recipes = db.relationship("Recipe", secondary="users_recipes_association", back_populates="users_saved")
  saved_stories = db.relationship("Story", secondary="users_stories_association", back_populates="users_saved")
  saved_events = db.relationship("Event", secondary="users_events_association", back_populates="users_saved")
  events_attending = db.relationship("Event", secondary="users_events_attendance_association", back_populates="users_attending")
  
  def __init__(self, **kwargs):
    """
    Initialize User object/entry
    """
    self.username = kwargs.get("username", "")
    self.password_digest = bcrypt.hashpw(kwargs.get("password").encode("utf8"), bcrypt.gensalt(rounds=13))
    self.renew_session()

  def _url_safe_b64(self):
    """
    Generate a url-safe base64 encoded hex string
    """
    return hashlib.sha1(os.urandom(64)).hexdigest()

  def renew_session(self):
    """
    Renew session
    """
    self.session_token = self._url_safe_b64()
    self.refresh_token = self._url_safe_b64()
    self.session_expiration = datetime.datetime.now() + datetime.timedelta(days=1)

  def verify_password(self, password):
    """
    Verify password
    """
    return bcrypt.checkpw(password.encode("utf8"), self.password_digest) 
  
  def verify_session_token(self, session_token):
    """
    Verify session token
    """
    return self.session_token == session_token and datetime.datetime.now() < self.session_expiration


  def verify_refresh_token(self, refresh_token):
    """
    Verify refresh token
    """
    return self.refresh_token == refresh_token

  def serialize(self):
    """ 
    Serialize a user object
    """
    return {
      "id": self.id,
      "username": self.username,
      "recipes": [r.simple_serialize() for r in self.recipes],
      "stories": [s.simple_serialize() for s in self.stories],
      "events": [e.simple_serialize() for e in self.events],
      "ingredients": [i.simple_serialize() for i in self.ingredients],
      "saved_recipes": [r.simple_serialize() for r in self.saved_recipes],
      "saved_stories": [s.simple_serialize() for s in self.saved_stories],
      "saved_events": [e.simple_serialize() for e in self.saved_events],
      "events_attending": [e.simple_serialize() for e in self.events_attending]
    }


class Story(db.Model): 
  """ 
  Story Model
  """
  __tablename__ = "stories"
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
  # user = db.relationship("User", back_populates="stories")
  image_url = db.Column(db.String, nullable=False)
  title = db.Column(db.String, nullable=False)
  caption = db.Column(db.String, nullable=False)
  created_at = db.Column(db.DateTime, nullable=False)
  users_saved = db.relationship("User", secondary="users_stories_association", cascade = "delete")

  def __init__(self, **kwargs):
    """
    Initialize Story object/entry
    """
    self.user_id = kwargs.get("user_id", "")
    # self.user = kwargs.get("user")
    self.image_url = kwargs.get("image_url", "")
    self.title = kwargs.get("title", "")
    self.caption = kwargs.get("caption", "")
    self.created_at = kwargs.get("created_at", "")

  def serialize(self):
    """ 
    Serialize a story object
    """
    return {
      "id": self.id,
      # "user": self.user,
      "image_url": self.image_url,
      "title": self.title,
      "caption": self.caption,
      "created_at": self.created_at.isoformat()
    }
  
  def simple_serialize(self):
    """
    Serialize a story object without user
    """
    return {
      "id": self.id,
      "image_url": self.image_url,
      "title": self.title,
      "caption": self.caption,
      "created_at": self.created_at.isoformat()
    }


class Event(db.Model): 
  """ 
  Event Model
  """
  __tablename__ = "events"
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
  # user = db.relationship("User", back_populates="events")
  image_url = db.Column(db.String, nullable=False)
  title = db.Column(db.String, nullable=False)
  caption = db.Column(db.String, nullable=False)
  number_going = db.Column(db.Integer, nullable=False)
  # time = db.Column(db.DateTime, nullable=True)
  location = db.Column(db.String, nullable=False)
  created_at = db.Column(db.DateTime, nullable=False)
  users_saved = db.relationship("User", secondary="users_events_association", cascade = "delete")
  users_attending = db.relationship("User", secondary="users_events_attendance_association", back_populates="events_attending", cascade="delete")

  def __init__(self, **kwargs):
    """
    Initialize Event object/entry
    """
    self.user_id = kwargs.get("user_id", "")
    # self.user = kwargs.get("user")
    self.image_url = kwargs.get("image_url", "")
    self.title = kwargs.get("title", "")
    self.caption = kwargs.get("caption", "")
    self.number_going = kwargs.get("number_going", 0)
    # self.time = kwargs.get("time", "")
    self.location = kwargs.get("location", "")
    self.created_at = kwargs.get("created_at", "")

  def serialize(self):
    """ 
    Serialize an event object
    """
    return {
      "id": self.id,
      # "user": self.user,
      "image_url": self.image_url,
      "user_id": self.user_id,
      "title": self.title,
      "caption": self.caption,
      "number_going": self.number_going,
      # "time": self.time.isoformat(),
      "location": self.location,
      "created_at": self.created_at.isoformat()
    }
  
  def simple_serialize(self):
    """
    Serialize an event object without user
    """
    return {
      "id": self.id,
      "image_url": self.image_url,
      "title": self.title,
      "caption": self.caption,
      "number_going": self.number_going,
      # "time": self.time.isoformat(),
      "location": self.location,
      "created_at": self.created_at.isoformat()
    }


class Recipe(db.Model): 
  """ 
  Recipe Model
  """
  __tablename__ = "recipes"
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  title = db.Column(db.String, nullable=False)
  description = db.Column(db.String, nullable=False) 
  instructions = db.Column(db.Text, nullable=True)
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
  # user = db.relationship("User", back_populates="recipes")
  rating = db.Column(db.Integer, nullable=True)
  time = db.Column(db.Integer, nullable=False)
  servings = db.Column(db.Integer, nullable=False)
  image_url = db.Column(db.String, nullable=True)
  ingredients = db.relationship("Ingredient", secondary=recipe_ingredient_association_table, back_populates = "recipes")
  created_at = db.Column(db.DateTime, nullable=False)
  users_saved = db.relationship("User", secondary="users_recipes_association", cascade = "delete")
  ai_generated = db.Column(db.Boolean, nullable=False)

  def __init__(self, **kwargs):
    """
    Initialize Recipe object/entry
    """
    self.title = kwargs.get("title", "")
    self.description = kwargs.get("description", "")
    self.instructions = json.dumps(kwargs.get("instructions", []))
    self.user_id = kwargs.get("user_id", "")
    # self.user = kwargs.get("user")
    self.rating = kwargs.get("rating")
    self.time = kwargs.get("time", 0)
    self.servings = kwargs.get("servings", 1)
    self.image_url = kwargs.get("image_url", "")
    self.created_at = kwargs.get("created_at", "")
    self.ai_generated = kwargs.get("ai_generated", False)

  
  def serialize(self):
    """ 
    Serialize a recipe object
    """
    return {
      "id": self.id,
      "title": self.title,
      "description": self.description,
      "instructions": json.loads(self.instructions),
      # "user": self.user,
      "rating": self.rating,
      "time": self.time,
      "servings": self.servings,
      "image_url": self.image_url,
      "ingredients": [i.simple_serialize() for i in self.ingredients],
      "created_at": self.created_at.isoformat(),
      "ai_generated": self.ai_generated
    }
  
  def simple_serialize(self):
    """ 
    Serialize a recipe object without user
    """
    return {
      "id": self.id,
      "title": self.title,
      "description": self.description,
      "instructions": json.loads(self.instructions),
      "rating": self.rating,
      "time": self.time,
      "servings": self.servings,
      "image_url": self.image_url,
      "ingredients": [i.simple_serialize() for i in self.ingredients],
      "created_at": self.created_at.isoformat()
    }


class Ingredient(db.Model): 
  """ 
  Ingredient Model
  """
  __tablename__ = "ingredients"
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  name = db.Column(db.String, nullable=False)
  image_url = db.Column(db.String, nullable=False)
  recipes = db.relationship("Recipe", secondary=recipe_ingredient_association_table, back_populates="ingredients")
  users = db.relationship("User", secondary="user_ingredient_association", back_populates="ingredients")


  # Relationship to RecipeIngredientAssociation
  # ingredient_recipes = db.relationship(
  #     "RecipeIngredientAssociation", back_populates="ingredient", cascade="all, delete-orphan"
  # )

  def __init__(self, **kwargs):
    """
    Initialize Ingredient object/entry
    """
    # self.user_id = kwargs.get("user_id")
    self.name = kwargs.get("name", "")
    self.image_url = kwargs.get("image_url", "")

  def simple_serialize(self):
    """ 
    Serialize an ingredient object without recipes
    """
    return {
      "id": self.id,
      "name": self.name,
      "image_url": self.image_url
    }