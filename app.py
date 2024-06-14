from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import random
from datetime import date
from questions import questions

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    streak = db.Column(db.Integer, default=0)
    total_time = db.Column(db.Float, default=0.0)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_daily_question():
    random.seed(date.today().toordinal())
    return random.choice(questions)

@app.route('/')
def home():
    if 'streak' not in session:
        session['streak'] = 0
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('home'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return 'Username already exists'
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    return f'Logged in as: {current_user.username}'

@app.route('/api/trivia', methods=['GET'])
def get_trivia():
    question = get_daily_question()
    return jsonify({'id': question['id'], 'question': question['question']})

@app.route('/api/answer', methods=['POST'])
@login_required
def check_answer():
    try:
        data = request.get_json()
        print(f"Received data: {data}")

        if not data:
            print("No data received!")
            return jsonify({"error": "No data received"}), 400

        question_id = data.get('id')
        user_answer = data.get('answer').lower()

        if not question_id or not user_answer:
            print("Missing 'id' or 'answer' in the received data")
            return jsonify({"error": "Missing 'id' or 'answer' in the received data"}), 400

        try:
            question_id = int(question_id)
        except ValueError:
            print("Invalid question ID format!")
            return jsonify({"error": "Invalid question ID format"}), 400

        print(f"Received questionID: {question_id}")
        print(f"User answer: {user_answer}")

        question = next((q for q in questions if q['id'] == question_id), None)

        if question is None:
            print("Question not found!")
            return jsonify({"correct": False, "correct_answer": "Unknown question ID"}), 400

        correct = question['answer'].lower() == user_answer

        if correct:
            current_user.streak += 1
        else:
            current_user.streak = 0

        print(f"Correct answer: {question['answer']}")

        db.session.commit()

        return jsonify({"correct": correct, "correct_answer": question['answer']})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Bad request"}), 400

if __name__ == '__main__':
    app.run(debug=True)
