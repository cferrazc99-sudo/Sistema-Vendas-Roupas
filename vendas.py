import streamlit as st
import pandas as pd
import time
import base64
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from database import conectar

# --- FUNÇÕES DE APOIO ---
def m(valor):
    """Formatação Moeda Real R$ 1.234,56"""
    try:
        if valor is None: return "R$ 0,00"
        return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except: return "R$ 0,00"

def img_to_b64(blob):
    if blob: return f"data:image/png;base64,{base64.b64encode(blob).decode()}"
    return None

def aplicar_estilos():
    """Injeta CSS para Cabeçalhos Azul Petróleo e Efeito Zoom"""
    st.markdown("""
    <style>
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
    .zoom:hover { transform: scale(3.5); transition: 0.4s; z-index: 999; position: relative; border: 2px solid #005f6b; }
    </style>
    """, unsafe_allow_html=True)

def renderizar_tabela_estilizada(df):
    """Gera tabela HTML centralizada com cabeçalho Azul Petróleo"""
    header_html = "".join([f'<th style="background-color: #005f73; color: white; font-weight: bold; text-align: center; padding: 10px; border: 1px solid #ccc;">{col}</th>' for col in df.columns])
    rows_html = ""
    for _, row in df.iterrows():
        rows_html += "<tr>" + "".join([f'<td style="text-align: center; padding: 8px; border: 1px solid #eee;">{val}</td>' for val in row]) + "</tr>"
    html = f"""<div style="display: flex; justify-content: center;"><table style="width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 13px;"><thead><tr>{header_html}</tr></thead><tbody>{rows_html}</tbody></table></div>"""
    st.markdown(html, unsafe_allow_html=True)

def calcular_vencimentos(data_venda, frequencia, qtd):
    datas = []
    for i in range(1, qtd + 1):
        if frequencia == "Semanal": nova_data = data_venda + timedelta(weeks=i)
        elif frequencia == "Quinzenal": nova_data = data_venda + timedelta(days=15*i)
        else: nova_data = data_venda + relativedelta(months=i)
        datas.append(nova_data.strftime('%Y-%m-%d'))
    return datas

