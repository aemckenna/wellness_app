#main.py

from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
import re
import hashlib

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'wellness_app'

# Database connection function for SQLite
def get_db_connection():
    if 'db' not in g:
        g.db = sqlite3.connect('wellness_app.db', timeout=60)
        g.db.row_factory = sqlite3.Row
    return g.db

# Close the database connection after each request
@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Login route
@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        
        # Hash password for secure comparison
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Query database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username = ? AND password = ?', (username, hashed_password))
        account = cursor.fetchone()

        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('workout'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('index.html')

@app.route('/workout/', methods=['GET', 'POST'])
def workout():
    msg = ''
    exercises = []
    
    if 'loggedin' in session:
        username = session['username']
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM accounts WHERE username = ?', (username,))
        account = cursor.fetchone()
        user_id = account['id']

        # Fetch splits for the logged-in user
        cursor.execute('SELECT * FROM splits WHERE user_id = ?', (user_id,))
        splits = cursor.fetchall()

        if request.method == 'POST':
            if 'name' in request.form:
                # Handle creating a new split
                split_name = request.form['name']
                if split_name:
                    cursor.execute('INSERT INTO splits (user_id, name) VALUES (?, ?)', (user_id, split_name))
                    conn.commit()
                    msg = 'Split created successfully!'
                else:
                    msg = 'Please provide a valid split name.'
            elif 'workout-split' in request.form:
                # Handle selecting a split and fetching associated exercises
                selected_split_id = request.form['workout-split']
                cursor.execute('SELECT * FROM exercises WHERE id IN (SELECT exercise_id FROM workout_logs WHERE split_id = ?)', (selected_split_id,))
                exercises = cursor.fetchall()

            elif 'exercise_name' in request.form:
                # Handle creating a new exercise
                exercise_name = request.form['exercise_name']
                split_id = request.form['split_id']  # hidden field to store split ID
                if exercise_name and split_id:
                    cursor.execute('INSERT INTO exercises (name) VALUES (?)', (exercise_name,))
                    exercise_id = cursor.lastrowid
                    # Optionally link this exercise to a workout log (if necessary)
                    cursor.execute('INSERT INTO workout_logs (user_id, exercise_id, split_id, date, sets, reps, weight) VALUES (?, ?, ?, date("now"), 0, 0, 0)', 
                                   (user_id, exercise_id, split_id))
                    conn.commit()
                    msg = 'Exercise created successfully!'
                else:
                    msg = 'Please provide a valid exercise name.'

        return render_template('workout.html', splits=splits, exercises=exercises, msg=msg)
    else:
        return redirect(url_for('login'))

# Logout route
@app.route('/logout/')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# Registration route
@app.route('/register/', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username = ?', (username,))
        account = cursor.fetchone()

        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only letters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Hash password securely
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute('INSERT INTO accounts (username, password, email) VALUES (?, ?, ?)', (username, hashed_password, email,))
            conn.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('register.html', msg=msg)

if __name__ == '__main__':
    app.run(debug=True)
