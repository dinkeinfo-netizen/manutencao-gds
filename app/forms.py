from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField, FileField, BooleanField, RadioField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional
from app.models import Localizacao, Equipamento, Mecanico
from wtforms.fields import MultipleFileField


class FinalizarOSForm(FlaskForm):
    descricao_servico = TextAreaField('Descrição do Serviço Realizado', validators=[DataRequired()])
    materiais_utilizados = TextAreaField('Materiais Utilizados')
    mecanico_responsavel = SelectField('Mecânico Responsável', coerce=int, validators=[DataRequired()])
    fotos = MultipleFileField('Fotos')
    
    # Checklist atualizado para SIM/NÃO (usando RadioField ou StringField)
    graxa_oleo = RadioField('Há graxa/óleo escorrendo?', 
                           choices=[('sim', 'SIM'), ('nao', 'NÃO')], 
                           validators=[Optional()])
    limpeza = RadioField('Limpeza realizada?', 
                        choices=[('sim', 'SIM'), ('nao', 'NÃO')], 
                        validators=[Optional()])
    pecas_soltas = RadioField('Peças soltas?', 
                             choices=[('sim', 'SIM'), ('nao', 'NÃO')], 
                             validators=[Optional()])
    equipamento_liberado = RadioField('Equipamento liberado?', 
                                     choices=[('sim', 'SIM'), ('nao', 'NÃO')], 
                                     validators=[Optional()])
    
    nome_mecanico = StringField('Nome do Mecânico', validators=[DataRequired()])
    nome_conferente = StringField('Nome do Conferente', validators=[DataRequired()])
    
    submit = SubmitField('Finalizar')

    def __init__(self, *args, **kwargs):
        super(FinalizarOSForm, self).__init__(*args, **kwargs)
        # Popular mecânicos automaticamente
        try:
            self.mecanico_responsavel.choices = [(0, 'Selecione um mecânico')] + [
                (mec.id, mec.nome) for mec in Mecanico.query.order_by(Mecanico.nome).all()
            ]
        except Exception as e:
            print(f"Erro ao carregar mecânicos: {e}")
            self.mecanico_responsavel.choices = [(0, 'Erro ao carregar mecânicos')]


class OrdemServicoForm(FlaskForm):
    solicitante = StringField('Nome do Solicitante', validators=[DataRequired()])
    localizacao_id = SelectField('Localização/Área', coerce=int, validators=[DataRequired()])
    tipo_manutencao = SelectField('Tipo de Manutenção', choices=[
        ('corretiva', 'Corretiva'),
        ('preventiva', 'Preventiva')
    ], validators=[DataRequired()])
    tipo_parada = SelectField('Tipo de Parada', choices=[
        ('mecanica', 'Mecânica'),
        ('eletrica', 'Elétrica'),
        ('pneumatica', 'Pneumática'),
        ('predial', 'Predial'),
    ], validators=[DataRequired()])
    equipamento_id = SelectField('Equipamento', coerce=int, validators=[DataRequired()])
    motivo = TextAreaField('Motivo da Quebra', validators=[DataRequired()])
    submit = SubmitField('Criar Ordem de Serviço')

    def __init__(self, *args, **kwargs):
        super(OrdemServicoForm, self).__init__(*args, **kwargs)
        
        try:
            # 🔧 CORREÇÃO: Popular localizações automaticamente
            self.localizacao_id.choices = [(0, 'Selecione uma localização')] + [
                (loc.id, f"{loc.codigo} - {loc.nome}") 
                for loc in Localizacao.query.order_by(Localizacao.codigo).all()
            ]
            
            # 🎯 CORREÇÃO PRINCIPAL: Popular TODOS os equipamentos
            equipamentos = Equipamento.query.order_by(Equipamento.codigo).all()
            
            self.equipamento_id.choices = [(0, 'Selecione um equipamento')] + [
                (eq.id, f"{eq.codigo} - {eq.nome}") 
                for eq in equipamentos
            ]
            
            # Debug para verificar quantos equipamentos foram carregados
            print(f"🔍 Debug: {len(equipamentos)} equipamentos carregados no formulário")
            
        except Exception as e:
            print(f"❌ Erro ao carregar dados do formulário: {e}")
            # Fallback em caso de erro
            self.localizacao_id.choices = [(0, 'Erro ao carregar localizações')]
            self.equipamento_id.choices = [(0, 'Erro ao carregar equipamentos')]


class MecanicoForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    telefone = StringField('Telefone')
    submit = SubmitField('Salvar')


