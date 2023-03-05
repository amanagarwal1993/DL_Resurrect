# -*- coding: utf-8 -*-
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask_mail import Mail
from flask_moment import Moment
from flask_babel import Babel
from flask_babel import lazy_gettext as _l
from flask import request
#from flask_uploads import UploadSet, IMAGES, configure_uploads
from flask_talisman import Talisman
from flask_sslify import SSLify

flaskapp = Flask(__name__)
flaskapp.config.from_object(Config)
mail = Mail(flaskapp)

db = SQLAlchemy(flaskapp)
migrate = Migrate(flaskapp, db, compare_type=True)
moment = Moment(flaskapp)
babel = Babel(flaskapp)
sslify = SSLify(flaskapp)

csp = {
    'default-src':
    '\'self\'',
    'img-src': [
        '\'self\'', '*.amazonaws.com', '*.gravatar.com',
        'cdn.onlinewebfonts.com'
    ],
    'script-src': [
        '\'self\'', 'ajax.googleapis.com', 'http://cdnjs.cloudflare.com',
        'http://code.jquery.com'
    ],
    'style-src':
    '\'self\''
}

talisman = Talisman(flaskapp,
                    content_security_policy=csp,
                    content_security_policy_nonce_in=['script-src'])

login = LoginManager(flaskapp)
login.login_view = 'login'
login.login_message = _l("Please log in first.")

#images = UploadSet('images', IMAGES)
#configure_uploads(flaskapp, images)

from app import routes, models


@flaskapp.route('/')
def index():
    return 'Hello from Flask!'
