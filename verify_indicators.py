from app import create_app
from app.extensions import db
from app.models import CalendarioOperacional, ParametroMaquinaMensal, Equipamento, OrdemServico
from app.kpi_utils import get_tempo_total_nominal_frota
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    hoje = datetime.now()
    # Mocking the scenario describe by the user: 
    # 22 dias uteis de 10h (Total 220h) 
    # uma falha de 0.02h de downtime
    # MTBF deveria ser 219.98h
    
    # Let's see what the system currently calculates with ACTUAL data
    inicio_periodo = hoje - timedelta(days=30)
    horas_totais = get_tempo_total_nominal_frota(inicio_periodo, hoje)
    
    downtime_total = db.session.query(
        db.func.sum(OrdemServico.tempo_manutencao)
    ).filter(
        OrdemServico.status == 'Concluída',
        OrdemServico.tipo_manutencao == 'corretiva',
        OrdemServico.data_termino >= inicio_periodo
    ).scalar() or 0
    
    num_falhas = OrdemServico.query.filter(
        OrdemServico.status == 'Concluída',
        OrdemServico.tipo_manutencao == 'corretiva',
        OrdemServico.data_termino >= inicio_periodo
    ).count()
    
    print(f"--- VERIFICACAO ---")
    print(f"Horas Totais (Frota): {horas_totais}")
    print(f"Downtime Total: {downtime_total}")
    print(f"Número de Falhas: {num_falhas}")
    
    if num_falhas > 0:
        mtbf = (horas_totais - downtime_total) / num_falhas
        print(f"MTBF Calculado: {mtbf}")
        if abs(mtbf - 219.98) < 0.1:
            print("SUCESSO: MTBF proximo de 219.98")
        else:
            print(f"AVISO: MTBF divergente. Esperado ~219.98 se houver apenas 1 equipamento e 22 dias uteis.")
    else:
        print("SEM FALHAS NO PERIODO")

    # Check if there's any equipment with 0.02 downtime
    eq_002 = db.session.query(OrdemServico).filter(OrdemServico.tempo_manutencao == 0.02).first()
    if eq_002:
        print(f"Encontrada OS com 0.02h de downtime: {eq_002.numero_os} para equipamento {eq_002.equipamento_id}")