def modulo_vendas():
    aplicar_estilos()
    st.title("💰 Gestão de Vendas PRO")
    conn = conectar()
    
    if 'carrinho' not in st.session_state: st.session_state.carrinho = []
    if 'v_reset_key' not in st.session_state: st.session_state.v_reset_key = 0

    tab1, tab_fin, tab2, tab3 = st.tabs([
        "🆕 Registrar Venda", 
        "📊 Financeiro Vendas", 
        "📜 Histórico", 
        "✏ Editar/Excluir Venda"
    ])

    # ==========================================
    # TAB 1: REGISTRAR VENDA
    # ==========================================
    with tab1:
        rk = st.session_state.v_reset_key
        c1, c2 = st.columns(2)
        dt_venda = c1.date_input("Data da Venda", date.today(), key=f"dt_v_{rk}")
        df_cli = pd.read_sql_query("SELECT id, nome_cliente, is_revendedor, comissao FROM clientes", conn)
        cli_opts = {row['nome_cliente']: row for _, row in df_cli.iterrows()}
        sel_cli = c2.selectbox("Selecione o Cliente:", [""] + list(cli_opts.keys()), key=f"cli_{rk}")
        
        if sel_cli:
            cliente = cli_opts[sel_cli]
            st.divider()
            
            df_p = pd.read_sql_query("SELECT id, referencia, nome_produto, tamanho, foto, valor_compra FROM produtos WHERE vendido = 0", conn)
            ids_no_carro = [item['id'] for item in st.session_state.carrinho]
            df_p = df_p[~df_p['id'].isin(ids_no_carro)]
            
            if not df_p.empty:
                p_opts = {f"{r.referencia} - {r.nome_produto}": r for r in df_p.itertuples()}
                sel_prod = st.selectbox("Escolha o Produto:", [""] + list(p_opts.keys()), key=f"psel_{rk}")
                if sel_prod:
                    p = p_opts[sel_prod]
                    custo = float(p.valor_compra)
                    cp1, cp2, cp3 = st.columns([1, 2, 1.5])
                    img = img_to_b64(p.foto)
                    if img: cp1.markdown(f'<img src="{img}" class="zoom" style="width:120px">', unsafe_allow_html=True)
                    
                    cp2.write(f"**Preço de Custo:** {m(custo)}")
                    ganho = cp2.number_input("Percentual de Ganho (%)", 0.0, 500.0, 100.0, step=5.0, key=f"g_{p.id}")
                    venda_val = custo * (1 + (ganho / 100))
                    comis_val = venda_val * (cliente['comissao']/100) if cliente['is_revendedor'] else 0.0
                    lucro_val = venda_val - custo - comis_val
                    
                    cp3.metric("Preço Venda", m(venda_val))
                    cp3.metric("Valor de Revenda", m(comis_val))
                    cp3.metric("Lucro Estimado", m(lucro_val))
                    
                    f1, f2, f3 = st.columns(3)
                    v_ent = f1.number_input("Valor de Entrada", 0.0, venda_val, 0.0, key=f"e_{p.id}")
                    q_parc = f2.number_input("Quantidade de Parcelas", 1, 36, 1, key=f"q_{p.id}")
                    freq = f3.selectbox("Periodicidade", ["Semanal", "Quinzenal", "Mensal"], key=f"f_{p.id}")
                    
                    v_p = (venda_val - v_ent)/q_parc if q_parc > 0 else 0
                    vcs = calcular_vencimentos(dt_venda, freq, q_parc)
                    
                    df_simul = pd.DataFrame({
                        "Parcela": [f"{i+1}ª" for i in range(q_parc)], 
                        "Vencimento": [datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m/%Y') for d in vcs], 
                        "Valor": [m(v_p)] * q_parc
                    })
                    renderizar_tabela_estilizada(df_simul)
                    
                    if st.button("➕ INCLUIR NO PEDIDO"):
                        st.session_state.carrinho.append({
                            'id': p.id, 'ref': p.referencia, 'nome': p.nome_produto, 'tam': p.tamanho, 
                            'foto': p.foto, 'custo': custo, 'venda': venda_val, 'comis': comis_val, 
                            'lucro': lucro_val, 'entrada': v_ent, 'vencimentos': vcs, 'v_parc': v_p, 'qtd': q_parc
                        })
                        st.rerun()

        if st.session_state.carrinho:
            st.divider()
            st.subheader("🛒 Itens do Pedido")
            itens_resumo = []
            for item in st.session_state.carrinho:
                itens_resumo.append({"Ref": item['ref'], "Produto": item['nome'], "Venda": m(item['venda'])})
            st.table(pd.DataFrame(itens_resumo))
            
            if st.button("💾 FINALIZAR E SALVAR VENDA", type="primary", use_container_width=True):
                cur = conn.cursor()
                for i in st.session_state.carrinho:
                    cur.execute("INSERT INTO vendas (id_produto, id_cliente, valor_venda, valor_lucro, valor_comissao, data_venda, valor_entrada, num_parcelas) VALUES (?,?,?,?,?,?,?,?)", 
                                   (i['id'], cliente['id'], i['venda'], i['lucro'], i['comis'], str(dt_venda), i['entrada'], i['qtd']))
                    id_v = cur.lastrowid
                    cur.execute("UPDATE produtos SET vendido=1 WHERE id=?", (i['id'],))
                    for idx_p, v_d in enumerate(i['vencimentos']):
                        cur.execute("INSERT INTO vendas_pagamentos (id_venda, num_parcela, data_vencimento, valor_parcela, pago) VALUES (?,?,?,?,0)", (id_v, idx_p+1, v_d, i['v_parc']))
                conn.commit()
                st.session_state.carrinho = []
                st.session_state.v_reset_key += 1
                st.success("✅ Venda Salva!")
                time.sleep(1.5)
                st.rerun()

    # ==========================================
    # TAB_FIN: FINANCEIRO VENDAS
    # ==========================================
    with tab_fin:
        query_fin = """
            SELECT vp.*, p.nome_produto, c.nome_cliente 
            FROM vendas_pagamentos vp
            JOIN vendas v ON vp.id_venda = v.id
            JOIN produtos p ON v.id_produto = p.id
            JOIN clientes c ON v.id_cliente = c.id
        """
        df_f_base = pd.read_sql_query(query_fin, conn)

        if not df_f_base.empty:
            hoje = date.today()
            df_f_base['venc_dt'] = pd.to_datetime(df_f_base['data_vencimento']).dt.date
            df_f_base['status_label'] = df_f_base.apply(lambda x: "PAGO" if x['pago']==1 else ("ATRASADO" if x['venc_dt'] < hoje else "PENDENTE"), axis=1)

            # Métricas
            m1, m2, m3 = st.columns(3)
            m1.metric("✅ Total Recebido", m(df_f_base[df_f_base['pago']==1]['valor_parcela'].sum()))
            m2.metric("⏳ Pendente", m(df_f_base[df_f_base['status_label']=="PENDENTE"]['valor_parcela'].sum()))
            m3.metric("🚨 Atrasado", m(df_f_base[df_f_base['status_label']=="ATRASADO"]['valor_parcela'].sum()))

            st.markdown("---")
            c_f1, c_f2, c_f3 = st.columns([1.5, 1, 1])
            f_cli = c_f1.selectbox("Filtrar Cliente", ["Todos"] + sorted(df_f_base['nome_cliente'].unique().tolist()), key="f_cli_fin")
            f_status = c_f2.selectbox("Filtrar Status", ["Todos", "PENDENTE", "PAGO", "ATRASADO"], key="f_sta_fin")
            f_ordem = c_f3.selectbox("Ordenar por", ["Vencimento", "Cliente", "Valor", "ID"], key="f_ord_fin")

            df_v_fin = df_f_base.copy()
            if f_cli != "Todos": df_v_fin = df_v_fin[df_v_fin['nome_cliente'] == f_cli]
            if f_status != "Todos": df_v_fin = df_v_fin[df_v_fin['status_label'] == f_status]
            
            mapa_ordem = {"Vencimento": "venc_dt", "Cliente": "nome_cliente", "Valor": "valor_parcela", "ID": "id"}
            df_v_fin = df_v_fin.sort_values(by=mapa_ordem[f_ordem])

            # Cabeçalho Grade
            cols_h = st.columns([0.6, 1.5, 2, 0.6, 1.1, 1.1, 1, 0.8])
            titulos = ["ID", "Cliente", "Produto", "Parc.", "Vencimento", "Valor", "Status", "Ação"]
            for col, t in zip(cols_h, titulos):
                col.markdown(f'<div class="header-petroleo">{t}</div>', unsafe_allow_html=True)

            for _, r in df_v_fin.iterrows():
                row = st.columns([0.6, 1.5, 2, 0.6, 1.1, 1.1, 1, 0.8])
                cor_st = "green" if r['pago']==1 else ("red" if r['status_label']=="ATRASADO" else "#005f6b")
                
                # CORREÇÃO: Usando índices row[i] para evitar o erro AttributeError
                row[0].markdown(f'<div class="cell-data">{r["id"]}</div>', unsafe_allow_html=True)
                row[1].markdown(f'<div class="cell-data">{r["nome_cliente"]}</div>', unsafe_allow_html=True)
                row[2].markdown(f'<div class="cell-data">{r["nome_produto"]}</div>', unsafe_allow_html=True)
                row[3].markdown(f'<div class="cell-data">{r["num_parcela"]}</div>', unsafe_allow_html=True)
                row[4].markdown(f'<div class="cell-data">{r["venc_dt"].strftime("%d/%m/%Y")}</div>', unsafe_allow_html=True)
                row[5].markdown(f'<div class="cell-data">{m(r["valor_parcela"])}</div>', unsafe_allow_html=True)
                row[6].markdown(f'<div class="cell-data"><b style="color:{cor_st}">{r["status_label"]}</b></div>', unsafe_allow_html=True)
                
                if row[7].button("RECEBER" if r['pago']==0 else "↩", key=f"rec_{r['id']}", use_container_width=True):
                    conn.execute("UPDATE vendas_pagamentos SET pago=? WHERE id=?", (1 if r['pago']==0 else 0, r['id']))
                    conn.commit(); st.rerun()

    # ==========================================
    # TAB 2: HISTÓRICO GERENCIAL
    # ==========================================
    with tab2:
        query_h = """SELECT v.data_venda as Data, p.foto, p.referencia, p.nome_produto as Nome, p.tamanho as Tam, c.nome_cliente as Cliente, v.valor_venda as Venda, v.num_parcelas as Parcelas, ((v.valor_venda - v.valor_entrada) / v.num_parcelas) as Vl_Parc, v.valor_entrada as Entrada, p.valor_compra as Compra, v.valor_comissao as Comis, v.valor_lucro as Lucro FROM vendas v JOIN produtos p ON v.id_produto = p.id JOIN clientes c ON v.id_cliente = c.id ORDER BY v.id DESC"""
        df_h = pd.read_sql_query(query_h, conn)
        if not df_h.empty:
            df_h['Data_dt'] = pd.to_datetime(df_h['Data']).dt.date
            f1, f2 = st.columns(2)
            sel_c = f1.selectbox("Filtrar Cliente:", ["Todos"] + sorted(list(df_h['Cliente'].unique())), key="h_cli")
            per = f2.date_input("Filtrar Período:", [df_h['Data_dt'].min(), df_h['Data_dt'].max()], key="h_per")
            df_f = df_h.copy()
            if sel_c != "Todos": df_f = df_f[df_f['Cliente'] == sel_c]
            if isinstance(per, (list, tuple)) and len(per) == 2:
                df_f = df_f[(df_f['Data_dt'] >= per[0]) & (df_f['Data_dt'] <= per[1])]
            
            mh1, mh2 = st.columns(2)
            mh1.metric("Vendas Período", m(df_f['Venda'].sum())); mh2.metric("Lucro Período", m(df_f['Lucro'].sum()))
            
            st.markdown("""<div style="background-color: #005f73; padding: 10px; border-radius: 5px; color: white; font-weight: bold; font-size: 12px; text-align:center;"><table style="width:100%; border-collapse: collapse;"><tr><td style="width:7%">Data</td><td style="width:6%">Foto</td><td style="width:8%">Ref</td><td style="width:12%">Nome</td><td style="width:4%">Tam</td><td style="width:11%">Cliente</td><td style="width:8%">Venda</td><td style="width:6%">Parcelas</td><td style="width:8%">Vl.Parc</td><td style="width:8%">Entrada</td><td style="width:8%">Compra</td><td style="width:8%">Comis</td><td style="width:7%">Lucro</td></tr></table></div>""", unsafe_allow_html=True)
            for _, r in df_f.iterrows():
                row_h = st.columns([0.7, 0.6, 0.8, 1.2, 0.4, 1.1, 0.8, 0.6, 0.8, 0.8, 0.8, 0.8, 0.7])
                row_h[0].write(datetime.strptime(r['Data'], '%Y-%m-%d').strftime('%d/%m/%y'))
                img = img_to_b64(r['foto'])
                if img: row_h[1].markdown(f'<img src="{img}" class="zoom" style="width:40px">', unsafe_allow_html=True)
                else: row_h[1].write("🖼")
                row_h[2].write(r['referencia']); row_h[3].write(r['Nome']); row_h[4].write(r['Tam']); row_h[5].write(r['Cliente'])
                row_h[6].write(m(r['Venda'])); row_h[7].write(f"{r['Parcelas']}x"); row_h[8].write(m(r['Vl_Parc'])); row_h[9].write(m(r['Entrada']))
                row_h[10].write(m(r['Compra'])); row_h[11].write(m(r['Comis']))
                cor_l = "green" if r['Lucro']>0 else "red"
                row_h[12].markdown(f":{cor_l}[{m(r['Lucro'])}]")

    # ==========================================
    # TAB 3: EDITAR / EXCLUIR
    # ==========================================
    with tab3:
        st.subheader("✏ Alteração e Renegociação")
        df_v_edit = pd.read_sql_query("""SELECT v.id, v.data_venda, c.nome_cliente, p.referencia, p.nome_produto, v.id_produto FROM vendas v JOIN clientes c ON v.id_cliente = c.id JOIN produtos p ON v.id_produto = p.id ORDER BY v.id DESC""", conn)
        opts_v = {f"ID {r.id} | {r.nome_cliente} | {r.referencia} - {r.nome_produto}": (r.id, r.id_produto) for r in df_v_edit.itertuples()}
        sel_v = st.selectbox("Selecione a venda:", [""] + list(opts_v.keys()), key=f"sel_v_ed_{st.session_state.v_reset_key}")
        
        if sel_v:
            id_v, id_prod = opts_v[sel_v]
            v_info = conn.execute("SELECT * FROM vendas WHERE id=?", (id_v,)).fetchone()
            # v_info: [id, id_produto, id_cliente, valor_venda, valor_lucro, valor_comissao, data_venda, valor_entrada, num_parcelas]
            
            p_data = conn.execute("SELECT foto, valor_compra, nome_produto, referencia FROM produtos WHERE id=?", (id_prod,)).fetchone()
            c_data = conn.execute("SELECT comissao, is_revendedor FROM clientes WHERE id=?", (v_info[2],)).fetchone()
            
            p_pago = pd.read_sql_query(f"SELECT pago FROM vendas_pagamentos WHERE id_venda={id_v}", conn)['pago'].any()
            if p_pago: st.error("🚫 BLOQUEIO: Existem parcelas pagas.")
            
            ce1, ce2 = st.columns([1, 3])
            img_ed = img_to_b64(p_data[0])
            if img_ed: ce1.markdown(f'<img src="{img_ed}" class="zoom" style="width:150px">', unsafe_allow_html=True)
            custo_p = float(p_data[1])
            ce2.metric("💵 Custo Original", m(custo_p))
            ce2.write(f"**Produto:** {p_data[2]} | **Ref:** {p_data[3]}")
            st.divider()
            
            cs1, cs2, cs3 = st.columns(3)
            g_at = ((float(v_info[3]) / custo_p) - 1) * 100
            new_g = cs1.number_input("Novo Ganho (%)", 0.0, 500.0, float(g_at), step=5.0, disabled=p_pago, key="ed_g")
            new_v = custo_p * (1 + (new_g / 100))
            new_e = cs2.number_input("Nova Entrada", 0.0, new_v, float(v_info[7]), disabled=p_pago, key="ed_e")
            new_q = cs3.number_input("Novas Parcelas", 1, 36, int(v_info[8]), disabled=p_pago, key="ed_q")
            new_dt = cs1.date_input("Nova Data", datetime.strptime(v_info[6], '%Y-%m-%d').date(), disabled=p_pago, key="ed_dt")
            new_fr = cs2.selectbox("Nova Periodicidade", ["Semanal", "Quinzenal", "Mensal"], disabled=p_pago, key="ed_fr")
            
            new_comis = new_v * (c_data[0] / 100) if c_data[1] else 0.0
            new_lucro = new_v - custo_p - new_comis
            
            re1, re2, re3, re4 = st.columns(4)
            re1.metric("Custo", m(custo_p)); re2.metric("Venda", m(new_v)); re3.metric("Revenda", m(new_comis)); re4.metric("Lucro Líquido", m(new_lucro))
            
            v_p_n = (new_v - new_e) / new_q if new_q > 0 else 0
            vcs_n = calcular_vencimentos(new_dt, new_fr, new_q)
            df_sim_edt = pd.DataFrame({"Parcela": [f"{i+1}ª" for i in range(new_q)], "Vencimento": [datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m/%Y') for d in vcs_n], "Valor": [m(v_p_n)] * new_q})
            renderizar_tabela_estilizada(df_sim_edt)
            
            be1, be2 = st.columns(2)
            if be1.button("💾 CONFIRMAR ALTERAÇÕES", type="primary", disabled=p_pago, use_container_width=True):
                conn.execute("UPDATE vendas SET valor_venda=?, valor_lucro=?, valor_comissao=?, data_venda=?, valor_entrada=?, num_parcelas=? WHERE id=?", (new_v, new_lucro, new_comis, str(new_dt), new_e, new_q, id_v))
                conn.execute("DELETE FROM vendas_pagamentos WHERE id_venda=?", (id_v,))
                for idx, vd in enumerate(vcs_n): 
                    conn.execute("INSERT INTO vendas_pagamentos (id_venda, num_parcela, data_vencimento, valor_parcela, pago) VALUES (?,?,?,?,0)", (id_v, idx+1, vd, v_p_n))
                conn.commit(); st.session_state.v_reset_key += 1; st.success("Atualizado!"); time.sleep(1.5); st.rerun()
            
            if be2.button("🗑 EXCLUIR VENDA TOTALMENTE", disabled=p_pago, use_container_width=True):
                conn.execute("DELETE FROM vendas_pagamentos WHERE id_venda=?;", (id_v,))
                conn.execute("UPDATE produtos SET vendido=0 WHERE id=?;", (id_prod,))
                conn.execute("DELETE FROM vendas WHERE id=?;", (id_v,))
                conn.commit(); st.session_state.v_reset_key += 1; st.warning("Excluída!"); time.sleep(1.5); st.rerun()

    conn.close()

if __name__ == "__main__":
    modulo_vendas()
