# -*- coding: utf-8 -*-

import random
import string
import misaka
from datetime import datetime
from urlparse import urljoin
from time import time
import re

from flask import render_template, flash, redirect, session, url_for, request, g, abort
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from .forms import LoginForm, RegisterForm, EditForm, EraseForm, RecoverForm, ContactForm, EscreverArtigo, ComentarArtigo, SearchForm
from .models import User, Artigo, Comentario, Categoria, iterativeChildren
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.contrib.atom import AtomFeed
from .helper import send_email
from jinja2 import Markup
from flask.ext.sqlalchemy import get_debug_queries
import flask_admin as admin
from flask_admin.contrib import sqla
from flask_admin import helpers, expose
from config import DATABASE_QUERY_TIMEOUT


class SijaxHandler(object):
    '''
    A container class for all Sijax handlers.
    '''
    
    @staticmethod
    def like_artigo(obj_response, artigo_id, user_id):
        artigo = load_artigo(artigo_id)
        if artigo is None:
            return obj_response.alert("Erro de procedimento")
        user = load_user(user_id)
        if user is None:
            return obj_response.alert("Erro de procedimento")
        
        if user not in artigo.user_liked:
            if user in artigo.user_disliked:
                artigo.user_disliked.remove(user)
            
            artigo.user_liked.append(user)
            db.session.add(artigo)
            db.session.commit()
            
            likes = artigo.user_liked.all().__len__()
            dislikes = artigo.user_disliked.all().__len__()
            
            
            obj_response.script('$("#like_artigo{0}").html({1});'.format(artigo.id, likes))
            obj_response.script('$("#dislike_artigo{0}").html({1});'.format(artigo.id, dislikes))
            #obj_response.script('document.getElementById("{}").innerHTML = "{}";'.format('like_artigo' + str(artigo.id), likes))
            #obj_response.script('document.getElementById("{}").innerHTML = "{}";'.format('dislike_artigo' + str(artigo.id), dislikes))
            obj_response.alert("Curtiu")
        else:
            return obj_response.alert("Somente possivel curtir uma vez")
        
    @staticmethod
    def dislike_artigo(obj_response, artigo_id, user_id):
        artigo = load_artigo(artigo_id)
        if artigo is None:
            return obj_response.alert("Erro de procedimento")
        user = load_user(user_id)
        if user is None:
            return obj_response.alert("Erro de procedimento")
        
        if user not in artigo.user_disliked:
            if user in artigo.user_liked:
                artigo.user_liked.remove(user)
                
            artigo.user_disliked.append(user)
            db.session.add(artigo)
            db.session.commit()
            
            likes = artigo.user_liked.all().__len__()
            dislikes = artigo.user_disliked.all().__len__()
            
            obj_response.script('$("#like_artigo{0}").html({1});'.format(artigo.id, likes))
            obj_response.script('$("#dislike_artigo{0}").html({1});'.format(artigo.id, dislikes))
            #obj_response.script('document.getElementById("{}").innerHTML = "{}";'.format('like_artigo' + str(artigo.id), likes))
            #obj_response.script('document.getElementById("{}").innerHTML = "{}";'.format('dislike_artigo' + str(artigo.id), dislikes))
            obj_response.alert("Descurtiu")
        else:
            return obj_response.alert("Somente possivel descurtir uma vez")
    
    @staticmethod
    def like_comentario(obj_response, comentario_id, user_id):
        user = load_user(user_id)
        if user is None:
            return obj_response.alert("Erro de procedimento")
        comentario = Comentario.query.get(int(comentario_id))
        if comentario is None:
            return obj_response.alert("Erro de procedimento")
        
        if user not in comentario.user_liked:
            if user in comentario.user_disliked:
                comentario.user_disliked.remove(user)
                
            comentario.user_liked.append(user)
            db.session.add(comentario)
            db.session.commit()
            
            likes = comentario.user_liked.all().__len__()
            dislikes = comentario.user_disliked.all().__len__()
            
            obj_response.script('$("#like_coment{0}").html({1});'.format(comentario.id, likes))
            obj_response.script('$("#dislike_coment{0}").html({1});'.format(comentario.id, dislikes))
            #obj_response.script('document.getElementById("{}").innerHTML = "{}";'.format('like_coment' + str(comentario.id), likes))
            #obj_response.script('document.getElementById("{}").innerHTML = "{}";'.format('dislike_coment' + str(comentario.id), dislikes))
            obj_response.alert("Curtiu")
        else:
            return obj_response.alert("Somente possivel curtir uma vez")
        
    @staticmethod
    def dislike_comentario(obj_response, comentario_id, user_id):
        user = load_user(user_id)
        if user is None:
            return obj_response.alert("Erro de procedimento")
        comentario = Comentario.query.get(int(comentario_id))
        if comentario is None:
            return obj_response.alert("Erro de procedimento")
        
        if user not in comentario.user_disliked:
            if user in comentario.user_liked:
                comentario.user_liked.remove(user)
            
            comentario.user_disliked.append(user)
            db.session.add(comentario)
            db.session.commit()
            
            likes = comentario.user_liked.all().__len__()
            dislikes = comentario.user_disliked.all().__len__()
            
            obj_response.script('$("#like_coment{0}").html({1});'.format(comentario.id, likes))
            obj_response.script('$("#dislike_coment{0}").html({1});'.format(comentario.id, dislikes))
            #obj_response.script('document.getElementById("{}").innerHTML = "{}";'.format('like_coment' + str(comentario.id), likes))
            #obj_response.script('document.getElementById("{}").innerHTML = "{}";'.format('dislike_coment' + str(comentario.id), dislikes))
            obj_response.alert("Descurtiu")
        else:
            return obj_response.alert("Somente possivel descurtir uma vez")


