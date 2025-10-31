from flask import Flask
from fs_proxy.db import db
from logging.config import dictConfig
import logging

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '%(asctime)s fs_proxy %(levelname)-8s %(filename)s(%(lineno)d) %(funcName)s(): %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    },
    'disable_existing_loggers': False
})

# Create a Flask application instance
app = Flask(__name__)
app.config.from_object("fs_proxy.config.Config")

#sql alchemy con flask_sqlalchemy
#app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://"+_db_user+":"+_db_pw+"@"+_db_host+":"+_db_port+"/"+_db_name 
#app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"url":"mysql+pymysql://"+_db_user+":"+_db_pw+"@"+_db_host+":"+_db_port+"/"+_db_name,
#                                           "pool_size":_db_pool_size} 
#app.config['SQLALCHEMY_ECHO'] = False #para debug sql

db.init_app(app)
logging.debug("inicamos app flask")
# one time setup
with app.app_context():
    db.create_all()
    db.session.commit()
    logging.debug("init db")

#importamos todas las vistas definidas
from fs_proxy.views import * 



