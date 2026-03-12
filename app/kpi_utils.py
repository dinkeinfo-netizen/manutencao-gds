from datetime import date, timedelta, datetime
import calendar
from .extensions import db
from .models import CalendarioOperacional, ParametroMaquinaMensal, Equipamento

def get_dias_uteis(mes, ano):
    """
    Retorna a quantidade de dias úteis no mês baseada na tabela CalendarioOperacional.
    Se a tabela estiver vazia para o período, retorna 0.
    """
    dias = CalendarioOperacional.query.filter(
        db.extract('month', CalendarioOperacional.data) == mes,
        db.extract('year', CalendarioOperacional.data) == ano,
        CalendarioOperacional.eh_dia_util == True
    ).count()
    
    return dias

def get_tempo_nominal_disponivel(maquina_id, mes, ano):
    """
    Calcula o Tempo Nominal Disponível: (Dias Úteis * Horas Turno Dia).
    Retorna 0 se a máquina estiver inativa no período.
    """
    parametro = ParametroMaquinaMensal.query.filter_by(
        maquina_id=maquina_id,
        mes=mes,
        ano=ano
    ).first()
    
    if not parametro or not parametro.esta_ativa:
        return 0.0
        
    dias_uteis = get_dias_uteis(mes, ano)
    return dias_uteis * parametro.horas_turno_dia

def get_tempo_nominal_periodo(maquina_id, data_inicio, data_fim):
    """
    Calcula o Tempo Nominal Disponível em um intervalo de datas.
    """
    # Converter para date se for datetime
    d_inicio = data_inicio.date() if isinstance(data_inicio, datetime) else data_inicio
    d_fim = data_fim.date() if isinstance(data_fim, datetime) else data_fim
        
    # Buscar dias úteis no período
    dias_periodo = CalendarioOperacional.query.filter(
        CalendarioOperacional.data >= d_inicio,
        CalendarioOperacional.data <= d_fim,
        CalendarioOperacional.eh_dia_util == True
    ).all()
    
    if not dias_periodo:
        return 0.0
        
    # Agrupar por mês/ano para evitar queries repetitivas
    cache_params = {}
    total_horas = 0.0
    
    for dia in dias_periodo:
        key = (dia.data.month, dia.data.year)
        if key not in cache_params:
            param = ParametroMaquinaMensal.query.filter_by(
                maquina_id=maquina_id,
                mes=dia.data.month,
                ano=dia.data.year
            ).first()
            cache_params[key] = param
            
        param = cache_params[key]
        if param:
            if param.esta_ativa:
                total_horas += param.horas_turno_dia
        else:
            # Default 8h se não parametrizado
            total_horas += 8.0
            
    return total_horas

def get_tempo_total_nominal_frota(data_inicio, data_fim):
    """
    Soma o tempo nominal de todos os equipamentos ativos no período.
    """
    equipamentos = Equipamento.query.all()
    total = 0.0
    for eq in equipamentos:
        total += get_tempo_nominal_periodo(eq.id, data_inicio, data_fim)
    return total

def populate_calendar_if_empty(mes, ano):
    """
    Popula o calendário para o mês/ano caso não exista.
    Marca sábados e domingos como não úteis por padrão.
    """
    first_day = date(ano, mes, 1)
    last_day = date(ano, mes, calendar.monthrange(ano, mes)[1])
    
    current = first_day
    while current <= last_day:
        exists = CalendarioOperacional.query.filter_by(data=current).first()
        if not exists:
            # 5 = Saturday, 6 = Sunday
            eh_util = current.weekday() < 5
            novo_dia = CalendarioOperacional(
                data=current,
                eh_dia_util=eh_util,
                descricao='Fim de Semana' if not eh_util else 'Dia de Trabalho'
            )
            db.session.add(novo_dia)
        current += timedelta(days=1)
    
    db.session.commit()
