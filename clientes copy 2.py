import streamlit as st
import pandas as pd
import time
import re
from database import conectar
import sqlite3

def validar_email(email):
    """Valida se o email possui o formato básico com @ e um domínio."""
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email.strip()) is not None

def verificar_duplicidade(conn, cpf_cnpj, email, telefone, usuario_id, id_cliente=None):
    condicoes = []
    params = []
    
    doc_limpo = re.sub(r'\D', '', cpf_cnpj) if cpf_cnpj else ""
    tel_limpo = re.sub(r'\D', '', telefone) if telefone else ""
    em_limpo = email.strip() if email else ""
    
    if doc_limpo:
        condicoes.append("cpf_cnpj = ?")
        params.append(doc_limpo)
    if em_limpo:
        condicoes.append("email = ?")
        params.append(em_limpo)
    if tel_limpo:
        condicoes.append("telefone = ?")
        params.append(tel_limpo)
        
    if not condicoes:
        return None
        
    query = f"SELECT nome_cliente FROM clientes WHERE id_usuario = {usuario_id} AND ({' OR '.join(condicoes)})"
    if id_cliente:
        query += " AND id != ?"
        params.append(id_cliente)
        
    return conn.execute(query, params).fetchone()

def aplicar_mascara_telefone_str(tel_cru):
    """Formata strings numéricas puras para exibição nos campos de texto."""
    num = re.sub(r'\D', '', str(tel_cru))
    if len(num) == 9: 
        return f"{num[:5]}-{num[5:]}"
    elif len(num) == 8: 
        return f"{num[:4]}-{num[4:]}"
    return num

def aplicar_mascara_cpf_cnpj(doc_cru):
    """Aplica máscara dinâmica de CPF ou CNPJ baseada no tamanho numérico."""
    num = re.sub(r'\D', '', str(doc_cru))
    if len(num) == 11:
        return f"{num[:3]}.{num[3:6]}.{num[6:9]}-{num[9:]}"
    elif len(num) == 14:
        return f"{num[:2]}.{num[2:5]}.{num[5:8]}/{num[8:12]}-{num[12:]}"
    return num

def aplicar_mascara_telefone(row):
    ddd = str(row['ddd']).strip() if row['ddd'] else ""
    tel = str(row['telefone']).strip() if row['telefone'] else ""
    tel_limpo = re.sub(r'\D', '', tel)
    
    if not tel_limpo:
        return ""
        
    corpo = aplicar_mascara_telefone_str(tel_limpo)
    if ddd:
        ddd_limpo = re.sub(r'\D', '', ddd)
        return f"({ddd_limpo}) {corpo}"
    return corpo

