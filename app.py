import streamlit as st
import vendas
import compras
import clientes
import fornecedores  # 1. Importação do novo arquivo

# CONFIGURAÇÃO DE LAYOUT
st.set_page_config(
    page_title="Sistema de Gestão", 
    layout="wide", 
    page_icon="💎",
    initial_sidebar_state="expanded"
)

# CSS (Mantido conforme seu original)
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

def main():
    # Menu Lateral Principal
    st.sidebar.title("💎 Navegação")
    menu = st.sidebar.radio(
        "Selecione o Módulo:",
        ["💰 Vendas", "📦 Estoque & Compras", "👥 Clientes & Fornecedores"],
        index=0
    )

    st.sidebar.divider()

    # Chamada dos Módulos
    if menu == "💰 Vendas":
        vendas.modulo_vendas()
        
    elif menu == "📦 Estoque & Compras":
        compras.modulo_compras()
        
    elif menu == "👥 Clientes & Fornecedores":
        # 4. SUBMENU: Aparece apenas quando "Clientes & Fornecedores" está selecionado
        st.sidebar.subheader("Submenu")
        submenu = st.sidebar.radio(
            "Selecione a Opção:",
            ["Clientes", "Fornecedores"],
            key="submenu_pessoas"
        )
        
        st.sidebar.divider()

        # Lógica para chamar cada arquivo separado
        if submenu == "Clientes":
            # 2. Chama a função no arquivo clientes.py
            clientes.modulo_clientes()
        else:
            # 3. Chama a função no arquivo fornecedores.py
            fornecedores.modulo_fornecedores()

    st.sidebar.caption("Usuário: Administrador")

if __name__ == "__main__":
    main()