@app.route('/', methods=['GET', 'POST'])
@app.route('/index/', methods=['GET', 'POST'])
@app.route('/index/page/<int:page>/', methods=['GET', 'POST'])
def index(page=1):
    if g.sijax.is_sijax_request:
        g.sijax.register_object(SijaxHandler)
        return g.sijax.process_request()
    
    artigos = Artigo.query.order_by(Artigo.id.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], True)
    return render_template('index.html',
                           titulo='Blog do Bosta - Home',
                           artigos=artigos)


@app.before_request
def before_request():
    g.user = current_user
    g.request_start_time = time()
    g.request_time = lambda: "%.3fs" % (time() - g.request_start_time)    
    


@app.after_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= DATABASE_QUERY_TIMEOUT:
            app.logger.warning("SLOW QUERY: %s\nParameters: %s\nDuration: %fs\nContext: %s\n" % (
                query.statement, query.parameters, query.duration, query.context))
    return response


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


def load_artigo(id):
    return Artigo.query.get(int(id))


def get_removido():
    u_list = []
    for u in User.query.filter_by(nome='removido'):
        u_list.append(u)

    if len(u_list) == 0:
        removido = User(nome='removido',
                        email='removido@removido.com.br',
                        about_me='Local onde ficam abrigados artigos e comentarios de contas que foram excluidas',
                        senha=generate_password_hash('12035987h@+~vsdafçoihasdoivugv12',
                                                     method='pbkdf2:sha256'))
        db.session.add(removido)
        db.session.commit()
        return removido
    else:
        return u_list[0]


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        senha = form.senha.data
        registered_user = User.query.filter_by(email=email).first()

        if registered_user is None:
            flash('Usuario nao registrado', 'alert-danger')
            return redirect(url_for('login'))

        passed = registered_user.check_password(senha)

        if not passed:
            flash('Email ou Senha incorretos', 'alert-danger')
            return redirect(url_for('login'))
        else:
            session['remember_me'] = form.remember_me.data
            login_user(registered_user, remember=session[
                       'remember_me'], force=True)
            registered_user.last_seen = datetime.utcnow()
            db.session.add(registered_user)
            db.session.commit()
            flash('Login realizado com sucesso', 'alert-info')
            return redirect(request.args.get('next') or url_for('index'))
    return render_template('login.html',
                           titulo='Fazer Login',
                           form=form)


@app.route('/logout/')
def logout(page=1):
    # Reset recovery password
    if current_user.temp_senha != 'pbkdf2:sha256:1000$uTgUMcR5$a9034e4b77636b4e7ae92a8e6cf4e4a6da49d680ab88a20dfac3695da6941c5e':
        current_user.temp_senha = 'pbkdf2:sha256:1000$uTgUMcR5$a9034e4b77636b4e7ae92a8e6cf4e4a6da49d680ab88a20dfac3695da6941c5e'
        db.session.add(current_user)
        db.session.commit()

    # Logout
    logout_user()
    flash('Logout realizado com sucesso', 'alert-info')
    artigos = Artigo.query.order_by(Artigo.id.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], True)
    
    return render_template('index.html',
                           titulo='Blog do Bosta - Home',
                           artigos=artigos)


@app.route('/minhaconta/')
@login_required
def minhaconta():
    id = current_user.get_id()
    return redirect(url_for('usuario', id=id))