def modulo_clientes(usuario_id):
    st.title("👥 Gestão de Clientes")
    conn = conectar()
    conn.row_factory = st.session_state.get('row_factory', None) 
    
    tab1, tab2, tab3 = st.tabs(["🆕 Cadastro", "🔍 Lista", "✏️ Editar"])
    
    # --- ABA 1: CADASTRO ---
    # --- ABA 1: CADASTRO CORRIGIDA ---
    with tab1:
        st.subheader("Novo Cliente")
        if 'key_cli' not in st.session_state: st.session_state.key_cli = 0
        if 'cad_cli_doc' not in st.session_state: st.session_state.cad_cli_doc = ""
        if 'cad_cli_ddd' not in st.session_state: st.session_state.cad_cli_ddd = ""
        if 'cad_cli_tel' not in st.session_state: st.session_state.cad_cli_tel = ""
        
        is_rev = st.checkbox("Este cliente é um REVENDEDOR?", key="chk_cad_rev")
        comissao_cad = st.number_input("Comissão (%)", 0, 100, 0, step=1) if is_rev else 0
        
        with st.form(key=f"f_cad_cli_{st.session_state.key_cli}"):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome Completo*")
            # st.info("🔍 Passei aqui 1")
            
            doc_raw = c2.text_input("CPF/CNPJ", value=st.session_state.cad_cli_doc, placeholder="Apenas números")
            # st.info("🔍 Passei aqui 2")
            d1, d2, d3 = st.columns([0.6, 1.5, 3])
            ddd_raw = d1.text_input("DDD*", value=st.session_state.cad_cli_ddd, max_chars=2)
            # st.info("🔍 Passei aqui 3")
            if ddd_raw != st.session_state.cad_cli_ddd:
                # st.info("🔍 Passei aqui 3.5")
                # st.info("🔍 [DEBUG] Conteúdo lido pelo Python neste 1 instante:")
                # st.write(f"**DDD Raw:** '{ddd_raw}' (Tamanho: {len(ddd_raw)})")
                # st.error("⚠️ O campo DDD deve conter apenas números1.")
                st.session_state.cad_cli_ddd = ddd_raw

            # st.info("🔍 Passei aqui 4")
            if doc_raw != st.session_state.cad_cli_doc:
                # st.info("🔍 Passei aqui 4.5")
                st.session_state.cad_cli_doc = aplicar_mascara_cpf_cnpj(doc_raw)
                # st.rerun()
            
            c3, c4 = st.columns(2)
            email = c3.text_input("Email*")
            contato = c4.text_input("Pessoa de Contato")
            # st.info("🔍 Passei aqui 5")
            # d1, d2, d3 = st.columns([0.6, 1.5, 3])
            
            # ddd_raw = d1.text_input("DDD*", value=st.session_state.cad_cli_ddd, max_chars=2)
            # if ddd_raw != st.session_state.cad_cli_ddd:
            #     st.info("🔍 [DEBUG] Conteúdo lido pelo Python neste 1 instante:")
            #     st.write(f"**DDD Raw:** '{ddd_raw}' (Tamanho: {len(ddd_raw)})")
            #     st.error("⚠️ O campo DDD deve conter apenas números.")
            #     st.session_state.cad_cli_ddd = ddd_raw
            
            tel_raw = d2.text_input("Tel*", value=st.session_state.cad_cli_tel, placeholder="Apenas números")
            if tel_raw != st.session_state.cad_cli_tel:
                # st.info("🔍 Passei aqui 6")
                st.session_state.cad_cli_tel = aplicar_mascara_telefone_str(tel_raw)
                # st.rerun()
            
            end = d3.text_input("Endereço")
            obs = st.text_area("Observações")


            # 2. VALIDAÇÃO DE CAMPOS BRUTOS EM BRANCO (Antes de testar se é número ou letra)

            # st.info("🔍 Passei aqui")
            # APENAS UM BOTÃO EXECUTANDO TODA A LÓGICA
            if st.form_submit_button("Salvar Cliente"):
                print("🚀 EVENTO CAPTURADO: O usuário clicou no botão Salvar Cliente!")
                # st.info("🔍 [DEBUG] Conteúdo lido pelo Python neste 2 instante:")
                # st.write(f"**Nome:** '{nome}' (Tamanho: {len(nome)})")
                # st.write(f"**Email:** '{email}' (Tamanho: {len(email)})")
                # st.write(f"**DDD Raw:** '{ddd_raw}' (Tamanho: {len(ddd_raw)})")
                # st.write(f"**Tel Raw:** '{tel_raw}' (Tamanho: {len(tel_raw)})")
                # st.write(f"**Doc Raw:** '{doc_raw}' (Tamanho: {len(doc_raw)})")


            # 1. EXTRAÇÃO DOS NÚMEROS (Higienização das variáveis locais)
                doc_limpo = re.sub(r'\D', '', st.session_state.cad_cli_doc)
                ddd_limpo = re.sub(r'\D', '', ddd_raw)
                tel_limpo = re.sub(r'\D', '', st.session_state.cad_cli_tel)
                
                # 2. VALIDAÇÃO DE CAMPOS BRUTOS EM BRANCO (Antes de testar se é número ou letra)
                if not nome.strip() or not email.strip() or not ddd_raw.strip() or not doc_raw.strip():
                    st.error("🚫 Todos os campos obrigatórios (*) devem ser preenchidos.dentro do botão ")
                
                # 3. VALIDAÇÕES ESPECÍFICAS DE CONTEÚDO (Captura letras digitadas incorretamente)
                elif not ddd_limpo or len(ddd_raw) != len(ddd_limpo):
                    st.error("⚠️ O campo DDD deve conter apenas números.")
                elif not tel_limpo or len(tel_raw) != len(tel_limpo):
                    st.error("⚠️ O campo Telefone deve conter apenas números.")
                elif len(tel_limpo) < 8 or len(tel_limpo) > 9:
                    st.error("⚠️ O telefone deve conter exatamente 8 (fixo) ou 9 (celular) números.")
                elif not validar_email(email):
                    st.error("🚫 Erro: O formato do e-mail informado é inválido (ex: usuario@dominio.com).")
                elif doc_raw.strip() and len(doc_raw) != len(doc_limpo):
                    st.error("⚠️ O campo CPF/CNPJ deve conter apenas números.")
                elif doc_raw.strip() and len(doc_limpo) not in [11, 14]:
                    st.error("⚠️ O CPF deve conter 11 números ou o CNPJ deve conter 14 números.")
                elif verificar_duplicidade(conn, doc_limpo, email, tel_limpo, usuario_id):
                    st.error("🚫 Erro: Dados duplicados detectados (email/telefone/documento já cadastrados).")
                
                # 4. SALVAMENTO NO BANCO
                else:
                    conn.execute("""
                        INSERT INTO clientes (id_usuario, nome_cliente, cpf_cnpj, ddd, telefone, email, contato_pessoa, endereco, observacao, is_revendedor, comissao) 
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    """, (usuario_id, nome, doc_limpo, ddd_limpo, tel_limpo, email.strip(), contato, end, obs, (1 if is_rev else 0), comissao_cad))
                    conn.commit()
                    st.success("✅ Cliente cadastrado com sucesso!")
                    st.session_state.key_cli += 1
                    st.session_state.cad_cli_doc = ""
                    st.session_state.cad_cli_ddd = ""
                    st.session_state.cad_cli_tel = ""
                    time.sleep(1.2)
                    st.rerun()
                    
    # --- ABA 2: LISTA ---
    with tab2:
        st.subheader("🔍 Consulta de Clientes")
        filtro_nome = st.text_input("Pesquisar por nome:")
        df = pd.read_sql_query(f"SELECT id, nome_cliente, cpf_cnpj, ddd, telefone, email, is_revendedor, comissao FROM clientes WHERE id_usuario = {usuario_id}", conn)
        
        if not df.empty:
            if filtro_nome:
                df = df[df['nome_cliente'].str.contains(filtro_nome, case=False, na=False)]
                
            df['Telefone'] = df.apply(aplicar_mascara_telefone, axis=1)
            df['cpf_cnpj'] = df['cpf_cnpj'].apply(aplicar_mascara_cpf_cnpj)
            df['Tipo'] = df['is_revendedor'].apply(lambda x: "🟢 Revendedor" if x else "👤 Final")
            
            df_display = df[['id', 'nome_cliente', 'cpf_cnpj', 'Telefone', 'email', 'Tipo', 'comissao']]
            df_display.columns = ['ID', 'Nome', 'CPF/CNPJ', 'Telefone', 'E-mail', 'Tipo', 'Comissão %']
            
            estilo = df_display.style.set_table_styles([
                {'selector': 'th', 'props': [('background-color', '#004d4d'), ('color', 'white'), ('font-weight', 'bold')]}
            ]).format({'Comissão %': '{:,.0f}%'}).hide(axis="index")
            st.table(estilo)
        else:
            st.info("Nenhum cliente encontrado.")
            
    # --- ABA 3: EDITAR ---
    with tab3:
        st.subheader("✏️ Alterar Cliente")
        df_c = pd.read_sql_query(f"SELECT * FROM clientes WHERE id_usuario = {usuario_id}", conn)
        if not df_c.empty:
            opcoes = {f"ID {r['id']} | {r['nome_cliente']}": r['id'] for _, r in df_c.iterrows()}
            sc = st.selectbox("Selecione o cliente:", [""] + list(opcoes.keys()))
            
            if sc:
                id_cli = opcoes[sc]
                c_data = df_c[df_c['id'] == id_cli].iloc[0]
                
                if f"edit_cli_doc_{id_cli}" not in st.session_state:
                    st.session_state[f"edit_cli_doc_{id_cli}"] = aplicar_mascara_cpf_cnpj(c_data['cpf_cnpj'])
                if f"edit_cli_ddd_{id_cli}" not in st.session_state:
                    st.session_state[f"edit_cli_ddd_{id_cli}"] = re.sub(r'\D', '', str(c_data['ddd'])) if c_data['ddd'] else ""
                if f"edit_cli_tel_{id_cli}" not in st.session_state:
                    st.session_state[f"edit_cli_tel_{id_cli}"] = aplicar_mascara_telefone_str(c_data['telefone'])
                
                ere = st.checkbox("Revendedor?", value=bool(c_data['is_revendedor']), key=f"ed_rev_{id_cli}")
                com_ed = st.number_input("% Comissão", value=int(c_data['comissao']), min_value=0, max_value=100, step=1, key=f"ed_com_{id_cli}") if ere else 0
                
                with st.form(f"f_ed_cli_{id_cli}"):
                    c1, c2 = st.columns(2)
                    en = c1.text_input("Nome*", value=c_data['nome_cliente'])
                    
                    ed_raw = c2.text_input("CPF/CNPJ", value=st.session_state[f"edit_cli_doc_{id_cli}"])
                    if ed_raw != st.session_state[f"edit_cli_doc_{id_cli}"]:
                        st.session_state[f"edit_cli_doc_{id_cli}"] = aplicar_mascara_cpf_cnpj(ed_raw)
                        st.rerun()
                    
                    ee = c1.text_input("Email*", value=c_data['email'])
                    ect = c2.text_input("Contato", value=c_data['contato_persona'] if 'contato_persona' in c_data else c_data.get('contato_pessoa', ''))
                    
                    d1, d2, d3 = st.columns([0.6, 1.5, 3])
                    
                    eddd_raw = d1.text_input("DDD", value=st.session_state[f"edit_cli_ddd_{id_cli}"], max_chars=2)
                    st.session_state[f"edit_cli_ddd_{id_cli}"] = eddd_raw
                    
                    etel_raw = d2.text_input("Tel", value=st.session_state[f"edit_cli_tel_{id_cli}"])
                    if etel_raw != st.session_state[f"edit_cli_tel_{id_cli}"]:
                        st.session_state[f"edit_cli_tel_{id_cli}"] = aplicar_mascara_telefone_str(etel_raw)
                        st.rerun()
                    
                    eend = d3.text_input("Endereço", value=c_data['endereco'])
                    eob = st.text_area("Observações", value=c_data['observacao'])
                    
                    c_btn1, c_btn2 = st.columns(2)
                    btn_update = c_btn1.form_submit_button("💾 Salvar Alterações")
                    btn_delete = c_btn2.form_submit_button("🗑️ EXCLUIR")
                    
                    if btn_update:
                        ed_limpo = re.sub(r'\D', '', st.session_state[f"edit_cli_doc_{id_cli}"])
                        eddd_limpo = re.sub(r'\D', '', st.session_state[f"edit_cli_ddd_{id_cli}"])
                        etel_limpo = re.sub(r'\D', '', st.session_state[f"edit_cli_tel_{id_cli}"])

                        if not en.strip() or not ee.strip() or not eddd_raw.strip() or not etel_raw.strip():
                            st.error("🚫 Nome, Email, DDD e Telefone são de preenchimento obrigatório.")
                        elif not eddd_limpo.isdigit():
                            st.error("⚠️ O campo DDD deve conter apenas números.")
                        elif not etel_limpo.isdigit():
                            st.error("⚠️ O campo Telefone deve conter apenas números.")
                        elif not validar_email(ee):
                            st.error("🚫 Erro: O e-mail informado é inválido.")
                        elif ed_raw.strip() and not ed_limpo.isdigit():
                            st.error("⚠️ O campo CPF/CNPJ deve conter apenas números.")
                        elif ed_raw.strip() and len(ed_limpo) not in [11, 14]:
                            st.error("⚠️ O documento deve conter exatamente 11 (CPF) ou 14 (CNPJ) números.")
                        elif len(etel_limpo) < 8 or len(etel_limpo) > 9:
                            st.error("⚠️ O telefone deve conter 8 ou 9 números.")
                        elif verificar_duplicidade(conn, ed_limpo, ee, etel_limpo, usuario_id, id_cli):
                            st.error("🚫 Erro: Duplicidade detectada.")
                        else:
                            conn.execute("""
                                UPDATE clientes SET nome_cliente=?, cpf_cnpj=?, ddd=?, telefone=?, email=?, 
                                contato_pessoa=?, endereco=?, observacao=?, is_revendedor=?, comissao=? WHERE id=? and id_usuario=?
                            """, (en, ed_limpo, eddd_limpo, etel_limpo, ee.strip(), ect, eend, eob, (1 if ere else 0), com_ed, id_cli, usuario_id))
                            conn.commit()
                            st.success("✅ Atualizado!")
                            
                            if f"edit_cli_doc_{id_cli}" in st.session_state: del st.session_state[f"edit_cli_doc_{id_cli}"]
                            if f"edit_cli_ddd_{id_cli}" in st.session_state: del st.session_state[f"edit_cli_ddd_{id_cli}"]
                            if f"edit_cli_tel_{id_cli}" in st.session_state: del st.session_state[f"edit_cli_tel_{id_cli}"]
                            
                            time.sleep(1)
                            st.rerun()
                            
                    if btn_delete:
                        try:
                            conn.execute("DELETE FROM clientes WHERE id=? AND id_usuario=?", (id_cli, usuario_id))
                            conn.commit()
                            st.success("Cliente removido com sucesso!")
                            
                            if f"edit_cli_doc_{id_cli}" in st.session_state: del st.session_state[f"edit_cli_doc_{id_cli}"]
                            if f"edit_cli_ddd_{id_cli}" in st.session_state: del st.session_state[f"edit_cli_ddd_{id_cli}"]
                            if f"edit_cli_tel_{id_cli}" in st.session_state: del st.session_state[f"edit_cli_tel_{id_cli}"]
                            
                            time.sleep(1)
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("⚠️ Não é possível excluir este cliente pois existem vendas ou movimentações vinculadas ao nome dele.")
    conn.close()
