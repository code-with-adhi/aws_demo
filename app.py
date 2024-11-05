from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import mysql.connector

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# SQLAlchemy configuration for user-related data
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Update this to your preferred database if necessary
db = SQLAlchemy(app)

# MySQL configuration for direct database interactions
def get_db_connection():
    return mysql.connector.connect(
        host='adhithya.cliemgumq0vs.us-east-1.rds.amazonaws.com',
        user='admin',
        password='adhithya123',
        database='adhithya'
    )

# SQLAlchemy Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

# Route Definitions
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
        except KeyError as e:
            flash(f"Missing field in form: {str(e)}", "error")
            return redirect(url_for('register'))
        
        if db.session.query(User).filter_by(email=email).first():
            flash('Email already exists. Please login or use a different email.', 'error')
            return redirect(url_for('login'))

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.id
        flash('Registration successful!', 'success')
        return redirect(url_for('confirm'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=email, password=password).first()

        if user:
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid login credentials. Please try again.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return render_template('dashboard.html')
    return redirect(url_for('login'))

@app.route('/transaction', methods=['GET', 'POST'])
def transaction():
    if 'user_id' in session:
        if request.method == 'POST':
            try:
                recipient_id = request.form['recipient_id']
                amount = float(request.form['amount'])
            except KeyError as e:
                flash(f"Missing field in form: {str(e)}", "error")
                return redirect(url_for('transaction'))
            except ValueError:
                flash("Invalid amount entered.", "error")
                return redirect(url_for('transaction'))

            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute("SELECT balance FROM accounts WHERE user_id = %s", (session['user_id'],))
            user_balance = cursor.fetchone()[0]

            if user_balance >= amount:
                cursor.execute("UPDATE accounts SET balance = balance - %s WHERE user_id = %s", (amount, session['user_id']))
                cursor.execute("UPDATE accounts SET balance = balance + %s WHERE user_id = %s", (amount, recipient_id))

                cursor.execute("INSERT INTO account_statements (user_id, transaction_type, transaction_amount, transaction_date, description) VALUES (%s, 'Debit', %s, %s, 'Transfer')", (session['user_id'], amount, datetime.now()))
                cursor.execute("INSERT INTO account_statements (user_id, transaction_type, transaction_amount, transaction_date, description) VALUES (%s, 'Credit', %s, %s, 'Transfer')", (recipient_id, amount, datetime.now()))

                connection.commit()
                flash("Transaction successful!", "success")
            else:
                flash("Insufficient balance.", "error")

            cursor.close()
            connection.close()
            return redirect(url_for('dashboard'))

        return render_template('transaction.html')
    return redirect(url_for('login'))

@app.route('/check-balance')
def check_balance():
    if 'user_id' in session:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT balance FROM accounts WHERE user_id = %s", (session['user_id'],))
        balance = cursor.fetchone()[0]

        cursor.close()
        connection.close()
        return render_template('check_balance.html', balance=balance)
    return redirect(url_for('login'))

# SQLAlchemy database table creation
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