@app.route('/user/<int:id>/')
def usuario(id=None):
    id = int(id)
    user = load_user(id)

    if user is None:
        flash('Usuario nao existente', 'alert-danger')
        return redirect(url_for('index'))

    artigos = Artigo.query.filter_by(author=user).order_by(Artigo.id.desc())

    admins = app.config['ADMINS']
    return render_template('user.html',
                           user=user,
                           artigos=artigos,
                           admins=admins)


@app.route('/register/', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        nome = form.nome.data
        email = form.email.data
        senha = generate_password_hash(form.senha.data, method='pbkdf2:sha256')
        about_me = form.about_me.data
        user = User(nome=nome,
                    email=email,
                    senha=senha,
                    about_me=about_me,
                    registered_on=datetime.utcnow(),
                    last_seen=datetime.utcnow())

        db.session.add(user)
        db.session.commit()
        flash('Usuario cadastrado com sucesso', 'alert-info')
        if g.user.is_authenticated:
            logout_user()

        login_user(user)
        return redirect(url_for('minhaconta'))
    return render_template('register.html', form=form)


@app.route('/edit/', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.email)
    if form.validate_on_submit():
        g.user.nome = form.nome.data
        g.user.email = form.email.data
        g.user.senha = generate_password_hash(
            form.senha.data, method='pbkdf2:sha256')
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Alteracoes salvas com sucesso', 'alert-info')
        return redirect(url_for('minhaconta'))
    else:
        form.nome.data = g.user.nome
        form.email.data = g.user.email
        form.about_me.data = g.user.about_me

    return render_template('edit.html', form=form, user=g.user)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


@app.route('/apagar/', methods=['GET', 'POST'])
@login_required
def apagar():
    form = EraseForm()
    user = load_user(g.user.id)
    email = g.user.email

    if form.validate_on_submit():
        if form.apagar.data is True:
            removido = get_removido()
            for art in Artigo.query.filter_by(author=user):
                art.author = removido
                db.session.add(art)

            for com in Comentario.query.filter_by(author=user):
                com.author = removido
                db.session.add(com)
            db.session.commit()
            
            for com in user.com_liked:
                com.user_liked.remove(user)
                db.session.add(com)
            db.session.commit()
            
            for com in user.com_disliked:
                com.user_disliked.remove(user)
                db.session.add(com)
            db.session.commit()
            
            for art in user.art_liked:
                art.user_liked.remove(user)
                db.session.add(art)
            db.session.commit()
            
            for art in user.art_disliked:
                art.user_disliked.remove(user)
                db.session.add(art)
            db.session.commit()

            logout_user()
            db.session.delete(user)
            db.session.commit()
            flash('Usuario {} removido com sucesso'.format(user.email), 'alert-info')
            return redirect(url_for('index'))
        else:
            flash('Remocao nao confirmada pelo usuario', 'alert-danger')

    return render_template('apagar.html',
                           user=user,
                           form=form)


@app.route('/recovery/', methods=['GET', 'POST'])
def recovery():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('index'))

    form = RecoverForm()
    if form.validate_on_submit():
        email = form.email.data
        nova_senha = ''.join(random.choice(
            string.ascii_uppercase + string.digits) for _ in range(6))
        novo_hash = generate_password_hash(nova_senha, method='pbkdf2:sha256')
        user = User.query.filter_by(email=email).first()
        user.temp_senha = novo_hash
        db.session.add(user)
        db.session.commit()
        send_email('Recuperacao de senha - Fraternidade Avareense',
                   app.config['ADMINS'][0],
                   [email],
                   render_template('email_recover.txt',
                                   user=user,
                                   nova_senha=nova_senha))
        flash('Senha temporaria enviada. Verifique seu e-mail', 'alert-info')
        return redirect(url_for('recovery'))

    return render_template('recovery.html', form=form)


@app.route('/contato/', methods=['GET', 'POST'])
def contato():
    form = ContactForm()
    user = g.user
    if user.is_authenticated:
        form.nome.data = user.nome
        form.email.data = user.email

    if form.validate_on_submit():
        nome = form.nome.data
        email = form.email.data
        assunto = form.assunto.data
        mensagem = form.mensagem.data
        send_email(assunto,
                   email,
                   [app.config['ADMINS'][0]],
                   mensagem)
        flash('Mensagem enviada', 'alert-info')
        return redirect(url_for('index'))

    return render_template('contato.html', form=form, user=user)


