import os
import sys

# Add project root to sys.path
sys.path.append('/manutencao-gds')

from app import create_app
from app.extensions import db
from app.models import CalendarioOperacional, ParametroMaquinaMensal, Equipamento, OrdemServico
from app.kpi_utils import get_tempo_total_nominal_frota, get_tempo_nominal_periodo
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    hoje = datetime.now()
    inicio_periodo = hoje - timedelta(days=30)
    
    print(f"--- DEBUG KPI ---")
    print(f"Hoze: {hoje}")
    print(f"Inicio Periodo (30 dias): {inicio_periodo}")
    
    # Check Calendar
    dias_uteis = CalendarioOperacional.query.filter(
        CalendarioOperacional.data >= inicio_periodo.date(),
        CalendarioOperacional.data <= hoje.date(),
        CalendarioOperacional.eh_dia_util == True
    ).all()
    print(f"Dias uteis no periodo de 30 dias: {len(dias_uteis)}")
    for d in dias_uteis:
        print(f"  - {d.data}")

    # Check Equipments
    equipamentos = Equipamento.query.all()
    print(f"Equipamentos no banco: {len(equipamentos)}")
    
    total_frota = 0
    for eq in equipamentos:
        horas_eq = get_tempo_nominal_periodo(eq.id, inicio_periodo, hoje)
        print(f"Equipamento {eq.codigo} ({eq.nome}): {horas_eq}h nominais")
        # Check specific params for this equipment
        params = ParametroMaquinaMensal.query.filter_by(maquina_id=eq.id).all()
        for p in params:
            print(f"   Param: {p.mes}/{p.ano} - {p.horas_turno_dia}h, Ativa: {p.esta_ativa}")
        total_frota += horas_eq
        
    print(f"Total Nominal Frota (Calculado): {total_frota}")
    
    # Check OSs
    oss = OrdemServico.query.filter(
        OrdemServico.status == 'Concluída',
        OrdemServico.tipo_manutencao == 'corretiva',
        OrdemServico.data_termino >= inicio_periodo
    ).all()
    print(f"OS corretivas concluidas no periodo: {len(oss)}")
    downtime_sum = 0
    for o in oss:
        print(f"  OS {o.numero_os}: {o.tempo_manutencao}h")
        downtime_sum += (o.tempo_manutencao or 0)
    print(f"Soma Downtime: {downtime_sum}")
    
    if len(oss) > 0:
        mtbf = (total_frota - downtime_sum) / len(oss)
        print(f"MTBF (Total Frota): {mtbf}")
        
    # Check if they want calendar-based instead
    cal_hours_base_10 = len(dias_uteis) * 10
    cal_hours_base_8 = len(dias_uteis) * 8
    print(f"Base Calendario (22 dias x 10h): {cal_hours_base_10}")
    print(f"Base Calendario (22 dias x 8h): {cal_hours_base_8}")
