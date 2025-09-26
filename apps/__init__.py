# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import os
from flask_mail import Mail
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from flask_cors import CORS, cross_origin
#from apps.common.util import generate_math_problem
db = SQLAlchemy()
login_manager = LoginManager()



def register_extensions(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
    login_manager.init_app(app)


def register_blueprints(app):
    for module_name in ('authentication', 'home', 'admin'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)


def configure_database(app):

    @app.before_first_request
    def initialize_database():
        try:
            with app.app_context():
                db.create_all()
            #db.create_all()

        except Exception as e:

            print('> Error: DBMS Exception: ' + str(e) )

            # fallback to SQLite
            basedir = os.path.abspath(os.path.dirname(__file__))
            app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db.sqlite3')

            print('> Fallback to SQLite ')
            db.create_all()


    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()

from apps.authentication.oauth import github_blueprint

class ConfigClass(object):
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_SSL = False
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'office.jaikalki@gmail.com'
    MAIL_PASSWORD = 'iocf mlop nugj nuyl'
    MAIL_DEFAULT_SENDER = '"Jaikalki Technology" <office.jaikalki@gmail.com>'
    ADMINS = ['office.jaikalki@gmail.com']
    # Flask-User settings
    USER_APP_NAME = "Jaikalki Technology"  # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = True  # Enable email authentication
    USER_ENABLE_USERNAME = True  # Disable username authentication
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    USER_EMAIL_SENDER_EMAIL = "Jaikalki Technology"
    USER_ALLOW_LOGIN_WITHOUT_CONFIRMED_EMAIL = True
    USER_ENABLE_CONFIRM_EMAIL = False
    USER_CORPORATION_NAME = 'Jaikalki Technology'
    USER_COPYRIGHT_YEAR = 2024
mail = Mail()
def create_app(config):
    app = Flask(__name__)

    app.config.from_object(config)
    app.config.from_object(__name__ + '.ConfigClass')
    register_extensions(app)
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "https://jaikalki.com",


                "https://www.jaikalki.com",

                "localhost",
                "http://127.0.0.1:5000/",
                "https://gurutvapay.com/",
                "https://www.gurutvapay.com/"

            ]
        }
    })

    app.register_blueprint(github_blueprint, url_prefix="/login")

    register_blueprints(app)
    configure_database(app)
    #db.init_app(app)
    mail.init_app(app)
    return app
