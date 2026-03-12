from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file
from app.forms import OrdemServicoForm, MecanicoForm, EquipamentoForm, LocalizacaoForm, FinalizarOSForm, EditUserForm, ResetPasswordForm, CalendarioForm, ParametrosMaquinaForm
from app.extensions import db
from app.models import Mecanico, Equipamento, Localizacao, OrdemServico, User, ChecklistTemplate, ChecklistItem, ChecklistResposta, CalendarioOperacional, ParametroMaquinaMensal
from app.kpi_utils import get_dias_uteis, get_tempo_nominal_disponivel, populate_calendar_if_empty
from app.email_service import enviar_email_nova_os, enviar_email_os_finalizada
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os
from werkzeug.utils import secure_filename
from sqlalchemy import func
import traceback
import binascii
from app.utils import role_required, converter_para_boolean
from flask_login import current_user, login_required
from app.pdf_utils import generate_os_pdf

main_bp = Blueprint('main', __name__)

# Configurações de upload (mantidas aqui, mas acessadas via current_app no blueprint)
UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


## assinatura
def salvar_assinatura_digital(assinatura_base64, tipo, os_id):
    """
    Salva a assinatura digital como arquivo e retorna o nome do arquivo
    """
    try:
        if not assinatura_base64 or not assinatura_base64.startswith('data:image/png;base64,'):
            return None
            
        # Remove o prefixo data:image/png;base64,
        image_data = assinatura_base64.split(',')[1]
        
        # Decodifica base64
        binary_data = base64.b64decode(image_data)
        
        # Gera nome único para o arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        filename = f"assinatura_{tipo}_{os_id}_{timestamp}.png"
        
        # Cria diretório se não existir
        signatures_dir = os.path.join(current_app.root_path, 'static', 'signatures')
        if not os.path.exists(signatures_dir):
            os.makedirs(signatures_dir)
        # Salva o arquivo
        filepath = os.path.join(signatures_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(binary_data)
            
        return filename
        
    except (ValueError, binascii.Error) as e:
        current_app.logger.error(f"Erro ao processar assinatura {tipo}: {str(e)}")
        return None
## assinatura




# ========================================
# Funções Auxiliares
# ========================================

def gerar_numero_os():
    """
    Gera um número de OS sequencial baseado na data de hoje.
    Usa um lock simples ou tentativa de inserção se necessário, 
    mas aqui buscamos o último registro de forma robusta.
    """
    hoje = datetime.now().strftime('%y%m%d')
    # Buscar a maior OS do dia atual
    ultima_os = (
        db.session.query(OrdemServico.numero_os)
        .filter(OrdemServico.numero_os.like(f"{hoje}%"))
        .order_by(OrdemServico.numero_os.desc())
        .with_for_update() # Bloqueia a linha para evitar duplicidade em transações simultâneas
        .first()
    )
    if ultima_os:
        try:
            sequencia = int(ultima_os.numero_os[6:]) + 1
        except (ValueError, IndexError):
            sequencia = 1
    else:
        sequencia = 1
    return f"{hoje}{sequencia:04d}"

def calcular_tempo_manutencao(inicio, termino):
    if inicio and termino:
        delta = termino - inicio
        return round(delta.total_seconds() / 3600, 2)
    return 0

# ========================================
# Rotas Principais
# ========================================

@main_bp.route('/')
@login_required
def index():
    return render_template('index.html')

@main_bp.route('/manual')
@login_required
def manual():
    return render_template('manual.html')

## lancar os

# Trecho corrigido da função lancar_os em main.py

@main_bp.route('/lancar-os', methods=['GET', 'POST'])
@role_required('admin', 'mecanico', 'usuario')
def lancar_os():
    form = OrdemServicoForm()
    
    # Preencher selects
    form.localizacao_id.choices = [(loc.id, f"{loc.codigo} - {loc.nome}") for loc in Localizacao.query.order_by(Localizacao.nome).all()]
    form.equipamento_id.choices = [(eq.id, f"{eq.codigo} - {eq.nome}") for eq in Equipamento.query.order_by(Equipamento.nome).all()]
    
    if form.validate_on_submit():
        try:
            nova_os = OrdemServico(
                numero_os=gerar_numero_os(),
                solicitante=form.solicitante.data,
                localizacao_id=form.localizacao_id.data,
                tipo_manutencao=form.tipo_manutencao.data,
                tipo_parada=form.tipo_parada.data,
                equipamento_id=form.equipamento_id.data,
                motivo=form.motivo.data,
                mecanico_id=None,
                status='Aberta',
                data_inicio=datetime.now()
            )
            
            db.session.add(nova_os)
            db.session.commit()



            
            # Preparar dados para o email
            localizacao = Localizacao.query.get(form.localizacao_id.data)
            equipamento = Equipamento.query.get(form.equipamento_id.data)
            
            email_data = {
                'numero_os': nova_os.numero_os,
                'solicitante': nova_os.solicitante or 'N/A',
                'localizacao': f"{localizacao.codigo} - {localizacao.nome}" if localizacao else "N/A",
                'equipamento': f"{equipamento.codigo} - {equipamento.nome}" if equipamento else "N/A",
                'tipo_manutencao': nova_os.tipo_manutencao or 'N/A',
                'tipo_parada': nova_os.tipo_parada or 'N/A',
                'motivo': nova_os.motivo or 'N/A',
                'data_inicio': nova_os.data_inicio.strftime('%d/%m/%Y às %H:%M'),
                'data_envio': datetime.now().strftime('%d/%m/%Y às %H:%M')
            }
            
            # Log dos dados do email antes do envio
            current_app.logger.info(f"Dados para email: {email_data}")
            
            # Enviar email
            try:
                email_enviado = enviar_email_nova_os(email_data)
                if email_enviado:
                    flash('Ordem de Serviço criada com sucesso! Email enviado para a equipe de manutenção.', 'success')
                else:
                    flash('Ordem de Serviço criada com sucesso! Porém houve um problema no envio do email.', 'warning')
                
                # Independente do email, se for usuário comum, redireciona para a página de sucesso
                if current_user.role == 'usuario':
                    return render_template('email_enviado.html')
                else:
                    return redirect(url_for('main.manutencoes_andamento'))

            except Exception as email_error:
                current_app.logger.error(f"Erro ao enviar email: {str(email_error)}")
                import traceback
                current_app.logger.error(f"Traceback do erro de email: {traceback.format_exc()}")
                flash('Ordem de Serviço criada com sucesso! Porém não foi possível enviar o email.', 'warning')
                
                # Mesmo com erro fatal no código de email, redireciona corretamente por papel
                if current_user.role == 'usuario':
                    return render_template('email_enviado.html')
                else:
                    return redirect(url_for('main.manutencoes_andamento'))

            return redirect(url_for('main.manutencoes_andamento'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao criar OS: {str(e)}")
            flash(f'Erro ao criar OS: {str(e)}', 'danger')
    
    return render_template('lancar_os.html', form=form)

# Adicionar rota para testar email
@main_bp.route('/teste-email')
def teste_email():
    """Rota para testar configuração de email"""
    from app.email_service import testar_configuracao_email, enviar_email_teste
    
    # Primeiro testa a configuração
    config_ok, config_msg = testar_configuracao_email()
    
    if config_ok:
        # Se a configuração está OK, tenta enviar um email de teste
        email_ok, email_msg = enviar_email_teste()
        if email_ok:
            flash(f'✅ Email de teste enviado com sucesso! {email_msg}', 'success')
        else:
            flash(f'❌ Erro no envio do email: {email_msg}', 'danger')
    else:
        flash(f'❌ Erro na configuração: {config_msg}', 'danger')
    
    return redirect(url_for('main.index'))

#### lancar os

@main_bp.route('/manutencoes-andamento')
@role_required('admin', 'mecanico')
def manutencoes_andamento():
    status_filtro = ['Aberta', 'Em andamento']
    ordens = OrdemServico.query.filter(OrdemServico.status.in_(status_filtro)).order_by(OrdemServico.data_inicio.desc()).all()
    
    for os in ordens:
        # Se a OS está em andamento, usa data_inicio_execucao para calcular tempo
        # Se ainda está aberta, usa data_inicio (tempo de espera)
        if os.status == 'Em andamento' and os.data_inicio_execucao:
            os.tempo_decorrido = calcular_tempo_manutencao(os.data_inicio_execucao, datetime.now())
        else:
            os.tempo_decorrido = calcular_tempo_manutencao(os.data_inicio, datetime.now())
    
    mecanicos = Mecanico.query.order_by(Mecanico.nome).all()
    return render_template('manutencoes_andamento.html', ordens=ordens, mecanicos=mecanicos)

@main_bp.route('/manutencoes-concluidas')
@role_required('admin', 'mecanico')
def manutencoes_concluidas():
    ordens = OrdemServico.query.filter_by(status='Concluída').order_by(OrdemServico.data_termino.desc()).all()
    return render_template('manutencoes_concluidas.html', ordens=ordens)

####### Iniciar OS inicio #######

@main_bp.route('/iniciar-os/<int:os_id>', methods=['POST'])
def iniciar_os(os_id):
    """
    Inicia uma OS mudando seu status de 'Aberta' para 'Em andamento'
    e registra a data/hora de início da execução
    """
    ordem_servico = OrdemServico.query.get_or_404(os_id)
    
    # Verifica se a OS está no status correto para ser iniciada
    if ordem_servico.status != 'Aberta':
        flash(f'A OS {ordem_servico.numero_os} não pode ser iniciada. Status atual: {ordem_servico.status}', 'warning')
        return redirect(url_for('main.manutencoes_andamento'))
    
    mecanico_id = request.form.get('mecanico_id')
    if not mecanico_id:
        flash('Por favor, selecione um mecânico.', 'danger')
        return redirect(url_for('main.manutencoes_andamento'))
        
    try:
        mecanico = Mecanico.query.get(mecanico_id)
        if not mecanico:
            flash('Mecânico não encontrado.', 'danger')
            return redirect(url_for('main.manutencoes_andamento'))

        # Atualiza o status e registra a data/hora de início da execução
        ordem_servico.status = 'Em andamento'
        ordem_servico.data_inicio_execucao = datetime.now()
        ordem_servico.mecanico_id = mecanico.id
        ordem_servico.nome_mecanico = mecanico.nome
        
        db.session.commit()
        
        flash(f'OS {ordem_servico.numero_os} iniciada por {mecanico.nome} com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao iniciar OS {os_id}: {str(e)}")
        flash(f'Erro ao iniciar OS: {str(e)}', 'danger')
        
    return redirect(url_for('main.manutencoes_andamento'))

# ========================================
# Finalizar OS
# ========================================

@main_bp.route('/finalizar-os/<int:os_id>', methods=['GET', 'POST'])
def finalizar_os(os_id):
    ordem_servico = OrdemServico.query.get_or_404(os_id)
    
    # Verifica se a OS está no status correto para ser finalizada
    if ordem_servico.status not in ['Em andamento']:
        flash(f'A OS {ordem_servico.numero_os} não pode ser finalizada. Status atual: {ordem_servico.status}', 'warning')
        return redirect(url_for('main.manutencoes_andamento'))
    
    form = FinalizarOSForm()
    
    # Preencher seleção de mecânicos
    form.mecanico_responsavel.choices = [(m.id, m.nome) for m in Mecanico.query.order_by(Mecanico.nome).all()]
    
    if form.validate_on_submit():
        try:
            # Processar upload de fotos
            fotos_paths = []
            
            if form.fotos.data:
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                for foto in form.fotos.data:
                    if foto and foto.filename and allowed_file(foto.filename):
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                        filename = f"{timestamp}_{secure_filename(foto.filename)}"
                        filepath = os.path.join(upload_dir, filename)
                        foto.save(filepath)
                        fotos_paths.append(filename)
            
            # Processar assinaturas digitais
            assinatura_mecanico_data = request.form.get('mechanic_signature')
            assinatura_conferente_data = request.form.get('inspector_signature')
            
            assinatura_mecanico_filename = None
            assinatura_conferente_filename = None
            
            if assinatura_mecanico_data:
                assinatura_mecanico_filename = salvar_assinatura_digital(
                    assinatura_mecanico_data, 'mecanico', os_id
                )
                
            if assinatura_conferente_data:
                assinatura_conferente_filename = salvar_assinatura_digital(
                    assinatura_conferente_data, 'conferente', os_id
                )
            
            # Atualizar dados da OS
            ordem_servico.fotos_paths = fotos_paths
            ordem_servico.descricao_servico = form.descricao_servico.data
            ordem_servico.materiais_utilizados = form.materiais_utilizados.data
            ordem_servico.mecanico_id = form.mecanico_responsavel.data 
            
            # 🔧 CONVERSÃO CORRETA PARA BOOLEAN - ESTA É A PARTE CRÍTICA!
            ordem_servico.graxa_oleo = converter_para_boolean(form.graxa_oleo.data)
            ordem_servico.limpeza = converter_para_boolean(form.limpeza.data)
            ordem_servico.pecas_soltas = converter_para_boolean(form.pecas_soltas.data)
            ordem_servico.equipamento_liberado = converter_para_boolean(form.equipamento_liberado.data)
            
            ordem_servico.nome_mecanico = form.nome_mecanico.data
            ordem_servico.nome_conferente = form.nome_conferente.data
            
            # Salvar dados das assinaturas
            if assinatura_mecanico_data:
                ordem_servico.assinatura_mecanico = assinatura_mecanico_data
                ordem_servico.data_assinatura_mecanico = datetime.now()
                
            if assinatura_conferente_data:
                ordem_servico.assinatura_conferente = assinatura_conferente_data
                ordem_servico.data_assinatura_conferente = datetime.now()
            
            ordem_servico.status = 'Concluída'
            ordem_servico.data_termino = datetime.now()
            
            # Calcula o tempo de manutenção usando data_inicio_execucao se disponível
            data_inicio_calculo = ordem_servico.data_inicio_execucao or ordem_servico.data_inicio
            ordem_servico.tempo_manutencao = calcular_tempo_manutencao(
                data_inicio_calculo, ordem_servico.data_termino
            )

            # 🔧 LOG DE DEBUG ANTES DE SALVAR
            current_app.logger.info(f"💾 Finalizando OS {os_id}:")
            current_app.logger.info(f"  - graxa_oleo: {ordem_servico.graxa_oleo} (tipo: {type(ordem_servico.graxa_oleo)})")
            current_app.logger.info(f"  - limpeza: {ordem_servico.limpeza} (tipo: {type(ordem_servico.limpeza)})")
            current_app.logger.info(f"  - pecas_soltas: {ordem_servico.pecas_soltas} (tipo: {type(ordem_servico.pecas_soltas)})")
            current_app.logger.info(f"  - equipamento_liberado: {ordem_servico.equipamento_liberado} (tipo: {type(ordem_servico.equipamento_liberado)})")

            # Processar checklist dinâmico
            for key, value in request.form.items():
                if key.startswith('checklist_item_'):
                    try:
                        item_id = int(key.replace('checklist_item_', ''))
                        valor_bool = (value == 'sim')
                        resposta = ChecklistResposta(
                            ordem_servico_id=os_id,
                            checklist_item_id=item_id,
                            valor=valor_bool
                        )
                        db.session.add(resposta)
                    except (ValueError, TypeError):
                        continue

            db.session.commit()
            
            # Enviar email de finalização (opcional)
            try:
                mecanico = Mecanico.query.get(ordem_servico.mecanico_id) if ordem_servico.mecanico_id else None
                equipamento = ordem_servico.equipamento
                
                email_data_finalizacao = {
                    'numero_os': ordem_servico.numero_os,
                    'equipamento': f"{equipamento.codigo} - {equipamento.nome}" if equipamento else "N/A",
                    'mecanico': mecanico.nome if mecanico else ordem_servico.nome_mecanico or "N/A",
                    'tempo_manutencao': ordem_servico.tempo_manutencao,
                    'data_termino': ordem_servico.data_termino.strftime('%d/%m/%Y às %H:%M')
                }
                
                # Descomentar a linha abaixo se quiser enviar email na finalização também
                # enviar_email_os_finalizada(email_data_finalizacao)
                
            except Exception as email_error:
                current_app.logger.error(f"Erro ao enviar email de finalização: {str(email_error)}")
            
            flash('OS finalizada com sucesso com assinaturas digitais!', 'success')
            return redirect(url_for('main.manutencoes_concluidas'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"❌ Erro ao finalizar OS {os_id}: {str(e)}")
            import traceback
            traceback.print_exc() 
            flash(f'Erro ao finalizar OS: {str(e)}', 'danger')
    
    # Preencher dados iniciais
    if ordem_servico.mecanico:
        form.nome_mecanico.data = ordem_servico.mecanico.nome 
    
    return render_template('finalizar_os.html', form=form, os=ordem_servico)

#### finaliza os Fim ######


@main_bp.route('/dashboard')
@role_required('admin', 'mecanico')
def dashboard():
    # Garantir que o calendário está populado para o período
    hoje = datetime.now()
    inicio_periodo = hoje - timedelta(days=30)
    
    # Popula o mês atual e o anterior para garantir cobertura dos 30 dias
    populate_calendar_if_empty(hoje.month, hoje.year)
    mes_anterior = (hoje.replace(day=1) - timedelta(days=1))
    populate_calendar_if_empty(mes_anterior.month, mes_anterior.year)

    # Estatísticas básicas
    total_os = OrdemServico.query.count()
    os_abertas = OrdemServico.query.filter_by(status='Aberta').count()
    os_andamento = OrdemServico.query.filter_by(status='Em andamento').count()
    os_concluidas = OrdemServico.query.filter_by(status='Concluída').count()
    
    # Tempo Nominal Disponível da Frota no Período
    from app.kpi_utils import get_tempo_total_nominal_frota
    horas_totais_periodo = get_tempo_total_nominal_frota(inicio_periodo, hoje)

    # MTTR Geral (Apenas Corretivas Concluídas no período)
    mttr_geral = db.session.query(
        func.avg(OrdemServico.tempo_manutencao)
    ).filter(
        OrdemServico.status == 'Concluída',
        OrdemServico.tipo_manutencao == 'corretiva',
        OrdemServico.data_termino >= inicio_periodo,
        OrdemServico.tempo_manutencao.isnot(None)
    ).scalar() or 0

    # Downtime Total (Soma de tempo_manutencao de corretivas no período)
    downtime_total = db.session.query(
        func.sum(OrdemServico.tempo_manutencao)
    ).filter(
        OrdemServico.status == 'Concluída',
        OrdemServico.tipo_manutencao == 'corretiva',
        OrdemServico.data_termino >= inicio_periodo
    ).scalar() or 0

    # Número de Falhas (Corretivas no período)
    num_falhas = OrdemServico.query.filter(
        OrdemServico.status == 'Concluída',
        OrdemServico.tipo_manutencao == 'corretiva',
        OrdemServico.data_termino >= inicio_periodo
    ).count()

    # MTBF (Mean Time Between Failures)
    # Lógica: (Tempo Nominal Total - Tempo de Parada Corretiva) / Número de Falhas
    mtbf_geral = 0
    if num_falhas > 0:
        mtbf_geral = (horas_totais_periodo - downtime_total) / num_falhas

    # Disponibilidade (%)
    # Lógica: (Tempo Nominal Total - Tempo de Parada) / Tempo Nominal Total * 100
    disponibilidade_geral = 0
    if horas_totais_periodo > 0:
        disponibilidade_geral = ((horas_totais_periodo - downtime_total) / horas_totais_periodo) * 100

    # Pareto: Top 5 equipamentos que geram mais corretivas
    pareto_equipamentos = db.session.query(
        Equipamento.nome,
        func.count(OrdemServico.id).label('total_os'),
        func.sum(OrdemServico.tempo_manutencao).label('total_downtime')
    ).join(OrdemServico).filter(
        OrdemServico.tipo_manutencao == 'corretiva',
        OrdemServico.data_inicio >= inicio_periodo
    ).group_by(Equipamento.id).order_by(func.count(OrdemServico.id).desc()).limit(5).all()

    # MTTR por Mecânico (Concluídas)
    mttr_por_mecanico = db.session.query(
        Mecanico.nome,
        func.avg(OrdemServico.tempo_manutencao).label('mttr'),
        func.count(OrdemServico.id).label('total_os')
    ).join(OrdemServico).filter(
        OrdemServico.status == 'Concluída',
        OrdemServico.tempo_manutencao.isnot(None)
    ).group_by(Mecanico.id).order_by(func.avg(OrdemServico.tempo_manutencao).asc()).all()

    return render_template('dashboard.html',
                         total_os=total_os,
                         os_abertas=os_abertas,
                         os_andamento=os_andamento,
                         os_concluidas=os_concluidas,
                         mttr_geral=round(float(mttr_geral), 2),
                         mtbf_geral=round(float(mtbf_geral), 2),
                         disponibilidade_geral=round(float(disponibilidade_geral), 2),
                         pareto_equipamentos=pareto_equipamentos,
                         mttr_por_mecanico=mttr_por_mecanico)

@main_bp.route('/api/dashboard/data')
@role_required('admin', 'mecanico')
def api_dashboard_data():
    """Retorna todos os dados de indicadores para os gráficos Chart.js"""
    try:
        from app.kpi_utils import get_tempo_total_nominal_frota
        hoje = datetime.now()
        inicio_periodo = hoy_menos_30 = hoje - timedelta(days=30)
        
        # Garante calendário
        populate_calendar_if_empty(hoje.month, hoje.year)
        mes_anterior = (hoje.replace(day=1) - timedelta(days=1))
        populate_calendar_if_empty(mes_anterior.month, mes_anterior.year)

        horas_totais_periodo = get_tempo_total_nominal_frota(inicio_periodo, hoje)

        # MTTR (Corretivas Concluídas)
        mttr_data = db.session.query(
            Equipamento.codigo,
            func.avg(OrdemServico.tempo_manutencao).label('mttr')
        ).join(OrdemServico).filter(
            OrdemServico.status == 'Concluída',
            OrdemServico.tipo_manutencao == 'corretiva',
            OrdemServico.data_termino >= inicio_periodo,
            OrdemServico.tempo_manutencao.isnot(None)
        ).group_by(Equipamento.id).order_by(func.avg(OrdemServico.tempo_manutencao).desc()).limit(10).all()

        # Tendência MTTR
        mttr_tendencia = db.session.query(
            func.date(OrdemServico.data_termino).label('data'),
            func.avg(OrdemServico.tempo_manutencao).label('mttr')
        ).filter(
            OrdemServico.status == 'Concluída',
            OrdemServico.tipo_manutencao == 'corretiva',
            OrdemServico.data_termino >= inicio_periodo
        ).group_by(func.date(OrdemServico.data_termino)).order_by('data').all()

        # Downtime por Equipamento (Pareto)
        pareto_data = db.session.query(
            Equipamento.codigo,
            func.sum(OrdemServico.tempo_manutencao).label('downtime')
        ).join(OrdemServico).filter(
            OrdemServico.tipo_manutencao == 'corretiva',
            OrdemServico.data_inicio >= inicio_periodo
        ).group_by(Equipamento.id).order_by(func.sum(OrdemServico.tempo_manutencao).desc()).limit(5).all()

        # Performance Mecânicos
        mttr_mecanicos = db.session.query(
            Mecanico.nome,
            func.avg(OrdemServico.tempo_manutencao).label('mttr')
        ).join(OrdemServico).filter(
            OrdemServico.status == 'Concluída',
            OrdemServico.tempo_manutencao.isnot(None),
            OrdemServico.data_termino >= inicio_periodo
        ).group_by(Mecanico.id).order_by(func.avg(OrdemServico.tempo_manutencao).asc()).all()

        # KPIs Gerais
        downtime_total = db.session.query(func.sum(OrdemServico.tempo_manutencao)).filter(
            OrdemServico.status == 'Concluída',
            OrdemServico.tipo_manutencao == 'corretiva',
            OrdemServico.data_termino >= inicio_periodo
        ).scalar() or 0
        
        num_falhas = OrdemServico.query.filter(
            OrdemServico.status == 'Concluída',
            OrdemServico.tipo_manutencao == 'corretiva',
            OrdemServico.data_termino >= inicio_periodo
        ).count()

        mttr_geral = downtime_total / num_falhas if num_falhas > 0 else 0
        mtbf_geral = (horas_totais_periodo - downtime_total) / num_falhas if num_falhas > 0 else 0
        disponibilidade = ((horas_totais_periodo - downtime_total) / horas_totais_periodo * 100) if horas_totais_periodo > 0 else 0

        return jsonify({
            'kpis': {
                'mttr': round(float(mttr_geral or 0), 2),
                'mtbf': round(float(mtbf_geral or 0), 2),
                'disponibilidade': round(float(disponibilidade or 0), 2)
            },
            'pareto': {
                'labels': [item.codigo for item in pareto_data],
                'values': [round(float(item.downtime or 0), 2) for item in pareto_data]
            },
            'mttr_equipamentos': {
                'labels': [item.codigo for item in mttr_data],
                'values': [round(float(item.mttr or 0), 2) for item in mttr_data]
            },
            'tendencia': {
                'labels': [item.data.strftime('%d/%m') for item in mttr_tendencia] if mttr_tendencia else [],
                'values': [round(float(item.mttr or 0), 2) for item in mttr_tendencia] if mttr_tendencia else []
            },
            'mecanicos': {
                'labels': [item.nome for item in mttr_mecanicos],
                'values': [round(float(item.mttr or 0), 2) for item in mttr_mecanicos]
            }
        })
    except Exception as e:
        current_app.logger.error(f"Erro na API de dashboard: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ========================================
# Exportação Excel
# ========================================

@main_bp.route('/exportar-excel')
@role_required('admin', 'mecanico')
def exportar_excel():
    """Exporta todas as ordens de serviço concluídas para Excel"""
    try:
        ordens = OrdemServico.query.filter_by(status='Concluída').order_by(OrdemServico.data_termino.desc()).all()
        
        data = []
        for os in ordens:
            data.append({
                'Número OS': os.numero_os,
                'Solicitante': os.solicitante,
                'Localização': os.localizacao.nome if os.localizacao else 'N/A',
                'Equipamento': os.equipamento.nome if os.equipamento else 'N/A',
                'Tipo Manutenção': os.tipo_manutencao,
                'Tipo Parada': os.tipo_parada,
                'Mecânico': os.nome_mecanico or (os.mecanico.nome if os.mecanico else 'N/A'),
                'Data Início': os.data_inicio.strftime('%d/%m/%Y %H:%M') if os.data_inicio else '',
                'Data Término': os.data_termino.strftime('%d/%m/%Y %H:%M') if os.data_termino else '',
                'Tempo (h)': os.tempo_manutencao,
                'Motivo': os.motivo,
                'Serviço Realizado': os.descricao_servico,
                'Materiais': os.materiais_utilizados,
                'SAP': os.sap or ''
            })
            
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Ordens Concluídas')
            
        output.seek(0)
        
        filename = f"relatorio_os_concluidas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        current_app.logger.error(f"Erro ao exportar Excel: {str(e)}")
        flash(f"Erro ao exportar Excel: {str(e)}", 'danger')
        return redirect(url_for('main.manutencoes_concluidas'))

@main_bp.route('/exportar-kpis-mecanico')
@role_required('admin')
def exportar_kpis_mecanico():
    """Exporta indicadores de MTTR por mecânico para Excel"""
    try:
        mttr_por_mecanico = db.session.query(
            Mecanico.nome,
            func.avg(OrdemServico.tempo_manutencao).label('mttr'),
            func.count(OrdemServico.id).label('total_os')
        ).join(OrdemServico).filter(
            OrdemServico.status == 'Concluída',
            OrdemServico.tempo_manutencao.isnot(None),
            OrdemServico.tempo_manutencao > 0
        ).group_by(Mecanico.id).all()
        
        data = []
        for item in mttr_por_mecanico:
            data.append({
                'Mecânico': item.nome,
                'MTTR (h)': round(float(item.mttr), 2),
                'Total OSs Concluídas': item.total_os
            })
            
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='MTTR por Mecânico')
            
        output.seek(0)
        
        filename = f"kpi_mecanicos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        current_app.logger.error(f"Erro ao exportar KPIs: {str(e)}")
        flash(f"Erro ao exportar KPIs: {str(e)}", 'danger')
        return redirect(url_for('main.dashboard'))

#### dashboard fim 

##@main_bp.route('/api/equipamentos/<int:localizacao_id>')
##def api_equipamentos(localizacao_id):
##    equipamentos = Equipamento.query.filter_by(localizacao_id=localizacao_id).all()
##    return jsonify([{'id': eq.id, 'nome': f"{eq.codigo} - {eq.nome}"} for eq in equipamentos])




# ========================================
# APIs e Endpoints
# ========================================

@main_bp.route('/api/equipamentos/<int:localizacao_id>')
def api_equipamentos(localizacao_id):
    """
    API que retorna todos os equipamentos disponíveis para seleção.
    Com tabelas separadas, qualquer equipamento pode ser usado em qualquer localização.
    
    Args:
        localizacao_id: ID da localização (usado apenas para contexto da OS)
    
    Returns:
        JSON com lista de todos os equipamentos formatados para dropdown
    """
    try:
        # Buscar todos os equipamentos do banco (sem filtro de localização)
        equipamentos = Equipamento.query.order_by(Equipamento.codigo).all()
        
        # Verificar se encontrou equipamentos
        if not equipamentos:
            current_app.logger.warning("⚠️ Nenhum equipamento encontrado no banco")
            return jsonify([])
        
        # Formatar dados para o dropdown JavaScript
        resultado = []
        for equipamento in equipamentos:
            resultado.append({
                'id': equipamento.id,
                'codigo': equipamento.codigo,
                'nome': equipamento.nome,
                'texto': f"{equipamento.codigo} - {equipamento.nome}"
            })
        
        # Log para debug
        current_app.logger.info(f"✅ API equipamentos: Retornando {len(resultado)} equipamentos para localização {localizacao_id}")
        
        return jsonify(resultado)
        
    except Exception as e:
        # Log do erro completo
        current_app.logger.error(f"❌ Erro na API equipamentos: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Resposta de erro em JSON
        return jsonify({
            'error': 'Erro interno do servidor',
            'message': 'Falha ao carregar lista de equipamentos',
            'details': str(e)
        }), 500


@main_bp.route('/api/equipamentos/buscar')
def api_buscar_equipamentos():
    """
    API para busca de equipamentos por termo (código ou nome).
    Útil para implementar busca em tempo real no frontend.
    """
    try:
        # Obter termo de busca da query string
        termo = request.args.get('termo', '').strip()
        
        if termo:
            # Buscar equipamentos que contenham o termo no código OU no nome
            equipamentos = Equipamento.query.filter(
                db.or_(
                    Equipamento.codigo.ilike(f'%{termo}%'),
                    Equipamento.nome.ilike(f'%{termo}%')
                )
            ).order_by(Equipamento.codigo).all()
            
            current_app.logger.info(f"🔍 Busca por '{termo}': {len(equipamentos)} equipamentos encontrados")
        else:
            # Se não há termo, retornar todos os equipamentos
            equipamentos = Equipamento.query.order_by(Equipamento.codigo).all()
            current_app.logger.info(f"📋 Busca sem filtro: {len(equipamentos)} equipamentos totais")
        
        # Formatar resultado
        resultado = []
        for eq in equipamentos:
            resultado.append({
                'id': eq.id,
                'codigo': eq.codigo,
                'nome': eq.nome,
                'texto': f"{eq.codigo} - {eq.nome}"
            })
        
        return jsonify(resultado)
        
    except Exception as e:
        current_app.logger.error(f"❌ Erro na busca de equipamentos: {str(e)}")
        return jsonify({
            'error': 'Erro na busca',
            'message': str(e)
        }), 500


@main_bp.route('/api/equipamentos/detalhes/<int:equipamento_id>')
def api_detalhes_equipamento(equipamento_id):
    """
    API para obter detalhes de um equipamento específico.
    """
    try:
        equipamento = Equipamento.query.get(equipamento_id)
        
        if not equipamento:
            return jsonify({
                'error': 'Equipamento não encontrado',
                'equipamento_id': equipamento_id
            }), 404
        
        # Buscar quantas OS existem para este equipamento
        total_os = OrdemServico.query.filter_by(equipamento_id=equipamento_id).count()
        os_abertas = OrdemServico.query.filter_by(
            equipamento_id=equipamento_id, 
            status='Aberta'
        ).count()
        
        return jsonify({
            'id': equipamento.id,
            'codigo': equipamento.codigo,
            'nome': equipamento.nome,
            'texto': f"{equipamento.codigo} - {equipamento.nome}",
            'estatisticas': {
                'total_os': total_os,
                'os_abertas': os_abertas,
                'os_finalizadas': total_os - os_abertas
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao buscar detalhes do equipamento {equipamento_id}: {str(e)}")
        return jsonify({
            'error': 'Erro interno',
            'message': str(e)
        }), 500


@main_bp.route('/api/localizacoes')
def api_localizacoes():
    """
    API que retorna todas as localizações disponíveis.
    """
    try:
        localizacoes = Localizacao.query.order_by(Localizacao.codigo).all()
        
        resultado = []
        for loc in localizacoes:
            resultado.append({
                'id': loc.id,
                'codigo': loc.codigo,
                'nome': loc.nome,
                'texto': f"{loc.codigo} - {loc.nome}"
            })
        
        current_app.logger.info(f"📍 API localizações: {len(resultado)} localizações disponíveis")
        return jsonify(resultado)
        
    except Exception as e:
        current_app.logger.error(f"❌ Erro na API localizações: {str(e)}")
        return jsonify({
            'error': 'Erro ao carregar localizações',
            'message': str(e)
        }), 500
### acerto fim







# Mecânicos
@main_bp.route('/config/mecanicos', methods=['GET', 'POST'])
@role_required('admin')
def config_mecanicos():
    form = MecanicoForm()
    mecanicos = Mecanico.query.all()
    
    if form.validate_on_submit():
        mecanico = Mecanico(
            nome=form.nome.data,
            email=form.email.data,
            telefone=form.telefone.data
        )
        db.session.add(mecanico)
        db.session.commit()
        flash('Mecânico cadastrado com sucesso!', 'success')
        return redirect(url_for('main.config_mecanicos'))
    
    return render_template('config/mecanicos.html', 
                         form=form, 
                         mecanicos=mecanicos)

@main_bp.route('/config/mecanicos/editar/<int:id>', methods=['GET', 'POST'])
@role_required('admin')
def editar_mecanico(id):
    mecanico = Mecanico.query.get_or_404(id)
    form = MecanicoForm(obj=mecanico)
    
    if form.validate_on_submit():
        form.populate_obj(mecanico)
        db.session.commit()
        flash('Mecânico atualizado com sucesso!', 'success')
        return redirect(url_for('main.config_mecanicos'))
    
    return render_template('config/editar_mecanico.html', form=form)

# Para a rota de excluir mecânico:
@main_bp.route('/config/mecanicos/excluir/<int:id>', methods=['POST'])
@role_required('admin')
def excluir_mecanico(id):
    # Verificação manual do CSRF se necessário
    # csrf_token = request.form.get('csrf_token')
    # if not csrf_token or not validate_csrf(csrf_token):
    #     flash('Token CSRF inválido', 'danger')
    #     return redirect(url_for('main.config_mecanicos'))
    
    try:
        mecanico = Mecanico.query.get_or_404(id)
        db.session.delete(mecanico)
        db.session.commit()
        flash('Mecânico excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir mecânico: {str(e)}', 'danger')
    return redirect(url_for('main.config_mecanicos'))


## dalmo /config/equipamentos ini

# Exemplo de como corrigir a route no seu arquivo routes/main.py

@main_bp.route('/config/equipamentos', methods=['GET', 'POST'])
@login_required
def config_equipamentos():
    form = EquipamentoForm()
    if form.validate_on_submit():
        try:
            equipamento = Equipamento(
                codigo=form.codigo.data,
                nome=form.nome.data
            )
            db.session.add(equipamento)
            db.session.commit()
            flash('Equipamento cadastrado com sucesso!', 'success')
            return redirect(url_for('main.config_equipamentos'))
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao salvar equipamento: {e}")
            flash('Erro ao salvar equipamento. Tente novamente.', 'danger')

    # Carregar equipamentos para exibição
    try:
        equipamentos = Equipamento.query.order_by(Equipamento.codigo).all()
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        equipamentos = []
        flash('Erro ao carregar dados.', 'error')

    return render_template('config/equipamentos.html',
                         form=form,
                         equipamentos=equipamentos)


@main_bp.route('/config/equipamentos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_equipamento(id):
    equipamento = Equipamento.query.get_or_404(id)
    form = EquipamentoForm(obj=equipamento)
    if form.validate_on_submit():
        equipamento.codigo = form.codigo.data
        equipamento.nome = form.nome.data
        try:
            db.session.commit()
            flash('Equipamento atualizado com sucesso!', 'success')
            return redirect(url_for('main.config_equipamentos'))
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao atualizar equipamento: {e}")
            flash('Erro ao atualizar equipamento. Tente novamente.', 'danger')
    return render_template('config/editar_equipamento.html', form=form, equipamento=equipamento)


@main_bp.route('/config/equipamentos/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_equipamento(id):
    try:
        equipamento = Equipamento.query.get_or_404(id)
        
        # Verificar se o equipamento tem ordens de serviço
        ordens_servico = OrdemServico.query.filter_by(equipamento_id=id).count()
        
        if ordens_servico > 0:
            flash(f'Não é possível excluir este equipamento. Ele possui {ordens_servico} ordem(ns) de serviço associada(s).', 'warning')
        else:
            db.session.delete(equipamento)
            db.session.commit()
            flash('Equipamento excluído com sucesso!', 'success')
            
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir equipamento: {e}")
        flash('Erro ao excluir equipamento. Tente novamente.', 'error')
    
    return redirect(url_for('main.config_equipamentos'))

## dalmo /config/equipamentos fim

# Localizações
@main_bp.route('/config/localizacoes', methods=['GET', 'POST'])
@role_required('admin')
def config_localizacoes():
    form = LocalizacaoForm()
    localizacoes = Localizacao.query.all()
    
    if form.validate_on_submit():
        localizacao = Localizacao(
            codigo=form.codigo.data,
            nome=form.nome.data
        )
        db.session.add(localizacao)
        db.session.commit()
        flash('Localização cadastrada com sucesso!', 'success')
        return redirect(url_for('main.config_localizacoes'))
    
    return render_template('config/localizacoes.html', 
                         form=form, 
                         localizacoes=localizacoes)

@main_bp.route('/config/localizacoes/editar/<int:id>', methods=['GET', 'POST'])
@role_required('admin')
def editar_localizacao(id):
    localizacao = Localizacao.query.get_or_404(id)
    form = LocalizacaoForm(obj=localizacao)
    
    if form.validate_on_submit():
        form.populate_obj(localizacao)
        db.session.commit()
        flash('Localização atualizada com sucesso!', 'success')
        return redirect(url_for('main.config_localizacoes'))
    
    return render_template('config/editar_localizacao.html', form=form)

# Para a rota de excluir localização:
@main_bp.route('/config/localizacoes/excluir/<int:id>', methods=['POST'])
@role_required('admin')
def excluir_localizacao(id):
    try:
        localizacao = Localizacao.query.get_or_404(id)
        db.session.delete(localizacao)
        db.session.commit()
        flash('Localização excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir localização: {str(e)}', 'danger')
    return redirect(url_for('main.config_localizacoes'))

@main_bp.route('/inserir-sap/<int:os_id>', methods=['POST'])
def inserir_sap(os_id):
    os = OrdemServico.query.get_or_404(os_id)
    sap = request.form.get('sap')
    
    # Validação básica
    if not sap.isdigit() or not (4 <= len(sap) <= 10):
        flash("SAP deve conter 4 a 10 dígitos numéricos!", "danger")
        return redirect(url_for('main.manutencoes_concluidas'))
    
    os.sap = sap
    db.session.commit()
    flash("SAP atualizado com sucesso!", "success")
    return redirect(url_for('main.manutencoes_concluidas'))

@main_bp.route('/detalhes-os/<int:os_id>')
def detalhes_os(os_id):
    """Exibe os detalhes completos de uma Ordem de Serviço"""
    os = OrdemServico.query.get_or_404(os_id)
    return render_template('detalhes_os.html', os=os)


@main_bp.route('/detalhes-os/<int:os_id>/pdf')
def detalhes_os_pdf(os_id):
    """Gera o PDF da Ordem de Serviço"""
    os_entry = OrdemServico.query.get_or_404(os_id)
    
    try:
        pdf_data = generate_os_pdf(os_entry)
        
        # Envia o arquivo como download
        filename = f"OS_{os_entry.numero_os}.pdf"
        
        return send_file(
            BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar PDF: {str(e)}")
        flash(f"Erro ao gerar PDF: {str(e)}", "danger")
        return redirect(url_for('main.detalhes_os', os_id=os_id))


@main_bp.route('/excluir-os/<int:os_id>', methods=['POST'])
def excluir_os(os_id):
    os = OrdemServico.query.get_or_404(os_id)
    try:
        db.session.delete(os)
        db.session.commit()
        flash('OS excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir OS: {str(e)}', 'danger')
    return redirect(url_for('main.manutencoes_concluidas'))

@main_bp.route('/usuarios')
@role_required('admin')
def listar_usuarios():
    usuarios = User.query.all()
    return render_template('usuarios.html', usuarios=usuarios)

@main_bp.route('/usuarios/excluir/<int:user_id>', methods=['POST'])
@role_required('admin')
def excluir_usuario(user_id):
    usuario = User.query.get_or_404(user_id)
    if usuario.id == current_user.id:
        flash('Você não pode excluir o próprio usuário logado.', 'danger')
        return redirect(url_for('main.listar_usuarios'))
    try:
        db.session.delete(usuario)
        db.session.commit()
        flash('Usuário excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir usuário: {str(e)}', 'danger')
    return redirect(url_for('main.listar_usuarios'))

@main_bp.route('/usuarios/editar/<int:user_id>', methods=['GET', 'POST'])
@role_required('admin')
def editar_usuario(user_id):
    usuario = User.query.get_or_404(user_id)
    form = EditUserForm(obj=usuario)
    if form.validate_on_submit():
        usuario.username = form.username.data
        usuario.email = form.email.data
        usuario.role = form.role.data
        try:
            db.session.commit()
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('main.listar_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar usuário: {str(e)}', 'danger')
    return render_template('editar_usuario.html', form=form, usuario=usuario)

@main_bp.route('/usuarios/redefinir-senha/<int:user_id>', methods=['GET', 'POST'])
@role_required('admin')
def redefinir_senha_usuario(user_id):
    usuario = User.query.get_or_404(user_id)
    form = ResetPasswordForm()
    if form.validate_on_submit():
        usuario.set_password(form.password.data)
        try:
            db.session.commit()
            flash('Senha redefinida com sucesso!', 'success')
            return redirect(url_for('main.listar_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao redefinir senha: {str(e)}', 'danger')
    return render_template('redefinir_senha.html', form=form, usuario=usuario)

# ========================================
# Importação em Massa
# ========================================

@main_bp.route('/importar-configuracoes', methods=['POST'])
@role_required('admin')
def importar_configuracoes():
    """Importa equipamentos e localizações via Excel"""
    try:
        if 'arquivo' not in request.files:
            flash('Nenhum arquivo enviado', 'danger')
            return redirect(request.referrer)
        
        file = request.files['arquivo']
        if file.filename == '':
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(request.referrer)

        # Lendo o Excel
        xl = pd.ExcelFile(file)
        if 'Equipamentos' not in xl.sheet_names or 'Localizacoes' not in xl.sheet_names:
            flash('O arquivo deve conter as abas "Equipamentos" e "Localizacoes".', 'danger')
            return redirect(request.referrer)

        df_equipamentos = pd.read_excel(xl, sheet_name='Equipamentos')
        df_localizacoes = pd.read_excel(xl, sheet_name='Localizacoes')
        
        counts = {'equipamentos': 0, 'localizacoes': 0}
        
        # 1. Importar Localizações primeiro (para garantir que existam para o vínculo)
        for _, row in df_localizacoes.iterrows():
            codigo = str(row['Codigo']).strip()
            nome = str(row['Nome']).strip()
            
            if not codigo or codigo == 'nan' or not nome or nome == 'nan':
                continue
                
            localizacao = Localizacao.query.filter_by(codigo=codigo).first()
            if not localizacao:
                localizacao = Localizacao(codigo=codigo, nome=nome)
                db.session.add(localizacao)
                counts['localizacoes'] += 1
            else:
                localizacao.nome = nome
        
        # Commit localizações para garantir que os IDs estejam disponíveis
        db.session.flush()
        
        # 2. Importar Equipamentos com vínculo
        for _, row in df_equipamentos.iterrows():
            codigo = str(row['Codigo']).strip()
            nome = str(row['Nome']).strip()
            # Nova coluna para vínculo
            codigo_loc = str(row.get('Localizacao', '')).strip()
            
            if not codigo or codigo == 'nan' or not nome or nome == 'nan':
                continue
                
            localizacao = None
            if codigo_loc and codigo_loc != 'nan':
                localizacao = Localizacao.query.filter_by(codigo=codigo_loc).first()

            equipamento = Equipamento.query.filter_by(codigo=codigo).first()
            if not equipamento:
                equipamento = Equipamento(codigo=codigo, nome=nome)
                if localizacao:
                    equipamento.localizacao_id = localizacao.id
                db.session.add(equipamento)
                counts['equipamentos'] += 1
            else:
                equipamento.nome = nome
                if localizacao:
                    equipamento.localizacao_id = localizacao.id

        db.session.commit()
        flash(f'Importação concluída: {counts["equipamentos"]} equipamentos e {counts["localizacoes"]} localizações adicionados/atualizados.', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro na importação: {str(e)}")
        flash(f'Erro ao processar arquivo: {str(e)}', 'danger')
        
    return redirect(request.referrer)

@main_bp.route('/baixar-template-importacao')
@role_required('admin')
def baixar_template_importacao():
    """Gera um template Excel para importação"""
    try:
        output = BytesIO()
        
        # Dados de exemplo atualizados com a coluna Localizacao
        data_eq = {
            'Codigo': ['EQP001', 'EQP002'], 
            'Nome': ['Equipamento Exemplo 1', 'Equipamento Exemplo 2'],
            'Localizacao': ['LOC001', 'LOC001'] # Exemplo de vínculo
        }
        data_loc = {
            'Codigo': ['LOC001', 'LOC002'], 
            'Nome': ['Localização Exemplo 1', 'Localização Exemplo 2']
        }
        
        df_eq = pd.DataFrame(data_eq)
        df_loc = pd.DataFrame(data_loc)
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_eq.to_excel(writer, index=False, sheet_name='Equipamentos')
            df_loc.to_excel(writer, index=False, sheet_name='Localizacoes')
            
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='template_importacao_gds.xlsx'
        )
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar template: {str(e)}")
        flash('Erro ao gerar template de importação.', 'danger')
@main_bp.route('/noc')
@login_required
def noc_monitor():
    """Painel de Monitoramento (NOC) para visualização em telas grandes"""
    # Buscar OS abertas e em andamento
    ordens_ativas = OrdemServico.query.filter(
        OrdemServico.status.in_(['Aberta', 'Em andamento'])
    ).order_by(OrdemServico.data_inicio.asc()).all()
    
    # Calcular quanto tempo cada uma está aberta e formatar
    agora = datetime.now()
    for os in ordens_ativas:
        delta = agora - os.data_inicio
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        os.tempo_decorrido = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        os.horas_total = hours # Para manter a lógica de alerta no template se necessário
        
    return render_template('noc_monitor.html', ordens=ordens_ativas)

# ========================================
# Gestão de Checklists
# ========================================

@main_bp.route('/config/checklists')
@role_required('admin')
def config_checklists():
    templates = ChecklistTemplate.query.all()
    equipamentos = Equipamento.query.all()
    return render_template('checklists.html', templates=templates, equipamentos=equipamentos)

@main_bp.route('/config/checklists/novo', methods=['POST'])
@role_required('admin')
def novo_checklist():
    nome = request.form.get('nome')
    descricao = request.form.get('descricao')
    if nome:
        template = ChecklistTemplate(nome=nome, descricao=descricao)
        db.session.add(template)
        db.session.commit()
        flash('Checklist criado com sucesso!', 'success')
    return redirect(url_for('main.config_checklists'))

@main_bp.route('/config/checklists/item/novo/<int:template_id>', methods=['POST'])
@role_required('admin')
def novo_item_checklist(template_id):
    pergunta = request.form.get('pergunta')
    if pergunta:
        max_ordem = db.session.query(func.max(ChecklistItem.ordem)).filter_by(template_id=template_id).scalar() or 0
        item = ChecklistItem(template_id=template_id, pergunta=pergunta, ordem=max_ordem + 1)
        db.session.add(item)
        db.session.commit()
        flash('Item adicionado!', 'success')
    return redirect(url_for('main.config_checklists'))

@main_bp.route('/config/checklists/excluir/<int:id>', methods=['POST'])
@role_required('admin')
def excluir_checklist(id):
    template = ChecklistTemplate.query.get_or_404(id)
    db.session.delete(template)
    db.session.commit()
    flash('Checklist excluído!', 'success')
    return redirect(url_for('main.config_checklists'))

@main_bp.route('/config/checklists/item/excluir/<int:id>', methods=['POST'])
@role_required('admin')
def excluir_item_checklist(id):
    item = ChecklistItem.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Item excluído!', 'success')
    return redirect(url_for('main.config_checklists'))

@main_bp.route('/config/checklists/associar-equipamento', methods=['POST'])
@role_required('admin')
def associar_checklist_equipamento():
    equipamento_id = request.form.get('equipamento_id')
    template_id = request.form.get('template_id')
    
    if equipamento_id and template_id:
        equipamento = Equipamento.query.get(equipamento_id)
        if template_id == '0':
            equipamento.checklist_template_id = None
        else:
            equipamento.checklist_template_id = template_id
        db.session.commit()
        flash('Associação atualizada com sucesso!', 'success')
    return redirect(url_for('main.config_checklists'))

@main_bp.route('/api/checklists/itens/<int:template_id>')
@login_required
def api_checklist_itens(template_id):
    itens = ChecklistItem.query.filter_by(template_id=template_id).order_by(ChecklistItem.ordem).all()
    return jsonify([{'id': i.id, 'pergunta': i.pergunta} for i in itens])


# ========================================
# Parametrização de Horas e Calendário
# ========================================

@main_bp.route('/config/calendario', methods=['GET', 'POST'])
@role_required('admin')
def config_calendario():
    mes = request.args.get('mes', datetime.now().month, type=int)
    ano = request.args.get('ano', datetime.now().year, type=int)
    
    # Garante que o calendário existe
    populate_calendar_if_empty(mes, ano)
    
    dias = CalendarioOperacional.query.filter(
        db.extract('month', CalendarioOperacional.data) == mes,
        db.extract('year', CalendarioOperacional.data) == ano
    ).order_by(CalendarioOperacional.data).all()
    
    return render_template('config/calendario.html', dias=dias, mes=mes, ano=ano)

@main_bp.route('/config/calendario/toggle', methods=['POST'])
@role_required('admin')
def toggle_dia_util():
    data_str = request.form.get('data')
    if data_str:
        dia = CalendarioOperacional.query.get(data_str)
        if dia:
            dia.eh_dia_util = not dia.eh_dia_util
            db.session.commit()
            return jsonify({'success': True, 'eh_dia_util': dia.eh_dia_util})
    return jsonify({'success': False}), 400

@main_bp.route('/config/parametros-maquina', methods=['GET', 'POST'])
@role_required('admin')
def config_parametros_maquina():
    mes_filtro = request.args.get('mes', datetime.now().month, type=int)
    ano_filtro = request.args.get('ano', datetime.now().year, type=int)
    
    form = ParametrosMaquinaForm()
    
    # Pre-prender filtros se for GET para facilitar o cadastro
    if request.method == 'GET':
        form.mes.data = mes_filtro
        form.ano.data = ano_filtro
    
    if form.validate_on_submit():
        maquina_id = form.maquina_id.data
        mes = form.mes.data
        ano = form.ano.data
        
        param = ParametroMaquinaMensal.query.filter_by(
            maquina_id=maquina_id, mes=mes, ano=ano
        ).first()
        
        if not param:
            param = ParametroMaquinaMensal(
                maquina_id=maquina_id, mes=mes, ano=ano
            )
            db.session.add(param)
            
        try:
            param.horas_turno_dia = float(form.horas_turno_dia.data.replace(',', '.'))
            param.esta_ativa = form.esta_ativa.data
            db.session.commit()
            flash('Parâmetros salvos com sucesso!', 'success')
        except ValueError:
            flash('Erro: Horas Turno Dia deve ser um número.', 'danger')
            
        return redirect(url_for('main.config_parametros_maquina', mes=mes, ano=ano))
    
    parametros = ParametroMaquinaMensal.query.filter_by(
        mes=mes_filtro, ano=ano_filtro
    ).order_by(
        ParametroMaquinaMensal.id.desc()
    ).all()
    
    return render_template('config/parametros_maquina.html', 
                          form=form, 
                          parametros=parametros, 
                          mes_filtro=mes_filtro, 
                          ano_filtro=ano_filtro)
