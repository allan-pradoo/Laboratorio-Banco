import pandas as pd
from sqlalchemy import create_engine, text
from unidecode import unidecode
import numpy as np
from urllib.parse import quote_plus
import os

print("🚀 Iniciando ETL StarComex...")

# ==========================================
# CONEXÃO ORIGEM (OLTP)
# ==========================================
oltp_user = os.getenv("OLTP_DB_USER", "consulta")
oltp_password = os.getenv("OLTP_DB_PASSWORD")
oltp_host = os.getenv("OLTP_DB_HOST", "mysql-3fa4fc41-giga-d6d4.l.aivencloud.com")
oltp_port = os.getenv("OLTP_DB_PORT", "13729")
oltp_name = os.getenv("OLTP_DB_NAME", "comex")

if not oltp_password:
    raise ValueError("Defina OLTP_DB_PASSWORD no ambiente.")

engine_origem = create_engine(
    f"mysql+pymysql://{oltp_user}:{quote_plus(oltp_password)}@{oltp_host}:{oltp_port}/{oltp_name}"
)

# ==========================================
# CONEXÃO DESTINO (DW)
# ==========================================
dw_user = os.getenv("DW_DB_USER", "root")
dw_password = os.getenv("DW_DB_PASSWORD")
dw_host = os.getenv("DW_DB_HOST", "localhost")
dw_port = os.getenv("DW_DB_PORT", "3306")
dw_name = os.getenv("DW_DB_NAME", "dw_comex")

if not dw_password:
    raise ValueError("Defina DW_DB_PASSWORD no ambiente.")

engine_dw = create_engine(
    f"mysql+pymysql://{dw_user}:{quote_plus(dw_password)}@{dw_host}:{dw_port}/{dw_name}"
)

# ==========================================
# LIMPAR DW (TRUNCATE)
# ==========================================
print("🧹 Limpando Data Warehouse...")

with engine_dw.connect() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))

    conn.execute(text("TRUNCATE TABLE Fato_Transacoes_Internacionais"))

    conn.execute(text("TRUNCATE TABLE Dim_Bloco_Economico_Origem"))
    conn.execute(text("TRUNCATE TABLE Dim_Transporte"))
    conn.execute(text("TRUNCATE TABLE Dim_Tipo_Transacao"))
    conn.execute(text("TRUNCATE TABLE Dim_Moeda_Destino"))
    conn.execute(text("TRUNCATE TABLE Dim_Moeda_Origem"))
    conn.execute(text("TRUNCATE TABLE Dim_Produto"))
    conn.execute(text("TRUNCATE TABLE Dim_Categoria_Produto"))
    conn.execute(text("TRUNCATE TABLE Dim_Pais_Destino"))
    conn.execute(text("TRUNCATE TABLE Dim_Pais_Origem"))
    conn.execute(text("TRUNCATE TABLE Dim_Tempo"))

    conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    conn.commit()

# ==========================================
# EXTRAÇÃO
# ==========================================
print("📥 Extraindo dados...")

df_transacoes = pd.read_sql("SELECT * FROM transacoes", engine_origem)
df_cambios = pd.read_sql("SELECT * FROM cambios", engine_origem)
df_produtos = pd.read_sql("SELECT * FROM produtos", engine_origem)
df_categorias = pd.read_sql("SELECT * FROM categoria_produtos", engine_origem)
df_paises = pd.read_sql("SELECT * FROM paises", engine_origem)
df_blocos = pd.read_sql("SELECT * FROM blocos_economicos", engine_origem)
df_moedas = pd.read_sql("SELECT * FROM moedas", engine_origem)
df_tipos = pd.read_sql("SELECT * FROM tipos_transacoes", engine_origem)
df_transportes = pd.read_sql("SELECT * FROM transportes", engine_origem)

# ==========================================
# TRANSFORMAÇÃO
# ==========================================
print("🧠 Transformando dados...")

def limpar(txt):
    if pd.isna(txt) or txt == "":
        return "NAO INFORMADO"
    return unidecode(str(txt).upper().strip())

