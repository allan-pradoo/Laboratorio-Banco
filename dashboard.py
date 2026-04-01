import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, URL
import os

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(page_title="StarComex - BI", layout="wide")

st.title("🌐 StarComex - Business Intelligence")
st.markdown("---")

# ==========================================
# CONEXÃO
# ==========================================
@st.cache_data
def get_data():
    dw_user = os.getenv("DW_DB_USER", "root")
    dw_password = os.getenv("DW_DB_PASSWORD")
    dw_host = os.getenv("DW_DB_HOST", "localhost")
    dw_port = int(os.getenv("DW_DB_PORT", "3306"))
    dw_name = os.getenv("DW_DB_NAME", "dw_comex")

    if not dw_password:
        st.error("Defina DW_DB_PASSWORD no ambiente.")
        st.stop()

    url_dw = URL.create(
        drivername="mysql+pymysql",
        username=dw_user,
        password=dw_password,
        host=dw_host,
        port=dw_port,
        database=dw_name
    )
    engine = create_engine(url_dw)

    query = """
    SELECT 
        f.valor_convertido, f.valor_transacao, f.quantidade_transacionada, f.taxa_cambio_aplicada,
        t.ano, t.nome_mes, t.mes, t.trimestre,
        po.nome_pais_origem, pd.nome_pais_destino,
        bo.nome_bloco as bloco_origem,
        prod.descricao_produto, prod.categoria_produto
    FROM Fato_Transacoes_Internacionais f
    LEFT JOIN Dim_Tempo t ON f.sk_tempo = t.sk_tempo
    LEFT JOIN Dim_Pais_Origem po ON f.sk_pais_origem = po.sk_pais_origem
    LEFT JOIN Dim_Pais_Destino pd ON f.sk_pais_destino = pd.sk_pais_destino
    LEFT JOIN Dim_Bloco_Economico_Origem bo ON f.sk_bloco_economico_origem = bo.sk_bloco_economico_origem
    LEFT JOIN Dim_Produto prod ON f.sk_produto = prod.sk_produto
    """
    return pd.read_sql(query, engine)

df = get_data()

# ==========================================
# FILTROS (SIDEBAR)
# ==========================================
st.sidebar.header("🎯 Filtros")

anos = sorted(df["ano"].dropna().unique())
ano_sel = st.sidebar.multiselect("Ano", anos, default=anos)

paises = sorted(df["nome_pais_origem"].dropna().unique())
pais_sel = st.sidebar.multiselect("País de Origem", paises)

categorias = sorted(df["categoria_produto"].dropna().unique())
cat_sel = st.sidebar.multiselect("Categoria", categorias)

df_filtrado = df.copy()

if ano_sel:
    df_filtrado = df_filtrado[df_filtrado["ano"].isin(ano_sel)]

if pais_sel:
    df_filtrado = df_filtrado[df_filtrado["nome_pais_origem"].isin(pais_sel)]

if cat_sel:
    df_filtrado = df_filtrado[df_filtrado["categoria_produto"].isin(cat_sel)]

# ==========================================
# KPIs
# ==========================================
st.header("📌 Visão Executiva")

c1, c2, c3, c4 = st.columns(4)

v_total = df_filtrado['valor_convertido'].sum()
q_total = df_filtrado['quantidade_transacionada'].sum()
n_trans = len(df_filtrado)
t_medio = v_total / n_trans if n_trans > 0 else 0

c1.metric("💰 Valor Total", f"R$ {v_total:,.2f}")
c2.metric("📦 Quantidade Total", f"{q_total:,.0f}")
c3.metric("🔄 Transações", f"{n_trans}")
c4.metric("📊 Ticket Médio", f"R$ {t_medio:,.2f}")

st.markdown("---")

# ==========================================
# EVOLUÇÃO TEMPORAL
# ==========================================
st.header("📈 Evolução Financeira")

col_filtro, col_grafico = st.columns([1, 4])

with col_filtro:
    periodicidade = st.radio(
        "Período",
        ["Mensal", "Trimestral", "Anual"],
        index=0
    )

