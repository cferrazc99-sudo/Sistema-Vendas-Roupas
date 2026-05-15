import streamlit as st
import pandas as pd
from datetime import datetime
from database import conectar # Usa a mesma função de conexão do seu projeto


def modulo_gestao_caixa(uid_ativo):
    st.header("🏧 Gestão de Caixa / Retiradas")
    
    # -------------------------------------------------------------------------
    # OPERAÇÕES DE BANCO DE DADOS (CRUD)
    # -------------------------------------------------------------------------
    def salvar_retirada(data, hora, valor, descricao):
        conn = conectar()
        conn.execute(
            "INSERT INTO retirada_caixa (id_usuario, data, hora, valor, descricao) VALUES (?, ?, ?, ?, ?)",
            (uid_ativo, data, hora, valor, descricao)
        )
        conn.commit()
        conn.close()

    def atualizar_retirada(id_registro, data, hora, valor, descricao):
        conn = conectar()
        conn.execute(
            "UPDATE retirada_caixa SET data=?, hora=?, valor=?, descricao=? WHERE id=? AND id_usuario=?",
            (data, hora, valor, descricao, id_registro, uid_ativo)
        )
        conn.commit()
        conn.close()

    def deletar_retirada(id_registro):
        conn = conectar()
        conn.execute("DELETE FROM retirada_caixa WHERE id=? AND id_usuario=?", (id_registro, uid_ativo))
        conn.commit()
        conn.close()

    # -------------------------------------------------------------------------
    # CARREGAMENTO E ISOLAMENTO DE DADOS (CONFORME LAYOUTS FORNECIDOS)
    # -------------------------------------------------------------------------
    # conn = conectar()
    
    # # 1. Fluxo de Pagamentos (Compras/Fornecedores) - Filtrando apenas parcelas pagas
    #     # 1. Fluxo de Pagamentos (Compras/Fornecedores) - Usando a data real de pagamento
    # try:
    #     df_compras = pd.read_sql_query(
    #         """
    #         SELECT data_pagamento as data, 'Fornecedor' as tipo, 'Compra Fornecedor' as desc, valor_parcela as valor 
    #         FROM fluxo_pagamentos 
    #         WHERE id_usuario = ? AND (pago = 'Sim' OR pago = 1) AND data_pagamento IS NOT NULL
    #         """, 
    #         conn, params=(uid_ativo,)
    #     )
    # except Exception:
    #     df_compras = pd.DataFrame(columns=['data', 'tipo', 'desc', 'valor'])
    
    # # 2. Vendas Pagamentos (Vendas/Clientes) - Usando a data real de recebimento
    # try:
    #     df_vendas = pd.read_sql_query(
    #         """
    #         SELECT data_pagamento as data, 'Cliente' as tipo, 'Venda Cliente' as desc, valor_parcela as valor 
    #         FROM vendas_pagamentos 
    #         WHERE id_usuario = ? AND (pago = 'Sim' OR pago = 1) AND data_pagamento IS NOT NULL
    #         """, 
    #         conn, params=(uid_ativo,)
    #     )
    # except Exception:
    #     df_vendas = pd.DataFrame(columns=['data', 'tipo', 'desc', 'valor'])

        
    # # 3. Retiradas de Caixa
    # try:
    #     df_retiradas = pd.read_sql_query(
    #         "SELECT id, data, hora, 'Retirada' as tipo, descricao as desc, valor FROM retirada_caixa WHERE id_usuario = ?", 
    #         conn, params=(uid_ativo,)
    #     )
    # except Exception:
    #     df_retiradas = pd.DataFrame(columns=['id', 'data', 'hora', 'tipo', 'desc', 'valor'])
    
    # conn.close()

    # # Garante a formatação numérica dos valores monetários para evitar erros de soma
    # for df in [df_compras, df_vendas, df_retiradas]:
    #     if not df.empty and 'valor' in df.columns:
    #         df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0.0)

    # -------------------------------------------------------------------------
    # CARREGAMENTO E ISOLAMENTO DE DADOS (AJUSTADO COM ENTRADAS CONSOLIDADOS)
    # -------------------------------------------------------------------------
    conn = conectar()
    
    # 1. Fluxo de Pagamentos (Compras/Fornecedores) - Apenas parcelas pagas
    try:
        df_compras = pd.read_sql_query(
            """
            SELECT data_pagamento as data, 'Fornecedor' as tipo, 'Pgto Parc Fornecedor' as desc, sum(valor_parcela) as valor 
            FROM fluxo_pagamentos 
            WHERE id_usuario = ? AND (pago = 'Sim' OR pago = 1) AND data_pagamento IS NOT NULL GROUP BY data_pagamento
            """, 
            conn, params=(uid_ativo,)
        )
    except Exception:
        df_compras = pd.DataFrame(columns=['data', 'tipo', 'desc', 'valor'])
    
    # [NOVO] 1.2 Consolidação de Valor de Entrada - Fornecedores (Tabela produtos)
    try:
        # df_entrada_forn = pd.read_sql_query(
        #     """
        #     SELECT data_compra as data, 'Fornecedor' as tipo, 'Pgto Entrada Fornecedor' as desc, SUM(valor_entrada) as valor
        #     FROM produtos
        #     WHERE id_usuario = ? AND data_compra IS NOT NULL AND valor_entrada > 0
        #     GROUP BY data_compra
        #     """,
        #     conn, params=(uid_ativo,)
        # )
    
        df_entrada_forn = pd.read_sql_query(
            """
            SELECT data_compra as data, 'Fornecedor' as tipo, 'Pgto Entrada Fornecedor' as desc, 
                   SUM(valor_entrada) as valor, SUM(valor_compra) as total_bruto_forn
            FROM produtos
            WHERE id_usuario = ? AND data_compra IS NOT NULL
            GROUP BY data_compra
            """,
            conn, params=(uid_ativo,)
        )
    except Exception:
        
        df_entrada_forn = pd.DataFrame(columns=['data', 'tipo', 'desc', 'valor'])
    
    # 2. Vendas Pagamentos (Vendas/Clientes) - Apenas parcelas pagas
    try:
        df_vendas = pd.read_sql_query(
            """
            SELECT data_pagamento as data, 'Cliente' as tipo, 'Venda Cliente' as desc, sum(valor_parcela) as valor 
            FROM vendas_pagamentos 
            WHERE id_usuario = ? AND (pago = 'Sim' OR pago = 1) AND data_pagamento IS NOT NULL group by data_pagamento
            """, 
            conn, params=(uid_ativo,)
        )
    except Exception:
        df_vendas = pd.DataFrame(columns=['data', 'tipo', 'desc', 'valor'])

    # [NOVO] 2.2 Consolidação de Valor de Entrada - Clientes (Tabela vendas)
    try:
    #     df_entrada_cli = pd.read_sql_query(
    #         """
    #         SELECT data_venda as data, 'Cliente' as tipo, 'Pgto Entrada Cliente' as desc, SUM(valor_entrada) as valor
    #         FROM vendas
    #         WHERE id_usuario = ? AND data_venda IS NOT NULL AND valor_entrada > 0
    #         GROUP BY data_venda
    #         """,
    #         conn, params=(uid_ativo,)
    #     )
    # except Exception:
    #     df_entrada_cli = pd.DataFrame(columns=['data', 'tipo', 'desc', 'valor'])
    
        df_entrada_cli = pd.read_sql_query(
            """
            SELECT data_venda as data, 'Cliente' as tipo, 'Pgto Entrada Cliente' as desc, 
                   SUM(valor_entrada) as valor, SUM(valor_venda) as total_bruto_cli, SUM(valor_comissao) as total_comis_cli
            FROM vendas
            WHERE id_usuario = ? AND data_venda IS NOT NULL
            GROUP BY data_venda
            """,
            conn, params=(uid_ativo,)
        )
    except Exception:
        df_entrada_cli = pd.DataFrame(columns=['data', 'tipo', 'desc', 'valor', 'total_bruto_cli', 'total_comis_cli'])
    
    # 3. Retiradas de Caixa
    try:
        df_retiradas = pd.read_sql_query(
            "SELECT id, data, hora, 'Retirada' as tipo, descricao as desc, valor FROM retirada_caixa WHERE id_usuario = ?", 
            conn, params=(uid_ativo,)
        )
    except Exception:
        df_retiradas = pd.DataFrame(columns=['id', 'data', 'hora', 'tipo', 'desc', 'valor'])
    
    conn.close()
    
    # Garante a formatação numérica dos valores monetários para evitar erros de soma
    lista_dataframes = [df_compras, df_entrada_forn, df_vendas, df_entrada_cli, df_retiradas]
    for df in lista_dataframes:
        if not df.empty and 'valor' in df.columns:
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0.0)


    # -------------------------------------------------------------------------
    # PAINEL 1: VALORES CONSOLIDADOS TOTAL (HISTÓRICO COMPLETO)
    # -------------------------------------------------------------------------
    st.subheader("📊 Resumo Consolidado Histórico")

    # --- INJEÇÃO DE CSS COM ALTURA FIXA DE CABEÇALHO PARA ALINHAMENTO MILIMÉTRICO ---
    st.markdown(
        """
        <style>
        /* 1. CONFIGURAÇÃO DO BLOCO DO CARD */
        div[data-testid="stMetric"] {
            display: flex !important;
            flex-direction: column !important;
            min-height: 105px !important;              /* Garante tamanho idêntico para todos */
            padding: 10px 8px !important;
            background-color: #f8f9fa !important;       /* Fundo cinza claro */
            border-radius: 6px !important;              /* Cantos arredondados */
        }

        /* 2. PADRONIZAÇÃO DA ÁREA VERTICAL DO CABEÇALHO/TÍTULO */
        div[data-testid="stMetric"] p,
        div[data-testid="stMetricLabel"] label,
        [data-testid="stMetricLabel"],
        .st-key-metric label {
            font-size: 16px !important;        /* Fonte 16px para encaixe perfeito nas colunas */
            font-weight: 900 !important;        /* Negrito ultra destacado */
            color: #000000 !important;          /* Preto puro */
            white-space: normal !important;     /* Permite quebra automática */
            word-wrap: break-word !important;
            line-height: 1.1 !important;
            margin: 0 !important;
            padding: 0 !important;
            
            /* SOLUÇÃO DO BUG: Força uma altura fixa para a caixa de texto do título */
            height: 44px !important;            
            min-height: 44px !important;
            max-height: 44px !important;
            display: -webkit-box !important;
            -webkit-line-clamp: 2 !important;   /* Limita visualmente a no máximo 2 linhas */
            -webkit-box-orient: vertical !important;
            overflow: hidden !important;
        }
        
        /* 3. ALINHAMENTO FIXO DA LINHA DOS NÚMEROS */
        div[data-testid="stMetricValue"] > div,
        [data-testid="stMetricValue"],
        .st-key-metric div {
            font-size: 15px !important;         /* Tamanho visível para os totais */
            font-weight: 700 !important;         /* Negrito marcante */
            white-space: nowrap !important;     /* Impede que o número quebre linha */
            
            /* Remove margens variáveis e força o início na mesma coordenada vertical */
            margin-top: 6px !important;         
            padding: 0 !important;
            display: block !important;
        }
        
        /* 4. OTIMIZAÇÃO DAS COLUNAS HORIZONTAIS */
        div[data-testid="column"] {
            padding: 0px 3px !important;        /* Otimiza o espaço entre os 7 blocos */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # --- CÁLCULO DAS MÉTRICAS (Mantido idêntico) ---
    tot_compras_hist = df_compras['valor'].sum() + df_entrada_forn['valor'].sum()
    tot_vendas_hist = df_vendas['valor'].sum() + df_entrada_cli['valor'].sum()
    tot_retiradas_hist = df_retiradas['valor'].sum()
    
    tot_a_receber_cli = df_entrada_cli['total_bruto_cli'].sum() if 'total_bruto_cli' in df_entrada_cli.columns else 0.0
    tot_a_pagar_forn = df_entrada_forn['total_bruto_forn'].sum() if 'total_bruto_forn' in df_entrada_forn.columns else 0.0
    tot_a_pagar_revenda = df_entrada_cli['total_comis_cli'].sum() if 'total_comis_cli' in df_entrada_cli.columns else 0.0
    saldo_potencial = tot_a_receber_cli - (tot_a_pagar_forn + tot_a_pagar_revenda)
    
    lcr_receb = tot_vendas_hist - (tot_a_pagar_forn + tot_a_pagar_revenda) # Lucro Recebido considerando o que falta
    pgt_pendente_forn = tot_compras_hist - tot_a_pagar_forn # Pagamentos Pendentes considerando o que falta pagar aos fornecedores   
    pgo_pendente_revenda = tot_retiradas_hist - tot_a_pagar_revenda # Pagamentos Pendentes considerando o que falta pagar de comissão para revenda
    pgt_pendente_vendas = tot_vendas_hist - tot_a_receber_cli # Pagamentos Pendentes considerando o que falta receber dos clientes
    # Criação da grid horizontal com 8 colunas (Mantido idêntico)
    mc1, mc2, mc3, mc4, mc5, mc6, mc7, mc8 = st.columns(8)
    
    mc1.metric("Total a Receber (Clientes)", f"R$ {tot_a_receber_cli:,.2f}")
    mc2.metric("Pendente Receber Cliente", f"R$ {pgt_pendente_vendas :,.2f}", delta=f"{pgt_pendente_vendas:,.2f}")
    mc3.metric("Total a Pagar (Fornecedores)", f"R$ {tot_a_pagar_forn:,.2f}")
    mc4.metric("Pgto Pendente Fornecedores", f"R$ {pgt_pendente_forn:,.2f}", delta=f"{pgt_pendente_forn:,.2f}")
    mc5.metric("Total a Pagar Revenda", f"R$ {tot_a_pagar_revenda:,.2f}")
    mc6.metric("Pgto Pendente Revenda", f"R$ {pgo_pendente_revenda:,.2f}", delta=f"{pgo_pendente_revenda:,.2f}")
    mc7.metric("Lucro Potencial", f"R$ {saldo_potencial:,.2f}")
    mc8.metric("Lucro Realizado", f"R$ {lcr_receb:,.2f}", delta=f"{lcr_receb:,.2f}")

    # -------------------------------------------------------------------------
    # FILTROS DINÂMICOS SIDEBAR
    # -------------------------------------------------------------------------
    st.sidebar.divider()
    st.sidebar.subheader("🔍 Filtros do Caixa")
    
    todas_datas = pd.concat([df_compras['data'], df_vendas['data'], df_retiradas['data']]).dropna().unique() if not (df_compras.empty and df_vendas.empty and df_retiradas.empty) else []
    todas_datas = sorted(list(todas_datas))
    
    filtro_data = st.sidebar.selectbox("Filtrar por Data Específica:", ["Todos"] + todas_datas)
    filtro_tipo = st.sidebar.selectbox("Filtrar por Evento:", ["Todos", "Fornecedor", "Cliente", "Retirada"])
    filtro_desc = st.sidebar.text_input("Filtrar por Termo de Descrição:")

       # -------------------------------------------------------------------------
    # CONSTRUÇÃO DA LISTAGEM GERAL UNIFICADA
    # -------------------------------------------------------------------------
    # df_c_t = df_compras.rename(columns={'tipo': 'Evento', 'desc': 'Descrição'})
    # df_v_t = df_vendas.rename(columns={'tipo': 'Evento', 'desc': 'Descrição'})
    # df_r_t = df_retiradas.rename(columns={'tipo': 'Evento', 'desc': 'Descrição'}).drop(columns=['id', 'hora'], errors='ignore')
    # df_geral = pd.concat([df_c_t, df_v_t, df_r_t], ignore_index=True)

    df_c_t = df_compras.rename(columns={'tipo': 'Evento', 'desc': 'Descrição'})
    df_ef_t = df_entrada_forn.rename(columns={'tipo': 'Evento', 'desc': 'Descrição'}) # NOVO
    df_v_t = df_vendas.rename(columns={'tipo': 'Evento', 'desc': 'Descrição'})
    df_ec_t = df_entrada_cli.rename(columns={'tipo': 'Evento', 'desc': 'Descrição'}) # NOVO
    df_r_t = df_retiradas.rename(columns={'tipo': 'Evento', 'desc': 'Descrição'}).drop(columns=['id', 'hora'], errors='ignore')
    
    # Concatena todas as 5 fontes de dados de movimentação
    df_geral = pd.concat([df_c_t, df_ef_t, df_v_t, df_ec_t, df_r_t], ignore_index=True)


    if df_geral.empty:
        df_geral = pd.DataFrame(columns=['data', 'Evento', 'Descrição', 'valor'])

    # Aplicação dos Filtros Dinâmicos
    if filtro_data != "Todos":
        df_geral = df_geral[df_geral['data'] == filtro_data]
    if filtro_tipo != "Todos":
        df_geral = df_geral[df_geral['Evento'] == filtro_tipo]
    if filtro_desc.strip() != "":
        df_geral = df_geral[df_geral['Descrição'].str.contains(filtro_desc, case=False, na=False)]

    #*******************************************************************************
    # 1. ORDENAÇÃO CRONOLÓGICA (Menor para Maior) para calcular o saldo corretamente
    #*******************************************************************************

    # prioridade_map = {'Compra Fornecedor': 1, 'Pgto Parcela Cliente': 3, 'Retirada': 5}
    # df_geral['prioridade'] = df_geral['Descrição'].map(prioridade_map).fillna(2)
    # df_geral = df_geral.sort_values(by=['data', 'prioridade'], ascending=[True, True]).drop(columns=['prioridade'])
    #     # 1. ORDENAÇÃO CRONOLÓGICA
    #     prioridade_map = {
    #         'Compra Fornecedor': 1, 
    #         'Pgto Entrada Fornecedor': 2, 
    #         'Venda Cliente': 3, 
    #         'Pgto Entrada Cliente': 4, 
    #         'Retirada': 5
    #     }
    # df_geral['prioridade'] = df_geral['Descrição'].map(prioridade_map).fillna(2)
    # df_geral = df_geral.sort_values(by=['data', 'prioridade'], ascending=[True, True]).drop(columns=['prioridade'])
      
        # 1. ORDENAÇÃO CRONOLÓGICA
    prioridade_map = {
        'Compra Fornecedor': 1, 
        'Pgto Entrada Fornecedor': 2, 
        'Pgto Parcela Cliente': 3, 
        'Pgto Entrada Cliente': 4, 
        'Retirada': 5
    }
    df_geral['prioridade'] = df_geral['Descrição'].map(prioridade_map).fillna(2)
    df_geral = df_geral.sort_values(by=['data', 'prioridade'], ascending=[True, True]).drop(columns=['prioridade'])
    
    # 2. CÁLCULO DO SALDO CUMULATIVO
    saldo_acumulado = []
    saldo_atual = 0.0
    for idx, row in df_geral.iterrows():
        v = row['valor']
        # Fornecedores, Compras, Entradas de Fornecedor e Retiradas subtraem do caixa
        if row['Descrição'] in ['Compra Fornecedor', 'Pgto Entrada Fornecedor', 'Retirada'] or row['Evento'] in ['Fornecedor', 'Retirada']:
            saldo_atual -= v
        else:
            saldo_atual += v
        saldo_acumulado.append(saldo_atual)
    df_geral['Saldo Cumulativo'] = saldo_acumulado

    # 2. CÁLCULO DO SALDO CUMULATIVO
    saldo_acumulado = []
    saldo_atual = 0.0
    for idx, row in df_geral.iterrows():
        v = row['valor']
        # Fornecedores, Compras, Entradas de Fornecedor e Retiradas subtraem do caixa
        if row['Descrição'] in ['Compra Fornecedor', 'Pgto Entrada Fornecedor', 'Retirada'] or row['Evento'] in ['Fornecedor', 'Retirada']:
            saldo_atual -= v
        else:
            saldo_atual += v
        saldo_acumulado.append(saldo_atual)
    df_geral['Saldo Cumulativo'] = saldo_acumulado


    # 2. CÁLCULO DO SALDO CUMULATIVO (A partir da menor data)
    saldo_acumulado = []
    saldo_atual = 0.0
    for idx, row in df_geral.iterrows():
        v = row['valor']
        # Correção da checagem: se envolver Fornecedor ou Retirada, SUBTRAI do caixa
        if row['Descrição'] in ['Compra Fornecedor', 'Retirada'] or row['Evento'] in ['Fornecedor', 'Retirada']:
            saldo_atual -= v
        else:
            saldo_atual += v
        saldo_acumulado.append(saldo_atual)
    df_geral['Saldo Cumulativo'] = saldo_acumulado

    # 3. INVERSÃO DA ORDENAÇÃO VISUAL (Maior data para a menor data)
    # O saldo já calculado fica fixado à respectiva linha corretamente
    df_geral = df_geral.iloc[::-1]
 

    # # -------------------------------------------------------------------------
    # # PAINEL 2: VALORES PARCIAIS (DO PERÍODO FILTRADO)
    # # -------------------------------------------------------------------------
    # st.subheader("📉 Resumo do Período Filtrado")
    # df_c_f = df_geral[df_geral['Evento'] == 'Fornecedor']
    # df_v_f = df_geral[df_geral['Evento'] == 'Cliente']
    # df_r_f = df_geral[df_geral['Evento'] == 'Retirada']
    
    # # tot_compras_f = df_c_f['valor'].sum()
    # # tot_vendas_f = df_v_f['valor'].sum()
    # # tot_retiradas_f = df_r_f['valor'].sum()
    # # saldo_f = tot_vendas_f - (tot_compras_f + tot_retiradas_f)

    # tot_compras_f = df_geral[df_geral['Evento'] == 'Fornecedor']['valor'].sum()
    # tot_vendas_f = df_geral[df_geral['Evento'] == 'Cliente']['valor'].sum()
    # tot_retiradas_f = df_geral[df_geral['Evento'] == 'Retirada']['valor'].sum()
    # saldo_f = tot_vendas_f - (tot_compras_f + tot_retiradas_f)


    # fc1, fc2, fc3, fc4 = st.columns(4)
    # fc1.metric("Compras no Período", f"R$ {tot_compras_f:,.2f}")
    # fc2.metric("Vendas no Período", f"R$ {tot_vendas_f:,.2f}")
    # fc3.metric("Retiradas no Período", f"R$ {tot_retiradas_f:,.2f}")
    # fc4.metric("Saldo do Período", f"R$ {saldo_f:,.2f}", delta=f"{saldo_f:,.2f}")

    # -------------------------------------------------------------------------
    # EXIBIÇÃO DA GRID ESTILIZADA (AZUL PETRÓLEO COM TEXTO BRANCO NO HEADER)
    # -------------------------------------------------------------------------
     
    def styler_caixa(row):
        desc = str(row.get('Descrição', row.get('desc', '')))
        envolvido = str(row.get('Evento', row.get('tipo', '')))
        
        # Se for Fornecedor OU se qualquer campo indicar Retirada, fica vermelho
        if envolvido == 'Fornecedor' or desc == 'Compra Fornecedor' or envolvido == 'Retirada' or desc == 'Retirada':
            return ['color: red; font-weight: bold;'] * len(row)
        
        return [''] * len(row)
        

    # -------------------------------------------------------------------------
    # EXIBIÇÃO DA GRID ESTILIZADA (LIMPA, EXPANDIDA E SEM CÓDIGO DUPLICADO)
    # -------------------------------------------------------------------------
    st.write("### 🧾 Extrato Unificado de Movimentações")
    
    if not df_geral.empty:
        df_visualizacao = df_geral.copy()
        
        # 1. Formatação do texto da coluna Valor (Adiciona o sinal de menos se for saída)
        # df_visualizacao['valor_texto'] = df_visualizacao.apply(
        #     lambda r: f"- R$ {r['valor']:,.2f}" if (
        #         r['Descrição'] in ['Compra Fornecedor', 'Retirada'] or 
        #         r['Evento'] in ['Fornecedor', 'Retirada']
        #     ) else f"R$ {r['valor']:,.2f}", axis=1
        # )
        
            # Adiciona o sinal de menos se for saída (incluindo o Pgto Entrada Fornecedor)
        df_visualizacao['valor_texto'] = df_visualizacao.apply(
            lambda r: f"- R$ {r['valor']:,.2f}" if (
                r['Descrição'] in ['Compra Fornecedor', 'Pgto Entrada Fornecedor', 'Retirada'] or 
                r['Evento'] in ['Fornecedor', 'Retirada']
            ) else f"R$ {r['valor']:,.2f}", axis=1
        )


        # 2. Formatação do texto da coluna Saldo
        df_visualizacao['saldo_texto'] = df_visualizacao['Saldo Cumulativo'].map(
            lambda x: f"- R$ {abs(x):,.2f}" if x < 0 else f"R$ {x:,.2f}"
        )
        
        # 3. Formatação da Data para o Padrão Brasileiro (DD/MM/AAAA)
        try:
            df_visualizacao['data'] = pd.to_datetime(df_visualizacao['data']).dt.strftime('%d/%m/%Y')
        except Exception:
            pass
            
        # 3. Reorganiza as colunas e renomeia para o layout final do cabeçalho
        df_final = df_visualizacao[['data', 'Evento', 'Descrição', 'valor_texto', 'saldo_texto']].copy()
        df_final = df_final.rename(columns={
            'data': 'Data', 
            'valor_texto': 'Valor', 
            'saldo_texto': 'Saldo'
        })

        # 4. Nova função de estilização precisa por célula (Element-wise)
        # def aplicar_estilos_caixa(df_dados):
        #     df_estilo = pd.DataFrame('', index=df_dados.index, columns=df_dados.columns)
        #     for idx, row_original in df_geral.iterrows():
        #         pos = df_dados.index[df_dados.index == idx]
        #         if len(pos) == 0:
        #             continue
        #         if row_original['Evento'] in ['Fornecedor', 'Retirada'] or row_original['Descrição'] in ['Compra Fornecedor', 'Retirada']:
        #             df_estilo.loc[pos, ['Data', 'Evento', 'Descrição', 'Valor']] = 'color: red; font-weight: bold;'
        #         if row_original['Saldo Cumulativo'] < 0:
        #             df_estilo.loc[pos, 'Saldo'] = 'color: red; font-weight: bold;'
        #     return df_estilo
        def aplicar_estilos_caixa(df_dados):
            df_estilo = pd.DataFrame('', index=df_dados.index, columns=df_dados.columns)
            for idx, row_original in df_geral.iterrows():
                pos = df_dados.index[df_dados.index == idx]
                if len(pos) == 0:
                    continue
                
                # Pega as saídas tradicionais e a nova descrição de Entrada do Fornecedor
                if row_original['Evento'] in ['Fornecedor', 'Retirada'] or row_original['Descrição'] in ['Compra Fornecedor', 'Pgto Entrada Fornecedor', 'Retirada']:
                    df_estilo.loc[pos, ['Data', 'Evento', 'Descrição', 'Valor']] = 'color: red; font-weight: bold;'
                    
                if row_original['Saldo Cumulativo'] < 0:
                    df_estilo.loc[pos, 'Saldo'] = 'color: red; font-weight: bold;'
            return df_estilo


        # 5. GERAÇÃO DO PACOTE DE ESTILOS COMBINADOS (Adiciona as propriedades estruturais da tabela)
        estilo_final = df_final.style.apply(aplicar_estilos_caixa, axis=None).set_table_styles([
            {
                'selector': 'th',
                'props': [
                    ('background-color', '#004d61 !important'), # Azul Petróleo absoluto
                    ('color', 'white !important'),              # Letras brancas absolutas
                    ('font-weight', 'bold !important'),         # Negrito absoluto
                    ('text-align', 'center !important'),
                    ('padding', '10px !important')
                ]
            }
        ]).set_properties(**{
            'text-align': 'center',
            'padding': '8px'
        })

        # 6. RENDERIZAÇÃO VIA HTML COMPACTA (Sem f-string para evitar conflitos de chaves)
        # O index=False remove a numeração da esquerda. O style width:100% estica a tabela de ponta a ponta.
        html_tabela = estilo_final.to_html(index=False, escape=False)
        html_tabela = html_tabela.replace('<table', '<table style="width:100%; border-collapse:collapse; margin-top:10px;" border="1" class="caixa-tabela"')

        st.markdown(html_tabela, unsafe_allow_html=True)
        st.write("") # Espaçador visual inferior
        # 3. Reorganiza as colunas e renomeia para o layout final do cabeçalho
    else:
        st.info("Nenhuma movimentação localizada para os filtros selecionados.")



    # # -------------------------------------------------------------------------
    # # PAINEL DE CONTROLE EXCLUSIVO PARA ALTERAÇÃO E EXCLUSÃO DE RETIRADAS
    # # -------------------------------------------------------------------------
    # st.divider()
    # st.write("### 🛠️ Painel de Controle de Retiradas")
    # if not df_retiradas.empty:
    #     lista_retiradas = {f"{row['data']} | {row['desc']} (R$ {row['valor']:.2f})": row['id'] for _, row in df_retiradas.iterrows()}
    #     ret_sel = st.selectbox("Selecione uma retirada de caixa para Alterar ou Excluir:", list(lista_retiradas.keys()))
    #     id_operacao = lista_retiradas[ret_sel]

    #     col_adm1, col_adm2, _ = st.columns([1, 1, 4])
        
    #     if col_adm1.button("✏️ Habilitar Edição", use_container_width=True):
    #         st.session_state.edit_retirada_id = id_operacao
    #         st.rerun()
            
    #     if col_adm2.button("🗑️ EXCLUIR REGISTRO", type="primary", use_container_width=True):
    #         deletar_retirada(id_operacao)
    #         st.warning("Registro de retirada removido permanentemente.")
    #         if st.session_state.edit_retirada_id == id_operacao:
    #             st.session_state.edit_retirada_id = None
    #         st.rerun()
    # else:
    #     st.info("Você ainda não possui nenhuma retirada registrada para editar ou excluir.")
