import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, URL
import os

LABELS = {
    "valor_convertido": "Valor Convertido (R$)",
    "valor_transacao": "Valor da Transacao (R$)",
    "quantidade_transacionada": "Quantidade Transacionada",
    "taxa_cambio_aplicada": "Taxa de Cambio Aplicada",
    "ano": "Ano",
    "mes": "Mes",
    "trimestre": "Trimestre",
    "nome_mes": "Mes",
    "nome_pais_origem": "Pais de Origem",
    "nome_pais_destino": "Pais de Destino",
    "bloco_origem": "Bloco Economico de Origem",
    "bloco_destino": "Bloco Economico de Destino",
    "categoria_produto": "Categoria do Produto",
    "descricao_produto": "Produto",
    "descricao_transporte": "Modal de Transporte",
    "moeda_origem": "Moeda de Origem",
    "moeda_destino": "Moeda de Destino",
    "Periodo": "Periodo"
}


def format_money(valor):
    valor_formatado = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {valor_formatado}"

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
        po.bloco_economico_origem as bloco_origem,
        pd.bloco_economico_destino as bloco_destino,
        mo.descricao_moeda_origem as moeda_origem,
        md.descricao_moeda_destino as moeda_destino,
        prod.descricao_produto, prod.categoria_produto,
        tr.descricao_transporte
    FROM Fato_Transacoes_Internacionais f
    LEFT JOIN Dim_Tempo t ON f.sk_tempo = t.sk_tempo
    LEFT JOIN Dim_Pais_Origem po ON f.sk_pais_origem = po.sk_pais_origem
    LEFT JOIN Dim_Pais_Destino pd ON f.sk_pais_destino = pd.sk_pais_destino
    LEFT JOIN Dim_Moeda_Origem mo ON f.sk_moeda_origem = mo.sk_moeda_origem
    LEFT JOIN Dim_Moeda_Destino md ON f.sk_moeda_destino = md.sk_moeda_destino
    LEFT JOIN Dim_Produto prod ON f.sk_produto = prod.sk_produto
    LEFT JOIN Dim_Transporte tr ON f.sk_transporte = tr.sk_transporte
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

moedas = sorted(df["moeda_origem"].dropna().unique())
moeda_sel = st.sidebar.multiselect("Moeda de Origem", moedas)

transportes = sorted(df["descricao_transporte"].dropna().unique())
transporte_sel = st.sidebar.multiselect("Modal de Transporte", transportes)

df_filtrado = df.copy()

if ano_sel:
    df_filtrado = df_filtrado[df_filtrado["ano"].isin(ano_sel)]

if pais_sel:
    df_filtrado = df_filtrado[df_filtrado["nome_pais_origem"].isin(pais_sel)]

if cat_sel:
    df_filtrado = df_filtrado[df_filtrado["categoria_produto"].isin(cat_sel)]

if moeda_sel:
    df_filtrado = df_filtrado[df_filtrado["moeda_origem"].isin(moeda_sel)]

if transporte_sel:
    df_filtrado = df_filtrado[df_filtrado["descricao_transporte"].isin(transporte_sel)]

# ==========================================
# KPIs
# ==========================================
st.header("📌 Visão Executiva")

c1, c2, c3, c4 = st.columns(4)

v_total = df_filtrado['valor_convertido'].sum()
q_total = df_filtrado['quantidade_transacionada'].sum()
n_trans = len(df_filtrado)
t_medio = v_total / n_trans if n_trans > 0 else 0

c1.metric("💰 Valor Total Movimentado", format_money(v_total))
c2.metric("📦 Quantidade Total Transacionada", f"{q_total:,.0f}")
c3.metric("🔄 Total de Transacoes", f"{n_trans}")
c4.metric("📊 Ticket Medio por Transacao", format_money(t_medio))
c1.caption(f"Valor completo: {format_money(v_total)}")

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
        template="plotly_dark",
        labels=LABELS
    )
    st.plotly_chart(fig, use_container_width=True)

