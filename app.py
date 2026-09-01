from datetime import datetime
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import os
from data_models import db, Author, Book
app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"

db.init_app(app)

with app.app_context():
    db.create_all()

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


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    authors = Author.query.all()

    if request.method == "POST":
        isbn = request.form["isbn"]
        title = request.form["title"]
        publication_year = request.form["publication_year"]
        author_id = request.form["author_id"]

        book = Book(
            isbn=isbn,
            title=title,
            publication_year=publication_year,
            author_id=author_id
        )

        db.session.add(book)
        db.session.commit()

        return render_template(
            "add_book.html",
            authors=authors,
            success="Book successfully added!"
        )

    return render_template("add_book.html", authors=authors)


@app.route("/")
def home():
    books = Book.query.all()

    return render_template("home.html", books=books)


if __name__ == "__main__":
    app.run(debug=True)