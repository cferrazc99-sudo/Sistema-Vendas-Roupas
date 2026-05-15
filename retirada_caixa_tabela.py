import sqlite3
import os

# 1. Garante que o banco seja modificado na pasta correta do projeto
diretorio_atual = os.path.dirname(os.path.abspath(__file__))

# Se este script estiver dentro de uma subpasta (como 'Setup Tabelas'), descomente a linha abaixo:
# diretorio_atual = os.path.dirname(diretorio_atual) 

caminho_banco = os.path.join(diretorio_atual, 'sistema_vendas.db')


def adicionar_coluna_tipo_evento():
    conn = sqlite3.connect(caminho_banco)
    cursor = conn.cursor()
    
    # Executa o comando SQL corretamente encapsulado em uma string Python
    try:
        cursor.execute("ALTER TABLE retirada_caixa ADD COLUMN tipo_evento TEXT;")
        print("Coluna 'tipo_evento' adicionada com sucesso em retirada_caixa.")
    except sqlite3.OperationalError:
        print("Aviso: A coluna 'tipo_evento' já existe na tabela retirada_caixa.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    adicionar_coluna_tipo_evento()  # Corrigido: removido os dois pontos (:)
