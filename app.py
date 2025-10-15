import os
from flask import Flask, render_template, url_for, flash, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, current_user

# Importações do nosso projeto
from models import db, login_manager, User
from forms import RegistrationForm, LoginForm

# --- CONFIGURAÇÃO BÁSICA ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-dificil-de-adivinhar'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'bookaholic.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- INICIALIZAÇÃO DAS EXTENSÕES ---
# Conecta os objetos (db, login_manager) com a nossa app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login' # Define a página de login

# --- ROTAS DA APLICAÇÃO ---
@app.route('/')
@app.route('/home')
def home():
    return render_template('base.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Conta criada com sucesso para {form.username.data}!', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Falha no login. Verifique o usuário e a senha.', 'danger')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

# --- EXECUÇÃO ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)