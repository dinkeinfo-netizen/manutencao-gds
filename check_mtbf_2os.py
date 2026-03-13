import sys
sys.path.append('/manutencao-gds')
from app import create_app
from app.extensions import db
from app.models import OrdemServico, Equipamento
from datetime import datetime, timedelta
import calendar

app = create_app()
with app.app_context():
    hoje = datetime.now()
    inicio_periodo = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ultimo_dia_mes = calendar.monthrange(hoje.year, hoje.month)[1]
    fim_mes = hoje.replace(day=ultimo_dia_mes, hour=23, minute=59, second=59)

    oss = OrdemServico.query.filter(
        OrdemServico.status == 'Concluída',
        OrdemServico.data_termino >= inicio_periodo,
        OrdemServico.data_termino <= fim_mes
    ).all()

    print(f"=== OS Concluídas no Mês ({hoje.month}/{hoje.year}) ===")
    print(f"Total de OS Concluídas: {len(oss)}")
    
    total_parada_geral = 0
    total_falhas_geral = 0
    
    for o in oss:
        print(f"ID: {o.id} | Numero: {o.numero_os} | Tipo: {o.tipo_manutencao} | Termino: {o.data_termino} | Tempo: {o.tempo_manutencao}h")
        if o.tipo_manutencao == 'corretiva':
            total_falhas_geral += 1
            total_parada_geral += (o.tempo_manutencao or 0)
            
    print(f"\nResumo formula MTBF Base:")
    print(f"Total Falhas (Corretivas): {total_falhas_geral}")
    print(f"Total Parada: {total_parada_geral}h")
    
    from app.kpi_utils import get_tempo_total_calendario_nominal
    horas_totais = get_tempo_total_calendario_nominal(inicio_periodo, fim_mes)
    print(f"Horas Totais Calendário: {horas_totais}h")
    
    if total_falhas_geral > 0:
        mtbf = (horas_totais - total_parada_geral) / total_falhas_geral
        print(f"Cálculo MTBF: ({horas_totais} - {total_parada_geral}) / {total_falhas_geral} = {mtbf}")
    else:
        print(f"Cálculo MTBF: 0 falhas -> {horas_totais}")
