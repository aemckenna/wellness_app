from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Connect to SQLite3 database
def get_db_connection():
    conn = sqlite3.connect('wellness.db')
    conn.row_factory = sqlite3.Row
    return conn

# Home route (displays workout tips and wellness content)
@app.route('/')
def home():
    conn = get_db_connection()
    workouts = conn.execute('SELECT * FROM workouts').fetchall()
    foods = conn.execute('SELECT * FROM foods').fetchall()
    conn.close()
    return render_template('index.html', workouts=workouts, foods=foods)

# Form for adding new workouts or food
@app.route('/add', methods=('GET', 'POST'))
def add():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        details = request.form['details']

        conn = get_db_connection()
        conn.execute('INSERT INTO workouts (name, details) VALUES (?, ?)', (name, details)) if category == 'workout' else conn.execute('INSERT INTO foods (name, details) VALUES (?, ?)', (name, details))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    return render_template('add.html')

if __name__ == '__main__':
    app.run(debug=True)