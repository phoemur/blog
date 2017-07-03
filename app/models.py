# -*- coding: utf-8 -*-

from hashlib import md5
from app import app, db
import flask_whooshalchemy as whooshalchemy
from werkzeug.security import generate_password_hash, check_password_hash

categorias_table = db.Table('categorias_table',
                            db.Column('artigo_id', db.Integer,
                                      db.ForeignKey('artigo.id')),
                            db.Column('categoria_id', db.Integer, db.ForeignKey('categoria.id')))
                            
artigo_likes = db.Table('artigo_likes',
                        db.Column('artigo_id', db.Integer, db.ForeignKey('artigo.id')),
                        db.Column('user_id', db.Integer, db.ForeignKey('user.id')))

artigo_dislikes = db.Table('artigo_dislikes',
                           db.Column('artigo_id', db.Integer, db.ForeignKey('artigo.id')),
                           db.Column('user_id', db.Integer, db.ForeignKey('user.id')))

comentario_likes = db.Table('comentario_likes',
                            db.Column('comentario_id', db.Integer, db.ForeignKey('comentario.id')),
                            db.Column('user_id', db.Integer, db.ForeignKey('user.id')))

comentario_dislikes = db.Table('comentario_dislikes',
                               db.Column('comentario_id', db.Integer, db.ForeignKey('comentario.id')),
                               db.Column('user_id', db.Integer, db.ForeignKey('user.id')))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(64), index=True, unique=False)
    email = db.Column(db.String(64), index=True, unique=True)
    senha = db.Column(db.String(100))
    temp_senha = db.Column(db.String(100))
    # generate_password_hash('senha', method='pbkdf2:sha256')
    about_me = db.Column(db.String(140))
    registered_on = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime)
    artigos = db.relationship('Artigo', backref='author', lazy='dynamic')
    comentarios = db.relationship(
        'Comentario', backref='author', lazy='dynamic')
    likes = db.relationship('Artigo', secondary=artigo_likes, backref=db.backref('user_liked', lazy='dynamic'))
    dislikes = db.relationship('Artigo', secondary=artigo_dislikes, backref=db.backref('user_disliked', lazy='dynamic'))
    com_likes = db.relationship('Comentario', secondary=comentario_likes, backref=db.backref('user_liked', lazy='dynamic'))
    com_dislikes = db.relationship('Comentario', secondary=comentario_dislikes, backref=db.backref('user_disliked', lazy='dynamic'))
    
    
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def avatar(self, size):
        return 'http://www.gravatar.com/avatar/%s?d=identicon&s=%d' % (md5(self.email).hexdigest(), size)
    
    def check_password(self, password):
        return check_password_hash(self.senha, password) or check_password_hash(self.temp_senha, password)

    def __repr__(self):
        return '<User {}>'.format(self.email)


class Artigo(db.Model):
    __searchable__ = ['texto']
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), index=True, unique=True)
    texto = db.Column(db.String(100000), index=False, unique=False)
    abstract = db.Column(db.String(300), index=False, unique=False)
    data = db.Column(db.DateTime)
    visitors = db.Column(db.Integer, default=1)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comentarios = db.relationship(
        'Comentario', backref='article', lazy='dynamic')
    cat = db.relationship('Categoria',
                          secondary=categorias_table,
                          backref=db.backref('artigos', lazy='dynamic'))
    likes = db.relationship('User', secondary=artigo_likes, backref=db.backref('art_liked', lazy='dynamic'))
    dislikes = db.relationship('User', secondary=artigo_dislikes, backref=db.backref('art_disliked', lazy='dynamic'))

    @property
    def com_quantidade(self):
        return Comentario.query.filter_by(article=self).count()

    def __repr__(self):
        return '<Artigo {}>'.format(self.titulo)


class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = nome = db.Column(db.String(64), index=True, unique=True)
    art = db.relationship('Artigo',
                          secondary=categorias_table,
                          backref=db.backref('categorias', lazy='dynamic'))

    def __repr__(self):
        return '<Categoria {}>'.format(self.id)


class Comentario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.String(700), index=True, unique=False)
    data = db.Column(db.DateTime)
    artigo_id = db.Column(db.Integer, db.ForeignKey('artigo.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    com_likes = db.relationship('User', secondary=comentario_likes, backref=db.backref('com_liked', lazy='dynamic'))
    com_dislikes = db.relationship('User', secondary=comentario_dislikes, backref=db.backref('com_disliked', lazy='dynamic'))
    parent = db.Column(db.Integer, db.ForeignKey('comentario.id'), default=None)
    
    def __repr__(self):
        return '<Comentario {}>'.format(self.id)
    
    @property
    def children(self):
        return Comentario.query.filter_by(parent=self.id)
    
    @property
    def nest_level(self):
        '''
        Recursively find the nest level of a comentary
        '''
        if self.parent is None:
            return 0
        else:
            return 1 + Comentario.query.get(self.parent).nest_level
        
    @property
    def positive(self):
        return self.user_liked.all().__len__()
    
    @property
    def negative(self):
        return self.user_disliked.all().__len__()
        

whooshalchemy.whoosh_index(app, Artigo)

def iterativeChildren(nodes):
    results = []
    while 1:
        newNodes = []
        if len(nodes) == 0:
            break
        for node in nodes:
            results.append(node)
            if len(node.children.all()) > 0:
                for child in node.children:
                    newNodes.append(child)
        nodes = newNodes
    return results
