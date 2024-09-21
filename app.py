from flask import Flask, render_template, request, redirect, url_for, flash
from data_models import db, Author, Book
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flashing messages

# Database setup
db_path = os.path.join(os.path.dirname(__file__), 'data', 'library.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    """
    Route to add a new author to the database.
    If the method is POST, the author details from the form are added to the database.
    On successful addition, a success message is flashed; otherwise, an error message is flashed.

    Returns:
        Rendered template for adding a new author or a redirect to the same page with a flash message.
    """
    if request.method == 'POST':
        name = request.form['name']
        birth_date = request.form['birthdate']
        date_of_death = request.form['date_of_death']
        author = Author(name=name, birth_date=birth_date, date_of_death=date_of_death)

        try:
            db.session.add(author)
            db.session.commit()
            flash('Author added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding author: {str(e)}", "error")
        return redirect(url_for('add_author'))

    return render_template('add_author.html')


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    """
    Route to add a new book to the database.
    Displays a form to add a book and processes the form submission (POST request).
    If a book with the same ISBN exists or the author doesn't exist, an error is flashed.

    Returns:
        Rendered template for adding a new book or a redirect to the same page with a flash message.
    """
    authors = Author.query.all()

    if request.method == 'POST':
        isbn = request.form['isbn']
        title = request.form['title']
        publication_year = request.form['publication_year']
        author_id = request.form['author_id']

        existing_book = Book.query.filter_by(isbn=isbn).first()
        if existing_book:
            flash("A book with this ISBN already exists!", "error")
            return redirect(url_for('add_book'))

        author = Author.query.get(author_id)
        if not author:
            flash("The selected author does not exist.", "error")
            return redirect(url_for('add_book'))

        book = Book(isbn=isbn, title=title, publication_year=publication_year, author_id=author_id)

        try:
            db.session.add(book)
            db.session.commit()
            flash('Book added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding book: {str(e)}", "error")
        return redirect(url_for('add_book'))

    return render_template('add_book.html', authors=authors)


@app.route('/')
def home():
    """
    Home route to display a list of books with the option to search and sort by title or author.
    Dynamically adds a cover image URL for each book using the Open Library Covers API.

    Returns:
        Rendered template for the home page with the list of books and cover URLs.
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

    # Add Open Library Covers API URL for each book's cover
    for book in books:
        book.cover_url = f"https://covers.openlibrary.org/b/isbn/{book.isbn}-L.jpg"

    return render_template('home.html', books=books)


@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    """
    Route to delete a specific book from the database.
    If the book is successfully deleted, a success message is flashed. If there's an error, an error message is flashed.
    Also deletes the author if no other books by that author exist.

    Args:
        book_id (int): The ID of the book to be deleted.

    Returns:
        A redirect to the home page with a flash message indicating success or failure.
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