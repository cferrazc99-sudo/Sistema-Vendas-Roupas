import streamlit as st
# 1. CONFIGURAÇÃO DE LAYOUT (Deve ser a primeira linha)
st.set_page_config(
    page_title="Sistema de Gestão", 
    layout="wide", 
    page_icon="💎",
    initial_sidebar_state="expanded"
)
import time
import vendas
import compras
import clientes
import fornecedores
import gestao_caixa 
import pandas as pd
from database import conectar

# CSS Original preservado
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        max-width: 98% !important;
        padding-top: 2rem !important;
        padding-right: 1.5rem !important;
        padding-left: 1.5rem !important;
        padding-bottom: 1rem !important;
    }
    [data-testid="stAppViewContainer"] > .main {
        width: 100vw !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE AUTENTICAÇÃO ---
def autenticar(login, senha):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM usuarios WHERE login = ? AND senha = ? AND status = 'ativo'", (login, senha))
    usuario = cursor.fetchone()
    conn.close()
    return usuario

def gestao_usuarios():
    st.write("DEBUG: A função de gestão foi chamada!") # <--- Adicione isso
    st.subheader("👥 Gestão de Assinantes (Acesso Admin)")
    conn = conectar()

    # 1. Inicializa o contador de reset no topo da página se ele não existir
    if "key_cadastro_user" not in st.session_state:
        st.session_state.key_cadastro_user = 0

    with st.expander("➕ Cadastrar Novo Assinante", expanded=False):
        # 2. Vincula a chave dinâmica ao formulário
        with st.form(f"novo_user_{st.session_state.key_cadastro_user}"):
            novo_nome = st.text_input("Nome Completo")
            novo_login = st.text_input("Login de Acesso")
            nova_senha = st.text_input("Senha Inicial", type="password")
            
            if st.form_submit_button("Finalizar Cadastro"):
                if not novo_nome or not novo_login or not nova_senha:
                    st.warning("⚠️ Todos os campos são obrigatórios.")
                else:
                    try:
                        conn.execute(
                            "INSERT INTO usuarios (nome, login, senha, status) VALUES (?,?,?,?)", 
                            (novo_nome, novo_login, nova_senha, "ativo")
                        )
                        conn.commit()
                        st.success(f"Usuário {novo_nome} cadastrado!")
                        
                        # 🚀 A MÁGICA AQUI: Mudar a chave força o Streamlit a destruir o 
                        # formulário antigo e desenhar um novo com todos os campos limpos.
                        st.session_state.key_cadastro_user += 1
                        
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        # Captura erros reais caso a inserção falhe (como login duplicado)
                        st.error("Erro: Este login já existe.")


    # --- 2. TABELA DE USUÁRIOS ATIVOS ---
    st.divider()
    st.write("### Assinantes Cadastrados")
    df_u = pd.read_sql_query("SELECT id, nome, login, status FROM usuarios", conn)
    st.dataframe(df_u, use_container_width=True)

    # --- 3. AÇÕES DE BLOQUEIO E EXCLUSÃO ---
    st.write("### 🛠 Painel de Controle")
    # Criamos uma lista de nomes para o seletor
    lista_nomes = df_u['nome'].tolist()
    user_sel = st.selectbox("Selecione um usuário para gerenciar:", lista_nomes)
    
    # Pegamos os dados do usuário escolhido no DataFrame
    dados_sel = df_u[df_u['nome'] == user_sel].iloc[0]
    u_id = int(dados_sel['id'])
    u_status = dados_sel['status']

    c1, c2, c3 = st.columns(3)
    
    # Botão de Bloqueio/Ativação
    if u_status == 'ativo':
        if c1.button(f"🚫 Bloquear {user_sel}", use_container_width=True):
            conn.execute("UPDATE usuarios SET status = 'suspenso' WHERE id = ?", (u_id,))
            conn.commit(); st.rerun()
    else:
        if c1.button(f"✅ Reativar {user_sel}", use_container_width=True):
            conn.execute("UPDATE usuarios SET status = 'ativo' WHERE id = ?", (u_id,))
            conn.commit(); st.rerun()

    # Botão de Reset de Senha
    if c2.button("🔑 Reset para '123'", use_container_width=True):
        conn.execute("UPDATE usuarios SET senha = '123' WHERE id = ?", (u_id,))
        conn.commit(); st.info("Senha resetada para 123")

    # Botão de Exclusão
    if c3.button("🗑️ EXCLUIR CONTA", type="primary", use_container_width=True):
        if u_id == 1:
            st.error("O Administrador Mestre não pode ser excluído.")
        else:
            conn.execute("DELETE FROM usuarios WHERE id = ?", (u_id,))
            conn.commit(); st.warning("Usuário removido."); time.sleep(1); st.rerun()

    conn.close() # <--- O fechamento fica aqui, no final de TUDO.


def main():
    # Inicializa estados de sessão

    if 'v_reset_key' not in st.session_state:
        st.session_state.v_reset_key = 0

    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
        st.session_state.usuario_id = None
        st.session_state.usuario_nome = ""

    # --- TELA DE LOGIN ---
    if not st.session_state.autenticado:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown("<h2 style='text-align: center;'>💎 Login do Assinante</h2>", unsafe_allow_html=True)
            with st.form("login_form"):
                user = st.text_input("Usuário")
                password = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar", use_container_width=True):
                    dados = autenticar(user, password)
                    if dados:
                        st.session_state.autenticado = True
                        st.session_state.usuario_id = dados[0]
                        st.session_state.usuario_nome = dados[1]
                        st.success("Acesso autorizado!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Usuário ou senha inválidos.")
        return # Interrompe a execução para não mostrar o menu abaixo


        # --- MENU LATERAL (APÓS LOGIN) ---
    st.sidebar.title("💎 Navegação")
    
    # Exibe nome do usuário original
    st.sidebar.write(f"👤 Logado como: **{st.session_state.usuario_nome}**")
    
    # --- NOVO: MODO SIMULAÇÃO PARA ADMIN ---
    if st.session_state.usuario_id == 1: # ID 1 é o seu admin
        st.sidebar.divider()
        st.sidebar.subheader("🛠 Modo Administrador")
        
        conn = conectar()
        df_usuarios = pd.read_sql_query("SELECT id, nome FROM usuarios WHERE status = 'ativo'", conn)
        conn.close()

        # Seletor de qual usuário simular
        lista_usuarios = {row['nome']: row['id'] for _, row in df_usuarios.iterrows()}
        nome_selecionado = st.sidebar.selectbox("Simular Visão de:", list(lista_usuarios.keys()))
        
        # O ID que será usado nos módulos será o do usuário selecionado aqui
        # uid_ativo = lista_usuarios[nome_selecionado]
        # Verifique se o nome_selecionado realmente existe antes de acessar o dicionário
        if nome_selecionado is not None and nome_selecionado in lista_usuarios:
            uid_ativo = lista_usuarios[nome_selecionado]
        else:
            # Se não houver ninguém selecionado, usa o ID do estado da sessão
            uid_ativo = st.session_state.get('usuario_id', None)

        # Só chama o restante do sistema se tivermos um ID válido
        # if uid_ativo:
        #     vendas.modulo_vendas(uid_ativo)

        if uid_ativo != 1:
            st.sidebar.warning(f"👁 Visualizando como: {nome_selecionado}")
    else:
        # Se não for admin, o UID ativo é o dele mesmo
        uid_ativo = st.session_state.usuario_id

    if st.sidebar.button("🚪 Sair", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()
    
        # 1. Botão que abre o formulário no menu lateral
    if st.sidebar.button("⚙️ Alterar Minha Senha", use_container_width=True):
        st.session_state.abrir_modal_senha = True

    # 2. O formulário de alteração (só aparece se o botão acima for clicado)
    if st.session_state.get('abrir_modal_senha', False):
        st.sidebar.divider()
        with st.sidebar.form("form_troca_senha_usuario"):
            st.write("🔒 **Trocar Senha**")
            senha_atual = st.text_input("Senha Atual", type="password")
            nova_senha = st.text_input("Nova Senha", type="password")
            confirma = st.text_input("Confirme a Nova", type="password")
            
            if st.form_submit_button("💾 Salvar", use_container_width=True):
                conn = conectar()
                # Verifica se a senha atual (que você resetou para 123) está correta
                check = conn.execute("SELECT 1 FROM usuarios WHERE id=? AND senha=?", 
                                    (st.session_state.usuario_id, senha_atual)).fetchone()
                
                if not check:
                    st.error("Senha atual incorreta!")
                elif nova_senha != confirma:
                    st.error("As senhas não coincidem!")
                elif len(nova_senha) < 3:
                    st.error("Senha muito curta!")
                else:
                    conn.execute("UPDATE usuarios SET senha = ? WHERE id = ?", 
                                (nova_senha, st.session_state.usuario_id))
                    conn.commit()
                    st.success("Senha alterada!")
                    st.session_state.abrir_modal_senha = False
                    time.sleep(1)
                    st.rerun()
                conn.close()
        
        if st.sidebar.button("❌ Cancelar"):
            st.session_state.abrir_modal_senha = False
            st.rerun()

    st.sidebar.divider()
    
    # # O restante do menu continua igual, mas usamos o 'uid_ativo' nas chamadas
    # menu = st.sidebar.radio(
    #     "Selecione o Módulo:",
    #     ["💰 Vendas", "📦 Estoque & Compras", "👥 Clientes & Fornecedores"]
    # )

     # 1. Definimos as opções que TODO MUNDO vê
    opcoes_menu = ["💰 Vendas", "📦 Estoque & Compras", "👥 Clientes & Fornecedores",  "🏧 Gestão de Caixa" ]
    
    # 2. Se for você (admin), adicionamos a opção secreta no final da lista
    if st.session_state.usuario_id == 1:
        opcoes_menu.append("⚙️ Gestão de Assinantes")

    # 3. Criamos o menu usando a lista que acabamos de montar
    menu = st.sidebar.radio("Selecione o Módulo:", opcoes_menu)


    if menu == "💰 Vendas":
        vendas.modulo_vendas(uid_ativo) # <--- Aqui usamos o ID simulado
        
    elif menu == "📦 Estoque & Compras":
        compras.modulo_compras(uid_ativo)
        
    elif menu == "👥 Clientes & Fornecedores":
        st.sidebar.subheader("Submenu")
        submenu = st.sidebar.radio("Selecione a Opção:", ["Clientes", "Fornecedores"], key="submenu_pessoas")
        
        if submenu == "Clientes":
            clientes.modulo_clientes(uid_ativo)
        else:
            fornecedores.modulo_fornecedores(uid_ativo)
    elif menu == "⚙️ Gestão de Assinantes":
        gestao_usuarios() # <--- Chama a função de gestão
    elif menu == "🏧 Gestão de Caixa":
        gestao_caixa.modulo_gestao_caixa(uid_ativo)

if __name__ == "__main__":
    main()
