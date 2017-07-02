# -*- coding: utf-8 -*-

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from flask.ext.misaka import Misaka
from flask.ext.moment import Moment
from flask.ext.pagedown import PageDown
import flask_admin as admin
from flask_admin.contrib import sqla
from flask_admin import helpers, expose
import flask_sijax
from os.path import join

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = '/login'
lm.login_message = 'Necessario fazer Login para entrar'
mail = Mail(app)
md = Misaka(app)
moment = Moment(app)
pagedown = PageDown(app)
sij = flask_sijax.Sijax(app)

if not app.debug:
    import logging
    LOGFILE = app.config['LOGFILE']
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(LOGFILE, 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('Blog Startup')

from app import views, models     

admin = admin.Admin(app, name='Blog', index_view=views.MyAdminIndexView(), template_mode='bootstrap3')
admin.add_view(views.MyModelView(models.User, db.session))
admin.add_view(views.MyModelView(models.Artigo, db.session))
admin.add_view(views.MyModelView(models.Categoria, db.session))
admin.add_view(views.MyModelView(models.Comentario, db.session))