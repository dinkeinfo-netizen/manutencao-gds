import sys
sys.path.append('/manutencao-gds')
from app import create_app
from app.extensions import db
from app.models import OrdemServico, Equipamento, Localizacao, Mecanico, CalendarioOperacional, ParametroMaquinaMensal
from datetime import datetime

app = create_app()
with app.app_context():
    print("=== Iniciando Diagnóstico do Sistema ===\n")
    
    # 1. Checagem de Orfãos e Integridade
    print("[1] Verificando Integridade de Dados:")
    oss_sem_equipamento = OrdemServico.query.filter(OrdemServico.equipamento_id == None).count()
    oss_sem_localizacao = OrdemServico.query.filter(OrdemServico.localizacao_id == None).count()
    if oss_sem_equipamento > 0: print(f"  ⚠️  ERRO: {oss_sem_equipamento} OS sem equipamento!")
    if oss_sem_localizacao > 0: print(f"  ⚠️  ERRO: {oss_sem_localizacao} OS sem localização!")
    
    # 2. Status e Mecânicos
    print("\n[2] Verificando Consistência de Status:")
    oss_andamento_sem_mecanico = OrdemServico.query.filter_by(status='Em andamento', mecanico_id=None).count()
    if oss_andamento_sem_mecanico > 0:
        print(f"  ⚠️  ALERTA: {oss_andamento_sem_mecanico} OS 'Em andamento' sem mecânico atribuído.")
    
    # 3. Tempos Negativos ou Irreais
    print("\n[3] Verificando Anomalias de Datas:")
    # Casos onde data_termino < data_inicio
    oss_datas_erradas = OrdemServico.query.filter(OrdemServico.data_termino < OrdemServico.data_inicio).count()
    if oss_datas_erradas > 0:
        print(f"  ⚠️  CRÍTICO: {oss_datas_erradas} OS com data de término anterior ao início!")
        
    # Casos com tempo_manutencao negativo ou nulo em concluídas
    oss_tempo_inconsistente = OrdemServico.query.filter(OrdemServico.status == 'Concluída', (OrdemServico.tempo_manutencao < 0) | (OrdemServico.tempo_manutencao == None)).count()
    if oss_tempo_inconsistente > 0:
        print(f"  ⚠️  ERRO: {oss_tempo_inconsistente} OS concluídas com tempo de manutenção inválido.")

    # 4. Calendário e Configurações
    print("\n[4] Verificando Configurações de KPI:")
    hoje = datetime.now()
    dias_março = CalendarioOperacional.query.filter(
        db.extract('month', CalendarioOperacional.data) == hoje.month,
        db.extract('year', CalendarioOperacional.data) == hoje.year
    ).count()
    if dias_março == 0:
        print(f"  ⚠️  AVISO: Calendário de {hoje.month}/{hoje.year} está vazio. KPIs não funcionarão!")
    
    equip_sem_params = 0
    for eq in Equipamento.query.all():
        p = ParametroMaquinaMensal.query.filter_by(maquina_id=eq.id, mes=hoje.month, ano=hoje.year).first()
        if not p:
            equip_sem_params += 1
    if equip_sem_params > 0:
        print(f"  ℹ️  INFO: {equip_sem_params} equipamentos sem parâmetros específicos para este mês (usando padrão 10h).")

    # 5. Segurança de Arquivos e Uploads
    import os
    upload_path = os.path.join('/manutencao-gds/app/static/uploads')
    if not os.path.exists(upload_path):
        print("  ⚠️  AVISO: Pasta de uploads não existe. Erro ao salvar fotos!")
        
    print("\n=== Diagnóstico Concluído ===")
