from db import db
from flask import Flask

app = Flask(__name__)
db_filename = "cms.db"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.create_all()


# your routes here


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
