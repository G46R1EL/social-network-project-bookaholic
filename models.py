from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager

# 1. Inicializamos as extensões SEM a aplicação Flask
db = SQLAlchemy()
login_manager = LoginManager()

# 2. Definimos nosso modelo de usuário
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# 3. Movemos o user_loader para cá também
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(120), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    authors = db.Column(db.String(200)) # Armazenaremos como uma string separada por vírgulas
    thumbnail = db.Column(db.String(200))

    def __repr__(self):
        return f'<Book {self.title}>'

class UserBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Quero Ler') # Ex: "Quero Ler", "Lendo", "Lido"
    current_page = db.Column(db.Integer, default=0)

    # Cria a relação para que possamos acessar o objeto User e Book a partir de UserBook
    user = db.relationship('User', backref=db.backref('user_books', lazy=True))
    book = db.relationship('Book', backref=db.backref('user_books', lazy=True))

    def __repr__(self):
        return f'<UserBook {self.user.username} - {self.book.title}>'