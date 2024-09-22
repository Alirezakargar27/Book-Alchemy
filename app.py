from flask import Flask, render_template, request, redirect, url_for, flash
from data_models import db, Author, Book
from flask_migrate import Migrate
import os
import requests

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flashing messages

# Database setup
db_path = os.path.join(os.path.dirname(__file__), 'data', 'library.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)  # Setup Flask-Migrate


def get_cover_url(isbn):
    """ Get the cover URL for a book using its ISBN. """
    cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
    response = requests.head(cover_url)  # Check if the cover exists
    if response.status_code == 200:
        return cover_url
    return None


@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    """
    Route to add a new author to the database.
    """
    if request.method == 'POST':
        name = request.form['name'].strip()  # Remove surrounding whitespace
        birth_date = request.form['birthdate']
        date_of_death = request.form['date_of_death']

        if not name:
            flash('Author name cannot be empty or only whitespace!', 'error')
            return render_template('add_author.html')

        author = Author(name=name, birth_date=birth_date, date_of_death=date_of_death)

        try:
            db.session.add(author)
            db.session.commit()
            flash('Author added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding author: {str(e)}", "error")

        # After adding the author, return the same page with a flash message instead of redirecting
        return render_template('add_author.html')

    return render_template('add_author.html')


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    """
    Route to add a new book to the database.
    """
    authors = Author.query.all()

    if request.method == 'POST':
        isbn = request.form['isbn'].strip()  # Remove surrounding whitespace
        title = request.form['title'].strip()
        publication_year = request.form['publication_year']
        author_id = request.form['author_id']

        if not isbn or not title:
            flash("ISBN and title cannot be empty or contain only whitespace!", "error")
            return render_template('add_book.html', authors=authors)

        existing_book = Book.query.filter_by(isbn=isbn).first()
        if existing_book:
            flash("A book with this ISBN already exists!", "error")
            return render_template('add_book.html', authors=authors)

        author = Author.query.get(author_id)
        if not author:
            flash("The selected author does not exist.", "error")
            return render_template('add_book.html', authors=authors)

        # Fetch the cover URL from Open Library
        cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
        response = requests.head(cover_url)  # Check if the cover exists
        if response.status_code != 200:
            cover_url = None  # No cover found, store None

        # Save book with cover URL in the database
        book = Book(isbn=isbn, title=title, publication_year=publication_year, author_id=author_id, cover_url=cover_url)

        try:
            db.session.add(book)
            db.session.commit()
            flash('Book added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding book: {str(e)}", "error")

        # After adding the book, return the same page with a flash message instead of redirecting
        return render_template('add_book.html', authors=authors)

    return render_template('add_book.html', authors=authors)

@app.route('/')
@app.route('/')
def home():
    """
    Home route to display a list of books with the option to search and sort by title or author.
    Dynamically adds a cover image URL for each book using the Open Library Covers API.
    """
    search_query = request.args.get('search')
    sort_by = request.args.get('sort_by', 'title')
    books_query = Book.query

    if search_query:
        books_query = books_query.filter(Book.title.ilike(f'%{search_query}%'))

    if sort_by == 'author':
        books_query = books_query.join(Author).order_by(Author.name)
    else:
        books_query = books_query.order_by(Book.title)

    books = books_query.all()

    # Dynamically add Open Library Covers API URL for each book's cover
    for book in books:
        # Generate cover URL based on the book's ISBN
        book.cover_url = f"https://covers.openlibrary.org/b/isbn/{book.isbn}-L.jpg"

    return render_template('home.html', books=books)

@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    """
    Route to delete a specific book from the database.
    """
    book = Book.query.get_or_404(book_id)
    author_id = book.author_id

    try:
        db.session.delete(book)
        db.session.commit()

        other_books = Book.query.filter_by(author_id=author_id).count()
        if other_books == 0:
            author = Author.query.get(author_id)
            db.session.delete(author)
            db.session.commit()

        flash('Book deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting book: {str(e)}", 'error')

    return redirect(url_for('home'))


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)