import logging
from os import close
import sqlite3
from sys import stderr, stdout

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

formatter = logging.Formatter('%(levelname)s:%(name)s:%(asctime)s, %(message)s', datefmt='%d/%m/%y, %H:%M:%S')
stderr_handler = logging.StreamHandler(stderr)
stdout_handler = logging.StreamHandler(stdout)
stderr_handler.setLevel(logging.DEBUG)
stdout_handler.setLevel(logging.DEBUG)
stderr_handler.setFormatter(formatter)
stdout_handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(stderr_handler)
logger.addHandler(stdout_handler)

DB_CONNECTION_COUNT = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global DB_CONNECTION_COUNT
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    DB_CONNECTION_COUNT += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        logger.info('Tried to retrieve article with non-existent ID %d!', post_id)
        return render_template('404.html'), 404
    else:
        logger.info('Article "%s" retrieved!', post['title'])
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    logger.info('"About Us" page retrieved!')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            logger.info('Article "%s" created!', title)
            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/healthz')
def healthz():
    return jsonify(result='OK - healthy')

@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    post_count = connection.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
    connection.close()
    return jsonify(db_connection_count=DB_CONNECTION_COUNT, post_count=post_count)

# start the application on port 3111
if __name__ == "__main__":
   app.run(host='0.0.0.0', port='3111')
