"""Database models for the library management system.

This module defines SQLAlchemy ORM models for managing books and authors,
including their attributes, relationships, and string representations.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Author(db.Model):
    """Represents a book author within the library database.

    Attributes:
        id (int): Unique identifier and primary key.
        name (str): Full name of the author.
        birthdate (date): Birth date of the author.
        date_of_death (date, optional): Date of death if applicable.
        books (list): List of books associated with this author.
    """

    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    birthdate = db.Column(db.Date, nullable=False)
    date_of_death = db.Column(db.Date, nullable=True)

    books = db.relationship(
        "Book",
        back_populates="author",
        cascade="all, delete-orphan",
    )

    def __str__(self):
        """Return the string representation of the author.

        Returns:
            str: The author's name.
        """
        return self.name


class Book(db.Model):
    """Represents a book entry within the library database.

    Attributes:
        id (int): Unique identifier and primary key.
        isbn (str): 13-character International Standard Book Number.
        title (str): Title of the book.
        publication_year (int): Year the book was published.
        rating (int, optional): Numerical user rating from 1 to 10.
        author_id (int): Foreign key referencing the associated author.
        author (Author): The Author object instance this book belongs to.
    """

    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(13), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    publication_year = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer)

    author_id = db.Column(
        db.Integer, db.ForeignKey("authors.id"), nullable=False
    )

    author = db.relationship("Author", back_populates="books")

    def __str__(self):
        """Return the string representation of the book.

        Returns:
            str: The book's title.
        """
        return self.title
    