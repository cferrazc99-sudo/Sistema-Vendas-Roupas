import streamlit as st

def modulo_pessoas():
    # Criando as abas conforme a imagem image_ff23b7.png
    tab_clientes, tab_fornecedores = st.tabs(["👤 Clientes", "🏭 Fornecedores"])

    # --- ABA DE CLIENTES ---
    with tab_clientes:
        st.subheader("Cadastro de Clientes")
        
        # Note: Removido o 'with st.form' para permitir a reatividade do campo comissão
        # Se preferir usar formulário, a comissão só apareceria após um refresh. 
        # Sem o st.form a experiência de "aparecer ao clicar" é instantânea.
        
        nome_cliente = st.text_input("Nome do Cliente*")

        # Linha 1: CPF/CNPJ, DDD e Telefone
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            cpf_cnpj = st.text_input("CPF / CNPJ")
        with col2:
            ddd = st.text_input("DDD", max_chars=2)
        with col3:
            telefone = st.text_input("Telefone")

        # Linha 2: Email e Contato
        col4, col5 = st.columns(2)
        with col4:
            email = st.text_input("E-mail")
        with col5:
            contato_pessoa = st.text_input("Contato")

        # Linha 3: Endereço
        endereco = st.text_input("Endereço")

        # Linha 4: Revendedor e Comissão (Condicional)
        col6, col7 = st.columns(2)
        with col6:
            is_revendedor = st.checkbox("É Revendedor?")
        
        with col7:
            # O campo só aparece se is_revendedor for True
            comissao = 0
            if is_revendedor:
                comissao = st.number_input("Comissão (%)", min_value=0, step=1, value=0)

        # Linha 5: Observação
        observacao = st.text_area("Observação")

        if st.button("Salvar Cliente"):
            if nome_cliente:
                # Aqui você salva no banco. Se is_revendedor for False, comissao será 0.
                st.success(f"Cliente {nome_cliente} salvo com sucesso!")
            else:
                st.error("O campo 'Nome do Cliente' é obrigatório.")

    # --- ABA DE FORNECEDORES ---
    with tab_fornecedores:
        st.subheader("Cadastro de Fornecedores")
        # Mantendo sua estrutura de fornecedores aqui...
        nome_fornecedor = st.text_input("Nome do Fornecedor*")
        if st.button("Salvar Fornecedor"):
            st.success("Fornecedor salvo!")