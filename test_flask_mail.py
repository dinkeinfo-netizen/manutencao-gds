from app import create_app
from flask_mail import Message
from app.email_service import mail
import logging

def test_flask_mail():
    app = create_app()
    app.config['MAIL_DEBUG'] = True
    
    with app.app_context():
        print("--- Testando com Flask-Mail (Modo Debug Ativo) ---")
        msg = Message(
            subject="Teste de Autenticação Flask-Mail",
            sender=app.config.get('MAIL_DEFAULT_SENDER') or app.config.get('MAIL_USERNAME'),
            recipients=[app.config.get('MAIL_USERNAME')],
            body="Este é um teste para verificar a autenticação via Flask-Mail."
        )
        
        try:
            print(f"Config: SERVER={app.config['MAIL_SERVER']}, PORT={app.config['MAIL_PORT']}, USER={app.config['MAIL_USERNAME']}")
            print(f"Enviando para {msg.recipients}...")
            mail.send(msg)
            print("✅ SUCESSO via Flask-Mail!")
        except Exception as e:
            print(f"❌ FALHA via Flask-Mail: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_flask_mail()
