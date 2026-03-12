#!/usr/bin/env python3
"""
Migração para alterar as colunas assinatura_mecanico e assinatura_conferente para TEXT no MySQL.
"""
import psycopg2
import os

def main():
    conn = psycopg2.connect(
        host=os.environ.get('POSTGRES_HOST', 'db'),
        user=os.environ.get('POSTGRES_USER', 'manutencao_user'),
        password=os.environ.get('POSTGRES_PASSWORD', 'manutencao_pass'),
        database=os.environ.get('POSTGRES_DB', 'manutencao_db'),
        port=5432
    )
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE ordens_servico ALTER COLUMN assinatura_mecanico TYPE TEXT;")
        cursor.execute("ALTER TABLE ordens_servico ALTER COLUMN assinatura_conferente TYPE TEXT;")
        # Note: In Postgres, if it was String(100), TYPE TEXT is fine.
        conn.commit()
        print('Migração concluída com sucesso!')
    except Exception as e:
        print(f'Erro na migração: {e}')
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main() 