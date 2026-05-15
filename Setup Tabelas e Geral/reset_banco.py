import sqlite3
import os

def criar_novo_banco():
    # Isso garante que o banco seja criado na MESMA PASTA deste arquivo .py
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_db = os.path.join(diretorio_atual, 'sistema_vendas.db')
    
    print(f"📍 Criando banco em: {caminho_db}")
    
    conn = sqlite3.connect(caminho_db)
    
    sql = """
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT, login TEXT UNIQUE, senha TEXT, status TEXT
    );

    CREATE TABLE IF NOT EXISTS fornecedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT, id_usuario INTEGER,
        nome_empresa TEXT, cnpj TEXT, ddd TEXT, telefone TEXT, 
        email TEXT, contato_pessoa TEXT, endereco TEXT, observacao TEXT,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, id_usuario INTEGER, id_fornecedor INTEGER,
        referencia TEXT, nome_produto TEXT, tamanho TEXT, foto BLOB,
        valor_compra REAL, valor_entrada REAL, num_parcelas INTEGER, valor_parcela REAL,
        data_compra TEXT, data_primeira_parcela TEXT, vendido INTEGER DEFAULT 0,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE RESTRICT,
        FOREIGN KEY (id_fornecedor) REFERENCES fornecedores(id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS fluxo_pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, id_usuario INTEGER, id_produto INTEGER,
        referencia TEXT, num_parcela INTEGER, data_vencimento TEXT, valor_parcela REAL, pago INTEGER DEFAULT 0,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE RESTRICT,
        FOREIGN KEY (id_produto) REFERENCES produtos(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, id_usuario INTEGER,
        nome_cliente TEXT, cpf_cnpj TEXT, ddd TEXT, telefone TEXT, email TEXT,
        endereco TEXT, is_revendedor INTEGER DEFAULT 0, comissao REAL, 
        contato_pessoa TEXT, observacao TEXT,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, id_usuario INTEGER, id_cliente INTEGER,
        id_produto INTEGER, valor_venda REAL, valor_lucro REAL, valor_comissao REAL,
        data_venda TEXT, valor_entrada REAL, num_parcelas INTEGER,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE RESTRICT,
        FOREIGN KEY (id_cliente) REFERENCES clientes(id) ON DELETE RESTRICT,
        FOREIGN KEY (id_produto) REFERENCES produtos(id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS vendas_pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, id_usuario INTEGER, id_venda INTEGER,
        num_parcela INTEGER, data_vencimento TEXT, valor_parcela REAL, pago INTEGER DEFAULT 0,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE RESTRICT,
        FOREIGN KEY (id_venda) REFERENCES vendas(id) ON DELETE CASCADE
    );
    """
    try:
        conn.executescript(sql)
        conn.commit()
        print("✅ Tabelas criadas com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    criar_novo_banco()
