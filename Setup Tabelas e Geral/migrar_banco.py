import sqlite3
import os

# Pega o caminho da pasta onde o script está salvo
diretorio = os.path.dirname(os.path.abspath(__file__))

# Nomes exatos dos arquivos (confira se o seu backup tem esse nome mesmo!)
arquivo_antigo = os.path.join(diretorio, 'sistema_vendas_BACKUP.db')
arquivo_novo = os.path.join(diretorio, 'sistema_vendas.db')

print(f"🔍 Buscando dados em: {arquivo_antigo}")
print(f"🎯 Gravando dados em: {arquivo_novo}")

# Verifica se o arquivo de backup realmente existe antes de continuar
if not os.path.exists(arquivo_antigo):
    print(f"❌ ERRO: O arquivo {arquivo_antigo} não foi encontrado!")
    print("Verifique se o nome do arquivo no Finder é exatamente 'sistema_vendas_BACKUP.db'")
else:
    conn_antigo = sqlite3.connect(arquivo_antigo)
    conn_novo = sqlite3.connect(arquivo_novo)
    # ... resto do seu código de migração ...