for df in [df_produtos, df_categorias, df_paises, df_blocos, df_moedas, df_tipos, df_transportes]:
    for col in df.select_dtypes(include=['object', 'string']).columns:
        df[col] = df[col].apply(limpar)

# Datas
df_cambios['data'] = pd.to_datetime(df_cambios['data'])
df_cambios['ano'] = df_cambios['data'].dt.year
df_cambios['mes'] = df_cambios['data'].dt.month
df_cambios['dia'] = df_cambios['data'].dt.day
df_cambios['trimestre'] = df_cambios['data'].dt.quarter
df_cambios['semestre'] = np.where(df_cambios['mes'] <= 6, 1, 2)

meses = {
    1:'JANEIRO',2:'FEVEREIRO',3:'MARCO',4:'ABRIL',5:'MAIO',6:'JUNHO',
    7:'JULHO',8:'AGOSTO',9:'SETEMBRO',10:'OUTUBRO',11:'NOVEMBRO',12:'DEZEMBRO'
}
dias = {
    0:'SEGUNDA',1:'TERCA',2:'QUARTA',3:'QUINTA',4:'SEXTA',5:'SABADO',6:'DOMINGO'
}

df_cambios['nome_mes'] = df_cambios['mes'].map(meses)
df_cambios['dia_da_semana'] = df_cambios['data'].dt.dayofweek.map(dias)

# Regras
df_transacoes = df_transacoes[df_transacoes['valor_monetario'] >= 0]
df_transacoes = df_transacoes[df_transacoes['pais_origem'] != df_transacoes['pais_destino']]

# Fato base
fato = pd.merge(df_transacoes, df_cambios, left_on='cambio_id', right_on='id', how='left')
fato = pd.merge(
    fato,
    df_produtos[['id', 'categoria_id']].rename(columns={'id': 'id_produto_origem'}),
    left_on='produto_id',
    right_on='id_produto_origem',
    how='left'
)
fato.drop(columns=['id_produto_origem'], inplace=True)
fato = pd.merge(
    fato,
    df_paises[['id', 'bloco_id']].rename(columns={'id': 'id_pais_origem'}),
    left_on='pais_origem',
    right_on='id_pais_origem',
    how='left'
)
fato.drop(columns=['id_pais_origem'], inplace=True)
fato['valor_convertido'] = fato['valor_monetario'] * fato['taxa_cambio']

# ==========================================
# CARGA - DIMENSÕES
# ==========================================
print("🧱 Carregando dimensões...")

# Tempo
dim_tempo = df_cambios[['data','dia','mes','nome_mes','trimestre','ano','semestre','dia_da_semana']].drop_duplicates()
dim_tempo.to_sql('Dim_Tempo', engine_dw, if_exists='append', index=False)

# Categoria
dim_cat = df_categorias[['id','descricao']].drop_duplicates()
dim_cat.columns = ['id_categoria','descricao_categoria']
dim_cat.to_sql('Dim_Categoria_Produto', engine_dw, if_exists='append', index=False)

# Produto
dim_prod = pd.merge(df_produtos, df_categorias, left_on='categoria_id', right_on='id')
dim_prod = dim_prod[['id_x','descricao_x','codigo_ncm','descricao_y']]
dim_prod.columns = ['id_produto','descricao_produto','codigo_ncm','categoria_produto']
dim_prod.to_sql('Dim_Produto', engine_dw, if_exists='append', index=False)

# País
dim_pais = pd.merge(df_paises, df_blocos, left_on='bloco_id', right_on='id')
dim_pais = dim_pais[['id_x','nome_x','codigo_iso','nome_y']]
dim_pais.columns = ['id_pais','nome_pais','codigo_iso','bloco']

dim_pais_origem = dim_pais.copy()
dim_pais_origem.columns = ['id_pais_origem','nome_pais_origem','codigo_iso_origem','bloco_economico_origem']
dim_pais_origem.to_sql('Dim_Pais_Origem', engine_dw, if_exists='append', index=False)

dim_pais_destino = dim_pais.copy()
dim_pais_destino.columns = ['id_pais_destino','nome_pais_destino','codigo_iso_destino','bloco_economico_destino']
dim_pais_destino.to_sql('Dim_Pais_Destino', engine_dw, if_exists='append', index=False)

