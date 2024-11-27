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

class Recipe(db.Model): 
  """ 
  Recipe Model
  """
  __tablename__ = "recipes"

class Ingredient(db.Model): 
  """ 
  Ingredient Model
  """
  __tablename__ = "ingredients"