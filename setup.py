from database import conectar

def carga_inicial():
    conn = conectar()
    cursor = conn.cursor()
    
    # 1. Cadastra um Fornecedor de Teste (Libera o Compras.py)
    cursor.execute("INSERT INTO fornecedores (nome_empresa, contato) VALUES ('Fornecedor Padrão', 'Geral')")
    
    # 2. Cadastra um Cliente de Teste (Libera o Vendas.py)
    cursor.execute("INSERT INTO clientes (nome_cliente, is_revendedor, comissao) VALUES ('Cliente Final', 0, 0.0)")
    
    conn.commit()
    conn.close()
    print("✅ Dados básicos inseridos! Agora as listas vão aparecer.")

if __name__ == "__main__":
    carga_inicial()
