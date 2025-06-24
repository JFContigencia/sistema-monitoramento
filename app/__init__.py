from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import pytz
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()
# A view de login agora está dentro do blueprint 'main', então usamos 'main.login'
login_manager.login_view = 'main.login'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    def format_datetime_local(value, format='%d/%m/%Y %H:%M:%S'):
        if value is None:
            return ""
        utc_dt = pytz.utc.localize(value)
        local_tz = pytz.timezone('America/Sao_Paulo')
        local_dt = utc_dt.astimezone(local_tz)
        return local_dt.strftime(format)

    app.jinja_env.filters['localtime'] = format_datetime_local

    # --- REGISTRO DO BLUEPRINT ---
    # Importa o blueprint de routes.py e o registra na aplicação
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    # -----------------------------

    # O import de models pode ser feito aqui ou fora, mas é importante
    # que o db seja criado antes de qualquer operação com ele.
    from app import models

    with app.app_context():
        db.create_all()

    return app
