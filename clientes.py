import streamlit as st
import pandas as pd
import time
import re
from database import conectar

def validar_email(email):
    """Valida se o email possui o formato básico com @ e um domínio."""
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email) is not None

def verificar_duplicidade(conn, cpf_cnpj, email, telefone, id_cliente=None):
    condicoes = []
    params = []

    if cpf_cnpj and cpf_cnpj.strip():
        condicoes.append("cpf_cnpj = ?")
        params.append(cpf_cnpj.strip())
    
    if email and email.strip():
        condicoes.append("email = ?")
        params.append(email.strip())
        
    if telefone and telefone.strip():
        condicoes.append("telefone = ?")
        params.append(telefone.strip())

    if not condicoes:
        return None

    query = f"SELECT nome_cliente FROM clientes WHERE ({' OR '.join(condicoes)})"
    if id_cliente:
        query += " AND id != ?"
        params.append(id_cliente)
        
    return conn.execute(query, params).fetchone()

def aplicar_mascara_telefone(row):
    ddd = str(row['ddd']).strip() if row['ddd'] else ""
    tel = str(row['telefone']).strip() if row['telefone'] else ""
    tel_limpo = re.sub(r'\D', '', tel)
    
    if not tel_limpo:
        return ""
    
    if len(tel_limpo) == 9:
        corpo = f"{tel_limpo[:5]}-{tel_limpo[5:]}"
    elif len(tel_limpo) == 8:
        corpo = f"{tel_limpo[:4]}-{tel_limpo[4:]}"
    else:
        corpo = tel_limpo

    if ddd:
        ddd_limpo = re.sub(r'\D', '', ddd)
        return f"({ddd_limpo}) {corpo}"
    return corpo

def modulo_clientes():
    st.title("👥 Gestão de Clientes")
    conn = conectar()
    conn.row_factory = st.session_state.get('row_factory', None) 
    
    tab1, tab2, tab3 = st.tabs(["🆕 Cadastro", "🔍 Lista", "✏️ Editar"])

    # --- ABA 1: CADASTRO ---
    with tab1:
        st.subheader("Novo Cliente")
        if 'key_cli' not in st.session_state: st.session_state.key_cli = 0
            
        is_rev = st.checkbox("Este cliente é um REVENDEDOR?", key="chk_cad_rev")
        comissao_cad = st.number_input("Comissão (%)", 0, 100, 0, step=1) if is_rev else 0

        with st.form(key=f"f_cad_cli_{st.session_state.key_cli}"):
            c1, c2 = st.columns(2)
            nome, doc = c1.text_input("Nome Completo*"), c2.text_input("CPF/CNPJ")
            c3, c4 = st.columns(2)
            email, contato = c3.text_input("Email*"), c4.text_input("Pessoa de Contato")
            d1, d2, d3 = st.columns([0.6, 1.5, 3])
            ddd, tel, end = d1.text_input("DDD"), d2.text_input("Tel"), d3.text_input("Endereço")
            obs = st.text_area("Observações")
            
            if st.form_submit_button("Salvar Cliente"):
                if nome and email:
                    if not validar_email(email):
                        st.error("🚫 Erro: O e-mail informado é inválido (deve conter @ e um domínio).")
                    elif verificar_duplicidade(conn, doc, email, tel):
                        st.error("🚫 Erro: Dados duplicados detectados.")
                    else:
                        conn.execute("""
                            INSERT INTO clientes (nome_cliente, cpf_cnpj, ddd, telefone, email, contato_pessoa, endereco, observacao, is_revendedor, comissao) 
                            VALUES (?,?,?,?,?,?,?,?,?,?)
                        """, (nome, doc, ddd, tel, email, contato, end, obs, (1 if is_rev else 0), comissao_cad))
                        conn.commit()
                        st.success("✅ Cadastrado!")
                        st.session_state.key_cli += 1
                        time.sleep(1); st.rerun()
                else:
                    st.error("Nome e Email são obrigatórios.")

    # --- ABA 2: LISTA ---
    with tab2:
        st.subheader("🔍 Consulta de Clientes")
        filtro_nome = st.text_input("Pesquisar por nome:")
        df = pd.read_sql_query("SELECT id, nome_cliente, cpf_cnpj, ddd, telefone, email, is_revendedor, comissao FROM clientes", conn)
        
        if not df.empty:
            if filtro_nome:
                df = df[df['nome_cliente'].str.contains(filtro_nome, case=False, na=False)]
            
            df['Telefone'] = df.apply(aplicar_mascara_telefone, axis=1)
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
        df_c = pd.read_sql_query("SELECT * FROM clientes", conn)
        if not df_c.empty:
            opcoes = {f"ID {r['id']} | {r['nome_cliente']}": r['id'] for _, r in df_c.iterrows()}
            sc = st.selectbox("Selecione o cliente:", [""] + list(opcoes.keys()))
            
            if sc:
                id_cli = opcoes[sc]
                c_data = df_c[df_c['id'] == id_cli].iloc[0]
                
                ere = st.checkbox("Revendedor?", value=bool(c_data['is_revendedor']), key=f"ed_rev_{id_cli}")
                com_ed = st.number_input("% Comissão", value=int(c_data['comissao']), min_value=0, max_value=100, step=1, key=f"ed_com_{id_cli}") if ere else 0

                with st.form(f"f_ed_cli_{id_cli}"):
                    c1, c2 = st.columns(2)
                    en, ed = c1.text_input("Nome*", value=c_data['nome_cliente']), c2.text_input("CPF/CNPJ", value=c_data['cpf_cnpj'])
                    ee, ect = c1.text_input("Email*", value=c_data['email']), c2.text_input("Contato", value=c_data['contato_pessoa'])
                    d1, d2, d3 = st.columns([0.6, 1.5, 3])
                    eddd, etel, eend = d1.text_input("DDD", value=c_data['ddd']), d2.text_input("Tel", value=c_data['telefone']), d3.text_input("Endereço", value=c_data['endereco'])
                    eob = st.text_area("Observações", value=c_data['observacao'])
                    
                    if st.form_submit_button("💾 Salvar Alterações"):
                        if not en or not ee:
                            st.error("🚫 Nome e Email obrigatórios.")
                        elif not validar_email(ee):
                            st.error("🚫 Erro: O e-mail informado é inválido.")
                        elif verificar_duplicidade(conn, ed, ee, etel, id_cli):
                            st.error("🚫 Erro: Duplicidade detectada.")
                        else:
                            conn.execute("""
                                UPDATE clientes SET nome_cliente=?, cpf_cnpj=?, ddd=?, telefone=?, email=?, 
                                contato_pessoa=?, endereco=?, observacao=?, is_revendedor=?, comissao=? WHERE id=?
                            """, (en, ed, eddd, etel, ee, ect, eend, eob, (1 if ere else 0), com_ed, id_cli))
                            conn.commit()
                            st.success("✅ Atualizado!"); time.sleep(1); st.rerun()
                    
                    if st.form_submit_button("🗑️ EXCLUIR"):
                        conn.execute("DELETE FROM clientes WHERE id=?", (id_cli,))
                        conn.commit()
                        st.warning("Removido."); time.sleep(1); st.rerun()
    conn.close()