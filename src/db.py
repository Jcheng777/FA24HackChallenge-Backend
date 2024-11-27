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
  posts = db.relationship("Post", back_populates="users", cascade="delete")
  recipes = db.relationship("Recipe", back_populates="users", cascade="delete")
  
  
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
      "username": self.username
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
      "created_at": self.created_at
    }


class MealTypeEnum(enum.Enum):
  breakfast = "breakfast"
  lunch = "lunch"
  dinner = "dinner"
  snack = "snack"
  any = "any"

class Recipe(db.Model): 
  """ 
  Recipe Model
  """
  __tablename__ = "recipes"
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  title = db.Column(db.String, nullable=False)
  description = db.Column(db.String, nullable=False) 
  instructions = db.Column(db.String, nullable=False)
  meal_type = db.Column(db.Enum(MealTypeEnum), nullable=True)
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
  post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)

  def __init__(self, **kwargs):
    """
    Initialize Recipe object/entry
    """
    self.title = kwargs.get("title", "")
    self.description = kwargs.get("description", "")
    self.instructions = kwargs.get("instructions", "")
    self.meal_type = kwargs.get("meal_type", MealTypeEnum.any)
    self.user_id = kwargs.get("user_id", "")
    self.post_id = kwargs.get("post_id", "")
  
  def serialize(self):
    """ 
    Serialize a recipe object
    """
    return {
      "id": self.id,
      "title": self.title,
      "description": self.description,
      "instructions": self.instructions,
      "meal_type": self.meal_type,
    }


class Ingredient(db.Model): 
  """ 
  Ingredient Model
  """
  __tablename__ = "ingredients"
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  name = db.Column(db.String, nullable=False)

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

class RecipeIngredientAssociation(db.Model):
  """ 
  Association table between Recipes and Ingredients
  """
  __tablename__ = "recipe_ingredient_association"
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"))
  ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredient.id"))
  quantity = db.Column(db.String, nullable=False)
  unit = db.Column(db.String, nullable=False)

  # Relationships
  ingredient = db.relationship("Ingredient", back_populates="ingredient_recipes")

  def __init__(self, **kwargs):
    self.recipe_id = kwargs.get("recipe_id")
    self.ingredient_id = kwargs.get("ingredient_id")
    self.quantity = kwargs.get("quantity", "")
    self.unit = kwargs.get("unit", "")
  
  def serialize(self):
    return {
        "id": self.id,
        "recipe_id": self.recipe_id,
        "ingredient_id": self.ingredient_id,
        "quantity": self.quantity,
        "unit": self.unit,
        "ingredient_name": self.ingredient.name if self.ingredient else None
    }