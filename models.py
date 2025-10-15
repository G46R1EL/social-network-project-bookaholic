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