if periodicidade == "Anual":
    df_chart = df_filtrado.groupby('ano')['valor_convertido'].sum().reset_index()
    df_chart = df_chart.sort_values('ano')
    x_axis = 'ano'

elif periodicidade == "Trimestral":
    df_chart = df_filtrado.groupby(['ano', 'trimestre'])['valor_convertido'].sum().reset_index()
    df_chart = df_chart.sort_values(['ano', 'trimestre'])
    df_chart['Periodo'] = df_chart['ano'].astype(str) + " - T" + df_chart['trimestre'].astype(str)
    x_axis = 'Periodo'

else:
    df_chart = df_filtrado.groupby(['ano', 'mes', 'nome_mes'])['valor_convertido'].sum().reset_index()
    df_chart = df_chart.sort_values(['ano', 'mes'])
    df_chart['Periodo'] = df_chart['ano'].astype(str) + " - " + df_chart['nome_mes']
    x_axis = 'Periodo'

# Crescimento %
df_chart['crescimento_%'] = df_chart['valor_convertido'].pct_change() * 100

with col_grafico:
    fig = px.line(
        df_chart,
        x=x_axis,
        y='valor_convertido',
        markers=True,
        title="Evolução do Volume Financeiro",
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)

# Insight
if not df_chart.empty:
    maior_valor = df_chart['valor_convertido'].max()
    periodo_pico = df_chart.loc[
        df_chart['valor_convertido'] == maior_valor, x_axis
    ].iloc[0]

    st.info(f"💡 Pico em **{periodo_pico}** com **R$ {maior_valor:,.2f}**")

st.markdown("---")

# ==========================================
# PAÍSES (ORIGEM E DESTINO)
# ==========================================
st.header("🌍 Análise Geográfica")

col1, col2 = st.columns(2)

with col1:
    df_origem = df_filtrado.groupby('nome_pais_origem')['valor_convertido']\
        .sum().nlargest(10).reset_index()

    fig = px.bar(df_origem, x='valor_convertido', y='nome_pais_origem',
                 orientation='h', title="Top 10 Países de Origem",
                 template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    df_destino = df_filtrado.groupby('nome_pais_destino')['valor_convertido']\
        .sum().nlargest(10).reset_index()

    fig = px.bar(df_destino, x='valor_convertido', y='nome_pais_destino',
                 orientation='h', title="Top 10 Países de Destino",
                 template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# BLOCOS ECONÔMICOS
# ==========================================
st.header("🏢 Blocos Econômicos")

df_bloco = df_filtrado.groupby('bloco_origem')['valor_convertido']\
    .sum().sort_values(ascending=True).reset_index()

fig = px.bar(
    df_bloco,
    x='valor_convertido',
    y='bloco_origem',
    orientation='h',
    title="Valor por Bloco Econômico",
    template="plotly_dark"
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==========================================
# PRODUTOS
# ==========================================
st.header("📦 Produtos e Categorias")

df_prod = df_filtrado.groupby(
    ['categoria_produto', 'descricao_produto']
)[['valor_convertido', 'quantidade_transacionada']].sum().reset_index()

fig = px.treemap(
    df_prod,
    path=['categoria_produto', 'descricao_produto'],
    values='valor_convertido',
    title="Participação por Produto",
    template="plotly_dark"
)
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# CAMBIO
# ==========================================
st.header("💱 Impacto Cambial")

df_cambio = df_filtrado.groupby('ano')[[
    'valor_transacao', 'valor_convertido'
]].sum().reset_index()

df_cambio['impacto_cambio'] = df_cambio['valor_convertido'] - df_cambio['valor_transacao']

fig = px.bar(
    df_cambio,
    x='ano',
    y=['valor_transacao', 'valor_convertido'],
    barmode='group',
    title="Valor Original vs Convertido",
    template="plotly_dark"
)
st.plotly_chart(fig, use_container_width=True)

# KPI CAMBIAL
impacto_total = df_cambio['impacto_cambio'].sum()
st.metric("💱 Impacto Cambial Total", f"R$ {impacto_total:,.2f}")
