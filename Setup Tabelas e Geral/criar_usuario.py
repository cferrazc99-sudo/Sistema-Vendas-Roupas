import sqlite3
import os

# 1. Garante que o banco seja criado na pasta do projeto, não na subpasta
diretorio_atual = os.path.dirname(os.path.abspath(__file__))

# Se este script estiver dentro de uma subpasta (como 'Setup Tabelas'), descomente a linha abaixo:
# diretorio_atual = os.path.dirname(diretorio_atual) 

caminho_banco = os.path.join(diretorio_atual, 'sistema_vendas.db')

def criar_tabela_usuarios():
    try:
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()

        # Criando a tabela conforme solicitado
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                login TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)

        # Criando um usuário administrador padrão (caso não exista)
        cursor.execute("""
            INSERT OR IGNORE INTO usuarios (nome, login, senha, status)
            VALUES ('Administrador', 'admin', '1234', 'Ativo')
        """)

        conn.commit()
        print(f"✅ Tabela 'usuarios' verificada/criada com sucesso em: {caminho_banco}")
        print("👤 Usuário padrão: login 'admin' | senha '1234'")

    except sqlite3.Error as e:
        print(f"❌ Erro ao criar tabela: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    criar_tabela_usuarios()


conn = sqlite3.connect('sistema_vendas.db')
cursor = conn.cursor()

try:
    # Ajuste os dados abaixo com o seu nome e login preferido
    cursor.execute("""
        INSERT INTO usuarios (id, nome, login, senha, status) 
        VALUES (1, 'Administrador', 'admin', '1234', 'Ativo')
    """)
    conn.commit()
    print("✅ Usuário administrador criado com ID 1!")
except sqlite3.IntegrityError:
    print("ℹ️ O usuário já existe no banco.")
finally:
    conn.close()
