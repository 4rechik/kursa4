from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from functools import wraps
import jwt
import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key'  # Обязательно смени на что-то ОЧЕНЬ секретное!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db' # SQLAlchemy: Путь к нашей SQLite базе данных
db = SQLAlchemy(app)
JWT_SECRET = 'another_very_secret_key'  # Ключ для подписи JWT

# SQLAlchemy: Определяем модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    todos = db.relationship('Todo', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# SQLAlchemy: Определяем модель задачи
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow) # SQLAlchemy: Добавляем timestamp

# Функция для проверки авторизации с помощью JWT
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('jwt_token')
        if not token:
            return redirect(url_for('login'))
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            user = db.session.execute(db.select(User).filter_by(username=data['username'])).scalar_one_or_none()
            if not user:
                return redirect(url_for('login'))
            session['user_id'] = user.id
            session['username'] = user.username
        except:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()
        if user:
            return render_template('register.html', error='Имя пользователя уже занято')
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        token = jwt.encode({'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, JWT_SECRET, algorithm='HS256')
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        response = redirect(url_for('todos_page'))
        response.set_cookie('jwt_token', token, httponly=True)
        return response
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()
        if user and user.check_password(password):
            token = jwt.encode({'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, JWT_SECRET, algorithm='HS256')
            session['user_id'] = user.id
            session['username'] = user.username
            response = redirect(url_for('todos_page'))
            response.set_cookie('jwt_token', token, httponly=True)
            return response
        return render_template('login.html', error='Неверное имя пользователя или пароль')
    return render_template('login.html')

@app.route('/logout')
@token_required
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    response = redirect(url_for('login'))
    response.delete_cookie('jwt_token')
    return response

@app.route('/')
@app.route('/<status>')
@app.route('/sort/<sort_by>')
@app.route('/<status>/sort/<sort_by>')
@token_required
def todos_page(status=None, sort_by='created_desc'):
    print(session.get('user_id'))
    user_id = session['user_id']
    query = db.select(Todo).filter_by(user_id=user_id)

    if status == 'done':
        query = query.filter_by(done=True)
    elif status == 'undone':
        query = query.filter_by(done=False)

    if sort_by == 'alpha_asc':
        query = query.order