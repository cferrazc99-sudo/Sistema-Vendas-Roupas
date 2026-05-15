import sqlite3
import os

# 1. Garante que o banco seja criado na pasta do projeto, não na subpasta
diretorio_atual = os.path.dirname(os.path.abspath(__file__))

# Se este script estiver dentro de uma subpasta (como 'Setup Tabelas'), descomente a linha abaixo:
# diretorio_atual = os.path.dirname(diretorio_atual) 

caminho_banco = os.path.join(diretorio_atual, 'sistema_vendas.db')

def limpar_banco_dados():
    caminho_banco = "sistema_vendas.db"
    
    try:
        # Abre a conexão com o banco de dados
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        
        # ⚠️ PASSO CRÍTICO: Desativa a checagem de chaves estrangeiras temporariamente
        cursor.execute("PRAGMA foreign_keys = OFF;")
        
        # Lista exata das tabelas visíveis na imagem do seu banco de dados
        tabelas = [
            "fluxo_pagamentos",
            "vendas_pagamentos",
            "vendas",
            "retirada_caixa",
            "retiradas",
            "produtos",
            "fornecedores",
            "clientes",
            "usuarios"
        ]
        
        print("🧼 Iniciando a limpeza das tabelas...")
        
        for tabela in tabelas:
            try:
                # Remove todos os dados da tabela
                cursor.execute(f"DELETE FROM {tabela};")
                
                # Zera os contadores de ID autoincremento para começarem do 1 novamente
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{tabela}';")
                
                print(f"✅ Dados da tabela '{tabela}' removidos com sucesso.")
            except sqlite3.OperationalError as e:
                # Ignora caso alguma tabela listada ainda não tenha sido criada no banco
                print(f"⚠️ Alerta na tabela '{tabela}': {e}")
        
        # Reativa a checagem de segurança de chaves estrangeiras
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Salva as alterações definitivamente no arquivo .db
        conn.commit()
        print("\n✨ Banco de dados limpo com sucesso! Todos os IDs foram resetados.")
        
        # Criando um usuário administrador padrão (caso não exista)
        cursor.execute("""
            INSERT OR IGNORE INTO usuarios (nome, login, senha, status)
            VALUES ('Administrador', 'admin', '1234', 'Ativo')
        """)

        conn.commit()
        print(f"✅ Tabela 'usuarios' verificada/criada com sucesso em: {caminho_banco}")
        print("👤 Usuário padrão: login 'admin' | senha '1234'")
        
    except Exception as e:
        print(f"❌ Erro ao tentar limpar o banco de dados: {e}")
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    limpar_banco_dados()
