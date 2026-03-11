# app/email_service.py

from flask_mail import Mail, Message
from flask import current_app, render_template_string
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

mail = Mail()

def init_mail(app):
    """Inicializa o Flask-Mail com a aplicação"""
    try:
        mail.init_app(app)
        
        # Define o sender padrão se não estiver configurado
        if not app.config.get('MAIL_DEFAULT_SENDER'):
            app.config['MAIL_DEFAULT_SENDER'] = app.config.get('MAIL_USERNAME')
            
        app.logger.info("Flask-Mail inicializado com sucesso")
        app.logger.info(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
        app.logger.info(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
        app.logger.info(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
        app.logger.info(f"MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
        app.logger.info(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
        
    except Exception as e:
        app.logger.error(f"Erro ao inicializar Flask-Mail: {str(e)}")

def testar_configuracao_email():
    """Testa a configuração de email"""
    try:
        config = current_app.config
        
        # Testa conexão SMTP
        server = smtplib.SMTP(config['MAIL_SERVER'], config['MAIL_PORT'])
        
        if config.get('MAIL_USE_TLS'):
            server.starttls()
            
        server.login(config['MAIL_USERNAME'], config['MAIL_PASSWORD'])
        server.quit()
        
        current_app.logger.info("Teste de configuração de email: SUCESSO")
        return True, "Configuração de email válida"
        
    except Exception as e:
        current_app.logger.error(f"Teste de configuração de email: FALHA - {str(e)}")
        return False, f"Erro na configuração: {str(e)}"

def enviar_email_nova_os(os_data):
    """
    Envia email para a equipe de manutenção quando uma nova OS é criada
    
    Args:
        os_data: Dicionário com os dados da OS
    """
    try:
        # Log dos dados recebidos
        current_app.logger.info(f"Iniciando envio de email para OS #{os_data.get('numero_os')}")
        
        # Validação básica dos dados
        if not os_data or not os_data.get('numero_os'):
            current_app.logger.error("Dados da OS inválidos para envio de email")
            return False
            
        # Template HTML para o email
        template_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Nova Ordem de Serviço</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background-color: #f5f5f5; 
                }
                .container {
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .header { 
                    background-color: #007bff; 
                    color: white; 
                    padding: 20px; 
                    text-align: center;
                }
                .header h2 {
                    margin: 0;
                    font-size: 24px;
                }
                .content { 
                    padding: 30px; 
                }
                .field { 
                    margin-bottom: 20px; 
                    border-bottom: 1px solid #eee;
                    padding-bottom: 15px;
                }
                .field:last-child {
                    border-bottom: none;
                }
                .label { 
                    font-weight: bold; 
                    color: #333; 
                    display: block;
                    margin-bottom: 5px;
                }
                .value { 
                    color: #666; 
                    font-size: 16px;
                }
                .urgent { 
                    color: #dc3545; 
                    font-weight: bold; 
                    background-color: #f8d7da;
                    padding: 5px 10px;
                    border-radius: 4px;
                    display: inline-block;
                }
                .motivo-box {
                    background-color: #f8f9fa; 
                    border-left: 4px solid #007bff;
                    padding: 15px; 
                    margin-top: 10px;
                    border-radius: 0 4px 4px 0;
                }
                .footer { 
                    background-color: #f8f9fa; 
                    padding: 20px; 
                    text-align: center;
                    font-size: 12px; 
                    color: #666; 
                    border-top: 1px solid #dee2e6;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🔧 Nova Ordem de Serviço Criada</h2>
                </div>
                
                <div class="content">
                    <div class="field">
                        <span class="label">Número da OS:</span>
                        <span class="value"><strong>{{ numero_os }}</strong></span>
                    </div>
                    
                    <div class="field">
                        <span class="label">Solicitante:</span>
                        <span class="value">{{ solicitante }}</span>
                    </div>
                    
                    <div class="field">
                        <span class="label">Localização/Área:</span>
                        <span class="value">{{ localizacao }}</span>
                    </div>
                    
                    <div class="field">
                        <span class="label">Equipamento:</span>
                        <span class="value">{{ equipamento }}</span>
                    </div>
                    
                    <div class="field">
                        <span class="label">Tipo de Manutenção:</span>
                        <span class="value {{ 'urgent' if tipo_manutencao == 'Corretiva' else '' }}">{{ tipo_manutencao }}</span>
                    </div>
                    
                    <div class="field">
                        <span class="label">Tipo de Parada:</span>
                        <span class="value">{{ tipo_parada }}</span>
                    </div>
                    
                    <div class="field">
                        <span class="label">Data/Hora de Abertura:</span>
                        <span class="value">{{ data_inicio }}</span>
                    </div>
                    
                    <div class="field">
                        <span class="label">Motivo da Quebra:</span>
                        <div class="motivo-box">
                            {{ motivo }}
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>Sistema de Manutenção GDS</strong></p>
                    <p>Email enviado automaticamente em {{ data_envio }}</p>
                    <p>Não responda a este email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Template de texto simples (fallback)
        template_texto = """
NOVA ORDEM DE SERVIÇO CRIADA

═══════════════════════════════════════════

Número da OS: {{ numero_os }}
Solicitante: {{ solicitante }}
Localização/Área: {{ localizacao }}
Equipamento: {{ equipamento }}
Tipo de Manutenção: {{ tipo_manutencao }}
Tipo de Parada: {{ tipo_parada }}
Data/Hora de Abertura: {{ data_inicio }}

Motivo da Quebra:
{{ motivo }}

═══════════════════════════════════════════
Sistema de Manutenção GDS
Email enviado automaticamente em {{ data_envio }}
        """
        
        # Renderizar templates
        html_body = render_template_string(template_html, **os_data)
        text_body = render_template_string(template_texto, **os_data)
        
        # Definir prioridade baseada no tipo de manutenção
        prioridade = "🚨 URGENTE - " if os_data.get('tipo_manutencao') == 'Corretiva' else ""
        
        # Definir destinatários
        destinatario_principal = current_app.config['MANUTENCAO_EMAIL']
        cc_emails = current_app.config.get('MANUTENCAO_CC_EMAILS', [])
        
        # Filtrar emails vazios da lista de CC
        cc_emails = [email.strip() for email in cc_emails if email.strip()]
        
        current_app.logger.info(f"Destinatário principal: {destinatario_principal}")
        current_app.logger.info(f"CCs: {cc_emails}")
        
        # Criar mensagem
        msg = Message(
            subject=f"{prioridade}Nova OS #{os_data.get('numero_os')} - {os_data.get('equipamento', 'N/A')}",
            sender=current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME'),
            recipients=[destinatario_principal],
            html=html_body,
            body=text_body
        )
        
        # Adicionar cópia para outros emails se configurado
        if cc_emails:
            msg.cc = cc_emails
        
        # Verificar se o mail está inicializado
        if not mail:
            current_app.logger.error("Flask-Mail não está inicializado")
            return False
            
        # Verificar configuração em tempo real
        conf = current_app.config
        pw = conf.get('MAIL_PASSWORD', '')
        masked_pw = pw[:2] + '*' * (len(pw) - 4) + pw[-2:] if len(pw) > 4 else '***'
        current_app.logger.info(f"DEBUG EMAIL - Server: {conf.get('MAIL_SERVER')}, User: {conf.get('MAIL_USERNAME')}, PW: {masked_pw}")

        # Enviar email
        mail.send(msg)
        current_app.logger.info(f"Email enviado com sucesso para OS #{os_data.get('numero_os')}")
        return True
        
    except Exception as e:
        error_msg = f"Erro ao enviar email para OS #{os_data.get('numero_os', 'N/A')}: {str(e)}"
        current_app.logger.error(error_msg)
        current_app.logger.error(f"Tipo do erro: {type(e).__name__}")
        
        # Log adicional para debug
        try:
            import traceback
            traceback_str = traceback.format_exc()
            current_app.logger.error(f"Traceback completo: {traceback_str}")
        except:
            pass
            
        return False

def enviar_email_os_finalizada(os_data):
    """
    Envia email quando uma OS é finalizada (opcional)
    """
    try:
        current_app.logger.info(f"Enviando email de finalização para OS #{os_data.get('numero_os')}")
        
        template_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Ordem de Serviço Finalizada</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background-color: #f5f5f5; 
                }
                .container {
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .header { 
                    background-color: #28a745; 
                    color: white; 
                    padding: 20px; 
                    text-align: center;
                }
                .header h2 {
                    margin: 0;
                    font-size: 24px;
                }
                .content { 
                    padding: 30px; 
                }
                .field { 
                    margin-bottom: 20px; 
                    border-bottom: 1px solid #eee;
                    padding-bottom: 15px;
                }
                .field:last-child {
                    border-bottom: none;
                }
                .label { 
                    font-weight: bold; 
                    color: #333; 
                    display: block;
                    margin-bottom: 5px;
                }
                .value { 
                    color: #666; 
                    font-size: 16px;
                }
                .footer { 
                    background-color: #f8f9fa; 
                    padding: 20px; 
                    text-align: center;
                    font-size: 12px; 
                    color: #666; 
                    border-top: 1px solid #dee2e6;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>✅ Ordem de Serviço Finalizada</h2>
                </div>
                
                <div class="content">
                    <div class="field">
                        <span class="label">Número da OS:</span>
                        <span class="value"><strong>{{ numero_os }}</strong></span>
                    </div>
                    
                    <div class="field">
                        <span class="label">Equipamento:</span>
                        <span class="value">{{ equipamento }}</span>
                    </div>
                    
                    <div class="field">
                        <span class="label">Mecânico Responsável:</span>
                        <span class="value">{{ mecanico }}</span>
                    </div>
                    
                    <div class="field">
                        <span class="label">Tempo Total:</span>
                        <span class="value">{{ tempo_manutencao }} horas</span>
                    </div>
                    
                    <div class="field">
                        <span class="label">Data de Finalização:</span>
                        <span class="value">{{ data_termino }}</span>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>Sistema de Manutenção GDS</strong></p>
                    <p>OS finalizada com sucesso!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        html_body = render_template_string(template_html, **os_data)
        
        msg = Message(
            subject=f"✅ OS #{os_data.get('numero_os')} Finalizada - {os_data.get('equipamento', 'N/A')}",
            sender=current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME'),
            recipients=[current_app.config['MANUTENCAO_EMAIL']],
            html=html_body
        )
        
        # Adicionar CCs se configurado
        cc_emails = current_app.config.get('MANUTENCAO_CC_EMAILS', [])
        cc_emails = [email.strip() for email in cc_emails if email.strip()]
        if cc_emails:
            msg.cc = cc_emails
        
        mail.send(msg)
        current_app.logger.info(f"Email de finalização enviado com sucesso para OS #{os_data.get('numero_os')}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Erro ao enviar email de finalização: {str(e)}")
        return False

def enviar_email_teste():
    """
    Função para testar o envio de emails
    """
    try:
        msg = Message(
            subject="Teste - Sistema de Manutenção GDS",
            recipients=[current_app.config['MANUTENCAO_EMAIL']],
            body="Este é um email de teste do Sistema de Manutenção GDS.\n\nSe você recebeu este email, a configuração está funcionando corretamente!",
            html="""
            <h2>Teste - Sistema de Manutenção GDS</h2>
            <p>Este é um email de teste do Sistema de Manutenção GDS.</p>
            <p><strong>Se você recebeu este email, a configuração está funcionando corretamente!</strong></p>
            <hr>
            <small>Email enviado em """ + datetime.now().strftime('%d/%m/%Y às %H:%M') + """</small>
            """
        )
        
        mail.send(msg)
        current_app.logger.info("Email de teste enviado com sucesso")
        return True, "Email de teste enviado com sucesso"
        
    except Exception as e:
        error_msg = f"Erro ao enviar email de teste: {str(e)}"
        current_app.logger.error(error_msg)
        return False, error_msg