@app.route('/artigo/<int:id>/', methods=['GET', 'POST'])
def read_artigo(id):
    if g.sijax.is_sijax_request:
        g.sijax.register_object(SijaxHandler)
        return g.sijax.process_request()
    
    id = int(id)
    artigo = load_artigo(id)

    if artigo is None:
        flash('Artigo nao existente', 'alert-danger')
        return redirect(url_for('index'))

    texto = Markup('\n' + artigo.texto)
    comentarios = Comentario.query.filter_by(article=artigo).filter_by(parent=None)
    form = ComentarArtigo()

    if form.validate_on_submit():
        if '@[responder_comentario@' in form.texto.data:
            parent = int(form.texto.data.split('@')[2])
            texto = form.texto.data.split('@')[3].lstrip(']')
        else:
            parent = None
            texto = form.texto.data
            
        com = Comentario(texto=texto,
                         parent=parent,
                         data=datetime.utcnow(),
                         artigo_id=artigo.id,
                         user_id=g.user.id)
        db.session.add(com)
        db.session.commit()
        return redirect(url_for('read_artigo', id=artigo.id))

    try:
        artigo.visitors += 1
    except TypeError:
        artigo.visitors = 1
        
    db.session.add(artigo)
    db.session.commit()
    return render_template('read_artigo.html',
                           artigo=artigo,
                           comentarios=comentarios,
                           form=form,
                           texto=texto)


def get_categoria(cat):
    categoria = Categoria.query.filter_by(nome=cat).first()

    if categoria is None:
        categoria = Categoria(nome=cat)
        db.session.add(categoria)
        db.session.commit()
        return categoria
    else:
        return categoria


@app.route('/escrever/', methods=['GET', 'POST'])
@login_required
def escrever():
    user = g.user
    if user.email not in app.config['ADMINS']:
        flash('Usuario nao autorizado a escrever artigos', 'alert-danger')
        return redirect(url_for('index'))

    form = EscreverArtigo()

    if form.validate_on_submit():
        titulo = form.titulo.data
        texto = form.texto.data
        abstract = form.desc.data
        artigo = Artigo(titulo=titulo,
                        texto=texto,
                        abstract=abstract,
                        data=datetime.utcnow(),
                        user_id=user.id)

        for c in sorted(form.categoria.data.split(',')):
            categoria = get_categoria(c)
            artigo.categorias.append(categoria)

        db.session.add(artigo)
        db.session.commit()
        flash('Artigo incluido com sucesso', 'alert-info')
        return redirect(url_for('minhaconta'))

    return render_template('escrever.html', user=user, form=form)


@app.route('/apagar_artigo/<int:id>/', methods=['GET', 'POST'])
@login_required
def apagar_artigo(id):
    id = int(id)
    artigo = load_artigo(id)

    if artigo is None:
        flash('Artigo nao existente', 'alert-danger')
        return redirect(url_for('index'))

    if g.user.id != artigo.author.id:
        flash('Somente o autor pode apagar um artigo', 'alert-danger')
        return redirect(url_for('index'))

    form = EraseForm()
    if form.validate_on_submit():
        if form.apagar.data is True:
            for com in Comentario.query.filter_by(article=artigo):
                for u in com.user_liked:
                    com.user_liked.remove(u)
                for u in com.user_disliked:
                    com.user_disliked.remove(u)
                db.session.add(com)
                db.session.commit()
                
                db.session.delete(com)
            db.session.commit()

            for cat in artigo.categorias:
                artigo.categorias.remove(cat)
            db.session.add(artigo)
            db.session.commit()
            
            for u in artigo.user_liked:
                artigo.user_liked.remove(u)
            for u in artigo.user_disliked:
                artigo.user_disliked.remove(u)
            db.session.add(artigo)
            db.session.commit()

            db.session.delete(artigo)
            db.session.commit()
            flash('Artigo removido com sucesso', 'alert-info')
            return redirect(url_for('index'))
        else:
            flash('Remocao nao confirmada', 'alert-danger')
            return redirect(url_for('index'))

    return render_template('apagar_artigo.html',
                           artigo=artigo,
                           user=g.user,
                           form=form)


