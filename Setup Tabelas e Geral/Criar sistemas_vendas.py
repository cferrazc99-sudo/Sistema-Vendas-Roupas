import sqlite3

def recriar_banco(nome_banco="sistema_vendas.db"):
    # Estabelece conexão com o banco de dados
    conn = sqlite3.connect(nome_banco)
    cursor = conn.cursor()
    
    try:
        print("⏳ Iniciando a reconstrução do banco de dados...")
        
        # Desativa temporariamente as chaves estrangeiras para permitir o DROP de tabelas interligadas
        cursor.execute("PRAGMA foreign_keys = OFF;")
        
        # 1. REMOÇÃO DAS TABELAS ANTIGAS (Ordem segura)
        cursor.execute("DROP TABLE IF EXISTS vendas_pagamentos;")
        cursor.execute("DROP TABLE IF EXISTS fluxo_pagamentos;")
        cursor.execute("DROP TABLE IF EXISTS vendas;")
        cursor.execute("DROP TABLE IF EXISTS produtos;")
        cursor.execute("DROP TABLE IF EXISTS retiradas;")
        cursor.execute("DROP TABLE IF EXISTS fornecedores;")
        cursor.execute("DROP TABLE IF EXISTS clientes;")
        cursor.execute("DROP TABLE IF EXISTS usuarios;")
        print("- Tabelas antigas deletadas com sucesso.")

        # Reativa as chaves estrangeiras para a criação correta dos relacionamentos
        cursor.execute("PRAGMA foreign_keys = ON;")

        # 2. CRIAÇÃO DAS NOVAS TABELAS COM INTEGRIDADE DEFINITIVA
        
        # Tabela: usuarios
        cursor.execute("""
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                login TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL,
                status TEXT NOT NULL
            );
        """)
        print("- Tabela 'usuarios' verificada/criada.")

        # Tabela: clientes
        cursor.execute("""
            CREATE TABLE clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario INTEGER NOT NULL,
                nome_cliente TEXT NOT NULL,
                cpf_cnpj TEXT,
                ddd TEXT,
                telefone TEXT UNIQUE,
                email TEXT UNIQUE,
                contato_pessoa TEXT,
                endereco TEXT,
                observacao TEXT,
                is_revendedor INTEGER DEFAULT 0,
                comissao REAL,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE RESTRICT
            );
        """)
        print("- Tabela 'clientes' verificada/criada.")

        # Tabela: fornecedores
        cursor.execute("""
            CREATE TABLE fornecedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario INTEGER NOT NULL,
                nome_empresa TEXT NOT NULL,
                cnpj TEXT,
                ddd TEXT,
                telefone TEXT,
                email TEXT,
                contato_pessoa TEXT,
                endereco TEXT,
                observacao TEXT,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE RESTRICT
            );
        """)
        print("- Tabela 'fornecedores' verificada/criada.")

        # Tabela: produtos (Fiel ao print do seu banco)
        cursor.execute("""
            CREATE TABLE produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario INTEGER NOT NULL,
                referencia TEXT,
                nome_produto TEXT NOT NULL,
                tamanho TEXT,
                foto BLOB,
                id_fornecedor INTEGER NOT NULL,
                valor_compra REAL,
                valor_entrada REAL,
                num_parcelas INTEGER,
                valor_parcela REAL,
                data_compra TEXT,
                vendido INTEGER DEFAULT 0,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE RESTRICT,
                FOREIGN KEY (id_fornecedor) REFERENCES fornecedores(id) ON DELETE RESTRICT
            );
        """)
        print("- Tabela 'produtos' verificada/criada.")

        # Tabela: fluxo_pagamentos
        cursor.execute("""
            CREATE TABLE fluxo_pagamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario INTEGER NOT NULL,
                id_produto INTEGER NOT NULL,
                referencia TEXT,
                num_parcela INTEGER,
                data_vencimento TEXT,
                valor_parcela REAL,
                pago INTEGER DEFAULT 0,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE RESTRICT,
                FOREIGN KEY (id_produto) REFERENCES produtos(id) ON DELETE CASCADE
            );
        """)
        print("- Tabela 'fluxo_pagamentos' verificada/criada.")

        # Tabela: retiradas
        cursor.execute("""
            CREATE TABLE retiradas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario INTEGER NOT NULL,
                data TEXT,
                hora TEXT,
                valor REAL,
                descricao TEXT,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE RESTRICT
            );
        """)
        print("- Tabela 'retiradas' verificada/criada.")

        # Tabela: vendas
        cursor.execute("""
            CREATE TABLE vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario INTEGER NOT NULL,
                id_produto INTEGER NOT NULL,
                id_cliente INTEGER NOT NULL,
                valor_venda REAL,
                valor_lucro REAL,
                valor_comissao REAL,
                data_venda TEXT,
                valor_entrada REAL,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE RESTRICT,
                FOREIGN KEY (id_produto) REFERENCES produtos(id) ON DELETE RESTRICT,
                FOREIGN KEY (id_cliente) REFERENCES clientes(id) ON DELETE RESTRICT
            );
        """)
        print("- Tabela 'vendas' verificada/criada.")

        # Tabela: vendas_pagamentos
        cursor.execute("""
            CREATE TABLE vendas_pagamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario INTEGER NOT NULL,
                id_venda INTEGER NOT NULL,
                num_parcela INTEGER,
                data_vencimento TEXT,
                valor_parcela REAL,
                pago INTEGER DEFAULT 0,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE RESTRICT,
                FOREIGN KEY (id_venda) REFERENCES vendas(id) ON DELETE CASCADE
            );
        """)
        print("- Tabela 'vendas_pagamentos' verificada/criada.")

        # 3. CRIAÇÃO DOS ÍNDICES DE PERFORMANCE
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientes_usuario ON clientes(id_usuario);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fornecedores_usuario ON fornecedores(id_usuario);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_produtos_usuario ON produtos(id_usuario);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_produtos_fornecedor ON produtos(id_fornecedor);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendas_cliente ON vendas(id_cliente);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendas_produto ON vendas(id_produto);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendas_pag_venda ON vendas_pagamentos(id_venda);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fluxo_produto ON fluxo_pagamentos(id_produto);")
        print("- Índices de busca e performance gerados.")

        # Confirma as alterações no arquivo físico do banco de dados
        conn.commit()
        print("✅ Banco de dados atualizado com sucesso!")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ Erro crítico ao reconstruir o banco de dados: {e}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    recriar_banco()
