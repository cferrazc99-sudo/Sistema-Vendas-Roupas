import sqlite3
import os

# Força o Python a olhar para a pasta onde o script está salvo
caminho_projeto = os.path.dirname(os.path.abspath(__file__))
caminho_db = os.path.join(caminho_projeto, 'sistema_vendas_BACKUP.db')

conn = sqlite3.connect(caminho_db)
cursor = conn.cursor()

try:
    # 1. Verifica quais tabelas realmente existem no banco para você não chutar no escuro
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tabelas_reais = [t[0] for t in cursor.fetchall()]
    print(f"📋 Tabelas encontradas no banco: {tabelas_reais}")

    # 2. Só deleta se a tabela existir na lista acima
    tabelas_para_limpar = ['vendas_pagamentos', 'vendas']
    
    for tab in tabelas_para_limpar:
        if tab in tabelas_reais:
            conn.execute(f"DELETE FROM {tab}")
            print(f"✅ Dados da tabela '{tab}' removidos.")
        else:
            print(f"⚠️ A tabela '{tab}' não existe neste arquivo .db")

    conn.commit()

except Exception as e:
    print(f"❌ Erro: {e}")
finally:
    conn.close()
