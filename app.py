# Import necessary libraries
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login page if not authenticated

# Set up the MySQL connection
def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',       
        user='root',
        password='password',    
        database='crud_blog'
    )
    return connection

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            return User(user['id'], user['username'], user['role'])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Define route for the homepage
@app.route('/')
@login_required  # Protect the page to require login
def home():
    # Create a connection to the database
    connection = get_db_connection()
    
    # Create a cursor object to execute queries
    cursor = connection.cursor(dictionary=True)

    # Query to select all blog posts & appropriate fields
    cursor.execute(''' 
        SELECT posts.*, categories.name AS category_name, users.username AS author_name
        FROM posts
        JOIN categories ON posts.category_id = categories.id
        JOIN users ON posts.user_id = users.id
    ''')
    
    # Fetch all results of the query
    posts = cursor.fetchall()

    # Close the database connection
    cursor.close()
    connection.close()

    # Render the posts on the homepage using an HTML template
    return render_template('home.html', posts=posts)

# Create the login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the user exists in the database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            user_obj = User(user['id'], user['username'], user['role'])
            login_user(user_obj)
            return redirect(url_for('home'))
        else:
            flash('Login failed. Check your username and/or password.', 'danger')

    return render_template('login.html')

# Create the logout route
@app.route('/logout')
@login_required  # Protect the page to require login
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Create the register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = 'user'  # Default role for regular users

        # Check if the username already exists in the database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        existing_user = cursor.fetchone()
        cursor.close()

        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return render_template('register.html')

        # Hash the password before saving
        hashed_password = generate_password_hash(password)

        # Insert the user into the database
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password, role) VALUES (%s, %s, %s)', 
                       (username, hashed_password, role))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
