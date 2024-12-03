from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# implement database model classes

class User(db.Model): 
  """ 
  User Model
  """
  __tablename__ = "users"
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  username = db.Column(db.String, nullable=False)
  email = db.Column(db.String, nullable=False)
  password = db.Column(db.String, nullable=False)
  posts = db.relationship("Post", cascade="delete")
  recipes = db.relationship("Recipe", cascade="delete")
  
  
  def __init__(self, **kwargs):
    """
    Initialize User object/entry
    """
    self.username = kwargs.get("username", "")
    self.email = kwargs.get("email", "")
    self.password = kwargs.get("password", "")

  def serialize(self):
    """ 
    Serialize a user object
    """
    return {
      "id": self.id,
      "username": self.username,
      "posts": [p.serialize() for p in self.posts]
    }


class Post(db.Model): 
  """ 
  Post Model
  """
  __tablename__ = "posts"
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
  recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=True)
  image_url = db.Column(db.String, nullable=False)
  title = db.Column(db.String, nullable=False)
  caption = db.Column(db.String, nullable=True)
  created_at = db.Column(db.DateTime, nullable=False)

  def __init__(self, **kwargs):
    """
    Initialize Post object/entry
    """
    self.user_id = kwargs.get("user_id", "")
    self.recipe_id = kwargs.get("recipe_id")
    self.image_url = kwargs.get("image_url", "")
    self.title = kwargs.get("title", "")
    self.caption = kwargs.get("caption", "")
    self.created_at = kwargs.get("created_at")

  def serialize(self):
    """ 
    Serialize a post object
    """
    return {
      "id": self.id,
      "user_id": self.user_id,
      "recipe_id": self.recipe_id,
      "image_url": self.image_url,
      "title": self.title,
      "caption": self.caption,
      "created_at": self.created_at.isoformat()
    }


recipe_ingredient_association_table = db.Table(
  """ 
  Association table between Recipes and Ingredients
  """
  "recipe_ingredient_association",
  db.Model.metadata,
  db.Column("recipe_id", db.Integer, db.ForeignKey("recipes.id")),
  db.Column("ingredient_id", db.Integer, db.ForeignKey("ingredients.id")),
  db.Column("quantity", db.String, nullable=False),
  db.Column("unit", db.String, nullable=False)
)


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
  post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
  rating = db.Column(db.Integer, nullable=True)
  time = db.Column(db.Integer, nullable=False)
  servings = db.Column(db.Integer, nullable=False)
  image_url = db.Column(db.String, nullable=False)
  ingredients = db.relationship("Ingredient", secondary=recipe_ingredient_association_table, back_populates = "recipes")

  def __init__(self, **kwargs):
    """
    Initialize Recipe object/entry
    """
    self.title = kwargs.get("title", "")
    self.description = kwargs.get("description", "")
    self.instructions = kwargs.get("instructions", "")
    self.user_id = kwargs.get("user_id", "")
    self.post_id = kwargs.get("post_id", "")
    self.rating = kwargs.get("rating", None)
    self.time = kwargs.get("time", 0)
    self.servings = kwargs.get("servings", 1)
    self.image_url = kwargs.get("image_url", "")

  
  def serialize(self):
    """ 
    Serialize a recipe object
    """
    return {
      "id": self.id,
      "title": self.title,
      "description": self.description,
      "instructions": self.instructions,
      "user_id": self.user_id,
      "rating": self.rating,
      "time": self.time,
      "servings": self.servings,
      "image_url": self.image_url,
      "ingredients": [i.serialize() for i in self.ingredients]
    }


class Ingredient(db.Model): 
  """ 
  Ingredient Model
  """
  __tablename__ = "ingredients"
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  name = db.Column(db.String, nullable=False)
  recipes = db.relationship("Recipe", secondary=recipe_ingredient_association_table, back_populates="ingredients")

  # Relationship to RecipeIngredientAssociation
  # ingredient_recipes = db.relationship(
  #     "RecipeIngredientAssociation", back_populates="ingredient", cascade="all, delete-orphan"
  # )

  def __init__(self, **kwargs):
    """
    Initialize Ingredient object/entry
    """
    self.name = kwargs.get("name", "")
  
  def serialize(self):
    """ 
    Serialize a recipe object
    """
    return {
      "id": self.id,
      "name": self.name
    }