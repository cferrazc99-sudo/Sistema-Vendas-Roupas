import streamlit as st
import pandas as pd
import time
import re
from database import conectar

def formatar_tel_v2(ddd, tel):
    num = re.sub(r'\D', '', f"{ddd}{tel}")
    if len(num) == 11: 
        return f"({num[:2]}) {num[2:7]}-{num[7:]}"
    elif len(num) == 10: 
        return f"({num[:2]}) {num[2:6]}-{num[6:]}"
    return num if num else ""

def aplicar_mascara_input(tel_cru):
    """Aplica a máscara pura no número de telefone para exibição nos campos."""
    num = re.sub(r'\D', '', str(tel_cru))
    if len(num) == 9: # Celular
        return f"{num[:5]}-{num[5:]}"
    elif len(num) == 8: # Fixo
        return f"{num[:4]}-{num[4:]}"
    return num

def aplicar_mascara_cnpj(cnpj_cru):
    """Aplica a máscara de CNPJ (12.345.678/0001-00) para exibição nos campos."""
    num = re.sub(r'\D', '', str(cnpj_cru))
    if len(num) == 14:
        return f"{num[:2]}.{num[2:5]}.{num[5:8]}/{num[8:12]}-{num[12:]}"
    return num

def validar_formato_email(email):
    padrao = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(padrao, email.strip()))

def verificar_duplicidade(cursor, cnpj, email, ddd, tel, id_atual=None):
    cnpj_limpo = re.sub(r'\D', '', cnpj) if cnpj else ""
    tel_limpo = re.sub(r'\D', '', tel) if tel else ""
    ddd_limpo = re.sub(r'\D', '', ddd) if ddd else ""
    
    if cnpj_limpo:
        query = "SELECT id FROM fornecedores WHERE cnpj = ? AND id_usuario = ?"
        params = [cnpj_limpo, st.session_state.usuario_id]
        if id_atual:
            query += " AND id != ?"
            params.append(id_atual)
        if cursor.execute(query, params).fetchone():
            return True, "⚠️ CNPJ já cadastrado para outro fornecedor."

    query_email = "SELECT id FROM fornecedores WHERE email = ? AND id_usuario = ?"
    params_email = [email.strip(), st.session_state.usuario_id]
    if id_atual:
        query_email += " AND id != ?"
        params_email.append(id_atual)
    if cursor.execute(query_email, params_email).fetchone():
        return True, "⚠️ Este E-mail já está em uso."

    if tel_limpo:
        query_tel = "SELECT id FROM fornecedores WHERE ddd = ? AND telefone = ? AND id_usuario = ?"
        params_tel = [ddd_limpo, tel_limpo, st.session_state.usuario_id]
        if id_atual:
            query_tel += " AND id != ?"
            params_tel.append(id_atual)
        if cursor.execute(query_tel, params_tel).fetchone():
            return True, "⚠️ Este Telefone já está cadastrado."
            
    return False, ""

