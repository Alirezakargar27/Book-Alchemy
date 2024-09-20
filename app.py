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


# Route to add an author
@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
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
            db.session.rollback()  # Roll back transaction if there's an error
            flash(f"Error adding author: {str(e)}", "error")
        return redirect(url_for('add_author'))

    return render_template('add_author.html')


# Route to add a book
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    authors = Author.query.all()  # Fetch all authors to show in the dropdown

    if request.method == 'POST':
        isbn = request.form['isbn']
        title = request.form['title']
        publication_year = request.form['publication_year']
        author_id = request.form['author_id']

        # Check if a book with the same ISBN already exists
        existing_book = Book.query.filter_by(isbn=isbn).first()
        if existing_book:
            flash("A book with this ISBN already exists!", "error")
            return redirect(url_for('add_book'))

        # Check if the author exists in the database
        author = Author.query.get(author_id)
        if not author:
            flash("The selected author does not exist.", "error")
            return redirect(url_for('add_book'))

        # Create a new Book instance
        book = Book(isbn=isbn, title=title, publication_year=publication_year, author_id=author_id)

        try:
            db.session.add(book)
            db.session.commit()
            flash('Book added successfully!', 'success')
        except Exception as e:
            db.session.rollback()  # Roll back transaction if there's an error
            flash(f"Error adding book: {str(e)}", "error")
        return redirect(url_for('add_book'))

    # Render the template for adding a new book, passing in the list of authors
    return render_template('add_book.html', authors=authors)


# Home route with search and book display
@app.route('/')
def home():
    search_query = request.args.get('search')
    sort_by = request.args.get('sort_by', 'title')  # Default sorting by title
    books_query = Book.query

    if search_query:
        # Search books by title using the LIKE operator (case-insensitive)
        books_query = books_query.filter(Book.title.ilike(f'%{search_query}%'))

    if sort_by == 'author':
        books_query = books_query.join(Author).order_by(Author.name)
    else:
        books_query = books_query.order_by(Book.title)

    books = books_query.all()

    # Render the homepage with the books that match the search query
    return render_template('home.html', books=books)


# Route to delete a book
@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    author_id = book.author_id

    try:
        db.session.delete(book)
        db.session.commit()

        # Check if the author has any other books
        other_books = Book.query.filter_by(author_id=author_id).count()
        if other_books == 0:
            author = Author.query.get(author_id)
            db.session.delete(author)
            db.session.commit()

        flash('Book deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()  # Roll back transaction if there's an error
        flash(f"Error deleting book: {str(e)}", "error")

    return redirect(url_for('home'))


# Initialize the database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)