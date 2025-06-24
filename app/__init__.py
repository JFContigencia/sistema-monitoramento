from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import pytz
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # --- Início da Adição do Filtro de Fuso Horário ---
    def format_datetime_local(value, format='%d/%m/%Y %H:%M:%S'):
        if value is None:
            return ""
        utc_dt = pytz.utc.localize(value)
        local_tz = pytz.timezone('America/Sao_Paulo') # Fuso Horário GMT-3
        local_dt = utc_dt.astimezone(local_tz)
        return local_dt.strftime(format)

    app.jinja_env.filters['localtime'] = format_datetime_local
    # --- Fim da Adição ---

    from app import routes, models

    with app.app_context():
        db.create_all()

    return app
