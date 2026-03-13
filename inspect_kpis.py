from app import create_app
from app.extensions import db
from app.models import CalendarioOperacional, ParametroMaquinaMensal, Equipamento, OrdemServico
from app.kpi_utils import get_tempo_total_nominal_frota
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    hoje = datetime.now()
    inicio_periodo = hoje - timedelta(days=30)
    
    print(f"Periodo: {inicio_periodo.date()} ate {hoje.date()}")
    
    dias_uteis = CalendarioOperacional.query.filter(
        CalendarioOperacional.data >= inicio_periodo.date(),
        CalendarioOperacional.data <= hoje.date(),
        CalendarioOperacional.eh_dia_util == True
    ).count()
    print(f"Dias uteis no periodo: {dias_uteis}")
    
    equipamentos = Equipamento.query.all()
    print(f"Total equipamentos: {len(equipamentos)}")
    for eq in equipamentos:
        print(f"Equipamento: {eq.codigo} - {eq.nome}")
        params = ParametroMaquinaMensal.query.filter_by(maquina_id=eq.id).all()
        for p in params:
            print(f"  Param: mes={p.mes}, ano={p.ano}, horas={p.horas_turno_dia}, ativa={p.esta_ativa}")
            
    horas_totais = get_tempo_total_nominal_frota(inicio_periodo, hoje)
    print(f"get_tempo_total_nominal_frota: {horas_totais}")
    
    downtime_total = db.session.query(
        db.func.sum(OrdemServico.tempo_manutencao)
    ).filter(
        OrdemServico.status == 'Concluída',
        OrdemServico.tipo_manutencao == 'corretiva',
        OrdemServico.data_termino >= inicio_periodo
    ).scalar() or 0
    print(f"Downtime total: {downtime_total}")
    
    num_falhas = OrdemServico.query.filter(
        OrdemServico.status == 'Concluída',
        OrdemServico.tipo_manutencao == 'corretiva',
        OrdemServico.data_termino >= inicio_periodo
    ).count()
    print(f"Numero de falhas: {num_falhas}")
    
    if num_falhas > 0:
        mtbf = (horas_totais - downtime_total) / num_falhas
        print(f"MTBF calculado: {mtbf}")
