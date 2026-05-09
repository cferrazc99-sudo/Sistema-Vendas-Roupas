from database import conectar
import sqlite3

def migrar_banco():
    conn = conectar()
    cursor = conn.cursor()
    
    print("Iniciando atualização do banco de dados...")

    # 1. Tenta adicionar colunas que podem estar faltando nos Produtos
    try:
        cursor.execute("ALTER TABLE produtos ADD COLUMN valor_parcela REAL DEFAULT 0.0")
        print("- Coluna 'valor_parcela' adicionada em produtos.")
    except sqlite3.OperationalError:
        print("- Coluna 'valor_parcela' já existe.")

    # 2. Tenta adicionar colunas nos Clientes
    try:
        cursor.execute("ALTER TABLE clientes ADD COLUMN is_revendedor INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE clientes ADD COLUMN comissao REAL DEFAULT 0.0")
        print("- Colunas de revenda adicionadas em clientes.")
    except sqlite3.OperationalError:
        print("- Colunas de revenda já existem.")

    # 3. Garante que a tabela de pagamentos de CLIENTES exista (para a Tab 4 de Vendas)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendas_pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_venda INTEGER,
        num_parcela INTEGER,
        data_vencimento TEXT,
        valor_parcela REAL,
        pago INTEGER DEFAULT 0,
        FOREIGN KEY (id_venda) REFERENCES vendas (id)
    )
    """)
    print("- Tabela 'vendas_pagamentos' verificada/criada.")

    conn.commit()
    conn.close()
    print("✅ Banco de dados atualizado com sucesso! Seus dados foram preservados.")

if __name__ == "__main__":
    migrar_banco()
