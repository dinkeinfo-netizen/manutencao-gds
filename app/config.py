import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-secreta-aleatoria-gds-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://manutencao_user:manutencao_pass@db:5432/manutencao_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'app/static/uploads'

    # Configurações de Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.office365.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'dalmo.junior@gdsusa.com.br')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'bwgvmgzkbvqvrfqb')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or MAIL_USERNAME
    
    # Email da equipe de manutenção
    MANUTENCAO_EMAIL = os.environ.get('MANUTENCAO_EMAIL', 'dalmo.junior@gdsusa.com.br')
    
    # Emails em cópia (opcional)
    MANUTENCAO_CC_EMAILS = os.environ.get('MANUTENCAO_CC_EMAILS', '').split(',') if os.environ.get('MANUTENCAO_CC_EMAILS') else []
    
    # Configurações adicionais de debug
    MAIL_DEBUG = True
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', 'False').lower() in ['true', 'on', '1']