class EquipamentoForm(FlaskForm):
    codigo = StringField('Código', validators=[DataRequired()])
    nome = StringField('Nome', validators=[DataRequired()])
    localizacao_id = SelectField('Localização', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Salvar')

    def __init__(self, *args, **kwargs):
        super(EquipamentoForm, self).__init__(*args, **kwargs)
        try:
            self.localizacao_id.choices = [(0, 'Selecione uma localização')] + [
                (loc.id, f"{loc.codigo} - {loc.nome}") 
                for loc in Localizacao.query.order_by(Localizacao.codigo).all()
            ]
        except Exception as e:
            print(f"Erro ao carregar localizações no EquipamentoForm: {e}")
            self.localizacao_id.choices = [(0, 'Erro ao carregar')]


class LocalizacaoForm(FlaskForm):
    codigo = StringField('Código', validators=[DataRequired()])
    nome = StringField('Nome', validators=[DataRequired()])
    submit = SubmitField('Salvar')


# 🎯 CLASSE ADICIONAL: Form para busca/filtro de equipamentos (opcional)
class BuscaEquipamentoForm(FlaskForm):
    """Formulário para busca e filtro de equipamentos"""
    termo_busca = StringField('Buscar Equipamento', 
                             render_kw={"placeholder": "Digite código ou nome..."})
    localizacao_filtro = SelectField('Filtrar por Localização', coerce=int)
    submit = SubmitField('Buscar')
    
    def __init__(self, *args, **kwargs):
        super(BuscaEquipamentoForm, self).__init__(*args, **kwargs)
        try:
            self.localizacao_filtro.choices = [
                (0, 'Todas as localizações'),
                (-1, 'Sem localização')
            ] + [
                (loc.id, f"{loc.codigo} - {loc.nome}") 
                for loc in Localizacao.query.order_by(Localizacao.codigo).all()
            ]
        except Exception as e:
            print(f"Erro ao carregar localizações para filtro: {e}")
            self.localizacao_filtro.choices = [(0, 'Erro ao carregar')]


# 🎯 CLASSE ADICIONAL: Form específico para seleção dinâmica de equipamentos
class EquipamentoDinamicoForm(FlaskForm):
    """Formulário com carregamento dinâmico de equipamentos por localização"""
    localizacao_id = SelectField('Localização', coerce=int, validators=[DataRequired()])
    equipamento_id = SelectField('Equipamento', coerce=int, validators=[DataRequired()])
    
    def __init__(self, localizacao_id=None, *args, **kwargs):
        super(EquipamentoDinamicoForm, self).__init__(*args, **kwargs)
        
        # Carregar localizações
        self.localizacao_id.choices = [(0, 'Selecione uma localização')] + [
            (loc.id, f"{loc.codigo} - {loc.nome}") 
            for loc in Localizacao.query.order_by(Localizacao.codigo).all()
        ]
        
        # Carregar equipamentos baseado na localização selecionada
        if localizacao_id:
            equipamentos = Equipamento.query.filter_by(localizacao_id=localizacao_id).order_by(Equipamento.codigo).all()
        else:
            equipamentos = Equipamento.query.order_by(Equipamento.codigo).all()
            
        self.equipamento_id.choices = [(0, 'Selecione um equipamento')] + [
            (eq.id, f"{eq.codigo} - {eq.nome}") 
            for eq in equipamentos
        ]


class RegistrationForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Tipo de Usuário', choices=[('admin', 'Admin'), ('mecanico', 'Mecânico'), ('usuario', 'Usuário')], validators=[DataRequired()])
    submit = SubmitField('Cadastrar')


class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')


class EditUserForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Tipo de Usuário', choices=[('admin', 'Admin'), ('mecanico', 'Mecânico'), ('usuario', 'Usuário')], validators=[DataRequired()])
    submit = SubmitField('Salvar Alterações')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Nova Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Redefinir Senha')

class CalendarioForm(FlaskForm):
    # Usado para editar um dia específico ou como base para lista
    data = StringField('Data', render_kw={'readonly': True})
    eh_dia_util = BooleanField('Dia Útil')
    descricao = StringField('Descrição')
    submit = SubmitField('Salvar')

class ParametrosMaquinaForm(FlaskForm):
    maquina_id = SelectField('Máquina', coerce=int, validators=[DataRequired()])
    mes = SelectField('Mês', coerce=int, choices=[(i, i) for i in range(1, 13)], validators=[DataRequired()])
    ano = SelectField('Ano', coerce=int, validators=[DataRequired()])
    horas_turno_dia = StringField('Horas/Dia', validators=[DataRequired()])
    esta_ativa = BooleanField('Está Ativa', default=True)
    submit = SubmitField('Salvar')
    
    def __init__(self, *args, **kwargs):
        super(ParametrosMaquinaForm, self).__init__(*args, **kwargs)
        self.maquina_id.choices = [(eq.id, f"{eq.codigo} - {eq.nome}") for eq in Equipamento.query.order_by(Equipamento.codigo).all()]
        self.ano.choices = [(y, y) for y in range(datetime.now().year - 1, datetime.now().year + 2)]
