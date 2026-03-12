import os
from fpdf import FPDF
from datetime import datetime
from io import BytesIO

class OSPDF(FPDF):
    def header(self):
        # Logo
        # self.image('logo.png', 10, 8, 33)
        self.set_font('helvetica', 'B', 15)
        self.set_text_color(30, 41, 59) # bg-dark color
        self.cell(0, 10, 'RELATÓRIO DE ORDEM DE SERVIÇO', border=False, align='C')
        self.ln(10)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 5, 'Sistema de Manutenção GDS - RQ MAN - 073 01', border=False, align='C')
        self.ln(10)
        # Linha horizontal
        self.set_draw_color(59, 130, 246) # Primary blue
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}} - Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")} - DINKE', align='C')

def generate_os_pdf(os_data):
    pdf = OSPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # OS Number and Title
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_fill_color(248, 250, 252)
    pdf.cell(0, 10, f'Ordem de Serviço #{os_data.numero_os}', ln=True, fill=True)
    
    # Seção 1: Informações da Solicitação
    pdf.ln(2)
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_fill_color(59, 130, 246) # Blue primary
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, ' INFORMAÇÕES DA SOLICITAÇÃO', ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    
    # Tabela de informações
    pdf.ln(2)
    pdf.set_font('helvetica', 'B', 9)
    
    data_items = [
        ('Solicitante:', os_data.solicitante or 'N/A'),
        ('Localização/Área:', f"{os_data.localizacao.codigo if os_data.localizacao else 'N/A'} - {os_data.localizacao.nome if os_data.localizacao else ''}"),
        ('Equipamento:', f"{os_data.equipamento.codigo if os_data.equipamento else 'N/A'} - {os_data.equipamento.nome if os_data.equipamento else ''}"),
        ('Tipo de Manutenção:', os_data.tipo_manutencao.title() if os_data.tipo_manutencao else 'N/A'),
        ('Tipo de Parada:', os_data.tipo_parada.title() if os_data.tipo_parada else 'N/A'),
        ('Data Início:', os_data.data_inicio.strftime('%d/%m/%Y %H:%M') if os_data.data_inicio else 'N/A'),
        ('Data Término:', os_data.data_termino.strftime('%d/%m/%Y %H:%M') if os_data.data_termino else 'N/A'),
    ]
    
    for label, value in data_items:
        pdf.set_font('helvetica', 'B', 9)
        pdf.cell(40, 7, label, border=0)
        pdf.set_font('helvetica', '', 9)
        pdf.cell(0, 7, value, ln=True, border=0)
    
    # Motivo
    pdf.ln(2)
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(0, 7, 'Motivo da Quebra/Manutenção:', ln=True)
    pdf.set_font('helvetica', '', 9)
    pdf.multi_cell(0, 5, os_data.motivo or 'N/A', border=1)
    
    # Seção 2: Detalhes da Execução
    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_fill_color(34, 197, 94) # Green success
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, ' DETALHES DA EXECUÇÃO', ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(40, 7, 'Mecânico Responsável:', border=0)
    pdf.set_font('helvetica', '', 9)
    pdf.cell(0, 7, os_data.nome_mecanico or 'N/A', ln=True)
    
    if os_data.nome_conferente:
        pdf.set_font('helvetica', 'B', 9)
        pdf.cell(40, 7, 'Conferente:', border=0)
        pdf.set_font('helvetica', '', 9)
        pdf.cell(0, 7, os_data.nome_conferente, ln=True)
    
    pdf.ln(2)
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(0, 7, 'Descrição do Serviço Realizado:', ln=True)
    pdf.set_font('helvetica', '', 9)
    pdf.multi_cell(0, 5, os_data.descricao_servico or 'N/A', border=1)
    
    if os_data.materiais_utilizados:
        pdf.ln(2)
        pdf.set_font('helvetica', 'B', 9)
        pdf.cell(0, 7, 'Materiais Utilizados:', ln=True)
        pdf.set_font('helvetica', '', 9)
        pdf.multi_cell(0, 5, os_data.materiais_utilizados, border=1)
        
    # Seção 3: Checklist
    if os_data.checklist_respostas or os_data.equipamento_liberado is not None:
        pdf.ln(5)
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_fill_color(245, 158, 11) # Amber/Warning
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, ' CHECKLIST DE VERIFICAÇÃO', ln=True, fill=True)
        pdf.ln(2)
        
        pdf.set_font('helvetica', '', 9)
        if os_data.checklist_respostas:
            for resp in os_data.checklist_respostas:
                status = 'SIM (OK)' if resp.valor else 'NÃO'
                pdf.cell(160, 6, resp.item.pergunta, border=0)
                pdf.set_font('helvetica', 'B', 9)
                pdf.cell(30, 6, status, ln=True, align='R')
                pdf.set_font('helvetica', '', 9)
        else:
            # Legado
            legacy_checklist = [
                ('Há graxa/óleo escorrendo?', 'NÃO' if not os_data.graxa_oleo else 'SIM'),
                ('Limpeza realizada?', 'SIM' if os_data.limpeza else 'NÃO'),
                ('Peças soltas?', 'NÃO' if not os_data.pecas_soltas else 'SIM'),
                ('Equipamento liberado para operação?', 'SIM' if os_data.equipamento_liberado else 'NÃO'),
            ]
            for q, a in legacy_checklist:
                pdf.cell(160, 6, q, border=0)
                pdf.set_font('helvetica', 'B', 9)
                pdf.cell(30, 6, a, ln=True, align='R')
                pdf.set_font('helvetica', '', 9)

    # Seção 4: Assinaturas
    pdf.ln(10)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(0, 8, ' ASSINATURAS DIGITAIS', ln=True)
    pdf.ln(5)
    
    # Espaço para assinaturas
    y_start_signatures = pdf.get_y()
    
    # Mecânico
    pdf.set_xy(10, y_start_signatures)
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(90, 5, 'Mecânico:', ln=True)
    pdf.set_font('helvetica', '', 8)
    pdf.cell(90, 5, os_data.nome_mecanico or 'N/A', ln=True)
    if os_data.data_assinatura_mecanico:
        pdf.cell(90, 5, f'Assinado em: {os_data.data_assinatura_mecanico.strftime("%d/%m/%Y %H:%M")}', ln=True)
    
    # Imagem da assinatura se existir
    if os_data.assinatura_mecanico:
        try:
            # Assinatura é base64, precisa converter ou salvar temporário
            import base64
            img_data = os_data.assinatura_mecanico.split(',')[1]
            img_bytes = base64.b64decode(img_data)
            temp_path = f"/tmp/sig_mec_{os_data.id}.png"
            with open(temp_path, 'wb') as f:
                f.write(img_bytes)
            pdf.image(temp_path, x=20, y=pdf.get_y(), w=60)
            os.remove(temp_path)
            pdf.ln(25) # Espaço para imagem
        except Exception as e:
            pdf.cell(90, 10, '[Erro ao carregar assinatura]', ln=True)
            
    # Conferente
    pdf.set_xy(110, y_start_signatures)
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(90, 5, 'Conferente:', ln=True)
    pdf.set_font('helvetica', '', 8)
    pdf.set_x(110)
    pdf.cell(90, 5, os_data.nome_conferente or 'N/A', ln=True)
    if os_data.data_assinatura_conferente:
        pdf.set_x(110)
        pdf.cell(90, 5, f'Assinado em: {os_data.data_assinatura_conferente.strftime("%d/%m/%Y %H:%M")}', ln=True)
        
    if os_data.assinatura_conferente:
        try:
            import base64
            img_data = os_data.assinatura_conferente.split(',')[1]
            img_bytes = base64.b64decode(img_data)
            temp_path = f"/tmp/sig_conf_{os_data.id}.png"
            with open(temp_path, 'wb') as f:
                f.write(img_bytes)
            pdf.image(temp_path, x=120, y=y_start_signatures + 15, w=60)
            os.remove(temp_path)
        except Exception as e:
            pdf.set_x(110)
            pdf.cell(90, 10, '[Erro ao carregar assinatura]', ln=True)

    return pdf.output()
