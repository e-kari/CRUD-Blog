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
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(''' 
        SELECT posts.*, categories.name AS category_name, users.username AS author_name
        FROM posts
        JOIN categories ON posts.category_id = categories.id
        JOIN users ON posts.user_id = users.id
    ''')
    posts = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('home.html', posts=posts)

# Create the login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            user_obj = User(user['id'], user['username'], user['role'])
            login_user(user_obj)
            return redirect(url_for('dashboard'))  # Redirect to dashboard after login
        else:
            flash('Login failed. Check your username and/or password.', 'danger')

    return render_template('login.html')

# Create the logout route
@app.route('/logout')
@login_required
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

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        existing_user = cursor.fetchone()
        cursor.close()

        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return render_template('register.html')

        hashed_password = generate_password_hash(password)

        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password, role) VALUES (%s, %s, %s)', 
                       (username, hashed_password, role))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Define the route for the dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    user_id = current_user.id
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(''' 
        SELECT posts.*, categories.name AS category_name
        FROM posts
        JOIN categories ON posts.category_id = categories.id
        WHERE posts.user_id = %s
    ''', (user_id,))
    
    user_posts = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('dashboard.html', posts=user_posts)

# Route to create a new post
@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Fetch only the 4 categories (IDs 1-4)
    cursor.execute('SELECT * FROM categories WHERE id IN (1, 2, 3, 4)')
    categories = cursor.fetchall()

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category_id = request.form['category']

        cursor.execute('INSERT INTO posts (title, content, category_id, user_id) VALUES (%s, %s, %s, %s)', 
                       (title, content, category_id, current_user.id))
        connection.commit()

        cursor.close()
        connection.close()

        flash('Post created successfully!', 'success')
        return redirect(url_for('dashboard'))

    cursor.close()
    connection.close()
    return render_template('create_post.html', categories=categories)

# Route to edit an existing post
@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Fetch only the 4 categories (IDs 1-4)
    cursor.execute('SELECT * FROM categories WHERE id IN (1, 2, 3, 4)')
    categories = cursor.fetchall()

    cursor.execute('SELECT * FROM posts WHERE id = %s AND user_id = %s', (post_id, current_user.id))
    post = cursor.fetchone()

    if not post:
        flash('Post not found or you do not have permission to edit it.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category_id = request.form['category']

        cursor.execute(''' 
            UPDATE posts 
            SET title = %s, content = %s, category_id = %s
            WHERE id = %s
        ''', (title, content, category_id, post_id))
        connection.commit()

        flash('Post updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    cursor.close()
    connection.close()

    return render_template('edit_post.html', post=post, categories=categories)

# Route to delete an existing post
@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Check if the current user is an admin (Enya) or the post belongs to the current user
    cursor.execute('SELECT * FROM posts WHERE id = %s', (post_id,))
    post = cursor.fetchone()

    if not post:
        flash('Post not found.', 'danger')
        return redirect(url_for('dashboard'))

    if current_user.username == 'enya' or post['user_id'] == current_user.id:
        # Admin or the user who created the post can delete the post
        cursor.execute('DELETE FROM posts WHERE id = %s', (post_id,))
        connection.commit()

        flash('Post deleted successfully!', 'success')
    else:
        flash('You do not have permission to delete this post.', 'danger')

    cursor.close()
    connection.close()

    return redirect(url_for('dashboard'))

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)