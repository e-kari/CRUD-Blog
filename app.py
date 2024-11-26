# Import necessary libraries
from flask import Flask, render_template
import mysql.connector

# Initialize Flask app
app = Flask(__name__)

# Set up the MySQL connection
def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',       # Usually 'localhost' for local setups
        user='root',
        password='password',
        database='crud_blog'
    )
    return connection

# Define route for the homepage
@app.route('/')
def home():
    # Create a connection to the database
    connection = get_db_connection()
    
    # Create a cursor object to execute queries
    cursor = connection.cursor(dictionary=True)

    # Query to select all blog posts
    cursor.execute('SELECT * FROM posts')  # Assuming you have a 'posts' table
    
    # Fetch all results of the query
    posts = cursor.fetchall()

    # Close the database connection
    cursor.close()
    connection.close()

    # Render the posts on the homepage using an HTML template
    return render_template('home.html', posts=posts)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
