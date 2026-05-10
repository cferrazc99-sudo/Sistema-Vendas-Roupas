import sqlite3
import os

def conectar():
    """Estabelece conexão com o banco de dados SQLite usando caminho absoluto dinâmico"""
    # Descobre o caminho da pasta onde este arquivo (database.py) está localizado
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    
    # Monta o caminho completo para o arquivo .db dentro da mesma pasta
    caminho_db = os.path.join(diretorio_atual, 'sistema_vendas.db')
    
    # Conecta ao banco de dados usando o caminho absoluto encontrado
    conn = sqlite3.connect(caminho_db, check_same_thread=False)
    
    # Habilita o acesso por nome de coluna (Row Factory)
    conn.row_factory = sqlite3.Row
    
    # Garante que as tabelas existam
    criar_tabelas(conn)
    
    return conn

def criar_tabelas(conn):
    cursor = conn.cursor()

    # 1. TABELA DE FORNECEDORES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fornecedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_empresa TEXT NOT NULL,
        contato TEXT,
        telefone TEXT
    )
    """)

    # 2. TABELA DE CLIENTES (Com regra de revenda e comissão)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_cliente TEXT NOT NULL,
        telefone TEXT,
        is_revendedor INTEGER DEFAULT 0, -- 0=Não, 1=Sim
        comissao REAL DEFAULT 0.0        -- % de comissão se for revendedor
    )
    """)

    # 3. TABELA DE PRODUTOS (Auditoria e Trava de Vendido)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referencia TEXT,
        nome_produto TEXT NOT NULL,
        tamanho TEXT,
        foto BLOB,
        id_fornecedor INTEGER,
        valor_compra REAL,     -- Preço de Custo
        valor_entrada REAL,    -- Entrada paga ao fornecedor
        num_parcelas INTEGER,
        valor_parcela REAL,
        data_compra TEXT,
        vendido INTEGER DEFAULT 0, -- 0=Estoque, 1=Vendido
        FOREIGN KEY (id_fornecedor) REFERENCES fornecedores (id)
    )
    """)

    # 4. TABELA DE VENDAS (Cabeçalho da Venda e Lucro)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_produto INTEGER,
        id_cliente INTEGER,
        valor_venda REAL,
        valor_lucro REAL,
        valor_comissao REAL,    -- Valor de revenda/comissão
        data_venda TEXT,
        valor_entrada REAL,     -- Entrada paga pelo cliente
        num_parcelas INTEGER,
        FOREIGN KEY (id_produto) REFERENCES produtos (id),
        FOREIGN KEY (id_cliente) REFERENCES clientes (id)
    )
    """)

    # 5. FLUXO FINANCEIRO: PAGAMENTOS AO FORNECEDOR (Contas a Pagar)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fluxo_pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_produto INTEGER,
        referencia TEXT,
        num_parcela INTEGER,
        data_vencimento TEXT,
        valor_parcela REAL,
        pago INTEGER DEFAULT 0, -- 0=Não, 1=Sim
        FOREIGN KEY (id_produto) REFERENCES produtos (id)
    )
    """)

    # 6. FLUXO FINANCEIRO: RECEBIMENTOS DE CLIENTES (Contas a Receber)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendas_pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_venda INTEGER,
        num_parcela INTEGER,
        data_vencimento TEXT,
        valor_parcela REAL,
        pago INTEGER DEFAULT 0, -- 0=Não, 1=Sim
        FOREIGN KEY (id_venda) REFERENCES vendas (id)
    )
    """)

    conn.commit()

# Exemplo de uso para inicializar o banco se rodar este arquivo diretamente
if __name__ == "__main__":
    conectar()
    print("✅ Banco de Dados e Tabelas sincronizados com sucesso!")
