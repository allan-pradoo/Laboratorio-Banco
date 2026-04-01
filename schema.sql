-- =========================================================================
-- PASSO 1: CRIAÇÃO DAS TABELAS DIMENSÃO (As pontas da estrela)
-- =========================================================================

-- Dimensão Tempo [cite: 97-104]
-- Guarda as informações das datas em que as transações ocorreram.
CREATE TABLE Dim_Tempo (
    sk_tempo INT AUTO_INCREMENT PRIMARY KEY,
    data DATE,
    dia INT,
    mes INT,
    nome_mes VARCHAR(20),
    trimestre INT,
    ano INT,
    -- Campos extras solicitados na transformação[cite: 179, 181]:
    semestre INT, 
    dia_da_semana VARCHAR(20)
);

-- Dimensão País de Origem [cite: 107-111]
CREATE TABLE Dim_Pais_Origem (
    sk_pais_origem INT AUTO_INCREMENT PRIMARY KEY,
    id_pais_origem INT,
    nome_pais_origem VARCHAR(100),
    codigo_iso_origem VARCHAR(10),
    bloco_economico_origem VARCHAR(100)
);

-- Dimensão País de Destino [cite: 114-118]
CREATE TABLE Dim_Pais_Destino (
    sk_pais_destino INT AUTO_INCREMENT PRIMARY KEY,
    id_pais_destino INT,
    nome_pais_destino VARCHAR(100),
    codigo_iso_destino VARCHAR(10),
    bloco_economico_destino VARCHAR(100)
);

-- Dimensão Categoria do Produto [cite: 127-130]
CREATE TABLE Dim_Categoria_Produto (
    sk_categoria_produto INT AUTO_INCREMENT PRIMARY KEY,
    id_categoria INT,
    descricao_categoria VARCHAR(150)
);

-- Dimensão Produto [cite: 121-126]
CREATE TABLE Dim_Produto (
    sk_produto INT AUTO_INCREMENT PRIMARY KEY,
    id_produto INT,
    descricao_produto VARCHAR(255),
    codigo_ncm VARCHAR(50),
    categoria_produto VARCHAR(150)
);

-- Dimensão Moeda de Origem [cite: 133-137]
CREATE TABLE Dim_Moeda_Origem (
    sk_moeda_origem INT AUTO_INCREMENT PRIMARY KEY,
    id_moeda_origem INT,
    descricao_moeda_origem VARCHAR(100),
    pais_moeda_origem VARCHAR(100)
);

-- Dimensão Moeda de Destino [cite: 138-140]
CREATE TABLE Dim_Moeda_Destino (
    sk_moeda_destino INT AUTO_INCREMENT PRIMARY KEY,
    id_moeda_destino INT,
    descricao_moeda_destino VARCHAR(100),
    pais_moeda_destino VARCHAR(100)
);

-- Dimensão Tipo de Transação [cite: 143-146]
CREATE TABLE Dim_Tipo_Transacao (
    sk_tipo_transacao INT AUTO_INCREMENT PRIMARY KEY,
    id_tipo_transacao INT,
    descricao_tipo_transacao VARCHAR(100)
);

-- Dimensão Transporte [cite: 147-150]
CREATE TABLE Dim_Transporte (
    sk_transporte INT AUTO_INCREMENT PRIMARY KEY,
    id_transporte INT,
    descricao_transporte VARCHAR(100)
);

-- Dimensão Bloco Econômico de Origem
-- (Criada para satisfazer a chave estrangeira pedida na Fato [cite: 94])
CREATE TABLE Dim_Bloco_Economico_Origem (
    sk_bloco_economico_origem INT AUTO_INCREMENT PRIMARY KEY,
    id_bloco INT,
    nome_bloco VARCHAR(100)
);

-- =========================================================================
-- PASSO 2: CRIAÇÃO DA TABELA FATO (O centro da estrela)
-- =========================================================================

-- Tabela Fato Transações Internacionais 
-- Reúne todas as chaves estrangeiras (sk_) e as medidas (valores numéricos) [cite: 78-94].
CREATE TABLE Fato_Transacoes_Internacionais (
    -- Chaves Estrangeiras (Mapeamento com as Dimensões) 
    sk_tempo INT,
    sk_pais_origem INT,
    sk_pais_destino INT,
    sk_produto INT,
    sk_categoria_produto INT,
    sk_moeda_origem INT,
    sk_moeda_destino INT,
    sk_tipo_transacao INT,
    sk_transporte INT,
    sk_bloco_economico_origem INT,
    
    -- Medidas (Os números do negócio) 
    quantidade_transacionada DECIMAL(15,2),
    valor_transacao DECIMAL(15,2),
    valor_convertido DECIMAL(15,2),
    taxa_cambio_aplicada DECIMAL(10,4),
    custo_transporte DECIMAL(15,2),
    
    -- Relacionamentos (Foreign Keys)
    FOREIGN KEY (sk_tempo) REFERENCES Dim_Tempo(sk_tempo),
    FOREIGN KEY (sk_pais_origem) REFERENCES Dim_Pais_Origem(sk_pais_origem),
    FOREIGN KEY (sk_pais_destino) REFERENCES Dim_Pais_Destino(sk_pais_destino),
    FOREIGN KEY (sk_produto) REFERENCES Dim_Produto(sk_produto),
    FOREIGN KEY (sk_categoria_produto) REFERENCES Dim_Categoria_Produto(sk_categoria_produto),
    FOREIGN KEY (sk_moeda_origem) REFERENCES Dim_Moeda_Origem(sk_moeda_origem),
    FOREIGN KEY (sk_moeda_destino) REFERENCES Dim_Moeda_Destino(sk_moeda_destino),
    FOREIGN KEY (sk_tipo_transacao) REFERENCES Dim_Tipo_Transacao(sk_tipo_transacao),
    FOREIGN KEY (sk_transporte) REFERENCES Dim_Transporte(sk_transporte),
    FOREIGN KEY (sk_bloco_economico_origem) REFERENCES Dim_Bloco_Economico_Origem(sk_bloco_economico_origem)
);