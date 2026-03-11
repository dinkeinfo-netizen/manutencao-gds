#!/usr/bin/env python3
import sys
import os
from sqlalchemy import text

# Adicionar o diretório pai ao path para importar o módulo app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from app.extensions import db
from app.config import Config

def check_equipamentos_structure():
    """Verifica a estrutura atual da tabela equipamentos"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    with app.app_context():
        try:
            # Verificar se conseguimos conectar ao banco
            db.session.execute(text('SELECT 1'))
            print("✅ Conexão com o banco estabelecida com sucesso!")
            
            # Verificar estrutura da tabela equipamentos
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('equipamentos')
            
            print("\n📋 Estrutura atual da tabela 'equipamentos':")
            print("-" * 50)
            
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
                
            # Verificar se existe coluna 'localizacao' (sem _id)
            has_localizacao = any(col['name'] == 'localizacao' for col in columns)
            has_localizacao_id = any(col['name'] == 'localizacao_id' for col in columns)
            
            print(f"\n🔍 Análise:")
            print(f"  - Coluna 'localizacao' existe: {has_localizacao}")
            print(f"  - Coluna 'localizacao_id' existe: {has_localizacao_id}")
            
            if has_localizacao and not has_localizacao_id:
                print("\n❌ PROBLEMA IDENTIFICADO:")
                print("   Existe uma coluna 'localizacao' que deveria ser 'localizacao_id'")
                print("   Isso está causando conflito com a tabela localizacoes")
                
            elif not has_localizacao and has_localizacao_id:
                print("\n✅ Estrutura correta:")
                print("   A tabela usa 'localizacao_id' como chave estrangeira")
                
            elif has_localizacao and has_localizacao_id:
                print("\n⚠️  CONFLITO IDENTIFICADO:")
                print("   Existem AMBAS as colunas 'localizacao' e 'localizacao_id'")
                print("   Isso pode causar problemas de integridade")
                
            else:
                print("\n❓ ESTRUTURA INESPERADA:")
                print("   Não há colunas relacionadas à localização")
                
        except Exception as e:
            print(f"❌ Erro ao verificar estrutura: {str(e)}")

if __name__ == '__main__':
    check_equipamentos_structure() 