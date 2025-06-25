import os
from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# App Configuration
# Get the absolute path of the directory where this file is located
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Database Configuration
# Set the database URI. We are using SQLite.
# The database file will be named 'library.db' and will be located in our project folder.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'library.db')

# This is optional but recommended to disable a feature we don't need
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Define the path for our upload folder
app.config['UPLOAD_FOLDER'] = 'static/images/uploads'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize the database object. This links SQLAlchemy to our Flask app.
db = SQLAlchemy(app)


# Database Model Definition
# This class defines the 'book' table in our database.
# It inherits from db.Model, the base class for all models in Flask-SQLAlchemy.
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    title = db.Column(db.String(100), nullable=False) 
    author = db.Column(db.String(100), nullable=False) 
    year = db.Column(db.Integer, nullable=False) 
    description = db.Column(db.Text, nullable=False) 
    cover_image = db.Column(db.String(100), nullable=False, default='images/default_cover.jpg')

    # A helper method to provide a readable representation of the object, useful for debugging.
    def __repr__(self):
        return f'<Book {self.title}>'


# Routes Definition 

# READ all books (Homepage)
@app.route('/')
def index():
    # Use the Book model to query the database for all books.
    all_books = Book.query.all()
    # Pass the list of book objects to the template.
    return render_template('index.html', books=all_books)

# READ a single book (Detail Page)
@app.route('/book/<int:book_id>')
def book_detail(book_id):
    # .get_or_404() is a handy Flask-SQLAlchemy method.
    # It tries to get a record by its ID, and if it doesn't exist, it automatically triggers a 404 Not Found error.
    book = Book.query.get_or_404(book_id)
    return render_template('book_detail.html', book=book)

# CREATE a new book
@app.route('/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        cover_path = 'images/default_cover.jpg' # Start with the default

        # Check if a file was uploaded
        if 'cover_image' in request.files:
            uploaded_file = request.files['cover_image']
            
            # Check if the file has a name (i.e., a file was actually selected)
            if uploaded_file.filename != '':
                # Sanitize the filename to prevent security issues
                filename = secure_filename(uploaded_file.filename)
                
                # Create the full save path
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Save the file to our 'uploads' folder
                uploaded_file.save(save_path)
                
                # Store the path to be saved in the database
                cover_path = f'images/uploads/{filename}'

        # Now create the Book object with the correct cover path
        new_book = Book(
            title=request.form['title'],
            author=request.form['author'],
            year=int(request.form['year']),
            description=request.form['description'],
            cover_image=cover_path # Use the determined path
        )
        
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for('index'))
        
    return render_template('add_book.html')


# UPDATE an existing book
@app.route('/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book_to_update = Book.query.get_or_404(book_id)

    if request.method == 'POST':
        # Update the text fields
        book_to_update.title = request.form['title']
        book_to_update.author = request.form['author']
        book_to_update.year = int(request.form['year'])
        book_to_update.description = request.form['description']
        
        # --- Handle the file upload ---
        # Check if a file was included in the request
        if 'cover_image' in request.files:
            uploaded_file = request.files['cover_image']
            
            # Check if the user selected a file to upload
            if uploaded_file.filename != '':
                # Secure the filename
                filename = secure_filename(uploaded_file.filename)
                # Create the full save path
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                # Save the new file
                uploaded_file.save(save_path)
                # Update the database record with the new path
                book_to_update.cover_image = f'images/uploads/{filename}'
        
        # If no new file was uploaded, the book_to_update.cover_image remains unchanged.
        
        # Commit all changes to the database
        db.session.commit()
        return redirect(url_for('book_detail', book_id=book_to_update.id))

    # For a GET request, just show the form
    return render_template('edit_book.html', book=book_to_update)

# DELETE a book
@app.route('/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book_to_delete = Book.query.get_or_404(book_id)
    
    # Delete the book from the database session.
    db.session.delete(book_to_delete)
    # Commit the deletion.
    db.session.commit()
    
    return redirect(url_for('index'))

# Error Handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Run the Application 
if __name__ == '__main__':
    # We check if the database file exists. If not, we create it.
    # This ensures that db.create_all() is only run once.
    with app.app_context():
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        if not os.path.exists(os.path.join(basedir, 'library.db')):
            print("Creating database and tables...")
            db.create_all()
            print("Database created successfully!")

    app.run(debug=False)