def modulo_fornecedores(id_usuario):
    st.title("🏢 Gestão de Fornecedores")
    conn = conectar()
    
    tab1, tab2, tab3 = st.tabs(["🆕 Cadastro", "🔍 Consulta", "✏ Editar/Excluir"])
    
    # --- TAB 1: CADASTRO ---
    with tab1:
        st.subheader("Novo Fornecedor")
        if 'key_form' not in st.session_state: 
            st.session_state.key_form = 0
            
        with st.form(key=f"f_cad_forn_{st.session_state.key_form}"):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome da Empresa*")
            
            # PASSO 1: Apresentação limpa dos campos na tela, sem máscaras ou reruns que travam o foco
            cnpj_raw = c2.text_input("CNPJ", placeholder="Ex: 12345678000100", max_chars=14)
            
            c3, c4 = st.columns(2)
            email = c3.text_input("Email*")
            contato = c4.text_input("Pessoa de Contato")
            
            d1, d2, d3 = st.columns([0.6, 1.5, 3])
            ddd_raw = d1.text_input("DDD*", max_chars=2)
            tel_raw = d2.text_input("Telefone*", placeholder="Ex: 997619817", max_chars=9)
            
            end = d3.text_input("Endereço Completo")
            obs = st.text_area("Observações")
            
            if st.form_submit_button("Salvar Fornecedor"):
                # PASSO 2: Todo o controle de validação ocorre aqui dentro após o clique
                cnpj_validado = re.sub(r'\D', '', cnpj_raw)
                ddd_validado = re.sub(r'\D', '', ddd_raw)
                tel_validado = re.sub(r'\D', '', tel_raw)
                
                if not nome or not email or not ddd_raw or not tel_raw:
                    st.error("Nome, Email, DDD e Telefone são obrigatórios.")
                elif email.strip() and not validar_formato_email(email):
                    st.error("⚠ O formato do e-mail digitado é inválido.")
                elif cnpj_raw.strip() and (len(cnpj_raw) != len(cnpj_validado) or len(cnpj_validado) != 14):
                    # PASSO 3: O sistema avisa o erro, mas não altera os dados da tela para o usuário ajustar
                    st.error("⚠ O CNPJ deve conter exatamente 14 dígitos numéricos.")
                elif len(ddd_raw) != len(ddd_validado):
                    st.error("⚠ O campo DDD aceita apenas valores numéricos.")
                elif len(tel_raw) != len(tel_validado) or len(tel_validado) < 8 or len(tel_validado) > 9:
                    st.error("⚠ O telefone deve conter apenas 8 ou 9 números numéricos.")
                else:
                    cursor = conn.cursor()
                    tem_duplicidade, mensagem = verificar_duplicidade(cursor, cnpj_validado, email, ddd_validado, tel_validado)
                    
                    if tem_duplicidade:
                        st.error(mensagem)
                    else:
                        cursor.execute("""
                            INSERT INTO fornecedores (id_usuario, nome_empresa, cnpj, ddd, telefone, email, contato_pessoa, endereco, observacao) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (id_usuario, nome, cnpj_validado, ddd_validado, tel_validado, email.strip(), contato, end, obs))
                        conn.commit()
                        st.success(f"✅ {nome} salvo!")
                        st.session_state.key_form += 1
                        time.sleep(1.2)
                        st.rerun()

    # --- TAB 2: CONSULTA ---
    with tab2:
        df = pd.read_sql_query("SELECT * FROM fornecedores WHERE id_usuario = ?", conn, params=[id_usuario])
        if not df.empty:
            df['Telefone Formatado'] = df.apply(lambda x: formatar_tel_v2(x['ddd'], x['telefone']), axis=1)
            df['cnpj'] = df['cnpj'].apply(aplicar_mascara_cnpj)
            st.dataframe(df[['nome_empresa', 'cnpj', 'Telefone Formatado', 'email', 'contato_pessoa', 'endereco', 'observacao']].rename(columns={
                'nome_empresa':'Empresa','cnpj':'CNPJ','email':'E-mail','contato_pessoa':'Contato','endereco':'Endereço','observacao':'Obs'
            }), use_container_width=True)

    # --- TAB 3: EDIÇÃO/EXCLUIR ---
    with tab3:
        df_list = pd.read_sql_query("SELECT id, nome_empresa FROM fornecedores WHERE id_usuario = ?", conn, params=[id_usuario])
        sel = st.selectbox("Escolha para editar:", [""] + list(df_list['nome_empresa']), key="sel_f_edit")
        
        if sel:
            id_f = int(df_list[df_list['nome_empresa'] == sel]['id'].iloc[0])
            d = conn.execute("SELECT id_usuario, nome_empresa, cnpj, ddd, telefone, email, contato_pessoa, endereco, observacao FROM fornecedores WHERE id=? AND id_usuario=?", (id_f, id_usuario)).fetchone()
            
            # Correção do travamento da tela: Dados nativos puxados direto da tupla d do banco de dados, sem session_state intermediário
            with st.form(f"f_ed_forn_{id_f}"):
                enome = st.text_input("Nome da Empresa*", value=d[1])
                ecnpj_raw = st.text_input("CNPJ", value=d[2], max_chars=14)
                
                e3, e4, e5 = st.columns([0.6, 1.5, 3])
                eddd_raw = e3.text_input("DDD*", value=str(d[3]), max_chars=2)
                etel_raw = e4.text_input("Tel*", value=str(d[4]), max_chars=9)
                
                eend = e5.text_input("Endereço Completo", value=d[7])
                eemail = st.text_input("Email*", value=d[5])
                econt = st.text_input("Contato", value=d[6])
                eobs = st.text_area("Obs", value=d[8])
                
                col_b1, col_b2 = st.columns(2)
                btn_update = col_b1.form_submit_button("💾 Salvar Alterações")
                btn_delete = col_b2.form_submit_button("🗑 EXCLUIR FORNECEDOR")
                
                if btn_update:
                    ecnpj_validado = re.sub(r'\D', '', ecnpj_raw)
                    eddd_validado = re.sub(r'\D', '', eddd_raw)
                    etel_validado = re.sub(r'\D', '', etel_raw)
                    
                    if not enome or not eemail or not eddd_raw or not etel_raw:
                        st.error("🚫 Nome da Empresa, Email, DDD e Telefone são obrigatórios.")
                    elif eemail.strip() and not validar_formato_email(eemail):
                        st.error("⚠ O formato do e-mail digitado é inválido.")
                    elif ecnpj_raw.strip() and (len(ecnpj_raw) != len(ecnpj_validado) or len(ecnpj_validado) != 14):
                        st.error("⚠ O CNPJ deve conter exatamente 14 dígitos numéricos.")
                    elif len(eddd_raw) != len(eddd_validado):
                        st.error("⚠ O campo DDD aceita apenas valores numéricos.")
                    elif len(etel_raw) != len(etel_validado) or len(etel_validado) < 8 or len(etel_validado) > 9:
                        st.error("⚠ O telefone deve conter apenas 8 ou 9 números numéricos.")
                    else:
                        cursor = conn.cursor()
                        tem_duplicidade, mensagem = verificar_duplicidade(cursor, ecnpj_validado, eemail, eddd_validado, etel_validado, id_atual=id_f)
                        
                        if tem_duplicidade:
                            st.error(mensagem)
                        else:
                            cursor.execute("""
                                UPDATE fornecedores SET nome_empresa=?, cnpj=?, ddd=?, telefone=?, email=?, contato_pessoa=?, endereco=?, observacao=? WHERE id=? AND id_usuario=?
                            """, (enome, ecnpj_validado, eddd_validado, etel_validado, eemail.strip(), econt, eend, eobs, id_f, id_usuario))
                            conn.commit()
                            st.success("Atualizado com sucesso!")
                            time.sleep(1)
                            st.rerun()
                
                if btn_delete:
                    count_prod = conn.execute("SELECT COUNT(*) FROM produtos WHERE id_fornecedor = ? AND id_usuario = ?", (id_f, id_usuario)).fetchone()[0]
                    if count_prod > 0:
                        st.error(f"🚫 BLOQUEIO: Possui {count_prod} produto(s) vinculados.")
                    else:
                        conn.execute("DELETE FROM fornecedores WHERE id=? AND id_usuario=?", (id_f, id_usuario))
                        conn.commit()
                        st.warning("Fornecedor removido.")
                        time.sleep(1.2)
                        st.rerun()
    conn.close()
