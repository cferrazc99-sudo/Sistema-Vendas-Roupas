import streamlit as st
import pandas as pd
import time
import re
from database import conectar

def formatar_tel_v2(ddd, tel):
    num = re.sub(r'\D', '', f"{ddd}{tel}")
    if len(num) == 11: return f"({num[:2]}) {num[2:7]}-{num[7:]}"
    elif len(num) == 10: return f"({num[:2]}) {num[2:6]}-{num[6:]}"
    return num if num else ""

def verificar_duplicidade(cursor, cnpj, email, ddd, tel, id_atual=None):
    """
    Retorna (True, 'mensagem') se houver duplicata, senão (False, '').
    id_atual é usado na edição para não dar erro ao comparar o registro consigo mesmo.
    """
    # Limpeza de strings
    cnpj_limpo = re.sub(r'\D', '', cnpj) if cnpj else ""
    tel_limpo = re.sub(r'\D', '', tel) if tel else ""
    ddd_limpo = re.sub(r'\D', '', ddd) if ddd else ""
    
    # 1. Verificar CNPJ (Somente se preenchido)
    if cnpj_limpo:
        query = "SELECT id FROM fornecedores WHERE cnpj = ?"
        params = [cnpj_limpo]
        if id_atual:
            query += " AND id != ?"
            params.append(id_atual)
        if cursor.execute(query, params).fetchone():
            return True, "⚠️ CNPJ já cadastrado para outro fornecedor."

    # 2. Verificar E-mail
    query_email = "SELECT id FROM fornecedores WHERE email = ?"
    params_email = [email]
    if id_atual:
        query_email += " AND id != ?"
        params_email.append(id_atual)
    if cursor.execute(query_email, params_email).fetchone():
        return True, "⚠️ Este E-mail já está em uso."

    # 3. Verificar Telefone (DDD + Número)
    if tel_limpo:
        query_tel = "SELECT id FROM fornecedores WHERE ddd = ? AND telefone = ?"
        params_tel = [ddd_limpo, tel_limpo]
        if id_atual:
            query_tel += " AND id != ?"
            params_tel.append(id_atual)
        if cursor.execute(query_tel, params_tel).fetchone():
            return True, "⚠️ Este Telefone já está cadastrado."

    return False, ""