# Moeda
# =========================
# MOEDA ORIGEM
# =========================
dim_moeda_origem = df_moedas[['id','descricao','pais']].copy()

dim_moeda_origem.columns = [
    'id_moeda_origem',
    'descricao_moeda_origem',
    'pais_moeda_origem'
]

dim_moeda_origem.to_sql(
    'Dim_Moeda_Origem',
    engine_dw,
    if_exists='append',
    index=False
)

# =========================
# MOEDA DESTINO
# =========================
dim_moeda_destino = df_moedas[['id','descricao','pais']].copy()

dim_moeda_destino.columns = [
    'id_moeda_destino',
    'descricao_moeda_destino',
    'pais_moeda_destino'
]

dim_moeda_destino.to_sql(
    'Dim_Moeda_Destino',
    engine_dw,
    if_exists='append',
    index=False
)
# Tipo
df_tipos.rename(columns={'id':'id_tipo_transacao','descricao':'descricao_tipo_transacao'})\
    .to_sql('Dim_Tipo_Transacao', engine_dw, if_exists='append', index=False)

# Transporte
df_transportes.rename(columns={'id':'id_transporte','descricao':'descricao_transporte'})\
    .to_sql('Dim_Transporte', engine_dw, if_exists='append', index=False)

# Bloco
df_blocos.rename(columns={'id':'id_bloco','nome':'nome_bloco'})\
    .to_sql('Dim_Bloco_Economico_Origem', engine_dw, if_exists='append', index=False)

# ==========================================
# FATO (COM SKs)
# ==========================================
print("📊 Construindo fato...")

fato['data'] = pd.to_datetime(fato['data'], errors='coerce')
dim_tempo_db = pd.read_sql("SELECT sk_tempo, data FROM Dim_Tempo", engine_dw, parse_dates=['data'])
dim_tempo_db['data'] = pd.to_datetime(dim_tempo_db['data'], errors='coerce')
fato = pd.merge(fato, dim_tempo_db, on='data', how='left')

dim_prod_db = pd.read_sql("SELECT sk_produto, id_produto FROM Dim_Produto", engine_dw)
fato = pd.merge(fato, dim_prod_db, left_on='produto_id', right_on='id_produto', how='left')

dim_cat_db = pd.read_sql("SELECT sk_categoria_produto, id_categoria FROM Dim_Categoria_Produto", engine_dw)
fato = pd.merge(fato, dim_cat_db, left_on='categoria_id', right_on='id_categoria', how='left')

dim_pais_o = pd.read_sql("SELECT sk_pais_origem, id_pais_origem FROM Dim_Pais_Origem", engine_dw)
fato = pd.merge(fato, dim_pais_o, left_on='pais_origem', right_on='id_pais_origem', how='left')

dim_pais_d = pd.read_sql("SELECT sk_pais_destino, id_pais_destino FROM Dim_Pais_Destino", engine_dw)
fato = pd.merge(fato, dim_pais_d, left_on='pais_destino', right_on='id_pais_destino', how='left')

dim_bloco_o = pd.read_sql("SELECT sk_bloco_economico_origem, id_bloco FROM Dim_Bloco_Economico_Origem", engine_dw)
fato = pd.merge(fato, dim_bloco_o, left_on='bloco_id', right_on='id_bloco', how='left')

# FINAL
fato_final = fato[[
    'sk_tempo','sk_pais_origem','sk_pais_destino','sk_produto','sk_categoria_produto','sk_bloco_economico_origem',
    'quantidade','valor_monetario','valor_convertido','taxa_cambio'
]].copy()

fato_final.columns = [
    'sk_tempo','sk_pais_origem','sk_pais_destino','sk_produto','sk_categoria_produto','sk_bloco_economico_origem',
    'quantidade_transacionada','valor_transacao','valor_convertido','taxa_cambio_aplicada'
]

fato_final['custo_transporte'] = 0.0

fato_final.to_sql('Fato_Transacoes_Internacionais', engine_dw, if_exists='append', index=False)

print("🎉 ETL FINALIZADO COM SUCESSO!")
