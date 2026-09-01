from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
from data_models import db, Author, Book
app = Flask(__name__)
app.secret_key = "dev-secret-key"

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
    search = request.args.get("search", "")
    sort_by = request.args.get("sort_by", "title")

    if search:
        books = Book.query.filter(Book.title.ilike(f"%{search}%")).all()
    elif sort_by == "author":
        books = Book.query.join(Author).order_by(Author.name).all()
    else:
        books = Book.query.order_by(Book.title).all()

    return render_template("home.html", books=books, search=search)


@app.route("/book/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)

    db.session.delete(book)
    db.session.commit()

    flash("The book was successfully deleted!")

    return redirect(url_for("home"))


@app.route("/book/<int:book_id>")
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)

    return render_template("book_detail.html", book=book)


@app.route("/author/<int:author_id>")
def author_detail(author_id):
    author = Author.query.get_or_404(author_id)

    return render_template("author_detail.html", author=author)


@app.route("/author/<int:author_id>/delete", methods=["POST"])
def delete_author(author_id):
    author = Author.query.get_or_404(author_id)

    db.session.delete(author)
    db.session.commit()

    flash("The Author was successfully deleted!")

    return redirect(url_for("home"))


@app.route("/book/<int:book_id>/rate", methods=["POST"])
def rate_book(book_id):
    book = Book.query.get_or_404(book_id)

    rating = int(request.form["rating"])

    if 1 <= rating <= 10:
        book.rating = rating
        db.session.commit()
        flash("Book was rated successfully!")
    else:
        flash("The rating must be between 1 and 10!")

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)