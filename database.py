import sqlite3
import os
import sys
import sqlite3
import os

def conectar():
    diretorio = os.path.dirname(os.path.abspath(__file__))
    caminho_db = os.path.join(diretorio, 'sistema_vendas.db')
    conn = sqlite3.connect(caminho_db, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;") 
    return conn


def conectar():
    """Conecta ao banco e garante a criação das tabelas"""
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_db = os.path.join(diretorio_atual, 'sistema_vendas.db')
    
    conn = sqlite3.connect(caminho_db, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    # Chama a criação das tabelas toda vez que conecta
    # Se já existirem, ele apenas pula (por causa do IF NOT EXISTS)
    criar_tabelas(conn)
    
    return conn

def criar_tabelas(conn):
    cursor = conn.cursor()

    # 1. FORNECEDORES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fornecedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_empresa TEXT NOT NULL,
        contato TEXT,
        telefone TEXT
    )
    """)

    # 2. CLIENTES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_cliente TEXT NOT NULL,
        telefone TEXT,
        is_revendedor INTEGER DEFAULT 0,
        comissao REAL DEFAULT 0.0
    )
    """)

    # 3. PRODUTOS (Garante o campo 'vendido')
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referencia TEXT,
        nome_produto TEXT NOT NULL,
        tamanho TEXT,
        foto BLOB,
        id_fornecedor INTEGER,
        valor_compra REAL,
        valor_entrada REAL,
        num_parcelas INTEGER,
        valor_parcela REAL,
        data_compra TEXT,
        vendido INTEGER DEFAULT 0, 
        FOREIGN KEY (id_fornecedor) REFERENCES fornecedores (id)
    )
    """)

    # 4. VENDAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_produto INTEGER,
        id_cliente INTEGER,
        valor_venda REAL,
        valor_lucro REAL,
        valor_comissao REAL,
        data_venda TEXT,
        valor_entrada REAL,
        num_parcelas INTEGER,
        FOREIGN KEY (id_produto) REFERENCES produtos (id),
        FOREIGN KEY (id_cliente) REFERENCES clientes (id)
    )
    """)

    # 5. CONTAS A PAGAR (Fornecedores)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fluxo_pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_produto INTEGER,
        referencia TEXT,
        num_parcela INTEGER,
        data_vencimento TEXT,
        valor_parcela REAL,
        pago INTEGER DEFAULT 0,
        FOREIGN KEY (id_produto) REFERENCES produtos (id)
    )
    """)

    # 6. CONTAS A RECEBER (Clientes - ABA FINANCEIRO VENDAS)
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

    conn.commit()

if __name__ == "__main__":
    conectar()
    print("✅ Banco de Dados sincronizado!")
