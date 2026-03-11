#!/usr/bin/env python3
import sys
import os
from sqlalchemy import text

# Adicionar o diretório pai ao path para importar o módulo app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from app.extensions import db
from app.config import Config

def add_localizacao_id_column():
    """
    Adiciona a coluna localizacao_id à tabela equipamentos
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    with app.app_context():
        try:
            # Verificar se a coluna já existe
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('equipamentos')]
            
            if 'localizacao_id' not in columns:
                print("🔧 Adicionando coluna 'localizacao_id' à tabela equipamentos...")
                
                # Adicionar a coluna localizacao_id
                db.session.execute(text('ALTER TABLE equipamentos ADD COLUMN localizacao_id INT'))
                
                # Adicionar a chave estrangeira
                db.session.execute(text('ALTER TABLE equipamentos ADD CONSTRAINT fk_equipamentos_localizacao FOREIGN KEY (localizacao_id) REFERENCES localizacoes(id)'))
                
                # Verificar se existem localizações para definir um valor padrão
                result = db.session.execute(text('SELECT COUNT(*) as count FROM localizacoes'))
                count = result.fetchone()[0]
                
                if count > 0:
                    # Pegar o ID da primeira localização
                    result = db.session.execute(text('SELECT id FROM localizacoes LIMIT 1'))
                    first_location_id = result.fetchone()[0]
                    
                    # Atualizar todos os equipamentos existentes para usar a primeira localização
                    db.session.execute(text(f'UPDATE equipamentos SET localizacao_id = {first_location_id}'))
                    print(f"✅ Equipamentos existentes associados à localização ID {first_location_id}")
                else:
                    print("⚠️  Nenhuma localização encontrada. Crie localizações antes de adicionar equipamentos.")
                
                db.session.commit()
                print("✅ Coluna 'localizacao_id' adicionada com sucesso!")
                
            else:
                print("ℹ️  Coluna 'localizacao_id' já existe na tabela.")
                
            # Verificar estrutura final
            columns = inspector.get_columns('equipamentos')
            print("\n📋 Estrutura final da tabela 'equipamentos':")
            print("-" * 50)
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
                
        except Exception as e:
            print(f"❌ Erro ao adicionar coluna: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    add_localizacao_id_column() 