import os
import requests
from flask import Flask, render_template, url_for, flash, redirect, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, current_user, login_required

# Importações do nosso projeto
from models import db, login_manager, User, Book, UserBook
from forms import RegistrationForm, LoginForm, BookSearchForm, UpdateBookForm

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

# Adicionamos o decorator @login_required para proteger esta página
@app.route('/search', methods=['GET', 'POST'])
@login_required 
def search():
    form = BookSearchForm()
    books_data = [] # Lista para guardar os livros encontrados

    if form.validate_on_submit():
        query = form.search_query.data
        # URL da API do Google Books
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=10"
        
        try:
            response = requests.get(url)
            response.raise_for_status() # Lança um erro para respostas ruins (4xx ou 5xx)
            
            # Pega os dados em formato JSON
            search_results = response.json()
            
            # 'items' é a chave que contém a lista de livros na resposta da API
            if 'items' in search_results:
                for item in search_results.get('items', []):
                    volume_info = item.get('volumeInfo', {})
                    # Precisamos tratar casos onde a informação pode não existir
                    book = {
                        'google_id': item.get('id'),
                        'title': volume_info.get('title', 'Título não disponível'),
                        'authors': volume_info.get('authors', ['Autor desconhecido']),
                        'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail', '')
                    }
                    books_data.append(book)
            else:
                 flash('Nenhum livro encontrado para sua busca.', 'info')

        except requests.exceptions.RequestException as e:
            flash(f'Erro ao se comunicar com a API do Google Books: {e}', 'danger')

    return render_template('search.html', form=form, books=books_data)

@app.route('/add_book', methods=['POST'])
@login_required
def add_book():
    # Pega o ID do livro enviado pelo formulário no template
    google_id = request.form.get('google_id')
    
    # Verifica se já temos o livro no nosso banco de dados
    book = Book.query.filter_by(google_id=google_id).first()

    # Se não temos o livro, buscamos na API e salvamos
    if not book:
        url = f"https://www.googleapis.com/books/v1/volumes/{google_id}"
        response = requests.get(url)
        book_data = response.json().get('volumeInfo', {})
        
        book = Book(
            google_id=google_id,
            title=book_data.get('title'),
            authors=', '.join(book_data.get('authors', [])),
            thumbnail=book_data.get('imageLinks', {}).get('thumbnail')
        )
        db.session.add(book)
        db.session.commit()

    # Verifica se o usuário já não tem este livro na estante
    user_book_exists = UserBook.query.filter_by(user_id=current_user.id, book_id=book.id).first()
    if not user_book_exists:
        user_book = UserBook(user_id=current_user.id, book_id=book.id)
        db.session.add(user_book)
        db.session.commit()
        flash(f'"{book.title}" foi adicionado à sua estante!', 'success')
    else:
        flash(f'"{book.title}" já está na sua estante.', 'info')
        
    return redirect(url_for('search'))

@app.route('/my_shelf')
@login_required
def my_shelf():
    # Busca todos os livros da estante do usuário logado
    user_books = UserBook.query.filter_by(user_id=current_user.id).all()
    return render_template('my_shelf.html', user_books=user_books, UpdateBookForm=UpdateBookForm)

@app.route('/update_book/<int:user_book_id>', methods=['POST'])
@login_required
def update_book(user_book_id):
    # Encontra o livro na estante do usuário
    book_to_update = UserBook.query.get_or_404(user_book_id)

    # Verifica se o livro realmente pertence ao usuário logado (segurança)
    if book_to_update.user_id != current_user.id:
        flash('Operação não permitida.', 'danger')
        return redirect(url_for('my_shelf'))

    form = UpdateBookForm()
    # Populamos o formulário com os dados que vêm do POST request
    if form.validate_on_submit():
        book_to_update.status = form.status.data
        book_to_update.current_page = form.current_page.data
        db.session.commit()
        flash(f'"{book_to_update.book.title}" atualizado com sucesso!', 'success')
    else:
        # Se houver erros de validação, podemos exibi-los
        flash('Não foi possível atualizar o livro. Verifique os dados.', 'danger')

    return redirect(url_for('my_shelf'))

# --- Rota do Chatbot ---
@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    # Nosso "banco de dados" de perguntas e respostas
    qa_pairs = {
        "como adiciono um livro?": "Para adicionar um livro, vá para a página 'Buscar Livros', pesquise pelo título ou autor e, nos resultados, clique no botão 'Adicionar à Estante'.",
        "como vejo meus livros?": "Você pode ver todos os seus livros salvos clicando no link 'Minha Estante' na barra de navegação superior.",
        "como mudo o status de um livro?": "Na sua estante, cada livro terá um formulário. Você pode selecionar o novo status (Lendo, Lido, etc.) e até anotar a página em que parou. Depois, clique em 'Atualizar'.",
        "preciso estar logado para usar o site?": "Sim, para buscar e gerenciar sua estante de livros, você precisa criar uma conta e fazer o login."
    }

    question = None
    answer = None

    if request.method == 'POST':
        # Pega a pergunta do formulário, converte para minúsculas para facilitar a correspondência
        question = request.form.get('question', '').lower()
        # Busca a resposta no dicionário. Se não encontrar, retorna uma resposta padrão.
        answer = qa_pairs.get(question, "Desculpe, não entendi a sua pergunta. Tente uma das perguntas sugeridas.")
        
    # Passamos as perguntas disponíveis para o template para que o usuário saiba o que perguntar
    available_questions = qa_pairs.keys()

    return render_template('chatbot.html', 
                           available_questions=available_questions, 
                           question=question, 
                           answer=answer)

# --- EXECUÇÃO ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)