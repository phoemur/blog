# -*- coding: utf-8 -*-

from flask_wtf import Form, RecaptchaField
from wtforms import StringField, BooleanField, PasswordField, TextAreaField
from flask_pagedown.fields import PageDownField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from .models import User


class LoginForm(Form):
    email = StringField('email', validators=[DataRequired(message='Obrigatorio preencher o email'),
                                             Email(message='Email Invalido')])
    senha = PasswordField('senha', [DataRequired(
        message='Obrigatorio preencher a senha')])
    remember_me = BooleanField('remember_me', default=False)
    recaptcha = RecaptchaField()


class RegisterForm(Form):
    nome = StringField('Nome Completo', validators=[
                       DataRequired('Obrigatorio preencher o nome')])
    email = StringField('Email', validators=[DataRequired(message='Obrigatorio preencher o email'),
                                             Email(message='Email Invalido')])
    confirm_email = StringField('Confirmar Email', validators=[DataRequired(message='Obrigatorio confirmar o email'),
                                                               EqualTo('email',
                                                                       message='Emails devem ser iguais')])

    senha = PasswordField('Senha', [DataRequired(
        message='Obrigatorio preencher a senha')])
    confirm = PasswordField('Repetir Senha', [DataRequired(message='Obrigatorio preencher a senha'),
                                              EqualTo('senha',
                                                      message='Senhas devem ser iguais')])
    about_me = TextAreaField('about_me', validators=[Length(min=0,
                                                            max=140,
                                                            message='Maximo de 140 caracteres')])
    recaptcha = RecaptchaField()

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False
        user = User.query.filter_by(email=self.email.data).first()
        if user is not None:
            self.email.errors.append(
                'O e-mail pretendido ja esta em uso por outro usuario.')
            return False
        return True


class EditForm(Form):
    nome = StringField('Nome Completo', validators=[
                       DataRequired('Obrigatorio preencher o nome')])
    email = StringField('Email', validators=[DataRequired(message='Obrigatorio preencher o email'),
                                             Email(message='Email Invalido')])
    senha = PasswordField('Senha', [DataRequired(
        message='Obrigatorio preencher a senha')])
    confirm = PasswordField('Repetir Senha', [DataRequired(message='Obrigatorio preencher a senha'),
                                              EqualTo('senha',
                                                      message='Senhas devem ser iguais')])
    about_me = TextAreaField('about_me', validators=[Length(min=0,
                                                            max=140,
                                                            message='Maximo de 140 caracteres')])

    def __init__(self, email_original, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.email_original = email_original

    def validate(self):
        if not Form.validate(self):
            return False
        if self.email.data == self.email_original:
            return True
        user = User.query.filter_by(email=self.email.data).first()
        if user is not None:
            self.email.errors.append(
                'O e-mail pretendido ja esta em uso por outro usuario.')
            return False
        return True


class EraseForm(Form):
    apagar = BooleanField('apagar', default=False)


class RecoverForm(Form):
    email = StringField('Email', validators=[DataRequired(message='Obrigatorio preencher o email'),
                                             Email(message='Email Invalido')])
    recaptcha = RecaptchaField()

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False
        user = User.query.filter_by(email=self.email.data).first()
        if user is None:
            self.email.errors.append(
                'Esta conta nao existe. Favor cadastrar-se.')
            return False
        return True


class ContactForm(Form):
    nome = StringField('Nome Completo', validators=[
                       DataRequired('Obrigatorio preencher o nome')])
    email = StringField('Email', validators=[DataRequired(message='Obrigatorio preencher o email'),
                                             Email(message='Email Invalido')])
    assunto = StringField('Assunto', validators=[DataRequired('Obrigatorio preencher assunto'),
                                                 Length(min=0, max=140, message='Maximo de 140 caracteres')])
    mensagem = TextAreaField('Mensagem', validators=[DataRequired('Obrigatorio preencher a mensagem'),
                                                     Length(min=0, max=2048, message='Mensagem muito Longa')])
    recaptcha = RecaptchaField()


class EscreverArtigo(Form):
    titulo = StringField('Título', validators=[
                         DataRequired('Obrigatorio preencher o Titulo')])
    categoria = StringField('Categoria', validators=[DataRequired('Obrigatorio preencher ao menos uma categoria'),
                                                     Length(min=0, max=140, message='Maximo de 140 caracteres')])
    desc = StringField('Descricao', validators=[DataRequired('Obrigatorio preencher a descricao'),
                                                Length(min=0, max=300, message='Maximo de 300 caracteres')])
    texto = PageDownField('Mensagem', validators=[DataRequired('Obrigatorio preencher o conteudo'),
                                                  Length(min=0, max=100000, message='Artigo muito Longo')])
    recaptcha = RecaptchaField()


class ComentarArtigo(Form):
    texto = TextAreaField('Mensagem', validators=[DataRequired('Obrigatorio preencher o conteudo'),
                                                  Length(min=0, max=700, message='Comentario muito longo')])
    recaptcha = RecaptchaField()


class SearchForm(Form):
    search = StringField('search', validators=[
                         DataRequired('Preencha a busca')])