@app.route('/editar_artigo/<int:id>/', methods=['GET', 'POST'])
@login_required
def editar_artigo(id):
    id = int(id)
    artigo = load_artigo(id)

    if artigo is None:
        flash('Artigo nao existente', 'alert-danger')
        return redirect(url_for('index'))

    if g.user.id != artigo.author.id:
        flash('Somente o autor pode editar um artigo', 'alert-danger')
        return redirect(url_for('index'))

    form = EscreverArtigo()

    if form.validate_on_submit():
        artigo.titulo = form.titulo.data
        artigo.texto = form.texto.data
        artigo.abstract = form.desc.data
        artigo.data = datetime.utcnow()
        artigo.categorias = []
        db.session.add(artigo)
        db.session.commit()
        
        for c in sorted(form.categoria.data.split(',')):
            categoria = get_categoria(c.rstrip().lstrip())
            artigo.categorias.append(categoria)

        db.session.add(artigo)
        db.session.commit()
        flash('Artigo editado com sucesso', 'alert-info')
        return redirect(url_for('index'))
    else:
        form.titulo.data = artigo.titulo
        form.texto.data = artigo.texto
        form.desc.data = artigo.abstract
        cat_list = [c.nome for c in artigo.categorias.all()]
        form.categoria.data = ','.join(cat_list)

    return render_template('editar_artigo.html',
                           user=g.user,
                           artigo=artigo,
                           form=form)


@app.route('/artigo/<int:id_art>/apagar_comentario/<int:id_com>/')
@login_required
def apagar_comentario(id_art, id_com):
    id_art = int(id_art)
    id_com = int(id_com)
    comentario = Comentario.query.get(id_com)
    
    if comentario is None:
        flash('Comentario nao encontrado', 'alert-danger')
        return redirect(url_for('read_artigo', id=id_art))
    
    if not g.user == comentario.author:
        flash('Somente o dono pode apagar um comentario', 'alert-danger')
        return redirect(url_for('read_artigo', id=id_art))
    
    for u in comentario.user_liked:
        comentario.user_liked.remove(u)
        
    for u in comentario.user_disliked:
        comentario.user_disliked.remove(u)

    db.session.add(comentario)
    db.session.commit()
    
    if len(comentario.children.all()) == 0:
        db.session.delete(comentario)
        db.session.commit()
    else:
        comentario.author = get_removido()
        comentario.texto = 'Comentario removido pelo autor'
        db.session.add(comentario)
        db.session.commit()
       
    flash('Comentario removido com sucesso', 'alert-info')
    return redirect(url_for('read_artigo', id=id_art))


@app.route('/search', methods=['GET', 'POST'])
def search():
    if g.sijax.is_sijax_request:
        g.sijax.register_object(SijaxHandler)
        return g.sijax.process_request()
    
    form = SearchForm()
    resultados = []

    if form.validate_on_submit():
        resultados = Artigo.query.whoosh_search(form.search.data, app.config[
                                                'MAX_SEARCH_RESULTS']).order_by(Artigo.id.desc())

    return render_template('search.html', form=form, resultados=resultados)


def make_external(url):
    return urljoin(request.url_root, url)


@app.route('/recent.atom')
def recent_feed():
    feed = AtomFeed('Artigos Recentes',
                    feed_url=request.url, url=request.url_root)
    artigos = Artigo.query.order_by(Artigo.data.desc()).limit(5).all()

    for artigo in artigos:
        feed.add(artigo.titulo, misaka.html(artigo.texto),
                 content_type='html',
                 author=artigo.author.nome,
                 url=make_external(url_for('read_artigo', id=artigo.id)),
                 updated=artigo.data)

    return feed.get_response()


@app.route('/categoria/<int:id>/', methods=['GET', 'POST'])
@app.route('/categoria/<int:id>/page/<int:page>/', methods=['GET', 'POST'])
def cat_articles(id, page=1):
    if g.sijax.is_sijax_request:
        g.sijax.register_object(SijaxHandler)
        return g.sijax.process_request()
    
    id = int(id)
    cat = Categoria.query.filter_by(id=id).first()
    if cat is not None:
        artigos = cat.artigos.order_by(Artigo.id.desc()).paginate(
            page, app.config['POSTS_PER_PAGE'], True)
    else:
        abort(404)

    return render_template('cat_articles.html',
                           artigos=artigos,
                           cat=cat)


@app.route('/categorias/')
def categorias():
    categorias = Categoria.query.all()
    categorias.sort(key=lambda x: len(x.artigos.all()), reverse=True)
    return render_template('categorias.html', categorias=categorias)


# Create customized model view class
class MyModelView(sqla.ModelView):
    def is_accessible(self):
        return current_user.is_authenticated
    
# Create customized index view class that handles login & registration
class MyAdminIndexView(admin.AdminIndexView):
    @expose('/')
    def index(self):
        if g.user is not None and g.user.is_authenticated:
            if g.user.email in app.config['ADMINS']:
                return super(MyAdminIndexView, self).index()
        abort(403)
