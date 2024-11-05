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
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
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
        email = request.form['email']
        password = request.form['password']
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
            recipient_id = request.form['recipient_id']
            amount = float(request.form['amount'])

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

@app.route('/account-creation', methods=['GET', 'POST'])
def account_creation():
    if 'user_id' in session:
        if request.method == 'POST':
            account_type = request.form['account_type']
            initial_balance = float(request.form['initial_balance'])

            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute("INSERT INTO accounts (user_id, balance, account_type) VALUES (%s, %s, %s)", (session['user_id'], initial_balance, account_type))
            connection.commit()

            cursor.close()
            connection.close()
            flash("Account created successfully!", "success")
            return redirect(url_for('dashboard'))

        return render_template('account_creation.html')
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

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user_id' in session:
        if request.method == 'POST':
            amount = float(request.form['deposit_amount'])
            account_type = request.form['account_type']

            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute("UPDATE accounts SET balance = balance + %s WHERE user_id = %s AND account_type = %s", (amount, session['user_id'], account_type))
            cursor.execute("INSERT INTO account_statements (user_id, transaction_type, transaction_amount, transaction_date) VALUES (%s, 'Credit', %s, %s)", (session['user_id'], amount, datetime.now()))

            connection.commit()
            cursor.close()
            connection.close()
            flash("Deposit successful!", "success")
            return redirect(url_for('dashboard'))

        return render_template('deposit.html')
    return redirect(url_for('login'))

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/confirm')
def confirm():
    return render_template('confirm.html')

@app.route('/account-login', methods=['GET', 'POST'])
def account_login():
    if request.method == 'POST':
        # Placeholder for account login logic if needed
        pass
    return render_template('account_login.html')

@app.route('/statement')
def statements():
    if 'user_id' in session:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT transaction_type, transaction_amount, transaction_date, description FROM account_statements WHERE user_id = %s ORDER BY transaction_date DESC", (session['user_id'],))
        transactions = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template('statement.html', transactions=transactions)
    return redirect(url_for('login'))

# SQLAlchemy database table creation
if __name__ == "__main__":
    # Ensure tables are created if not existing
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
