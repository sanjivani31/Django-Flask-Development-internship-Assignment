from flask import Flask, render_template, request, redirect, session
import sqlite3
import bcrypt
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Create a connection to the database
conn = sqlite3.connect('database.db')

# Create a cursor object to execute SQL queries
cursor = conn.cursor()

# Create a users table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL
    )
''')

# Create a posts table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')

# Create a comments table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_id INTEGER,
        comment TEXT NOT NULL,
        FOREIGN KEY (post_id) REFERENCES posts (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')

# Create a likes table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_id INTEGER,
        like_status INTEGER,
        FOREIGN KEY (post_id) REFERENCES posts (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')

# Commit the changes and close the connection
conn.commit()
conn.close()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/forum', methods=['GET', 'POST'])
def forum():
    # Check if the user is logged in
    if 'user_id' not in session:
        return redirect('/login')  # Redirect unsigned users to the login page

    if request.method == 'POST':
        # Get the form data
        title = request.form['title']
        content = request.form['content']
        user_id = session['user_id']

        # Create a connection to the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Insert the new post into the database
        cursor.execute('INSERT INTO posts (title, content, user_id) VALUES (?, ?, ?)',
                       (title, content, user_id))
        post_id = cursor.lastrowid  # Get the ID of the last inserted row
        conn.commit()

        # Close the connection
        conn.close()

        return redirect(f'/forum/{post_id}')  # Redirect to the new post's page

    else:
        # Retrieve all posts from the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM posts ORDER BY id DESC')
        posts = cursor.fetchall()
        conn.close()

        return render_template('forum.html', posts=posts)


@app.route('/forum/<int:post_id>', methods=['GET', 'POST'])
def post_details(post_id):
    # Check if the user is logged in
    if 'user_id' not in session:
        return redirect('/login')  # Redirect unsigned users to the login page

    if request.method == 'POST':
        # Get the form data
        comment = request.form['comment']
        user_id = session['user_id']

        # Create a connection to the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Insert the new comment into the database
        cursor.execute('INSERT INTO comments (post_id, user_id, comment) VALUES (?, ?, ?)',
                       (post_id, user_id, comment))
        conn.commit()

        # Close the connection
        conn.close()

        return redirect(f'/forum/{post_id}')  # Refresh the page to show the new comment

    else:
        # Retrieve the post and its comments from the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Retrieve the post
        cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
        post = cursor.fetchone()

        if post is None:
            conn.close()
            return redirect('/forum')

        # Retrieve the comments
        cursor.execute('SELECT * FROM comments WHERE post_id = ? ORDER BY id ASC', (post_id,))
        comments = cursor.fetchall()
        conn.close()

        return render_template('post_details.html', post=post, comments=comments)





@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Check if the user is already logged in
    if 'user_id' in session:
        return redirect('/forum')

    if request.method == 'POST':
        # Get the form data
        username = request.form['username']
        email = request.form['email']
        password = request.form['password'].encode('utf-8')

        # Create a connection to the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Check if the username or email already exist
        cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
        user = cursor.fetchone()

        if user is None:
            # Hash the password
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

            # Insert the new user into the database
            cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                           (username, email, hashed_password))
            conn.commit()

            # Close the connection
            conn.close()

            return redirect('/login')  # Redirect to the login page after successful signup

        else:
            # Close the connection
            conn.close()

            error = 'Username or email already exists'
            return render_template('signup.html', error=error)

    else:
        return render_template('signup.html')





@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if the user is already logged in
    if 'user_id' in session:
        return redirect('/forum')

    if request.method == 'POST':
        # Get the form data
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        # Create a connection to the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Retrieve the user with the provided username
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

        if user is not None and bcrypt.checkpw(password, user[3]):
            # Store the user ID in the session
            session['user_id'] = user[0]

            # Close the connection
            conn.close()

            return redirect('/forum')  # Redirect to the forum page after successful login

        else:
            # Close the connection
            conn.close()

            error = 'Invalid username or password'
            return render_template('login.html', error=error)

    else:
        return render_template('login.html')






@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        # Get the form data
        email = request.form['email']

        # Create a connection to the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Check if the email exists in the database
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user:
            # Send an email with a password reset link (not implemented here)
            message = 'Password reset link sent to your email'
            conn.close()
            return render_template('forgot_password.html', message=message)
        else:
            # Email not found, display an error message
            error = 'Email not found'
            return render_template('forgot_password.html', error=error)

    return render_template('forgot_password.html')






@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        # Get the form data
        email = request.form['email']
        new_password = request.form['new_password']

        # Create a connection to the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Update the user's password in the database
        cursor.execute('UPDATE users SET password = ? WHERE email = ?', (new_password, email))
        conn.commit()

        # Display a success message
        message = 'Password reset successfully'
        conn.close()
        return render_template('reset_password.html', message=message)

    return render_template('reset_password.html')






# ... Initialize Flask-Mail and configure email settings ...

# @app.route('/send_reset_email', methods=['POST'])
# def send_reset_email():
#     # Get the user's email from the form data
#     email = request.form['email']

#     # Generate a unique reset token for the user (you can use a library like UUID)

#     # Save the reset token in the database for the user

#     # Create the reset password email message
#     msg = Message('Password Reset', sender='your_email@example.com', recipients=[email])
#     msg.body = f"Click the link to reset your password: {request.url_root}/reset_password/{reset_token}"
    
#     # Send the email
#     mail.send(msg)

#     # Display a success message
#     message = 'Password reset email sent'
#     return render_template('forgot_password.html', message=message)




# # @app.route('/reset_password', methods=['POST'])
# def reset_password():
#     # Get the new password and reset token from the form data
#     password = request.form['password']
#     reset_token = request.form['reset_token']

#     # Verify the reset token (check if it exists and is valid)

#     # Update the user's password in the database

#     # Display a success message
#     message = 'Password reset successful'
#     return render_template('reset_password.html', message=message)



@app.route('/logout')
def logout():
    # Clear the session
    session.clear()

    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
