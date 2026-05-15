import os
import sqlite3

# 1. Descobre onde o script de setup está (Setup Tabelas e Geral)
caminho_setup = os.path.dirname(os.path.abspath(__file__))

# 2. SOBE UM NÍVEL para a pasta principal (sistema_vendas)
diretorio_projeto = os.path.dirname(caminho_setup)

# 3. Agora sim, monta o caminho no lugar certo
caminho_banco = os.path.join(diretorio_projeto, 'sistema_vendas.db')

print(f"O banco será acessado em: {caminho_banco}")

try:
    # Conecta usando o caminho dinâmico (sem C:/)
    conn = sqlite3.connect(caminho_banco)
    cursor = conn.cursor()

    # cursor.execute("""
    #     CREATE TABLE IF NOT EXISTS retiradas (
    #         id INTEGER PRIMARY KEY AUTOINCREMENT,
    #         id_usuario INTEGER,
    #         data TEXT,
    #         hora TEXT,
    #         valor REAL,
    #         descricao TEXT,
    #         FOREIGN KEY (id_usuario) REFERENCES usuarios (id)
    #     )
    # """)

    ALTER TABLE retirada_caixa ADD COLUMN tipo_evento TEXT;

    
    conn.commit()
    print("✅ Sucesso! Tabela 'retiradas' pronta para uso.")

except sqlite3.OperationalError as e:
    print(f"❌ Erro de permissão ou caminho: {e}")
finally:
    if 'conn' in locals():
        conn.close()
