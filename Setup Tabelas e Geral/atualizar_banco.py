import sqlite3
from database import conectar


def migrar_banco():
    conn = conectar()
    cursor = conn.cursor()

    print("Iniciando atualização do banco de dados...")

    try:
        # Tenta adicionar a coluna faltante na tabela vendas
        cursor.execute("ALTER TABLE vendas ADD COLUMN num_parcelas INTEGER;")
        conn.commit()
        print("Coluna 'num_parcelas' adicionada com sucesso!")

    except sqlite3.OperationalError as e:
        # Evita erro caso a coluna já tenha sido criada antes
        if "duplicate column name" in str(e).lower():
            print("A coluna 'num_parcelas' já existe no banco de dados.")
        else:
            print(f"Erro operacional: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    migrar_banco()


    # # 1. Tenta adicionar colunas que podem estar faltando nos Produtos
    # try:
    #     cursor.execute("ALTER TABLE produtos ADD COLUMN valor_parcela REAL DEFAULT 0.0")
    #     print("- Coluna 'valor_parcela' adicionada em produtos.")
    # except sqlite3.OperationalError:
    #     print("- Coluna 'valor_parcela' já existe.")

    # # 2. Tenta adicionar colunas nos Clientes
    # try:
    #     cursor.execute("ALTER TABLE clientes ADD COLUMN is_revendedor INTEGER DEFAULT 0")
    #     cursor.execute("ALTER TABLE clientes ADD COLUMN comissao REAL DEFAULT 0.0")
    #     print("- Colunas de revenda adicionadas em clientes.")
    # except sqlite3.OperationalError:
    #     print("- Colunas de revenda já existem.")

    # # 3. Garante que a tabela de pagamentos de CLIENTES exista (para a Tab 4 de Vendas)
    # cursor.execute("""
    # CREATE TABLE IF NOT EXISTS vendas_pagamentos (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     id_venda INTEGER,
    #     num_parcela INTEGER,
    #     data_vencimento TEXT,
    #     valor_parcela REAL,
    #     pago INTEGER DEFAULT 0,
    #     FOREIGN KEY (id_venda) REFERENCES vendas (id)
    # )
    # """)
    # print("- Tabela 'vendas_pagamentos' verificada/criada.")

    



    # conn.commit()
    # conn.close()
    print("✅ Banco de dados atualizado com sucesso! Seus dados foram preservados.")

if __name__ == "__main__":
    migrar_banco()
