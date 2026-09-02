"""Library Management Web Application.

This module sets up a Flask application connected to a SQLite database
to manage an inventory of books and authors, including a book
recommendation system powered by OpenAI.
"""

from datetime import datetime
import os

from data_models import Author, Book, db
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
import requests

app = Flask(__name__)
app.secret_key = "dev-secret-key"

client = OpenAI()

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"
)

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/add_author", methods=["GET", "POST"])
def add_author():
    """Handle the addition of a new author via GET or POST request.

    Returns:
        str: The rendered HTML template for the add author page.
    """
    if request.method == "POST":
        name = request.form["name"]
        
        birthdate = datetime.strptime(
            request.form["birthdate"], "%Y-%m-%d"
        ).date()
        
        date_of_death = (
            datetime.strptime(request.form["date_of_death"], "%Y-%m-%d").date()
            if request.form["date_of_death"]
            else None
        )
        
        author = Author(
            name=name, birthdate=birthdate, date_of_death=date_of_death
        )
        
        db.session.add(author)
        db.session.commit()
        
        return render_template(
            "add_author.html", success="Author successfully added!"
        )
    
    return render_template("add_author.html")


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    """Handle the addition of a new book via GET or POST request.

    Returns:
        str: The rendered HTML template for the add book page.
    """
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
            author_id=author_id,
        )
        
        db.session.add(book)
        db.session.commit()
        
        return render_template(
            "add_book.html", authors=authors, success="Book successfully added!"
        )
    
    return render_template("add_book.html", authors=authors)


@app.route("/")
def home():
    """Render the homepage with a grid of books.

    Supports filtering by search query and sorting by title or author.

    Returns:
        str: The rendered HTML template for the home page.
    """
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
    """Delete a specific book from the database.

    Args:
        book_id (int): The ID of the book to be deleted.

    Returns:
        werkzeug.wrappers.Response: A redirect response to the home route.
    """
    book = Book.query.get_or_404(book_id)
    
    db.session.delete(book)
    db.session.commit()
    
    flash("The book was successfully deleted!")
    
    return redirect(url_for("home"))


@app.route("/book/<int:book_id>")
def book_detail(book_id):
    """Render the detail page for a specific book.

    Args:
        book_id (int): The ID of the book to display.

    Returns:
        str: The rendered HTML template for the book detail page.
    """
    book = Book.query.get_or_404(book_id)
    
    return render_template("book_detail.html", book=book)


@app.route("/author/<int:author_id>")
def author_detail(author_id):
    """Render the detail page for a specific author.

    Args:
        author_id (int): The ID of the author to display.

    Returns:
        str: The rendered HTML template for the author detail page.
    """
    author = Author.query.get_or_404(author_id)
    
    return render_template("author_detail.html", author=author)


@app.route("/author/<int:author_id>/delete", methods=["POST"])
def delete_author(author_id):
    """Delete a specific author from the database.

    Args:
        author_id (int): The ID of the author to be deleted.

    Returns:
        werkzeug.wrappers.Response: A redirect response to the home route.
    """
    author = Author.query.get_or_404(author_id)
    
    db.session.delete(author)
    db.session.commit()
    
    flash("The Author was successfully deleted!")
    
    return redirect(url_for("home"))


@app.route("/book/<int:book_id>/rate", methods=["POST"])
def rate_book(book_id):
    """Update the numerical rating of a specific book.

    Args:
        book_id (int): The ID of the book to rate.

    Returns:
        werkzeug.wrappers.Response: A redirect response to the home route.
    """
    book = Book.query.get_or_404(book_id)
    
    rating = int(request.form["rating"])
    
    if 1 <= rating <= 10:
        book.rating = rating
        db.session.commit()
        flash("Book was rated successfully!")
    else:
        flash("The rating must be between 1 and 10!")
    
    return redirect(url_for("home"))


def get_cover_url(title, author):
    """Fetch the thumbnail URL for a book cover using the Google Books API.

    Args:
        title (str): The title of the book.
        author (str): The name of the book's author.

    Returns:
        str or None: The URL of the book cover thumbnail, or None if not found.
    """
    url = "https://googleapis.com"
    params = {"q": f"intitle:{title} inauthor:{author}", "maxResults": 10}
    
    response = requests.get(url, params=params)
    
    print("GOOGLE BOOKS STATUS:", response.status_code)
    
    if response.status_code != 200:
        return None
    
    data = response.json()
    
    print("ANZAHL TREFFER:", data.get("totalItems", 0))
    
    for book in data.get("items", []):
        volume_info = book.get("volumeInfo", {})
        
        print(
            "TREFFER:",
            volume_info.get("title"),
            "|",
            volume_info.get("authors"),
            "| COVER:",
            volume_info.get("imageLinks"),
        )
        
        if volume_info.get("imageLinks"):
            return volume_info["imageLinks"].get("thumbnail")
    
    return None


@app.route("/recommendation")
def recommendation():
    """Generate a book recommendation using the OpenAI API.

    Analyses the user's existing book collection and ratings to suggest
    a single new book, then attempts to fetch its cover art.

    Returns:
        str: The rendered HTML template with recommendation details.
    """
    books = Book.query.all()
    book_list = []
    
    for book in books:
        book_info = f"{book.title} von {book.author.name}"
        
        if book.rating:
            book_info += f" (Bewertung: {book.rating}/10)"
        
        book_list.append(book_info)
    
    prompt = f"""
    Du bist ein Buchexperte.

    Der Nutzer hat folgende Bücher in seiner Bibliothek:

    {chr(10).join(book_list)}

    Empfiehl genau EIN weiteres Buch, das gut zu seiner bisherigen
    Bibliothek passt.

    Berücksichtige dabei auch die Bewertungen, sofern vorhanden.

    Gib deine Antwort exakt in diesem Format zurück:

    Titel: ...
    Autor: ...
    ISBN: ...
    Begründung: ...

    Verwende eine echte ISBN-13 des empfohlenen Buches.
    """
    
    response = client.responses.create(model="gpt-5.4-mini", input=prompt)
    
    recommendation_text = response.output_text
    lines = recommendation_text.splitlines()
    
    title = ""
    author = ""
    isbn = ""
    reason = ""
    
    for line in lines:
        if line.startswith("Titel:"):
            title = line.replace("Titel:", "").strip()
        
        elif line.startswith("Autor:"):
            author = line.replace("Autor:", "").strip()
        
        elif line.startswith("ISBN:"):
            isbn = line.replace("ISBN:", "").strip()
            isbn = isbn.replace("-", "").replace(" ", "")
        
        elif line.startswith("Begründung:"):
            reason = line.replace("Begründung:", "").strip()
    
    print("EMPFOHLENE ISBN:", isbn)
    print("EMPFOHLENER TITEL:", title)
    print("EMPFOHLENER AUTOR:", author)
    
    cover_url = get_cover_url(title, author)
    
    print("COVER URL:", cover_url)
    
    return render_template(
        "recommendation.html",
        title=title,
        author=author,
        isbn=isbn,
        reason=reason,
        cover_url=cover_url,
    )


if __name__ == "__main__":
    app.run(debug=True)
    