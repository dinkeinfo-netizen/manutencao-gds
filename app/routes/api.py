from flask import Flask
from .extensions import db, migrate, login_manager
import os
from flask_wtf.csrf import CSRFProtect

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    
    # Configurações
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chave-secreta-aleatoria-aqui')
    csrf = CSRFProtect(app) 
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'postgresql://manutencao_user:manutencao_pass@db:5432/manutencao_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicialização de extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Registrar blueprints
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    return app