# Insight
if not df_chart.empty:
    maior_valor = df_chart['valor_convertido'].max()
    periodo_pico = df_chart.loc[
        df_chart['valor_convertido'] == maior_valor, x_axis
    ].iloc[0]

    st.info(f"💡 Pico em **{periodo_pico}** com **{format_money(maior_valor)}**")

if len(df_chart) > 1:
    melhor_periodo = df_chart.loc[df_chart['crescimento_%'].idxmax()]
    pior_periodo = df_chart.loc[df_chart['crescimento_%'].idxmin()]
    periodo_crescimento = melhor_periodo[x_axis]
    periodo_queda = pior_periodo[x_axis]
    c_g1, c_g2 = st.columns(2)
    c_g1.metric(
        "📈 Maior Crescimento",
        f"{melhor_periodo['crescimento_%']:.2f}%",
        delta=f"Periodo: {periodo_crescimento}"
    )
    c_g2.metric(
        "📉 Maior Queda",
        f"{pior_periodo['crescimento_%']:.2f}%",
        delta=f"Periodo: {periodo_queda}"
    )

df_sazonal = df_filtrado.groupby(['mes', 'nome_mes'])['valor_convertido'].mean().reset_index()
df_sazonal = df_sazonal.sort_values('mes')

if not df_sazonal.empty:
    fig_sazonal = px.bar(
        df_sazonal,
        x='nome_mes',
        y='valor_convertido',
        title="Sazonalidade: Média Mensal do Valor Convertido",
        template="plotly_dark",
        labels=LABELS
    )
    st.plotly_chart(fig_sazonal, use_container_width=True)

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
                 template="plotly_dark", labels=LABELS)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    df_destino = df_filtrado.groupby('nome_pais_destino')['valor_convertido']\
        .sum().nlargest(10).reset_index()

    fig = px.bar(df_destino, x='valor_convertido', y='nome_pais_destino',
                 orientation='h', title="Top 10 Países de Destino",
                 template="plotly_dark", labels=LABELS)
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
    template="plotly_dark",
    labels=LABELS
)
st.plotly_chart(fig, use_container_width=True)

df_bloco_comp = pd.concat([
    df_filtrado.groupby('bloco_origem')['valor_convertido']
    .sum().reset_index()
    .rename(columns={'bloco_origem': 'bloco'})
    .assign(tipo='Origem'),
    df_filtrado.groupby('bloco_destino')['valor_convertido']
    .sum().reset_index()
    .rename(columns={'bloco_destino': 'bloco'})
    .assign(tipo='Destino')
], ignore_index=True)

df_bloco_comp = df_bloco_comp[df_bloco_comp['bloco'].notna()]
df_bloco_comp = df_bloco_comp.sort_values('valor_convertido', ascending=True)

fig_comp = px.bar(
    df_bloco_comp,
    x='valor_convertido',
    y='bloco',
    color='tipo',
    barmode='group',
    orientation='h',
    title="Comparativo: Bloco de Origem vs Destino",
    template="plotly_dark",
    labels=LABELS
)
st.plotly_chart(fig_comp, use_container_width=True)

st.markdown("---")

# ==========================================
# TRANSPORTE
# ==========================================
st.header("🚚 Modal de Transporte")

df_transporte = df_filtrado.groupby('descricao_transporte')[
    ['valor_convertido', 'quantidade_transacionada']
].sum().reset_index()
df_transporte = df_transporte[df_transporte['descricao_transporte'].notna()]
df_transporte = df_transporte.sort_values('valor_convertido', ascending=False)

