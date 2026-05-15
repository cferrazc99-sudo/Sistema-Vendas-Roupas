import streamlit as st
import pandas as pd
import time
import re
from database import conectar
import sqlite3

def validar_email(email):
    """Valida se o email possui o formato básico com @ e um domínio."""
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email) is not None

def verificar_duplicidade(conn, cpf_cnpj, email, telefone, usuario_id, id_cliente=None):
    condicoes = []
    params = []
    
    # 1. Validação CPF/CNPJ: Só verifica duplicidade na base se estiver preenchido
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
        
    query = f"SELECT nome_cliente FROM clientes WHERE id_usuario = {usuario_id} AND ({' OR '.join(condicoes)})"
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

def modulo_clientes(usuario_id):
    st.title("👥 Gestão de Clientes")
    conn = conectar()
    conn.row_factory = st.session_state.get('row_factory', None) 
    
    # Coloque isso logo no início da função modulo_clientes, antes de desenhar o formulário
    # with st.sidebar:
    # st.subheader("🛠️ Painel de Debug")
        
    #     # Exibe em tempo real se o botão foi clicado na última execução
    #     # Nota: No Streamlit, um botão de form só registra True no exato instante do envio
    # st.write("Último clique registrado no formulário:")
        
    #     # Inspeciona as variáveis brutas que estão na memória da página
    # st.json({
    #         "Chaves no Session State": list(st.session_state.keys()),
    #         "Key Atual do Formulário": st.session_state.get('key_cli', 0)
    #     })
                  
    tab1, tab2, tab3 = st.tabs(["🆕 Cadastro", "🔍 Lista", "✏ Editar"])
    
    with tab1:
        st.subheader("Novo Cliente")
        if 'key_cli' not in st.session_state: 
            st.session_state.key_cli = 0
        
        is_rev = st.checkbox("Este cliente é um REVENDEDOR?", key="chk_cad_rev")
        comissao_cad = st.number_input("Comissão (%)", 0, 100, 0, step=1) if is_rev else 0
        
        with st.form(key=f"f_cad_cli_{st.session_state.key_cli}"):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome Completo*")
            
            # PROPOSTA PASSO 1: Campos exibidos puramente sem validações em tempo real ou st.rerun
            doc_raw = c2.text_input("CPF/CNPJ", max_chars=14, help="Apenas números ou vazio")
            
            c3, c4 = st.columns(2)
            email = c3.text_input("Email*")
            contato = c4.text_input("Pessoa de Contato")
            
            d1, d2, d3 = st.columns([0.6, 1.5, 3])
            ddd_raw = d1.text_input("DDD", max_chars=2)
            tel_raw = d2.text_input("Tel", max_chars=9)
            
            end = d3.text_input("Endereço")
            obs = st.text_area("Observações")
            
            # PROPOSTA PASSO 2: Toda a validação ocorre estritamente dentro do botão de envio
            if st.form_submit_button("Salvar Cliente"):
                
                # Validação interna das regras de caracteres (apenas numéricos para checagem)
                # Note que NÃO alteramos os componentes da tela. O usuário ainda verá suas strings originais se falhar.
                doc_validado = re.sub(r'\D', '', doc_raw)
                ddd_validado = re.sub(r'\D', '', ddd_raw)
                tel_validado = re.sub(r'\D', '', tel_raw)
                
                # Início das checagens condicionais pós-clique
                if not nome or not email or not ddd_raw or not tel_raw:
                    st.error("🚫 Nome, Email, DDD e Telefone são obrigatórios.")
                    
                elif doc_raw and (len(doc_raw) != len(doc_validado)):
                    # PROPOSTA PASSO 3: O sistema aponta o erro, mas mantém o texto incorreto na tela para o usuário ajustar
                    st.error("🚫 O campo CPF/CNPJ aceita apenas valores numéricos ou vazio.")
                    
                elif len(ddd_raw) != len(ddd_validado):
                    st.error("🚫 O campo DDD aceita apenas valores numéricos.")
                    
                elif len(tel_raw) != len(tel_validado):
                    st.error("🚫 O campo Telefone aceita apenas valores numéricos.")
                    
                elif not validar_email(email):
                    st.error("🚫 Erro: O e-mail informado é inválido.")
                    
                elif verificar_duplicidade(conn, doc_validado, email, tel_validado, usuario_id):
                    st.error("🚫 Erro: Dados duplicados detectados (CPF/CNPJ, e-mail ou telefone já cadastrados).")
                    
                else:
                    # Se passou em tudo, grava na base os valores sanitizados e limpos
                    conn.execute("""
                        INSERT INTO clientes (id_usuario, nome_cliente, cpf_cnpj, ddd, telefone, email, contato_pessoa, endereco, observacao, is_revendedor, comissao) 
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    """, (usuario_id, nome, doc_validado, ddd_validado, tel_validado, email, contato, end, obs, (1 if is_rev else 0), comissao_cad))
                    conn.commit()
                    st.success("✅ Cadastrado com sucesso!")
                    st.session_state.key_cli += 1
                    time.sleep(1)
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
            st.subheader("✏ Alterar Cliente")
            df_c = pd.read_sql_query(f"SELECT * FROM clientes WHERE id_usuario = {usuario_id}", conn)
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
                        en = c1.text_input("Nome*", value=c_data['nome_cliente'])
                        
                        # Carrega o dado atual bruto vindo do banco de dados
                        ed_raw = c2.text_input("CPF/CNPJ", value=c_data['cpf_cnpj'], max_chars=14)
                        ee = c1.text_input("Email*", value=c_data['email'])
                        ect = c2.text_input("Contato", value=c_data['contato_pessoa'])
                        
                        d1, d2, d3 = st.columns([0.6, 1.5, 3])
                        eddd_raw = d1.text_input("DDD", value=c_data['ddd'], max_chars=2)
                        etel_raw = d2.text_input("Tel", value=c_data['telefone'], max_chars=9)
                        eend = d3.text_input("Endereço", value=c_data['endereco'])
                        eob = st.text_area("Observações", value=c_data['observacao'])
                        
                        col_btn1, col_btn2 = st.columns(2)
                        
                        if col_btn1.form_submit_button("💾 Salvar Alterações"):
                            ed_validado = re.sub(r'\D', '', ed_raw)
                            eddd_validado = re.sub(r'\D', '', eddd_raw)
                            etel_validado = re.sub(r'\D', '', etel_raw)
                            
                            if not en or not ee or not eddd_raw or not etel_raw:
                                st.error("🚫 Nome, Email, DDD e Telefone são obrigatórios.")
                            elif ed_raw and (len(ed_raw) != len(ed_validado)):
                                st.error("🚫 O campo CPF/CNPJ aceita apenas valores numéricos ou vazio.")
                            elif len(eddd_raw) != len(eddd_validado):
                                st.error("🚫 O campo DDD aceita apenas valores numéricos.")
                            elif len(etel_raw) != len(etel_validado):
                                st.error("🚫 O campo Telefone aceita apenas valores numéricos.")
                            elif not validar_email(ee):
                                st.error("🚫 Erro: O e-mail informado é inválido.")
                            elif verificar_duplicidade(conn, ed_validado, ee, etel_validado, usuario_id, id_cli):
                                st.error("🚫 Erro: Duplicidade detectada.")
                            else:
                                conn.execute("""
                                    UPDATE clientes SET nome_cliente=?, cpf_cnpj=?, ddd=?, telefone=?, email=?, contato_pessoa=?, endereco=?, observacao=?, is_revendedor=?, comissao=? WHERE id=? and id_usuario=?
                                """, (en, ed_validado, eddd_validado, etel_validado, ee, ect, eend, eob, (1 if ere else 0), com_ed, id_cli, usuario_id))
                                conn.commit()
                                st.success("✅ Atualizado!")
                                time.sleep(1)
                                st.rerun()
                                                    
                    if col_btn2.form_submit_button("🗑 EXCLUIR"):
                        try:
                            conn.execute("DELETE FROM clientes WHERE id=? AND id_usuario=?", (id_cli, usuario_id))
                            conn.commit()
                            st.success("Cliente removido com sucesso!")
                            time.sleep(1)
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("⚠ Não é possível excluir este cliente pois existem vendas ou movimentações vinculadas ao nome dele.")
    conn.close()
