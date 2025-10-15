from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Usuário',
                           validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nome de usuário já existe. Por favor, escolha outro.')

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Login')

class BookSearchForm(FlaskForm):
    search_query = StringField('Buscar por Título ou Autor', validators=[DataRequired()])
    submit = SubmitField('Buscar Livros')

class UpdateBookForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('Quero Ler', 'Quero Ler'),
        ('Lendo', 'Lendo'),
        ('Lido', 'Lido')
    ], validators=[DataRequired()])
    current_page = IntegerField('Página Atual', default=0)
    submit = SubmitField('Atualizar')