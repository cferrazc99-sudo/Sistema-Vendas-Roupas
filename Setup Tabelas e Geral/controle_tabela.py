import os
import sqlite3

# 1. Garante que o banco seja criado na pasta do projeto, não na subpasta
diretorio_atual = os.path.dirname(os.path.abspath(__file__))

# Se este script estiver dentro de uma subpasta (como 'Setup Tabelas'), descomente a linha abaixo:
# diretorio_atual = os.path.dirname(diretorio_atual) 

caminho_banco = os.path.join(diretorio_atual, 'sistema_vendas.db')

def inicializar_banco():
    # Conecta ao banco de dados físico no caminho configurado acima
    conexao = sqlite3.connect(caminho_banco)
    cursor = conexao.cursor()

    print(f"⚡ Conectado ao banco de dados em: {caminho_banco}")


    # -------------------------------------------------------------------------
    # 4. CRIAÇÃO DOS TRIGGERS DE INTEGRIDADE (RESTRIÇÕES DE EXCLUSÃO)
    # -------------------------------------------------------------------------
    
    # Regra 1: Não permite excluir cliente se houver vendas vinculadas
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS impedir_excluir_cliente_com_venda
    BEFORE DELETE ON clientes
    FOR EACH ROW
    BEGIN
        SELECT CASE 
            WHEN (SELECT 1 FROM vendas WHERE id_cliente = OLD.id LIMIT 1) IS NOT NULL 
            THEN RAISE(ABORT, 'Erro de Integridade: Não é possível excluir um cliente com vendas vinculadas.')
        END;
    END;
    """)

    # Regra 2: Não permite excluir produto se houver vínculo em vendas ou fluxo de pagamentos
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS impedir_excluir_produto_vinculado
    BEFORE DELETE ON produtos
    FOR EACH ROW
    BEGIN
        SELECT CASE 
            WHEN (SELECT 1 FROM vendas WHERE id_produto = OLD.id LIMIT 1) IS NOT NULL 
            THEN RAISE(ABORT, 'Erro de Integridade: Não é possível excluir um produto vinculado a uma venda.')
            WHEN (SELECT 1 FROM fluxo_pagamentos WHERE id_produto = OLD.id LIMIT 1) IS NOT NULL 
            THEN RAISE(ABORT, 'Erro de Integridade: Não é possível excluir um produto vinculado a um fluxo de pagamentos.')
        END;
    END;
    """)

    # Regra 3: Não permite excluir fluxo_pagamentos se o campo 'pago' for igual a 1
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS impedir_excluir_fluxo_pago
    BEFORE DELETE ON fluxo_pagamentos
    FOR EACH ROW
    BEGIN
        SELECT CASE 
            WHEN OLD.pago = 1 
            THEN RAISE(ABORT, 'Erro de Integridade: Não é possível excluir um fluxo de pagamento que já foi pago.')
        END;
    END;
    """)

    # Regra 4: Não permite excluir fornecedor se houver produtos cadastrados para ele
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS impedir_excluir_fornecedor_com_produto
    BEFORE DELETE ON fornecedores
    FOR EACH ROW
    BEGIN
        SELECT CASE 
            WHEN (SELECT 1 FROM produtos WHERE id_fornecedor = OLD.id LIMIT 1) IS NOT NULL 
            THEN RAISE(ABORT, 'Erro de Integridade: Não é possível excluir um fornecedor com produtos vinculados.')
        END;
    END;
    """)

    # Regra 5: Não permite excluir vendas se houver parcelas pagas (pago = 1) em vendas_pagamentos
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS impedir_excluir_venda_com_parcela_paga
    BEFORE DELETE ON vendas
    FOR EACH ROW
    BEGIN
        SELECT CASE 
            WHEN (SELECT 1 FROM vendas_pagamentos WHERE id_venda = OLD.id AND pago = 1 LIMIT 1) IS NOT NULL 
            THEN RAISE(ABORT, 'Erro de Integridade: Não é possível excluir uma venda que possui parcelas pagas.')
        END;
    END;
    """)

    print("- Gatilhos de integridade e regras de negócio gerados.")
    
    # Salva as alterações e fecha a conexão
    conexao.commit()
    conexao.close()
    print("🚀 Script finalizado com sucesso no VS Code!")

if __name__ == "__main__":
    inicializar_banco()
