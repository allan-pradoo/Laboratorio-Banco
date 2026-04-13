-- =========================================
-- DIMENSÕES (STAR SCHEMA)
-- =========================================

CREATE TABLE Dim_Tempo (
    sk_tempo INT AUTO_INCREMENT PRIMARY KEY,
    data DATE,
    dia INT,
    mes INT,
    nome_mes VARCHAR(20),
    trimestre INT,
    ano INT,
    semestre INT,
    dia_da_semana VARCHAR(20)
);

CREATE TABLE Dim_Pais_Origem (
    sk_pais_origem INT AUTO_INCREMENT PRIMARY KEY,
    id_pais_origem INT,
    nome_pais_origem VARCHAR(100),
    codigo_iso_origem VARCHAR(10),
    bloco_economico_origem VARCHAR(100)
);

CREATE TABLE Dim_Pais_Destino (
    sk_pais_destino INT AUTO_INCREMENT PRIMARY KEY,
    id_pais_destino INT,
    nome_pais_destino VARCHAR(100),
    codigo_iso_destino VARCHAR(10),
    bloco_economico_destino VARCHAR(100)
);

CREATE TABLE Dim_Produto (
    sk_produto INT AUTO_INCREMENT PRIMARY KEY,
    id_produto INT,
    descricao_produto VARCHAR(255),
    codigo_ncm VARCHAR(50),
    categoria_produto VARCHAR(150)
);

CREATE TABLE Dim_Moeda_Origem (
    sk_moeda_origem INT AUTO_INCREMENT PRIMARY KEY,
    id_moeda_origem INT,
    descricao_moeda_origem VARCHAR(100),
    pais_moeda_origem VARCHAR(100)
);

CREATE TABLE Dim_Moeda_Destino (
    sk_moeda_destino INT AUTO_INCREMENT PRIMARY KEY,
    id_moeda_destino INT,
    descricao_moeda_destino VARCHAR(100),
    pais_moeda_destino VARCHAR(100)
);

CREATE TABLE Dim_Tipo_Transacao (
    sk_tipo_transacao INT AUTO_INCREMENT PRIMARY KEY,
    id_tipo_transacao INT,
    descricao_tipo_transacao VARCHAR(100)
);

CREATE TABLE Dim_Transporte (
    sk_transporte INT AUTO_INCREMENT PRIMARY KEY,
    id_transporte INT,
    descricao_transporte VARCHAR(100)
);

-- =========================================
-- FATO
-- =========================================

CREATE TABLE Fato_Transacoes_Internacionais (
    id_fato INT AUTO_INCREMENT PRIMARY KEY,

    sk_tempo INT,
    sk_pais_origem INT,
    sk_pais_destino INT,
    sk_produto INT,
    sk_moeda_origem INT,
    sk_moeda_destino INT,
    sk_tipo_transacao INT,
    sk_transporte INT,

    quantidade_transacionada DECIMAL(15,2),
    valor_transacao DECIMAL(15,2),
    valor_convertido DECIMAL(15,2),
    taxa_cambio_aplicada DECIMAL(10,6),
    custo_transporte DECIMAL(15,2),

    FOREIGN KEY (sk_tempo) REFERENCES Dim_Tempo(sk_tempo),
    FOREIGN KEY (sk_pais_origem) REFERENCES Dim_Pais_Origem(sk_pais_origem),
    FOREIGN KEY (sk_pais_destino) REFERENCES Dim_Pais_Destino(sk_pais_destino),
    FOREIGN KEY (sk_produto) REFERENCES Dim_Produto(sk_produto),
    FOREIGN KEY (sk_moeda_origem) REFERENCES Dim_Moeda_Origem(sk_moeda_origem),
    FOREIGN KEY (sk_moeda_destino) REFERENCES Dim_Moeda_Destino(sk_moeda_destino),
    FOREIGN KEY (sk_tipo_transacao) REFERENCES Dim_Tipo_Transacao(sk_tipo_transacao),
    FOREIGN KEY (sk_transporte) REFERENCES Dim_Transporte(sk_transporte)
);