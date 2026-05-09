import streamlit as st
import pandas as pd
import base64
import time
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from database import conectar

# =========================================================================
# 1. UTILITÁRIOS, FORMATAÇÃO E CSS (RESTAURADO TOTAL)
# =========================================================================

def m(valor):
    """Formatação de Moeda Real R$ 1.234,56"""
    try:
        if valor is None: return "R$ 0,00"
        return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except: return "R$ 0,00"

def img_to_b64(blob):
    """Converte binário para base64 para efeito Zoom"""
    if blob:
        return f"data:image/png;base64,{base64.b64encode(blob).decode()}"
    return None

def aplicar_estilos():
    """Injeta CSS para Cabeçalhos Azul Petróleo, Zoom e Fidelidade Visual"""
    st.markdown("""
        <style>
            .main .block-container { max-width: 98% !important; padding-top: 1rem; }
            .zoom:hover { transform: scale(3.5); transition: 0.4s; z-index: 999; position: relative; border: 2px solid #005f6b; }
            .header-petroleo {
                background-color: #005f6b !important;
                color: #FFFFFF !important;
                font-weight: bold !important;
                padding: 12px 5px;
                text-align: center;
                border-radius: 4px;
                font-size: 0.85rem;
                text-transform: uppercase;
                margin-bottom: 2px;
            }
            .cell-data {
                display: flex; align-items: center; justify-content: center;
                height: 50px; text-align: center; border-bottom: 1px solid #f0f2f6; font-size: 0.85rem;
            }
            [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #005f6b; font-weight: bold; }
            .msg-bloqueio { 
                padding: 15px; border-radius: 8px; background-color: #fff3cd; 
                color: #856404; font-weight: bold; border: 1px solid #ffeeba; text-align: center; 
            }
        </style>
    """, unsafe_allow_html=True)

def gerar_grade_vencimentos(data_ini, qtd, total, entrada, periodicidade):
    """Lógica de Periodicidade Dinâmica"""
    grade = []
    valor_parc = (total - entrada) / qtd if qtd > 0 else 0
    for i in range(int(qtd)):
        if periodicidade == "Semanal":
            dt = data_ini + relativedelta(weeks=i+1)
        elif periodicidade == "Quinzenal":
            dt = data_ini + relativedelta(days=(i+1)*15)
        else: # Mensal
            dt = data_ini + relativedelta(months=i+1)
        #grade.append({"Parcela": f"{i+1}ª", "Vencimento": dt, "Valor": valor_parc})
        grade.append({"Parcela": i+1, "Vencimento": dt, "Valor": valor_parc})

    return pd.DataFrame(grade)

# =========================================================================
# 2. MÓDULO PRINCIPAL: GESTÃO DE COMPRAS
# =========================================================================

