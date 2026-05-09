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
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def img_to_b64(blob):
    if blob: return f"data:image/png;base64,{base64.b64encode(blob).decode()}"
    return None

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
    st.title("💰 Gestão de Vendas PRO")
    conn = conectar()
    
    if 'carrinho' not in st.session_state: st.session_state.carrinho = []
    if 'v_reset_key' not in st.session_state: st.session_state.v_reset_key = 0

    tab1, tab2, tab3 = st.tabs(["🆕 Registrar Venda", "📜 Histórico", "✏️ Editar/Excluir Venda"])

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
                    ganho = cp2.number_input("Percentual de Ganho sobre o Custo (%)", 0.0, 500.0, 100.0, step=5.0, key=f"g_{p.id}")
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
                    
                    df_simul = pd.DataFrame({"Parcela": [f"{i+1}ª" for i in range(q_parc)], "Vencimento": [datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m/%Y') for d in vcs], "Valor": [m(v_p)] * q_parc})
                    renderizar_tabela_estilizada(df_simul)

                    if st.button("➕ INCLUIR NO PEDIDO"):
                        st.session_state.carrinho.append({'id': p.id, 'ref': p.referencia, 'nome': p.nome_produto, 'tam': p.tamanho, 'foto': p.foto, 'custo': custo, 'venda': venda_val, 'comis': comis_val, 'lucro': lucro_val, 'entrada': v_ent, 'vencimentos': vcs, 'v_parc': v_p, 'qtd': q_parc})
                        st.rerun()
            else: st.warning("Sem produtos em estoque.")

            if st.session_state.carrinho:
                st.divider()
                st.subheader("🛒 Itens do Pedido")
                itens_resumo = []
                for idx, item in enumerate(st.session_state.carrinho):
                    itens_resumo.append({"Ref": item['ref'], "Produto": item['nome'], "Venda": m(item['venda']), "Custo": m(item['custo']), "Revenda": m(item['comis']), "Lucro": m(item['lucro'])})
                st.table(pd.DataFrame(itens_resumo))
                
                st.markdown("### 📊 Resumo Financeiro Total")
                t1, t2, t3, t4 = st.columns(4)
                tc, tv, tr, tl = sum(i['custo'] for i in st.session_state.carrinho), sum(i['venda'] for i in st.session_state.carrinho), sum(i['comis'] for i in st.session_state.carrinho), sum(i['lucro'] for i in st.session_state.carrinho)
                t1.metric("Total Custo", m(tc)); t2.metric("Total Venda", m(tv)); t3.metric("Total Revenda", m(tr)); t4.metric("Lucro Líquido", m(tl))

                if st.button("💾 FINALIZAR E SALVAR VENDA", type="primary", use_container_width=True):
                    cursor = conn.cursor()
                    for i in st.session_state.carrinho:
                        cursor.execute("INSERT INTO vendas (id_produto, id_cliente, valor_venda, valor_lucro, valor_comissao, data_venda, valor_entrada, num_parcelas) VALUES (?,?,?,?,?,?,?,?)", (i['id'], cliente['id'], i['venda'], i['lucro'], i['comis'], str(dt_venda), i['entrada'], i['qtd']))
                        id_v = cursor.lastrowid
                        cursor.execute("UPDATE produtos SET vendido=1 WHERE id=?", (i['id'],))
                        for idx_p, v_d in enumerate(i['vencimentos']):
                            cursor.execute("INSERT INTO vendas_pagamentos (id_venda, num_parcela, data_vencimento, valor_parcela) VALUES (?,?,?,?)", (id_v, idx_p+1, v_d, i['v_parc']))
                    conn.commit(); st.session_state.carrinho = []; st.session_state.v_reset_key += 1; st.success("✅ Venda Salva!"); time.sleep(1.5); st.rerun()

    # ==========================================
    # TAB 2: HISTÓRICO GERENCIAL
    # ==========================================
    with tab2:
        query = """SELECT v.data_venda as Data, p.foto, p.referencia, p.nome_produto as Nome, p.tamanho as Tam, c.nome_cliente as Cliente, v.valor_venda as Venda, v.num_parcelas as Parcelas, ((v.valor_venda - v.valor_entrada) / v.num_parcelas) as Vl_Parc, v.valor_entrada as Entrada, p.valor_compra as Compra, v.valor_comissao as Comis, v.valor_lucro as Lucro FROM vendas v JOIN produtos p ON v.id_produto = p.id JOIN clientes c ON v.id_cliente = c.id ORDER BY v.id DESC"""
        df_h = pd.read_sql_query(query, conn)
        if not df_h.empty:
            df_h['Data_dt'] = pd.to_datetime(df_h['Data']).dt.date
            f1, f2 = st.columns(2)
            sel_c = f1.selectbox("Filtrar Cliente:", ["Todos"] + sorted(list(df_h['Cliente'].unique())))
            per = f2.date_input("Filtrar Período:", [df_h['Data_dt'].min(), df_h['Data_dt'].max()])
            df_f = df_h.copy()
            if sel_c != "Todos": df_f = df_f[df_f['Cliente'] == sel_c]
            if isinstance(per, (list, tuple)) and len(per) == 2:
                df_f = df_f[(df_f['Data_dt'] >= per[0]) & (df_f['Data_dt'] <= per[1])]
            
            m1, m2 = st.columns(2)
            m1.metric("Vendas Período", m(df_f['Venda'].sum())); m2.metric("Lucro Período", m(df_f['Lucro'].sum()))

            st.markdown("""<div style="background-color: #005f73; padding: 10px; border-radius: 5px; color: white; font-weight: bold; font-size: 12px; text-align:center;"><table style="width:100%; border-collapse: collapse;"><tr><td style="width:7%">Data</td><td style="width:6%">Foto</td><td style="width:8%">Ref</td><td style="width:12%">Nome</td><td style="width:4%">Tam</td><td style="width:11%">Cliente</td><td style="width:8%">Venda</td><td style="width:6%">Parcelas</td><td style="width:8%">Vl.Parc</td><td style="width:8%">Entrada</td><td style="width:8%">Compra</td><td style="width:8%">Comis</td><td style="width:7%">Lucro</td></tr></table></div>""", unsafe_allow_html=True)
            for _, r in df_f.iterrows():
                row = st.columns([0.7, 0.6, 0.8, 1.2, 0.4, 1.1, 0.8, 0.6, 0.8, 0.8, 0.8, 0.8, 0.7])
                row[0].write(datetime.strptime(r['Data'], '%Y-%m-%d').strftime('%d/%m/%y'))
                img = img_to_b64(r['foto'])
                if img: row[1].markdown(f'<img src="{img}" class="zoom" style="width:40px">', unsafe_allow_html=True)
                else: row[1].write("🖼️")
                row[2].write(r['referencia']); row[3].write(r['Nome']); row[4].write(r['Tam']); row[5].write(r['Cliente'])
                row[6].write(m(r['Venda'])); row[7].write(f"{r['Parcelas']}x"); row[8].write(m(r['Vl_Parc'])); row[9].write(m(r['Entrada']))
                row[10].write(m(r['Compra'])); row[11].write(m(r['Comis']))
                cor_l = "green" if r['Lucro']>0 else "red"
                row[12].markdown(f":{cor_l}[{m(r['Lucro'])}]")

    # ==========================================
    # TAB 3: EDITAR / EXCLUIR
    # ==========================================
    with tab3:
        st.subheader("✏️ Alteração e Renegociação")
        df_v = pd.read_sql_query("""SELECT v.id, v.data_venda, c.nome_cliente, p.referencia, p.nome_produto FROM vendas v JOIN clientes c ON v.id_cliente = c.id JOIN produtos p ON v.id_produto = p.id ORDER BY v.id DESC""", conn)
        opts_v = {f"ID {r.id} | {r.nome_cliente} | {r.referencia} - {r.nome_produto}": r.id for r in df_v.itertuples()}
        sel_v = st.selectbox("Selecione a venda:", [""] + list(opts_v.keys()), key=f"sel_v_ed_{st.session_state.v_reset_key}")

        if sel_v:
            id_v = opts_v[sel_v]
            v_info = conn.execute("SELECT * FROM vendas WHERE id=?", (id_v,)).fetchone()
            id_prod, id_cli = v_info[1], v_info[2]
            p_data = conn.execute("SELECT foto, valor_compra, nome_produto, referencia FROM produtos WHERE id=?", (id_prod,)).fetchone()
            c_data = conn.execute("SELECT comissao, is_revendedor FROM clientes WHERE id=?", (id_cli,)).fetchone()
            custo_p = float(p_data[1])
            
            p_pago = pd.read_sql_query(f"SELECT pago FROM vendas_pagamentos WHERE id_venda={id_v}", conn)['pago'].any()
            if p_pago: st.error("🚫 BLOQUEIO: Existem parcelas pagas.")
            
            c_f1, c_f2 = st.columns([1, 3])
            img_ed = img_to_b64(p_data[0])
            if img_ed: c_f1.markdown(f'<img src="{img_ed}" class="zoom" style="width:150px">', unsafe_allow_html=True)
            c_f2.metric("💵 Custo Original", m(custo_p))
            c_f2.write(f"**Produto:** {p_data[2]} | **Ref:** {p_data[3]}")

            st.divider()
            c_s1, c_s2, c_s3 = st.columns(3)
            g_at = ((float(v_info[3]) / custo_p) - 1) * 100
            new_g = c_s1.number_input("Novo Percentual de Ganho (%)", 0.0, 500.0, float(g_at), step=5.0, disabled=p_pago)
            new_v = custo_p * (1 + (new_g / 100))
            new_e = c_s2.number_input("Nova Entrada", 0.0, new_v, float(v_info[7]), disabled=p_pago)
            new_q = c_s3.number_input("Novas Parcelas", 1, 36, int(v_info[8]), disabled=p_pago)
            new_dt = c_s1.date_input("Nova Data", datetime.strptime(v_info[6], '%Y-%m-%d').date(), disabled=p_pago)
            new_fr = c_s2.selectbox("Nova Periodicidade", ["Semanal", "Quinzenal", "Mensal"], disabled=p_pago)

            new_comis = new_v * (c_data[0] / 100) if c_data[1] else 0.0
            new_lucro = new_v - custo_p - new_comis
            
            st.markdown("#### 📊 Resumo da Nova Negociação")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Valor Custo", m(custo_p)); r2.metric("Valor Venda", m(new_v)); r3.metric("Valor Revenda", m(new_comis)); r4.metric("Lucro Líquido", m(new_lucro))

            v_p_n = (new_v - new_e) / new_q if new_q > 0 else 0
            vcs_n = calcular_vencimentos(new_dt, new_fr, new_q)
            df_n = pd.DataFrame({"Parcela": [f"{i+1}ª" for i in range(new_q)], "Vencimento": [datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m/%Y') for d in vcs_n], "Valor": [m(v_p_n)] * new_q, "Pago": ["Não"] * new_q})
            renderizar_tabela_estilizada(df_s if p_pago else df_n)

            b1, b2 = st.columns(2)
            if b1.button("💾 CONFIRMAR ALTERAÇÕES", type="primary", disabled=p_pago, use_container_width=True):
                conn.execute("UPDATE vendas SET valor_venda=?, valor_lucro=?, valor_comissao=?, data_venda=?, valor_entrada=?, num_parcelas=? WHERE id=?", (new_v, new_lucro, new_comis, str(new_dt), new_e, new_q, id_v))
                conn.execute("DELETE FROM vendas_pagamentos WHERE id_venda=?", (id_v,))
                for idx, vd in enumerate(vcs_n): conn.execute("INSERT INTO vendas_pagamentos (id_venda, num_parcela, data_vencimento, valor_parcela) VALUES (?,?,?,?)", (id_v, idx+1, vd, v_p_n))
                conn.commit(); st.session_state.v_reset_key += 1; st.success("Atualizado!"); time.sleep(1.5); st.rerun()

            if b2.button("🗑️ EXCLUIR VENDA TOTALMENTE", disabled=p_pago, use_container_width=True):
                conn.execute("DELETE FROM vendas_pagamentos WHERE id_venda=?;", (id_v,))
                conn.execute("UPDATE produtos SET vendido=0 WHERE id=?;", (id_prod,))
                conn.execute("DELETE FROM vendas WHERE id=?;", (id_v,))
                conn.commit(); st.session_state.v_reset_key += 1; st.warning("Excluída!"); time.sleep(1.5); st.rerun()

    conn.close()
