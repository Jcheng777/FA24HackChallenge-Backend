from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# association tables

""" 
Association table between Recipes and Ingredients
"""
recipe_ingredient_association_table = db.Table(
  "recipe_ingredient_association",
  db.Model.metadata,
  db.Column("recipe_id", db.Integer, db.ForeignKey("recipes.id")),
  db.Column("ingredient_id", db.Integer, db.ForeignKey("ingredients.id")),
  db.Column("quantity", db.String, nullable=False),
  db.Column("unit", db.String, nullable=False)
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

class User(db.Model): 
  """ 
  User Model
  """
  __tablename__ = "users"
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  username = db.Column(db.String, nullable=False)
  password = db.Column(db.String, nullable=False)
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
    self.password = kwargs.get("password", "")

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
      "ingredients": [i.serialize() for i in self.ingredients],
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
  time = db.Column(db.DateTime, nullable=False)
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
    self.number_going = 0
    self.time = kwargs.get("time", "")
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
      "title": self.title,
      "caption": self.caption,
      "number_going": self.number_going,
      "time": self.time.isoformat(),
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
      "time": self.time.isoformat(),
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
  instructions = db.Column(db.String, nullable=False)
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
  # user = db.relationship("User", back_populates="recipes")
  # rating = db.Column(db.Integer, nullable=True)
  time = db.Column(db.Integer, nullable=False)
  servings = db.Column(db.Integer, nullable=False)
  image_url = db.Column(db.String, nullable=True)
  ingredients = db.relationship("Ingredient", secondary=recipe_ingredient_association_table, back_populates = "recipes")
  created_at = db.Column(db.DateTime, nullable=False)
  users_saved = db.relationship("User", secondary="users_recipes_association", cascade = "delete")

  def __init__(self, **kwargs):
    """
    Initialize Recipe object/entry
    """
    self.title = kwargs.get("title", "")
    self.description = kwargs.get("description", "")
    self.instructions = kwargs.get("instructions", "")
    self.user_id = kwargs.get("user_id", "")
    # self.user = kwargs.get("user")
    # self.rating = kwargs.get("rating")
    self.time = kwargs.get("time", 0)
    self.servings = kwargs.get("servings", 1)
    self.image_url = kwargs.get("image_url", "")
    self.created_at = kwargs.get("created_at", "")

  
  def serialize(self):
    """ 
    Serialize a recipe object
    """
    return {
      "id": self.id,
      "title": self.title,
      "description": self.description,
      "instructions": self.instructions,
      # "user": self.user,
      # "rating": self.rating,
      "time": self.time,
      "servings": self.servings,
      "image_url": self.image_url,
      "ingredients": [i.serialize() for i in self.ingredients],
      "created_at": self.created_at.isoformat()
    }
  
  def simple_serialize(self):
    """ 
    Serialize a recipe object without user
    """
    return {
      "id": self.id,
      "title": self.title,
      "description": self.description,
      "instructions": self.instructions,
      # "rating": self.rating,
      "time": self.time,
      "servings": self.servings,
      "image_url": self.image_url,
      "ingredients": [i.serialize() for i in self.ingredients],
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
    self.user_id = kwargs.get("user_id")
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