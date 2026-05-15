import streamlit as st
import pandas as pd
from datetime import datetime

def modulo_retirada_recurso(uid_ativo, conectar):
    st.header("🏧 Gestão de Caixa / Retiradas de Recursos")
    
    # Inicializa variáveis de estado para controle de fluxo da interface
    if "edit_retirada_id" not in st.session_state:
        st.session_state.edit_retirada_id = None
    if "expandir_formulario" not in st.session_state:
        st.session_state.expandir_formulario = False

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE BANCO DE DADOS (CRUD)
    # -------------------------------------------------------------------------
    def salvar_retirada(data, hora, valor, descricao, tipo_evento):
        conn = conectar()
        conn.execute(
            "INSERT INTO retirada_caixa (id_usuario, data, hora, valor, descricao, tipo_evento) VALUES (?, ?, ?, ?, ?, ?)",
            (uid_ativo, data, hora, valor, descricao, tipo_evento)
        )
        conn.commit()
        conn.close()

    def atualizar_retirada(id_registro, data, hora, valor, descricao, tipo_evento):
        conn = conectar()
        conn.execute(
            "UPDATE retirada_caixa SET data=?, hora=?, valor=?, descricao=?, tipo_evento=? WHERE id=? AND id_usuario=?",
            (data, hora, valor, descricao, tipo_evento, id_registro, uid_ativo)
        )
        conn.commit()
        conn.close()

    def deletar_retirada(id_registro):
        conn = conectar()
        conn.execute("DELETE FROM retirada_caixa WHERE id=? AND id_usuario=?", (id_registro, uid_ativo))
        conn.commit()
        conn.close()

    # -------------------------------------------------------------------------
    # LEITURA E ORDENAÇÃO DE DADOS (PANDAS)
    # -------------------------------------------------------------------------
    conn = conectar()
    try:
        # df_retiradas = pd.read_sql_query(
        #     "SELECT id, data, hora, 'Retirada' as Evento, descricao as desc, valor FROM retirada_caixa WHERE id_usuario = ?", 
        #     conn, params=(uid_ativo,)
        # )
        # Substitua a query antiga por esta:
        df_retiradas = pd.read_sql_query(
            "SELECT id, data, hora, tipo_evento as tipo, descricao as desc, valor FROM retirada_caixa WHERE id_usuario = ?", 
            conn, params=(uid_ativo,)
        )
        if not df_retiradas.empty:
            df_retiradas = df_retiradas.sort_values(by=["data", "hora"], ascending=[False, False])
    except Exception:
        df_retiradas = pd.DataFrame(columns=['id', 'data', 'hora', 'tipo', 'desc', 'valor'])
    finally:
        conn.close()

    # -------------------------------------------------------------------------
    # 1. SEÇÃO DE AÇÕES (EDITAR E DELETAR) - AGORA EM PRIMEIRO LUGAR
    # -------------------------------------------------------------------------
    if not df_retiradas.empty:
        st.subheader("Modificar Registros")
        c_acao1, c_acao2 = st.columns(2)
        
        with c_acao1:
            # value=None força o campo numérico a iniciar totalmente em branco
            id_editar = st.number_input("ID para Editar", min_value=1, step=1, key="id_ed", value=None)
            if st.button("Carregar para Edição", use_container_width=True):
                if id_editar is not None and id_editar in df_retiradas['id'].values:
                    st.session_state.edit_retirada_id = id_editar
                    st.session_state.expandir_formulario = True # Força a abertura automática do formulário
                    st.rerun()
                else:
                    st.error("ID inválido ou não encontrado.")
                    
        with c_acao2:
            id_deletar = st.number_input("ID para Deletar", min_value=1, step=1, key="id_del", value=None)
            if st.button("Confirmar Exclusão", type="primary", use_container_width=True):
                if id_deletar is not None and id_deletar in df_retiradas['id'].values:
                    deletar_retirada(id_deletar)
                    st.success(f"Registro {id_deletar} removido!")
                    if st.session_state.edit_retirada_id == id_deletar:
                        st.session_state.edit_retirada_id = None
                        st.session_state.expandir_formulario = False
                    st.rerun()
                else:
                    st.error("ID inválido ou não encontrado.")

    # -------------------------------------------------------------------------
    # 2. FORMULÁRIO DE CADASTRO / EDIÇÃO - MOVIDO PARA DEPOIS DE MODIFICAR REGISTROS
    # -------------------------------------------------------------------------
    st.markdown("---")
    
    # O st.toggle substitui o expander permitindo controle de abertura programática via state
    form_visivel = st.toggle("➕ Mostrar Formulário: Lançar / Editar Retirada de Caixa", value=st.session_state.expandir_formulario)
    st.session_state.expandir_formulario = form_visivel

    if form_visivel:
        # Preenchimento condicional dos campos caso esteja em modo edição
        if st.session_state.edit_retirada_id and not df_retiradas.empty:
            row_edit = df_retiradas[df_retiradas['id'] == st.session_state.edit_retirada_id]
            if not row_edit.empty:
                # CORREÇÃO CRÍTICA: Uso correto do .iloc[0] acessando por índice posicional da série
                val_data = datetime.strptime(str(row_edit['data'].iloc[0]), "%Y-%m-%d").date()
                val_hora = datetime.strptime(str(row_edit['hora'].iloc[0]), "%H:%M:%S").time()
                val_valor = float(row_edit['valor'].iloc[0])
                val_desc = str(row_edit['desc'].iloc[0])
                st.info(f"Modo Edição Ativo: Alterando Registro ID {st.session_state.edit_retirada_id}")
            else:
                val_data, val_hora, val_valor, val_desc = datetime.today().date(), datetime.now().time(), 0.0, ""
        else:
            val_data, val_hora, val_valor, val_desc = datetime.today().date(), datetime.now().time(), 0.0, ""

        # O formulário utiliza uma chave dinâmica para forçar a limpeza completa dos dados ao salvar
        # if "form_key_index" not in st.session_state:
        #     st.session_state.form_key_index = 0

        # with st.form(f"form_retirada_{st.session_state.form_key_index}", clear_on_submit=True):
        #     c1, c2, c3 = st.columns(3)
        #     f_data = c1.date_input("Data", value=val_data)
        #     f_hora = c2.time_input("Hora", value=val_hora)
        #     f_valor = c3.number_input("Valor (R$)", min_value=0.0, value=val_valor, step=10.0)
        #     f_desc = st.text_input("Descrição da Retirada", value=val_desc)

        #     c_btn1, c_btn2 = st.columns(2)
        #     sub_btn = c_btn1.form_submit_button("Salvar Registro")

        #     if st.session_state.edit_retirada_id and c_btn2.form_submit_button("Cancelar Edição"):
        #         st.session_state.edit_retirada_id = None
        #         st.session_state.expandir_formulario = False
        #         st.rerun()

        #     if sub_btn:
        #         if f_desc.strip() == "" or f_valor <= 0:
        #             st.error("Preencha uma descrição válida e um valor maior que zero.")
        #         else:
        #             data_str = f_data.strftime("%Y-%m-%d")
        #             hora_str = f_hora.strftime("%H:%M:%S")
                    
        #             if st.session_state.edit_retirada_id:
        #                 atualizar_retirada(st.session_state.edit_retirada_id, data_str, hora_str, f_valor, f_desc)
        #                 st.success("Retirada atualizada com sucesso!")
        #                 st.session_state.edit_retirada_id = None
        #             else:
        #                 salvar_retirada(data_str, hora_str, f_valor, f_desc)
        #                 st.success("Retirada registrada com sucesso!")
                    
        #             # Altera o estado para fechar o formulário e limpar os campos text_input/number_input
        #             st.session_state.expandir_formulario = False
        #             st.session_state.form_key_index += 1
        #             st.rerun()
     # O formulário utiliza uma chave dinâmica para forçar a limpeza completa dos dados ao salvar
        if "form_key_index" not in st.session_state:
            st.session_state.form_key_index = 0

        with st.form(f"form_retirada_{st.session_state.form_key_index}", clear_on_submit=True):
            
            # Se estiver em modo edição, descobre qual era o tipo originalmente selecionado para preencher o padrão
            val_tipo = "Pagamento Revendedor"
            if st.session_state.edit_retirada_id and not df_retiradas.empty:
                if 'tipo' in row_edit.columns and not row_edit['tipo'].empty:
                    val_tipo_banco = str(row_edit['tipo'].iloc[0])
                    if val_tipo_banco in ["Pagamento Revendedor", "Retirada Recurso"]:
                        val_tipo = val_tipo_banco

            # Layout das colunas estendido para acomodar o novo campo
            # c1, c2, c3, c4 = st.columns(4)
            # f_data = c1.date_input("Data", value=val_data)
            # f_hora = c2.time_input("Hora", value=val_hora)
            # f_valor = c3.number_input("Valor (R$)", min_value=0.0, value=val_valor, step=10.0)
            
            # # INCLUSÃO: Campo de seleção posicionado na quarta coluna do formulário
            # lista_opcoes = ["Pagamento Revendedor", "Retirada Recurso"]
            # idx_padrao = lista_opcoes.index(val_tipo) if val_tipo in lista_opcoes else 0
            # tipo_evento_sel = c4.selectbox("Tipo de Evento:", options=lista_opcoes, index=idx_padrao)
            
            # f_desc = st.text_input("Descrição da Retirada", value=val_desc)
            
            # c_btn1, c_btn2 = st.columns(2)
            # sub_btn = c_btn1.form_submit_button("Salvar Registro")
                    # Layout das colunas estendido para acomodar o novo campo
        # 1. Cria as 4 colunas ANTES do formulário para permitir reatividade em tempo real
        # 1. Layout de 4 colunas unificado e reativo
        c1, c2, c3, c4 = st.columns(4)
        
        # 2. Renderização de todos os campos de entrada de dados de forma nativa
        f_data = c1.date_input("Data", value=val_data)
        f_hora = c2.time_input("Hora", value=val_hora)
        f_valor = c3.number_input("Valor (R$)", min_value=0.0, value=val_valor, step=10.0)
        
        lista_opcoes = ["Pagamento Revendedor", "Retirada Recurso"]
        idx_padrao = lista_opcoes.index(val_tipo) if val_tipo in lista_opcoes else 0
        tipo_evento_sel = c4.selectbox("Tipo de Evento:", options=lista_opcoes, index=idx_padrao)
        
        # 3. O campo descrição herda dinamicamente o valor selecionado no selectbox
        f_desc = st.text_input(
            "Descrição da Retirada", 
            value=tipo_evento_sel, 
            disabled=True
        )
        
        # 4. Área de botões de controle de fluxo de ações
        c_btn1, c_btn2 = st.columns(2)
        sub_btn = c_btn1.button("Salvar Registro", use_container_width=True, type="primary")
        
        # Botão de cancelamento visível apenas quando estiver editando um registro existente
        if st.session_state.edit_retirada_id and c_btn2.button("Cancelar Edição", use_container_width=True):
            st.session_state.edit_retirada_id = None
            st.session_state.expandir_formulario = False
            st.rerun()
        
        # 5. Processamento dos dados no clique do botão de salvar
        if sub_btn:
            if f_desc.strip() == "" or f_valor <= 0:
                st.error("Preencha uma descrição válida e um valor maior que zero.")
            else:
                data_str = f_data.strftime("%Y-%m-%d")
                hora_str = f_hora.strftime("%H:%M:%S")
                
                if st.session_state.edit_retirada_id:
                    # Executa a query de atualização no banco de dados
                    atualizar_retirada(st.session_state.edit_retirada_id, data_str, hora_str, f_valor, f_desc, tipo_evento_sel)
                    st.success("Retirada atualizada com sucesso!")
                    st.session_state.edit_retirada_id = None
                else:
                    # Executa a query de inserção de novo registro no banco de dados
                    salvar_retirada(data_str, hora_str, f_valor, f_desc, tipo_evento_sel)
                    st.success("Retirada registrada com sucesso!")
                
                # Reseta o formulário e força a atualização do estado da tela
                st.session_state.expandir_formulario = False
                st.rerun()

    # -------------------------------------------------------------------------
    # 3. HISTÓRICO DE RETIRADAS - POSICIONADO NO FINAL DO MÓDULO
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("📋 Histórico de Retiradas")
    
    if not df_retiradas.empty:
        st.dataframe(
            df_retiradas,
            column_config={
                "id": "ID",
                "data": "Data",
                "hora": "Hora",
                "Evento": "Evento",
                "desc": "Descrição",
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("Nenhuma retirada registrada para este usuário.")