if not df_transporte.empty:
    col_t1, col_t2 = st.columns(2)

    with col_t1:
        fig_transp_valor = px.bar(
            df_transporte,
            x='descricao_transporte',
            y='valor_convertido',
            title="Valor Movimentado por Modal de Transporte",
            template="plotly_dark",
            labels=LABELS
        )
        st.plotly_chart(fig_transp_valor, use_container_width=True)

    with col_t2:
        fig_transp_qtd = px.bar(
            df_transporte,
            x='descricao_transporte',
            y='quantidade_transacionada',
            title="Quantidade por Modal de Transporte",
            template="plotly_dark",
            labels=LABELS
        )
        st.plotly_chart(fig_transp_qtd, use_container_width=True)
else:
    st.info("Sem dados de transporte para os filtros selecionados.")

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
    template="plotly_dark",
    labels=LABELS
)
st.plotly_chart(fig, use_container_width=True)

col_prod1, col_prod2 = st.columns(2)

with col_prod1:
    df_cat_valor = df_filtrado.groupby('categoria_produto')['valor_convertido']\
        .sum().nlargest(10).reset_index()
    fig_cat_valor = px.bar(
        df_cat_valor,
        x='valor_convertido',
        y='categoria_produto',
        orientation='h',
        title="Top Categorias por Valor",
        template="plotly_dark",
        labels=LABELS
    )
    st.plotly_chart(fig_cat_valor, use_container_width=True)

with col_prod2:
    df_cat_qtd = df_filtrado.groupby('categoria_produto')['quantidade_transacionada']\
        .sum().nlargest(10).reset_index()
    fig_cat_qtd = px.bar(
        df_cat_qtd,
        x='quantidade_transacionada',
        y='categoria_produto',
        orientation='h',
        title="Top Categorias por Quantidade",
        template="plotly_dark",
        labels=LABELS
    )
    st.plotly_chart(fig_cat_qtd, use_container_width=True)

# ==========================================
# CAMBIO
# ==========================================
st.header("💱 Impacto Cambial")

df_cambio = df_filtrado.groupby('ano')[[
    'valor_transacao', 'valor_convertido'
]].sum().reset_index()

df_cambio['impacto_cambio'] = df_cambio['valor_convertido'] - df_cambio['valor_transacao']
df_cambio['Valor da Transacao (R$)'] = df_cambio['valor_transacao']
df_cambio['Valor Convertido (R$)'] = df_cambio['valor_convertido']

fig = px.bar(
    df_cambio,
    x='ano',
    y=['Valor da Transacao (R$)', 'Valor Convertido (R$)'],
    barmode='group',
    title="Valor Original vs Convertido",
    template="plotly_dark",
    labels=LABELS
)
st.plotly_chart(fig, use_container_width=True)

df_cambio['impacto_cambio_%'] = df_cambio.apply(
    lambda row: ((row['valor_convertido'] / row['valor_transacao']) - 1) * 100
    if row['valor_transacao'] else 0,
    axis=1
)

if df_filtrado['moeda_origem'].notna().any():
    df_cambio_moeda = df_filtrado.groupby('moeda_origem')[['valor_transacao', 'valor_convertido']]\
        .sum().reset_index()
    df_cambio_moeda['impacto_cambio'] = (
        df_cambio_moeda['valor_convertido'] - df_cambio_moeda['valor_transacao']
    )
    df_cambio_moeda = df_cambio_moeda.sort_values('valor_convertido', ascending=False).head(10)

    fig_moeda = px.bar(
        df_cambio_moeda,
        x='moeda_origem',
        y=['valor_transacao', 'valor_convertido'],
        barmode='group',
        title="Impacto Cambial por Moeda de Origem (Top 10)",
        template="plotly_dark",
        labels=LABELS
    )
    st.plotly_chart(fig_moeda, use_container_width=True)
else:
    st.info("Sem dados de moeda disponíveis na fato para análise cambial por moeda.")

# KPI CAMBIAL
impacto_total = df_cambio['impacto_cambio'].sum()
st.metric("💱 Impacto Cambial Total (R$)", format_money(impacto_total))