def modulo_compras():
    aplicar_estilos()
    st.title("📦 Gestão de Compras e Fluxo Financeiro")
    
    try:
        conn = conectar()
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return

    # Controle de Sessão para Limpeza e Chaves Únicas
    if 'key_reg' not in st.session_state: st.session_state.key_reg = 100
    if 'key_edt' not in st.session_state: st.session_state.key_edt = 500

    # Carregamento de Dados Base
    df_forn = pd.read_sql_query("SELECT id, nome_empresa FROM fornecedores ORDER BY nome_empresa", conn)
    df_prod = pd.read_sql_query("SELECT * FROM produtos", conn)
    
    tabs = st.tabs(["🆕 Registrar Compra", "📊 Financeiro Fornecedores", "🔍 Auditoria de Estoque", "✏ Editar/Excluir"])

    # --- ABA 1: REGISTRAR COMPRA ---
    with tabs[0]:
        st.subheader("Entrada de Mercadoria")
        k = st.session_state.key_reg
        c1, c2, c3 = st.columns([1, 2, 1])
        r_ref = c1.text_input("Ref / SKU", key=f"r1_{k}")
        r_nom = c2.text_input("Nome do Produto*", key=f"r2_{k}")
        r_tam = c3.text_input("Tamanho", key=f"r3_{k}")
        
        f1, f2 = st.columns([2, 1])
        r_for = f1.selectbox("Fornecedor", df_forn['nome_empresa'].tolist(), key=f"r4_{k}")
        r_img = f2.file_uploader("Foto da Peça", type=['jpg', 'png'], key=f"r5_{k}")
        
        st.markdown("#### Configuração Financeira")
        v1, v2, v3, v4, v5 = st.columns(5)
        v_tot = v1.number_input("Valor Total", min_value=0.0, step=0.01, key=f"v1_{k}")
        v_ent = v2.number_input("Entrada", min_value=0.0, step=0.01, key=f"v2_{k}")
        v_par = v3.number_input("Nº Parcelas", min_value=1, value=1, key=f"v3_{k}")
        v_per = v4.selectbox("Periodicidade", ["Mensal", "Quinzenal", "Semanal"], key=f"v4_{k}")
        v_dat = v5.date_input("Data Compra", date.today(), key=f"v5_{k}")

        df_sim = gerar_grade_vencimentos(v_dat, v_par, v_tot, v_ent, v_per)
        st.write("📋 **Simulação Financeira:**")
        st.dataframe(df_sim.assign(Valor=df_sim['Valor'].map(m)), use_container_width=True, hide_index=True)

        with st.form("f_reg"):
            if st.form_submit_button("🚀 SALVAR COMPRA", use_container_width=True):
                if r_nom and v_tot > 0:
                    id_f = int(df_forn[df_forn['nome_empresa'] == r_for]['id'].iloc[0])
                    v_unit = (v_tot - v_ent) / v_par
                    cur = conn.cursor()
                    cur.execute("""INSERT INTO produtos (referencia, nome_produto, tamanho, foto, id_fornecedor, 
                                valor_compra, valor_entrada, num_parcelas, valor_parcela, data_compra, vendido) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,0)""", 
                                (r_ref, r_nom, r_tam, r_img.read() if r_img else None, id_f, v_tot, v_ent, v_par, v_unit, str(v_dat)))
                    id_p = cur.lastrowid
                    for _, row in df_sim.iterrows():
                        cur.execute("INSERT INTO fluxo_pagamentos (id_produto, referencia, num_parcela, data_vencimento, valor_parcela, pago) VALUES (?,?,?,?,?,0)",
                                   (id_p, r_ref, int(row['Parcela']), str(row['Vencimento']), row['Valor']))
                    conn.commit()
                    st.success("✅ Compra registrada!")
                    st.session_state.key_reg += 1
                    time.sleep(0.5); st.rerun()

    # --- ABA 2: FINANCEIRO (INTEGRIDADE RECUPERADA) ---
    with tabs[1]:
        df_f_base = pd.read_sql_query("""SELECT fl.*, p.nome_produto, f.nome_empresa FROM fluxo_pagamentos fl 
                                      JOIN produtos p ON fl.id_produto = p.id 
                                      LEFT JOIN fornecedores f ON p.id_fornecedor = f.id""", conn)
        if not df_f_base.empty:
            hoje = date.today()
            df_f_base['venc_dt'] = pd.to_datetime(df_f_base['data_vencimento']).dt.date
            df_f_base['status_label'] = df_f_base.apply(lambda x: "PAGO" if x['pago']==1 else ("ATRASADO" if x['venc_dt'] < hoje else "PENDENTE"), axis=1)
            
            # Métricas (Restauradas)
            m1, m2, m3 = st.columns(3)
            m1.metric("✅ Total Pago", m(df_f_base[df_f_base['pago']==1]['valor_parcela'].sum()))
            m2.metric("⏳ Pendente", m(df_f_base[df_f_base['status_label']=="PENDENTE"]['valor_parcela'].sum()))
            m3.metric("🚨 Atrasado", m(df_f_base[df_f_base['status_label']=="ATRASADO"]['valor_parcela'].sum()))

            st.markdown("---")
            c_f1, c_f2, c_f3 = st.columns([1.5, 1, 1])
            f_forn = c_f1.selectbox("Filtrar Fornecedor", ["Todos"] + df_forn['nome_empresa'].tolist())
            f_status = c_f2.selectbox("Filtrar Status", ["Todos", "PENDENTE", "PAGO", "ATRASADO"])
            f_ordem = c_f3.selectbox("Ordenar por", ["Vencimento", "Fornecedor", "Valor", "Produto", "ID"])
            
            df_v = df_f_base.copy()
            if f_forn != "Todos": df_v = df_v[df_v['nome_empresa'] == f_forn]
            if f_status != "Todos": df_v = df_v[df_v['status_label'] == f_status]
            
            mapa_ordem = {"Vencimento": "venc_dt", "Fornecedor": "nome_empresa", "Valor": "valor_parcela", "Produto": "nome_produto", "ID": "id"}
            df_v = df_v.sort_values(by=mapa_ordem[f_ordem])

            cols_fin = st.columns([0.6, 1.5, 2, 0.6, 1.1, 1.1, 1, 0.8])
            for col, h in zip(cols_fin, ["ID", "Fornecedor", "Produto", "Parc.", "Vencimento", "Valor", "Status", "Ação"]):
                col.markdown(f'<div class="header-petroleo">{h}</div>', unsafe_allow_html=True)

            for _, r in df_v.iterrows():
                row = st.columns([0.6, 1.5, 2, 0.6, 1.1, 1.1, 1, 0.8])
                cor_st = "green" if r['pago']==1 else ("red" if r['status_label']=="ATRASADO" else "#005f6b")
                row[0].markdown(f'<div class="cell-data">{r["id"]}</div>', unsafe_allow_html=True)
                row[1].markdown(f'<div class="cell-data">{r["nome_empresa"]}</div>', unsafe_allow_html=True)
                row[2].markdown(f'<div class="cell-data">{r["nome_produto"]}</div>', unsafe_allow_html=True)
                row[3].markdown(f'<div class="cell-data">{r["num_parcela"]}</div>', unsafe_allow_html=True)
                row[4].markdown(f'<div class="cell-data">{r["venc_dt"].strftime("%d/%m/%Y")}</div>', unsafe_allow_html=True)
                row[5].markdown(f'<div class="cell-data">{m(r["valor_parcela"])}</div>', unsafe_allow_html=True)
                row[6].markdown(f'<div class="cell-data"><b style="color:{cor_st}">{r["status_label"]}</b></div>', unsafe_allow_html=True)
                if row[7].button("PAGAR" if r['pago']==0 else "↩", key=f"f_{r['id']}"):
                    conn.execute("UPDATE fluxo_pagamentos SET pago=? WHERE id=?", (1 if r['pago']==0 else 0, r['id']))
                    conn.commit(); st.rerun()

    # --- ABA 3: AUDITORIA (CABEÇALHO AZUL + FILTROS) ---
    with tabs[2]:
        ca1, ca2, ca3 = st.columns([2, 1, 1])
        f_aud_desc = ca1.text_input("Filtrar por Descrição")
        f_aud_status = ca2.selectbox("Status Estoque", ["Todos", "Em Estoque", "Vendido"])
        f_aud_forn = ca3.selectbox("Fornecedor Auditoria", ["Todos"] + df_forn['nome_empresa'].tolist())

        df_a = df_prod.copy()
        if f_aud_desc: df_a = df_a[df_a['nome_produto'].str.contains(f_aud_desc, case=False)]
        if f_aud_status == "Em Estoque": df_a = df_a[df_a['vendido'] == 0]
        elif f_aud_status == "Vendido": df_a = df_a[df_a['vendido'] == 1]
        if f_aud_forn != "Todos":
            id_f_aud = df_forn[df_forn['nome_empresa'] == f_aud_forn]['id'].iloc[0]
            df_a = df_a[df_a['id_fornecedor'] == id_f_aud]

        h_aud = st.columns([0.5, 0.7, 1.2, 1, 2.2, 0.6, 1, 1])
        for col, t in zip(h_aud, ["ID", "Foto", "Fornecedor", "Ref", "Descrição", "Tam", "Custo", "Status"]):
            col.markdown(f'<div class="header-petroleo">{t}</div>', unsafe_allow_html=True)
        
        for _, r in df_a.iterrows():
            ac = st.columns([0.5, 0.7, 1.2, 1, 2.2, 0.6, 1, 1])
            ac[0].markdown(f'<div class="cell-data">{r["id"]}</div>', unsafe_allow_html=True)
            b64 = img_to_b64(r['foto']); img_html = f'<img src="{b64}" class="zoom" width="45">' if b64 else "🖼️"
            ac[1].markdown(f'<div class="cell-data">{img_html}</div>', unsafe_allow_html=True)
            f_nome_aud = df_forn[df_forn['id'] == r['id_fornecedor']]['nome_empresa'].iloc[0] if not df_forn.empty else ""
            ac[2].markdown(f'<div class="cell-data">{f_nome_aud}</div>', unsafe_allow_html=True)
            ac[3].markdown(f'<div class="cell-data">{r["referencia"]}</div>', unsafe_allow_html=True)
            ac[4].markdown(f'<div class="cell-data">{r["nome_produto"]}</div>', unsafe_allow_html=True)
            ac[5].markdown(f'<div class="cell-data">{r["tamanho"]}</div>', unsafe_allow_html=True)
            ac[6].markdown(f'<div class="cell-data">{m(r["valor_compra"])}</div>', unsafe_allow_html=True)
            st_txt = "🟢 Estoque" if r['vendido']==0 else "🔴 Vendido"
            ac[7].markdown(f'<div class="cell-data">{st_txt}</div>', unsafe_allow_html=True)

    # --- ABA 4: EDITAR/EXCLUIR (RECUPERAÇÃO TOTAL DA TABELA E REGRAS) ---
    with tabs[3]:
        opcoes = [f"ID {r.id} | {r.nome_produto}" for r in df_prod.itertuples()]
        escolha = st.selectbox("Selecione o Item para Editar", [""] + opcoes, key=f"sel_{st.session_state.key_edt}")
        if escolha:
            id_sel = int(escolha.split('|')[0].replace('ID', '').strip())
            item = df_prod[df_prod['id'] == id_sel].iloc[0]
            
            # Verificações de Segurança
            tem_pago = (pd.read_sql_query("SELECT pago FROM fluxo_pagamentos WHERE id_produto=?", conn, params=[id_sel])['pago'] == 1).any()
            foi_vendido = item['vendido'] == 1
            
            col_i, col_f = st.columns([3, 1])
            e_nom = col_i.text_input("Editar Nome", value=item['nome_produto'])
            e_for = col_i.selectbox("Editar Fornecedor", df_forn['nome_empresa'].tolist(), index=df_forn['nome_empresa'].tolist().index(df_forn[df_forn['id']==item['id_fornecedor']]['nome_empresa'].iloc[0]))
            if item['foto']: col_f.image(item['foto'], width=100)
            e_img = col_f.file_uploader("Trocar Imagem")
            
            if tem_pago: st.markdown('<div class="msg-bloqueio">⚠️ Financeiro Bloqueado: Existem parcelas pagas.</div>', unsafe_allow_html=True)
            
            ev1, ev2, ev3, ev4, ev5 = st.columns(5)
            e_vt = ev1.number_input("Novo Valor Total", value=float(item['valor_compra']), disabled=tem_pago)
            e_ve = ev2.number_input("Nova Entrada", value=float(item['valor_entrada']), disabled=tem_pago)
            e_np = ev3.number_input("Parcelas", value=int(item['num_parcelas']), min_value=1, disabled=tem_pago)
            e_pe = ev4.selectbox("Periodicidade", ["Mensal", "Quinzenal", "Semanal"], disabled=tem_pago)
            e_dt = ev5.date_input("Data Base Compra", value=pd.to_datetime(item['data_compra']).date(), disabled=tem_pago)

            # TABELA DE VENCIMENTOS NA EDIÇÃO (RESTAURADA)
            st.markdown("### Visualização da Nova Grade Financeira:")
            df_sim_edt = gerar_grade_vencimentos(e_dt, e_np, e_vt, e_ve, e_pe)
            st.dataframe(df_sim_edt.assign(Valor=df_sim_edt['Valor'].map(m)), use_container_width=True, hide_index=True)

            with st.form("f_edt_submit"):
                if st.form_submit_button("💾 SALVAR ALTERAÇÕES", use_container_width=True):
                    id_forn_e = int(df_forn[df_forn['nome_empresa'] == e_for]['id'].iloc[0])
                    cur = conn.cursor()
                    cur.execute("UPDATE produtos SET nome_produto=?, id_fornecedor=?, foto=?, valor_compra=?, valor_entrada=?, num_parcelas=? WHERE id=?", 
                               (e_nom, id_forn_e, e_img.read() if e_img else item['foto'], e_vt, e_ve, e_np, id_sel))
                    if not tem_pago:
                        cur.execute("DELETE FROM fluxo_pagamentos WHERE id_produto=?", (id_sel,))
                        for _, row in df_sim_edt.iterrows():
                            cur.execute("INSERT INTO fluxo_pagamentos (id_produto, num_parcela, data_vencimento, valor_parcela, pago) VALUES (?,?,?,?,0)", 
                                       (id_sel, int(row['Parcela']), str(row['Vencimento']), row['Valor']))
                    conn.commit(); st.success("Atualizado!"); time.sleep(0.5); st.rerun()

            # BOTÃO DE EXCLUSÃO (RESTAURADO COM TODAS AS LINHAS DE SEGURANÇA)
            st.markdown("---")
            if not tem_pago and not foi_vendido:
                if st.button("🗑️ EXCLUIR DEFINITIVAMENTE", use_container_width=True):
                    conn.execute("DELETE FROM fluxo_pagamentos WHERE id_produto=?", (id_sel,))
                    conn.execute("DELETE FROM produtos WHERE id=?", (id_sel,))
                    conn.commit()
                    st.warning("Item removido do sistema."); time.sleep(0.5); st.rerun()
            else: st.info("ℹ️ Exclusão desabilitada: O item possui histórico de pagamento ou venda.")

    if conn: conn.close()

if __name__ == "__main__":
    modulo_compras()