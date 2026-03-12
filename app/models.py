from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin
from .extensions import db


class Mecanico(db.Model):
    __tablename__ = 'mecanicos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    telefone = db.Column(db.String(20))
    ordens_servico = db.relationship('OrdemServico', backref='mecanico', lazy=True)

class Equipamento(db.Model):
    __tablename__ = 'equipamentos'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    localizacao_id = db.Column(db.Integer, db.ForeignKey('localizacoes.id'))
    localizacao = db.relationship('Localizacao', backref='equipamentos')
    checklist_template_id = db.Column(db.Integer, db.ForeignKey('checklist_templates.id'))

class ChecklistTemplate(db.Model):
    __tablename__ = 'checklist_templates'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255))
    ativo = db.Column(db.Boolean, default=True)
    itens = db.relationship('ChecklistItem', backref='template', lazy=True, cascade="all, delete-orphan")
    equipamentos = db.relationship('Equipamento', backref='checklist_template', lazy=True)

class ChecklistItem(db.Model):
    __tablename__ = 'checklist_itens'
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('checklist_templates.id'), nullable=False)
    pergunta = db.Column(db.String(255), nullable=False)
    ordem = db.Column(db.Integer, default=0)

class ChecklistResposta(db.Model):
    __tablename__ = 'checklist_respostas'
    id = db.Column(db.Integer, primary_key=True)
    ordem_servico_id = db.Column(db.Integer, db.ForeignKey('ordens_servico.id'), nullable=False)
    checklist_item_id = db.Column(db.Integer, db.ForeignKey('checklist_itens.id'), nullable=False)
    valor = db.Column(db.Boolean)  # True = OK, False = Não OK
    observacao = db.Column(db.String(255))
    
    ordem_servico = db.relationship('OrdemServico', backref='checklist_respostas')
    item = db.relationship('ChecklistItem')

class Localizacao(db.Model):
    __tablename__ = 'localizacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)

class OrdemServico(db.Model):
    __tablename__ = 'ordens_servico'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_os = db.Column(db.String(20), unique=True, nullable=False)
    solicitante = db.Column(db.String(100), nullable=False)
    localizacao_id = db.Column(db.Integer, db.ForeignKey('localizacoes.id'), nullable=False)
    localizacao = db.relationship('Localizacao', backref='ordens_servico')
    tipo_manutencao = db.Column(db.String(50), nullable=False)
    tipo_parada = db.Column(db.String(50), nullable=False)
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamentos.id'), nullable=False)
    equipamento = db.relationship('Equipamento', backref='ordens_servico')
    motivo = db.Column(db.Text, nullable=False)
    mecanico_id = db.Column(db.Integer, db.ForeignKey('mecanicos.id'))
    data_inicio = db.Column(db.DateTime, nullable=False, default=datetime.now)
    data_inicio_execucao = db.Column(db.DateTime)  # Data quando o mecânico clicou em "Iniciar"
    data_termino = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Aberta')
    sap = db.Column(db.String(50))
    tempo_manutencao = db.Column(db.Float)
    descricao_servico = db.Column(db.Text)
    materiais_utilizados = db.Column(db.Text)
    fotos_paths = db.Column(db.JSON)  
    graxa_oleo = db.Column(db.Boolean)
    limpeza = db.Column(db.Boolean)
    pecas_soltas = db.Column(db.Boolean)
    equipamento_liberado = db.Column(db.Boolean)
    nome_mecanico = db.Column(db.String(100))
    nome_conferente = db.Column(db.String(100))
    assinatura_mecanico = db.Column(db.Text)  # Caminho da imagem/base64
    data_assinatura_mecanico = db.Column(db.DateTime)
    assinatura_conferente = db.Column(db.Text)
    data_assinatura_conferente = db.Column(db.DateTime)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'mecanico', 'usuario'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)
