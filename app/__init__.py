from flask import Flask
from .extensions import db, migrate, login_manager
from .config import Config
import os
from flask_wtf.csrf import CSRFProtect
from .email_service import init_mail
from flask import render_template

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.logger.info("APLICACAO INICIADA - CONFIG CARREGADA")

    # Inicializar extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Inicializar o Flask-Mail através do email_service
    init_mail(app)

    # Registrar blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Outras configurações
    csrf = CSRFProtect(app)
    
    # Criar diretório de uploads se não existir
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Criar tabelas
    with app.app_context():
        db.create_all()

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    return app
