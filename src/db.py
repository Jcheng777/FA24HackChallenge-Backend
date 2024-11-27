from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# implement database model classes

class User(db.Model): 
  """ 
  User Model
  """
  __tablename__ = "users"


class Post(db.Model): 
  """ 
  Post Model
  """
  __tablename__ = "posts"

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

  def __init__(self, **kwargs):
    """
    Initialize Recipe object/entry
    """
    self.title = kwargs.get("title", "")
    self.done = kwargs.get("description", "")
    self.instructions = kwargs.get("instructions", "")
    self.meal_type = kwargs.get("meal_type", MealTypeEnum.any)
  
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