def modulo_fornecedores(usuario_id):
    st.title("🏢 Gestão de Fornecedores")
    conn = conectar()
    tab1, tab2, tab3 = st.tabs(["🆕 Cadastro", "🔍 Consulta", "✏️ Editar/Excluir"])

    # --- TAB 1: CADASTRO ---
    with tab1:
        st.subheader("Novo Fornecedor")
        if 'key_form' not in st.session_state: st.session_state.key_form = 0

        with st.form(key=f"f_cad_forn_{st.session_state.key_form}"):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome da Empresa*")
            cnpj = c2.text_input("CNPJ")
            c3, c4 = st.columns(2)
            email = c3.text_input("Email*")
            contato = c4.text_input("Pessoa de Contato")
            d1, d2, d3 = st.columns([0.6, 1.5, 3])
            ddd = d1.text_input("DDD", max_chars=2)
            tel = d2.text_input("Telefone")
            end = d3.text_input("Endereço Completo")
            obs = st.text_area("Observações")
            botao_salvar = st.form_submit_button("Salvar Fornecedor")

        if botao_salvar:
            if nome and email:
                cursor = conn.cursor()
                # Validação de Duplicidade
                tem_duplicidade, mensagem = verificar_duplicidade(cursor, cnpj, email, ddd, tel)
                
                if tem_duplicidade:
                    st.error(mensagem)
                else:
                    cj_l = re.sub(r'\D', '', cnpj)
                    te_l = re.sub(r'\D', '', tel)
                    dd_l = re.sub(r'\D', '', ddd)
                    cursor.execute("INSERT INTO fornecedores (nome_empresa, cnpj, ddd, telefone, email, contato_pessoa, endereco, observacao) VALUES (?,?,?,?,?,?,?,?)", 
                                  (nome, cj_l, dd_l, te_l, email, contato, end, obs))
                    conn.commit()
                    st.success(f"✅ {nome} salvo!")
                    st.session_state.key_form += 1
                    time.sleep(1.2)
                    st.rerun()
            else: 
                st.error("Nome e Email são obrigatórios.")

    # --- TAB 2: CONSULTA ---
    with tab2:
        df = pd.read_sql_query("SELECT * FROM fornecedores", conn)
        if not df.empty:
            df['Telefone Formatado'] = df.apply(lambda x: formatar_tel_v2(x['ddd'], x['telefone']), axis=1)
            st.dataframe(df[['nome_empresa', 'cnpj', 'Telefone Formatado', 'email', 'contato_pessoa', 'endereco', 'observacao']].rename(columns={'nome_empresa':'Empresa','cnpj':'CNPJ','email':'E-mail','contato_pessoa':'Contato','endereco':'Endereço','observacao':'Obs'}), use_container_width=True)

    # --- TAB 3: EDIÇÃO ---
    with tab3:
        df_list = pd.read_sql_query("SELECT id, nome_empresa FROM fornecedores", conn)
        sel = st.selectbox("Escolha para editar:", [""] + list(df_list['nome_empresa']), key="sel_f_edit")
        
        if sel:
            id_f = int(df_list[df_list['nome_empresa'] == sel]['id'].iloc[0])
            d = conn.execute("SELECT * FROM fornecedores WHERE id=?", (id_f,)).fetchone()
            
            with st.form("f_ed_forn"):
                enome = st.text_input("Empresa", value=d[1])
                ecnpj = st.text_input("CNPJ", value=d[2])
                e3, e4, e5 = st.columns([0.6, 1.5, 3])
                eddd, etel, eend = e3.text_input("DDD", value=d[3]), e4.text_input("Tel", value=d[4]), e5.text_input("End", value=d[7])
                eemail, econt = st.text_input("Email", value=d[5]), st.text_input("Contato", value=d[6])
                eobs = st.text_area("Obs", value=d[8])
                
                col_b1, col_b2 = st.columns(2)
                btn_update = col_b1.form_submit_button("💾 Salvar Alterações")
                btn_delete = col_b2.form_submit_button("🗑️ EXCLUIR FORNECEDOR")

                if btn_update:
                    cursor = conn.cursor()
                    # Validação de Duplicidade (Passando id_f para ignorar o próprio registro)
                    tem_duplicidade, mensagem = verificar_duplicidade(cursor, ecnpj, eemail, eddd, etel, id_atual=id_f)
                    
                    if tem_duplicidade:
                        st.error(mensagem)
                    else:
                        ecj_l = re.sub(r'\D', '', ecnpj)
                        ete_l = re.sub(r'\D', '', etel)
                        edd_l = re.sub(r'\D', '', eddd)
                        cursor.execute("UPDATE fornecedores SET nome_empresa=?, cnpj=?, ddd=?, telefone=?, email=?, contato_pessoa=?, endereco=?, observacao=? WHERE id=?", 
                                     (enome, ecj_l, edd_l, ete_l, eemail, econt, eend, eobs, id_f))
                        conn.commit()
                        st.success("Atualizado!")
                        time.sleep(1)
                        st.rerun()
                
                if btn_delete:
                    count_prod = conn.execute("SELECT COUNT(*) FROM produtos WHERE id_fornecedor = ?", (id_f,)).fetchone()[0]
                    if count_prod > 0:
                        st.error(f"🚫 BLOQUEIO: Possui {count_prod} produto(s) vinculados.")
                    else:
                        conn.execute("DELETE FROM fornecedores WHERE id=?", (id_f,))
                        conn.commit()
                        st.warning("Fornecedor removido.")
                        time.sleep(1.2); st.rerun()
    conn.close()