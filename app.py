from datetime import datetime
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import os
from data_models import db, Author, Book
app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"

db.init_app(app)

# with app.app_context():
#     db.create_all()

@app.route("/add_author", methods=["GET", "POST"])
def add_author():
    if request.method == "POST":
        name = request.form["name"]
        
        birthdate = datetime.strptime(
            request.form["birthdate"], "%Y-%m-%d"
        ).date()

        date_of_death = datetime.strptime(
            request.form["date_of_death"], "%Y-%m-%d"
        ).date() if request.form["date_of_death"] else None

        author = Author(
            name=name,
            birthdate=birthdate,
            date_of_death=date_of_death
        )

        db.session.add(author)
        db.session.commit()

        return render_template(
            "add_author.html",
            success="Author successfully added!"
        )

    return render_template("add_author.html")