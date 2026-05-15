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
    """Injeta CSS para Cabeçalhos Azul Petróleo e Estilização do Carrinho"""
    st.markdown("""
    <style>
        .header-petroleo {
            background-color: #005f6b !important;
            color: #FFFFFF !important;
            font-weight: bold !important;
            padding: 10px;
            text-align: center;
            border-radius: 4px;
            font-size: 0.85rem;
            text-transform: uppercase;
        }
        .cell-data {
            display: flex; align-items: center; justify-content: center;
            height: 50px; text-align: center; border-bottom: 1px solid #f0f2f6; font-size: 0.85rem;
        }
        .zoom:hover { transform: scale(3.5); transition: 0.4s; z-index: 999; position: relative; border: 2px solid #005f6b; }
        .metric-container {
            background-color: #f8f9fb;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #005f6b;
            margin-bottom: 20px;
        }
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

def modulo_vendas(usuario_id):
    aplicar_estilos()
    st.title("💰 Gestão de Vendas PRO")
    conn = conectar()
    
    if 'carrinho' not in st.session_state: st.session_state.carrinho = []
    if 'v_reset_key' not in st.session_state: st.session_state.v_reset_key = 0

    tab1, tab_fin, tab2, tab3 = st.tabs([
        "🆕 Registrar Venda", 
        "📊 Financeiro Vendas", 
        "📜 Histórico de Venda", 
        "✏ Editar/Excluir Venda"
    ])

    # ==========================================
    # TAB 1: REGISTRAR VENDA (COM AJUSTES)
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
                    
                    # AJUSTE: Lógica de Pagamento à Vista
                    e_vista = (v_ent >= venda_val)
                    q_parc = f2.number_input("Quantidade de Parcelas", 0 if e_vista else 1, 36, 0 if e_vista else 1, disabled=e_vista, key=f"q_{p.id}")
                    freq = f3.selectbox("Periodicidade", ["Semanal", "Quinzenal", "Mensal"], disabled=e_vista, key=f"f_{p.id}")
                    
                    v_p = (venda_val - v_ent)/q_parc if q_parc > 0 else 0
                    vcs = calcular_vencimentos(dt_venda, freq, q_parc) if q_parc > 0 else []
                    
                    if not e_vista and q_parc > 0:
                        df_simul = pd.DataFrame({
                            "Parcela": [f"{i+1}ª" for i in range(q_parc)], 
                            "Vencimento": [datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m/%Y') for d in vcs], 
                            "Valor": [m(v_p)] * q_parc
                        })
                        renderizar_tabela_estilizada(df_simul)
                    elif e_vista:
                        st.info("✅ Venda configurada como PAGAMENTO À VISTA.")
                    
                    if st.button("➕ INCLUIR NO PEDIDO"):
                        st.session_state.carrinho.append({
                            'id': p.id, 'ref': p.referencia, 'nome': p.nome_produto, 'tam': p.tamanho, 
                            'custo': custo, 'venda': venda_val, 'comis': comis_val, 
                            'lucro': lucro_val, 'entrada': v_ent, 'vencimentos': vcs, 'v_parc': v_p, 'qtd': q_parc
                        })
                        st.rerun()

        if st.session_state.carrinho:
            st.divider()
            st.subheader("🛒 Itens do Pedido")
            
            # --- TOTALIZADORES ---
            t_venda = sum(i['venda'] for i in st.session_state.carrinho)
            t_custo = sum(i['custo'] for i in st.session_state.carrinho)
            t_lucro = sum(i['lucro'] for i in st.session_state.carrinho)
            
            st.markdown(f"""
                <div class="metric-container">
                    <span style='margin-right:30px'><b>TOTAL VENDA:</b> {m(t_venda)}</span>
                    <span style='margin-right:30px'><b>TOTAL CUSTO:</b> {m(t_custo)}</span>
                    <b>TOTAL LUCRO:</b> {m(t_lucro)}
                </div>
            """, unsafe_allow_html=True)

            # --- TABELA DE ITENS COM CABEÇALHO AZUL PETRÓLEO ---
            cols_h = st.columns([0.8, 1.8, 1, 1, 1, 1, 0.7, 1, 0.5])
            titulos = ["Ref", "Produto", "Venda", "Custo", "Revenda", "Lucro", "Parc.", "Vl. Parc", "Ação"]
            for col, t in zip(cols_h, titulos):
                col.markdown(f'<div class="header-petroleo">{t}</div>', unsafe_allow_html=True)

            for idx, item in enumerate(st.session_state.carrinho):
                r = st.columns([0.8, 1.8, 1, 1, 1, 1, 0.7, 1, 0.5])
                r[0].write(item['ref'])
                r[1].write(item['nome'])
                r[2].write(m(item['venda']))
                r[3].write(m(item['custo']))
                r[4].write(m(item['comis']))
                r[5].write(m(item['lucro']))
                r[6].write(f"{item['qtd']}x")
                r[7].write(m(item['v_parc']))
                if r[8].button("🗑️", key=f"del_{idx}"):
                    st.session_state.carrinho.pop(idx)
                    st.rerun()
            if st.button("💾 FINALIZAR E SALVAR VENDA", type="primary", use_container_width=True):

                    cur = conn.cursor()
                    for i in st.session_state.carrinho:
                    # Insere o registro mestre da venda
                        cur.execute("INSERT INTO vendas (id_produto, id_cliente, valor_venda, valor_lucro, valor_comissao, data_venda, valor_entrada, num_parcelas) VALUES (?,?,?,?,?,?,?,?)", 
                            (i['id'], cliente['id'], i['venda'], i['lucro'], i['comis'], str(dt_venda), i['entrada'], i['qtd']))
        
                        id_v = cur.lastrowid
        
                            # Marca o produto como vendido
                        cur.execute("UPDATE produtos SET vendido=1 WHERE id=?", (i['id'],))
        
                        # --- AJUSTE AQUI ---
                        # Só grava parcelas se houver quantidade E se o valor da parcela for maior que zero (ignora vendas à vista)
                        if i['qtd'] > 0 and i['v_parc'] > 0:
                            for idx_p, v_d in enumerate(i['vencimentos']):
                                cur.execute("INSERT INTO vendas_pagamentos (id_venda, num_parcela, data_vencimento, valor_parcela, pago) VALUES (?,?,?,?,0)", 
                                        (id_v, idx_p+1, v_d, i['v_parc']))

                    conn.commit()
                    st.session_state.carrinho = []
                    st.session_state.v_reset_key += 1
                    st.success("✅ Venda Salva!")
                    time.sleep(1.5)
                    st.rerun()


    # ==========================================
    # TAB_FIN: FINANCEIRO VENDAS (MANTIDA ORIGINAL)
    # ==========================================
    with tab_fin:
        query_fin = """
        SELECT vp.*, p.nome_produto, c.nome_cliente 
        FROM vendas_pagamentos vp
        JOIN vendas v ON vp.id_venda = v.id
        JOIN produtos p ON v.id_produto = p.id
        JOIN clientes c ON v.id_cliente = c.id
        WHERE vp.valor_parcela > 0
        """
        df_f_base = pd.read_sql_query(query_fin, conn)
        if not df_f_base.empty:
            hoje = date.today()
            df_f_base['venc_dt'] = pd.to_datetime(df_f_base['data_vencimento']).dt.date
            df_f_base['status_label'] = df_f_base.apply(lambda x: "PAGO" if x['pago']==1 else ("ATRASADO" if x['venc_dt'] < hoje else "PENDENTE"), axis=1)
            
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

            cols_h = st.columns([0.6, 1.5, 2, 0.6, 1.1, 1.1, 1, 0.8])
            titulos = ["ID", "Cliente", "Produto", "Parc.", "Vencimento", "Valor", "Status", "Ação"]
            for col, t in zip(cols_h, titulos):
                col.markdown(f'<div class="header-petroleo">{t}</div>', unsafe_allow_html=True)
            
            for _, r in df_v_fin.iterrows():
                row = st.columns([0.6, 1.5, 2, 0.6, 1.1, 1.1, 1, 0.8])
                cor_st = "green" if r['pago']==1 else ("red" if r['status_label']=="ATRASADO" else "#005f6b")
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
    # TAB 2: HISTÓRICO GERENCIAL (MANTIDA ORIGINAL)
    # ==========================================
        # ==========================================
    # TAB 2: HISTÓRICO GERENCIAL (REESTRUTURADA)
    # ==========================================
    with tab2:
        # QUERY ATUALIZADA: Agora traz o valor da Comissão (Revenda) e calcula o Lucro Efetivado real
        query_h = """
        SELECT 
            v.data_venda as Data, 
            c.nome_cliente as Cliente, 
            p.nome_produto as Produto, 
            v.valor_venda as Venda, 
            v.num_parcelas as Parcelas, 
            v.valor_entrada as Entrada, 
            p.valor_compra as Custo, 
            v.valor_comissao as Revenda, 
            v.valor_lucro as Lucro_Esperado,
            (COALESCE((SELECT SUM(valor_parcela) FROM vendas_pagamentos WHERE id_venda = v.id AND pago = 1), 0) 
             + v.valor_entrada - p.valor_compra - v.valor_comissao) as Lucro_Efetivado
        FROM vendas v 
        JOIN produtos p ON v.id_produto = p.id 
        JOIN clientes c ON v.id_cliente = c.id 
        ORDER BY v.id DESC
        """
        df_h = pd.read_sql_query(query_h, conn)
        
        if not df_h.empty:
            df_h['Data_dt'] = pd.to_datetime(df_h['Data']).dt.date
            f1, f2 = st.columns(2)
            sel_c = f1.selectbox("Filtrar Cliente:", ["Todos"] + sorted(list(df_h['Cliente'].unique())), key="h_cli")
            per = f2.date_input("Filtrar Período:", [df_h['Data_dt'].min(), df_h['Data_dt'].max()], key="h_per")
            
            df_f = df_h.copy()
            if sel_c != "Todos": 
                df_f = df_f[df_f['Cliente'] == sel_c]
            
            # Ajuste para extrair a data inicial e final da seleção
            if isinstance(per, (list, tuple)) and len(per) == 2:
                dt_ini, dt_fim = per
                df_f = df_f[(df_f['Data_dt'] >= dt_ini) & (df_f['Data_dt'] <= dt_fim)]

            mh1, mh2, mh3 = st.columns(3)
            mh1.metric("Vendas Período", m(df_f['Venda'].sum()))
            mh2.metric("Lucro Esperado", m(df_f['Lucro_Esperado'].sum()))
            mh3.metric("Lucro Efetivado", m(df_f['Lucro_Efetivado'].sum()))
            
            # CABEÇALHO EM DUAS LINHAS PARA CABER TUDO
            st.markdown("""<div style="background-color: #005f73; padding: 10px; border-radius: 5px; color: white; font-weight: bold; font-size: 11px; text-align:center;">
                <table style="width:100%; border-collapse: collapse;">
                    <tr>
                        <td style="width:10%">Data Vend</td>
                        <td style="width:15%">Cliente</td>
                        <td style="width:18%">Produto</td>
                        <td style="width:9%">Venda</td>
                        <td style="width:5%">Parc.</td>
                        <td style="width:9%">Entrada</td>
                        <td style="width:9%">Custo</td>
                        <td style="width:9%">Revenda</td>
                        <td style="width:9%">Lucro<br>Esperado</td>
                        <td style="width:9%">Lucro<br>Efetivado</td>
                    </tr>
                </table>
            </div>""", unsafe_allow_html=True)

            for _, r in df_f.iterrows():
                # Definição das colunas (9 colunas após remoção de Ref e Tam)
                row_h = st.columns([1, 1.5, 1.8, 0.9, 0.5, 0.9, 0.9, 0.9, 0.9, 0.9])
                
                row_h[0].write(datetime.strptime(r['Data'], '%Y-%m-%d').strftime('%d/%m/%y'))
                row_h[1].write(r['Cliente'])
                row_h[2].write(r['Produto'])
                row_h[3].write(m(r['Venda']))
                row_h[4].write(f"{r['Parcelas']}x")
                row_h[5].write(m(r['Entrada']))
                row_h[6].write(m(r['Custo']))
                row_h[7].write(m(r['Revenda']))
                
                # Cores para Lucros
                row_h[8].markdown(f":blue[{m(r['Lucro_Esperado'])}]")
                
                cor_efet = "green" if r['Lucro_Efetivado'] > 0 else "red"
                row_h[9].markdown(f":{cor_efet}[{m(r['Lucro_Efetivado'])}]")


    # ==========================================
    # TAB 3: EDITAR / EXCLUIR (MANTIDA ORIGINAL)
    # ==========================================
    with tab3:
        st.subheader("✏ Alteração e Renegociação")
        df_v_edit = pd.read_sql_query("""SELECT v.id, v.data_venda, c.nome_cliente, p.referencia, p.nome_produto, v.id_produto FROM vendas v JOIN clientes c ON v.id_cliente = c.id JOIN produtos p ON v.id_produto = p.id ORDER BY v.id DESC""", conn)
        opts_v = {f"ID {r.id} | {r.nome_cliente} | {r.referencia} - {r.nome_produto}": (r.id, r.id_produto) for r in df_v_edit.itertuples()}
        sel_v = st.selectbox("Selecione a venda:", [""] + list(opts_v.keys()), key=f"sel_v_ed_{st.session_state.v_reset_key}")
        
        if sel_v:
            id_v, id_prod = opts_v[sel_v]
            v_info = conn.execute("SELECT * FROM vendas WHERE id=?", (id_v,)).fetchone()
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
