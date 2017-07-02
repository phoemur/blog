import os
basedir = os.path.abspath(os.path.dirname(__file__))

DEBUG = True
CACHE_TYPE = 'simple'


SECRET_KEY = 'YOUR SECRET KEY'

WTF_CSRF_ENABLED = True
WTF_CSRF_SECRET_KEY = 'YOUR SECRET KEY'

RECAPTCHA_USE_SSL = False
RECAPTCHA_PUBLIC_KEY = 'YOUR SECRET KEY'
RECAPTCHA_PRIVATE_KEY = 'YOUR SECRET KEY'
RECAPTCHA_OPTIONS = {'theme': 'white'}


SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db') + '?check_same_thread=False'
#SQLALCHEMY_DATABASE_URI = "postgresql://blog:senhadebosta@localhost/blog"
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

LOGFILE = os.path.join(basedir, 'blog.log')

# Mail server settings
MAIL_SERVER = 'localhost'
MAIL_PORT = 8025
MAIL_USERNAME = None
MAIL_PASSWORD = None

# Administrator list
# Only users in this list will be able to write articles
ADMINS = ['admin@gmail.com',
          'admin@yahoo.com']

# Pagination
POSTS_PER_PAGE = 3

# Full-text search
WHOOSH_BASE = os.path.join(basedir, 'search.db')
MAX_SEARCH_RESULTS = 50

# slow database query threshold (in seconds)
SQLALCHEMY_RECORD_QUERIES = True
DATABASE_QUERY_TIMEOUT = 1.0

# Sijax
SIJAX_STATIC_PATH = os.path.join(basedir, 'app/static/js/sijax/')
SIJAX_JSON_URI = os.path.join(SIJAX_STATIC_PATH, 'json2.js')
