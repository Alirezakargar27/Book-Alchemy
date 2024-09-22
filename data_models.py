from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Text, nullable=False)
    date_of_death = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Author {self.name}>'


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(13), nullable=False, unique=True)
    title = db.Column(db.String(200), nullable=False)
    publication_year = db.Column(db.Integer, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)
    cover_url = db.Column(db.String(500), nullable=True)  # New field to store the cover URL

    author = db.relationship('Author', backref=db.backref('books', lazy=True))

    def __repr__(self):
        return f'<Book {self.title}>'