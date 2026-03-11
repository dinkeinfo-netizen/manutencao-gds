import os
from flask import Flask
from app.extensions import db
from app.models import User
from app.config import Config
from werkzeug.security import generate_password_hash

def reset_admin():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        # Busca o usuário admin
        admin = User.query.filter_by(username='admin').first()
        
        if admin:
            print(f"Usuário admin encontrado: {admin.email}. Resetando senha...")
            admin.set_password('admin123')
            db.session.commit()
            print("Senha do admin resetada com sucesso para: admin123")
        else:
            print("Usuário admin não encontrado. Criando novo...")
            new_admin = User(
                username='admin',
                email='admin@admin.com',
                role='admin'
            )
            new_admin.set_password('admin123')
            db.session.add(new_admin)
            db.session.commit()
            print("Novo usuário admin criado com sucesso!")
            print("Usuário: admin | Senha: admin123")

if __name__ == "__main__":
    reset_admin()
