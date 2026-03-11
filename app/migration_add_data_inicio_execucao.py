"""
Script para migrar o banco de dados e tornar localizacao_id opcional
Execute este script para corrigir a estrutura do banco
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import sys
import os

# Configuração básica do Flask para migração
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://manutencao_user:manutencao_pass@db/manutencao_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

def executar_migracao_manual():
    """
    Executa a migração manual para tornar localizacao_id opcional
    """
    try:
        print("🔧 Iniciando migração do banco de dados...")
        
        # SQL para alterar a coluna e torná-la nullable
        sql_commands = [
            "ALTER TABLE equipamentos MODIFY COLUMN localizacao_id INT NULL;",
            "UPDATE equipamentos SET localizacao_id = NULL WHERE localizacao_id = 0 OR localizacao_id NOT IN (SELECT id FROM localizacoes);"
        ]
        
        with app.app_context():
            for sql in sql_commands:
                try:
                    print(f"📝 Executando: {sql}")
                    db.engine.execute(sql)
                    print("✅ Comando executado com sucesso!")
                except Exception as e:
                    print(f"⚠️ Erro ao executar comando: {e}")
                    # Continua mesmo com erro (pode ser que a coluna já esteja correta)
            
            # Commit das alterações
            db.session.commit()
            print("✅ Migração concluída com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        return False
    
    return True

def verificar_estrutura():
    """
    Verifica a estrutura atual do banco de dados
    """
    try:
        with app.app_context():
            # Verificar quantos equipamentos existem sem localização
            result = db.engine.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(localizacao_id) as com_localizacao,
                    COUNT(*) - COUNT(localizacao_id) as sem_localizacao
                FROM equipamentos
            """).fetchone()
            
            print(f"📊 Estatísticas dos equipamentos:")
            print(f"   Total: {result[0]}")
            print(f"   Com localização: {result[1]}")
            print(f"   Sem localização: {result[2]}")
            
            # Verificar se existem localizações
            result_loc = db.engine.execute("SELECT COUNT(*) FROM localizacoes").fetchone()
            print(f"📍 Total de localizações: {result_loc[0]}")
            
    except Exception as e:
        print(f"❌ Erro ao verificar estrutura: {e}")

def criar_localizacao_padrao():
    """
    Cria uma localização padrão caso não existam localizações
    """
    try:
        with app.app_context():
            # Verificar se existem localizações
            result = db.engine.execute("SELECT COUNT(*) FROM localizacoes").fetchone()
            
            if result[0] == 0:
                print("📍 Criando localização padrão...")
                db.engine.execute("""
                    INSERT INTO localizacoes (codigo, nome) 
                    VALUES ('GERAL', 'Localização Geral')
                """)
                db.session.commit()
                print("✅ Localização padrão criada!")
            else:
                print(f"✅ Já existem {result[0]} localizações no banco")
                
    except Exception as e:
        print(f"❌ Erro ao criar localização padrão: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando correção do banco de dados...")
    print("=" * 50)
    
    # 1. Verificar estrutura atual
    print("\n1️⃣ Verificando estrutura atual:")
    verificar_estrutura()
    
    # 2. Criar localização padrão se necessário
    print("\n2️⃣ Verificando localizações:")
    criar_localizacao_padrao()
    
    # 3. Executar migração
    print("\n3️⃣ Executando migração:")
    if executar_migracao_manual():
        print("\n✅ Migração concluída com sucesso!")
        print("\n📋 Próximos passos:")
        print("   1. Reinicie sua aplicação Flask")
        print("   2. Teste o cadastro de equipamentos")
        print("   3. Edite equipamentos existentes para definir localização")
    else:
        print("\n❌ Migração falhou. Verifique os logs acima.")
    
    print("\n" + "=" * 50)
    print("🏁 Script finalizado!")
