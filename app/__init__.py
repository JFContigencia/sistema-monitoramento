from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login' # a rota de login

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    # --- Adicione esta nova importação do Blueprint aqui ---
    from app.routes import main_bp
    app.register_blueprint(main_bp) # <-- NOVA LINHA: Registra o Blueprint

    # Criar a pasta de uploads se não existir
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # NOTA: O Flask-SQLAlchemy já faz isso se o app_context for ativado.
    # Manter para garantir na primeira inicialização.
    with app.app_context():
        db.create_all()

    # NOTE: Não precisa mais importar 'models' aqui se não for usado diretamente,
    # mas manter a linha 'from app import routes, models' para a criação do DB
    # na linha com python -c é válido, porém aqui só importa o blueprint.
    # Se você já tinha `from app import models`, pode manter ou remover se não houver uso direto.

    return app
