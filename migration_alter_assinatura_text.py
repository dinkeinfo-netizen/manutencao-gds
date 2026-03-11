#!/usr/bin/env python3
"""
Migração para alterar as colunas assinatura_mecanico e assinatura_conferente para TEXT no MySQL.
"""
import mysql.connector
import os

def main():
    conn = mysql.connector.connect(
        host=os.environ.get('MYSQL_HOST', 'db'),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', ''),
        database=os.environ.get('MYSQL_DATABASE', 'manutencao_gds')
    )
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE ordens_servico MODIFY assinatura_mecanico TEXT;")
        cursor.execute("ALTER TABLE ordens_servico MODIFY assinatura_conferente TEXT;")
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