/*
Trabalho 1 Parte 3, Guilherme Lelinski e Mauricio Taques
Criação do esquema de dados do sistema
*/

CREATE TABLE medico (
    id_medico SERIAL PRIMARY KEY,
    nome      VARCHAR(150) NOT NULL,
    crm       VARCHAR(9) NOT NULL
);

-- Filial é criada antes de Vendedor porque Vendedor referencia Filial
-- (cada vendedor trabalha em exatamente uma filial).
CREATE TABLE filial (
    id_filial     SERIAL PRIMARY KEY,
    codigo_filial VARCHAR(10) UNIQUE NOT NULL,
    cnpj          VARCHAR(20) UNIQUE NOT NULL,
    nome_fantasia VARCHAR(150) NOT NULL,
    nome_gerente  VARCHAR(150) NOT NULL,
    telefone      VARCHAR(20),
    endereco      TEXT
);

CREATE TABLE vendedor (
    id_vendedor         SERIAL PRIMARY KEY,
    id_filial           INTEGER NOT NULL REFERENCES filial(id_filial),
    nome                VARCHAR(150) NOT NULL,
    cpf                 VARCHAR(12) UNIQUE NOT NULL,
    matricula           INTEGER UNIQUE NOT NULL,
    cargo               VARCHAR(20) NOT NULL,
    data_admissao       DATE NOT NULL,
    comissao_percentual NUMERIC(5,1)
);

CREATE TABLE cliente (
    id_cliente      SERIAL PRIMARY KEY,
    nome            VARCHAR(150) NOT NULL,
    cpf             VARCHAR(12) UNIQUE NOT NULL,
    telefone        VARCHAR(20),
    mail            VARCHAR(100),
    data_nascimento DATE
);

CREATE TABLE fornecedor (
    id_fornecedor       SERIAL PRIMARY KEY,
    cnpj                VARCHAR(20) UNIQUE NOT NULL,
    razao_social        VARCHAR(150) UNIQUE NOT NULL,
    nome_fantasia       VARCHAR(150) NOT NULL, 
    mail                VARCHAR(100),
    telefone            VARCHAR(20),
    condicoes_pagamento VARCHAR(50),
    endereco            TEXT
);

CREATE TABLE produto (
    id_produto       SERIAL PRIMARY KEY,
    codigo_de_barras BIGINT UNIQUE NOT NULL,
    nome_produto     VARCHAR(150) NOT NULL,
    categoria        VARCHAR(100) CHECK (categoria IN ('Medicamento', 'Cosmético', 'Higiene Pessoal', 'Conveniência')),
    fabricante       VARCHAR(150) NOT NULL,
    principio_ativo  VARCHAR(50),
    preco_custo      NUMERIC(10,2) CHECK (preco_custo >= 0),
    preco_venda      NUMERIC(10,2) CHECK (preco_venda >= 0),
    margem_lucro     NUMERIC(10, 2) GENERATED ALWAYS AS (preco_venda - preco_custo) STORED,
    descricao        TEXT
);

CREATE TABLE lote (
    id_lote         SERIAL PRIMARY KEY,
    id_produto      INTEGER NOT NULL REFERENCES produto(id_produto),
    id_fornecedor   INTEGER NOT NULL REFERENCES fornecedor(id_fornecedor),
    numero_lote     INTEGER UNIQUE NOT NULL,
    data_fabricacao DATE NOT NULL,
    data_validade   DATE NOT NULL,
    quantidade      INTEGER NOT NULL DEFAULT 0 CHECK (quantidade >= 0)
);

CREATE TABLE medicamento (
    id_medicamento SERIAL PRIMARY KEY,
    id_produto     INTEGER NOT NULL REFERENCES produto(id_produto),
    controlado     BOOLEAN DEFAULT FALSE
);

CREATE TABLE prescricao (
    id_prescricao     SERIAL PRIMARY KEY,
    id_medico         INTEGER NOT NULL REFERENCES medico(id_medico),
    numero_prescricao INTEGER,
    data              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE item_prescricao (
    id_item_prescricao SERIAL PRIMARY KEY,
    id_medicamento     INTEGER NOT NULL REFERENCES medicamento(id_medicamento),
    id_prescricao      INTEGER NOT NULL REFERENCES prescricao(id_prescricao),
    posologia          TEXT
);

CREATE TABLE estoque (
    id_estoque     SERIAL PRIMARY KEY,
    id_lote        INTEGER NOT NULL REFERENCES lote(id_lote),
    id_produto     INTEGER NOT NULL REFERENCES produto(id_produto),
    id_filial      INTEGER NOT NULL REFERENCES filial(id_filial),
    estoque_maximo INTEGER DEFAULT 0 CHECK (estoque_maximo >= 0),
    estoque_minimo INTEGER DEFAULT 0 CHECK (estoque_minimo >= 0),
    quantidade     INTEGER NOT NULL DEFAULT 0 CHECK (quantidade >= 0),
    CONSTRAINT check_estoque_min_max CHECK (estoque_maximo >= estoque_minimo)
);

CREATE TABLE reposicao_estoque (
    id_reposicao      SERIAL PRIMARY KEY,
    id_fornecedor     INTEGER NOT NULL REFERENCES fornecedor(id_fornecedor),
    id_filial_destino INTEGER NOT NULL REFERENCES filial(id_filial),
    numero_pedido     INTEGER UNIQUE NOT NULL,
    data_pedido       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status            VARCHAR(20) CHECK (status IN ('PENDENTE', 'APROVADO', 'ENVIADO', 'RECEBIDO', 'CANCELADO')) DEFAULT 'PENDENTE',
    valor_total       NUMERIC(12,2) DEFAULT 0
);

-- Recebido é criada antes de Item_Reposicao porque Item_Reposicao referencia
-- Recebido (id_recebido: indica em qual recebimento o item entrou).
CREATE TABLE recebido (
    id_recebido  SERIAL PRIMARY KEY,
    id_reposicao INTEGER NOT NULL REFERENCES reposicao_estoque(id_reposicao),
    quantidade   INTEGER NOT NULL DEFAULT 0 CHECK (quantidade >= 0),
    data         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    divergência  TEXT
);

CREATE TABLE item_reposicao (
    id_item_reposicao SERIAL PRIMARY KEY,
    id_reposicao      INTEGER NOT NULL REFERENCES reposicao_estoque(id_reposicao),
    id_produto        INTEGER NOT NULL REFERENCES produto(id_produto),
    id_lote           INTEGER NOT NULL REFERENCES lote(id_lote),
    id_recebido       INTEGER REFERENCES recebido(id_recebido),
    quantidade        INTEGER NOT NULL DEFAULT 0 CHECK (quantidade >= 0),
    valor_unitario    NUMERIC(10,2) NOT NULL CHECK (valor_unitario >= 0),
    valor_total       NUMERIC(12,2) GENERATED ALWAYS AS (quantidade * valor_unitario) STORED
);

CREATE TABLE venda (
    id_venda        SERIAL PRIMARY KEY,
    id_filial       INTEGER NOT NULL REFERENCES filial(id_filial),
    id_vendedor     INTEGER NOT NULL REFERENCES vendedor(id_vendedor),
    id_cliente      INTEGER REFERENCES cliente(id_cliente),
    cupom_fiscal    INTEGER UNIQUE NOT NULL CHECK (cupom_fiscal BETWEEN 100000 AND 999999),
    data_hora       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    forma_pagamento VARCHAR(20) CHECK (forma_pagamento IN ('Pix', 'Cartão de Crédito', 'Cartão de Débito')),
    valor_total     NUMERIC(12,2) DEFAULT 0
);

CREATE TABLE item_venda (
    id_item_venda  SERIAL PRIMARY KEY,
    id_venda       INTEGER NOT NULL REFERENCES venda(id_venda),
    id_produto     INTEGER NOT NULL REFERENCES produto(id_produto),
    id_prescricao  INTEGER REFERENCES prescricao(id_prescricao), 
    quantidade     INTEGER NOT NULL DEFAULT 0 CHECK (quantidade >= 0),
    preco_unitario NUMERIC(10,2) NOT NULL CHECK (preco_unitario >= 0),
    desconto       NUMERIC(10,2),
    valor_total    NUMERIC(12,2) GENERATED ALWAYS AS ((quantidade * preco_unitario) - ((quantidade * preco_unitario) * desconto)) STORED
);

CREATE TABLE devolucao (
    id_devolucao    SERIAL PRIMARY KEY,
    id_venda        INTEGER NOT NULL REFERENCES venda(id_venda),
    data_devolucao  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    motivo          TEXT,
    tipo            VARCHAR(20) CHECK (tipo IN ('REEMBOLSO', 'TROCA'))
);

CREATE TABLE item_devolucao (
    id_item_devolucao SERIAL PRIMARY KEY,
    id_devolucao      INTEGER NOT NULL REFERENCES devolucao(id_devolucao),
    id_produto        INTEGER NOT NULL REFERENCES produto(id_produto),
    quantidade        INTEGER NOT NULL CHECK (quantidade > 0)
);

BEGIN;

-- 1. Medico
-- 10 registros
INSERT INTO medico (nome, crm) VALUES
    ('Ricardo Almeida',          '37545-SC'),
    ('Fernanda Souza',           '3856-SC'),
    ('Marcelo Teixeira',         '31229-PR'),
    ('Juliana Carvalho',         '876486-RJ'),
    ('Paulo Mendes',             '67583-SC'),
    ('Ana Beatriz Rocha',        '36237-SC'),
    ('Carlos Eduardo Lima',      '16534-SC'),
    ('Patrícia Nunes',           '9743-SC'),
    ('Henrique Barbosa',         '10342-SC'),
    ('Camila Ferreira',          '4471-SC');

-- 1.1 Filial (inserida antes de Vendedor por causa do FK vendedor.id_filial)
-- 3 registros
INSERT INTO filial (codigo_filial, cnpj, nome_fantasia, nome_gerente, telefone, endereco) VALUES
    ('FIL-001', '12.345.678/0001-01', 'FarmaJoinville Centro',  'Roberto Mendes',  '(47) 3322-0001', 'Rua Princesa Isabel, 500, Centro, Joinville/SC'),
    ('FIL-002', '12.345.678/0002-02', 'FarmaJoinville Norte',   'Sandra Ferreira', '(47) 3322-0002', 'Av. Santos Dumont, 1200, Boa Vista, Joinville/SC'),
    ('FIL-003', '12.345.678/0003-03', 'FarmaJoinville Sul',     'Marcos Andrade',  '(47) 3322-0003', 'Rua XV de Novembro, 800, Aventureiro, Joinville/SC');

-- 2. Vendedor
-- 10 registros (id_filial: cada vendedor trabalha em uma única filial)
INSERT INTO vendedor (id_filial, nome, cpf, matricula, cargo, data_admissao, comissao_percentual) VALUES
    (1, 'João Pereira',        '10122233344', 1001, 'Atendente',  '2021-03-10', 2.5),
    (1, 'Aline Martins',       '20233344455', 1002, 'Atendente',  '2020-07-15', 2.5),
    (2, 'Rafael Costa',        '30344455566', 1003, 'Atendente',  '2022-01-20', 2.5),
    (1, 'Bruna Oliveira',      '40455566677', 1004, 'Farmacêutico','2019-05-08', 3.0),
    (2, 'Diego Nascimento',    '50566677788', 1005, 'Atendente',  '2023-02-14', 2.5),
    (2, 'Tatiane Rodrigues',   '60677788899', 1006, 'Farmacêutico','2018-11-30', 3.0),
    (3, 'Lucas Freitas',       '70788899900', 1007, 'Atendente',  '2022-08-01', 2.5),
    (3, 'Mariana Gomes',       '80899900011', 1008, 'Atendente',  '2021-10-25', 2.5),
    (3, 'Thiago Batista',      '90900011122', 1009, 'Farmacêutico','2017-06-18', 3.0),
    (1, 'Vanessa Cunha',       '01011122233', 1010, 'Atendente',  '2023-09-05', 2.5);
 
-- 3. Cliente
-- 15 registros
INSERT INTO cliente (nome, cpf, telefone, mail, data_nascimento) VALUES
    ('Ana Paula Ferreira',  '11122233301', '(47) 99101-0001', 'ana.ferreira@email.com',   '1985-04-12'),
    ('Bruno Costa',         '22233344402', '(47) 99101-0002', 'bruno.costa@email.com',    '1990-08-23'),
    ('Carla Menezes',       '33344455503', '(47) 99101-0003', 'carla.menezes@email.com',  '1978-11-05'),
    ('Daniel Rocha',        '44455566604', '(47) 99101-0004', 'daniel.rocha@email.com',   '1995-02-17'),
    ('Eduarda Lima',        '55566677705', '(47) 99101-0005', 'eduarda.lima@email.com',   '2000-06-30'),
    ('Fábio Nascimento',    '66677788806', '(47) 99101-0006', 'fabio.nasc@email.com',     '1982-09-14'),
    ('Gabriela Torres',     '77788899907', '(47) 99101-0007', 'gabi.torres@email.com',    '1998-03-22'),
    ('Henrique Alves',      '88899900008', '(47) 99101-0008', 'henrique.alves@email.com', '1975-12-01'),
    ('Isabela Martins',     '99900011109', '(47) 99101-0009', 'isabela.m@email.com',      '1993-07-19'),
    ('João Vitor Pires',    '00011122210', '(47) 99101-0010', 'joaovitor.p@email.com',    '1988-05-08'),
    ('Larissa Cunha',       '11133355511', '(47) 99101-0011', 'larissa.cunha@email.com',  '2001-01-25'),
    ('Marcos Oliveira',     '22244466612', '(47) 99101-0012', 'marcos.oliv@email.com',    '1970-10-11'),
    ('Natália Sousa',       '33355577713', '(47) 99101-0013', 'natalia.sousa@email.com',  '1996-08-03'),
    ('Otávio Gomes',        '44466688814', '(47) 99101-0014', 'otavio.gomes@email.com',   '1983-04-27'),
    ('Patrícia Duarte',     '55577799915', '(47) 99101-0015', 'patricia.d@email.com',     '1991-12-15');
 
-- 4. Fornecedor
-- 10 registros
INSERT INTO fornecedor (cnpj, razao_social, nome_fantasia, mail, telefone, condicoes_pagamento, endereco) VALUES
    ('60.798.633/0001-78', 'EMS S.A.',                    'EMS Pharma',     'vendas@ems.com.br',         '(11) 4196-9000', '30 dias',  'Rodovia SP-101, Km 08, Hortolândia/SP'),
    ('44.734.671/0001-51', 'Medley Farmacêutica Ltda',    'Medley',         'comercial@medley.com.br',   '(11) 4133-6000', '30/60',    'Av. Prefeito Luís Walter, Sumaré/SP'),
    ('02.932.074/0001-91', 'Hypermarcas S.A.',            'Hypera Pharma',  'hypera@hypera.com.br',      '(11) 3897-9797', '28 DDL',   'Av. das Nações Unidas, 14401, São Paulo/SP'),
    ('61.190.096/0001-92', 'Eurofarma Laboratórios S.A.', 'Eurofarma',      'contato@eurofarma.com.br',  '(11) 3627-4500', '30/60/90', 'Av. Vereador José Diniz, São Paulo/SP'),
    ('25.005.218/0001-94', 'Cimed Indústria Farmac. Ltda','Cimed',          'cimed@cimed.com.br',        '(35) 3829-9000', 'À vista',  'Av. Zuca Lino Ferreira, Poços de Caldas/MG'),
    ('12.345.001/0001-01', 'Unimed Distribuidora Ltda',   'UniDistrib',     'unidistrib@ud.com.br',      '(47) 3333-0001', '30 dias',  'Rua XV de Novembro, 500, Joinville/SC'),
    ('12.345.002/0001-02', 'DrogariaMax Distrib. ME',     'DrogariaMax',    'max@drogariamax.com.br',    '(47) 3333-0002', '15 dias',  'Rua Blumenau, 200, Joinville/SC'),
    ('12.345.003/0001-03', 'Cosméticos Sul Ltda',         'CosméticosSul',  'sul@cosmeticossul.com.br',  '(48) 3222-0001', '30/60',    'Av. Beira Mar, 100, Florianópolis/SC'),
    ('12.345.004/0001-04', 'HigieneTotal Eireli',         'HigieneTotal',   'total@higienatotal.com.br', '(41) 3111-0001', '28 DDL',   'Rua das Flores, 300, Curitiba/PR'),
    ('12.345.005/0001-05', 'Nutrição & Saúde Ltda',       'NutriSaúde',     'nutri@nutrisaude.com.br',   '(11) 3000-0001', '30 dias',  'Av. Paulista, 1000, São Paulo/SP');
 
-- 5. Produto
-- 20 registros
INSERT INTO produto (codigo_de_barras, nome_produto, categoria, fabricante,
                     principio_ativo, preco_custo, preco_venda, descricao) VALUES
    -- Medicamentos controlados
    (7891234560001, 'Ritalina 10mg cx/30',      'Medicamento', 'Novartis',   'Metilfenidato',      45.00,  89.90, 'Metilfenidato 10mg — 30 comprimidos'),
    (7891234560002, 'Rivotril 2mg cx/30',        'Medicamento', 'Roche',      'Clonazepam',         28.00,  54.90, 'Clonazepam 2mg — 30 comprimidos'),
    (7891234560003, 'Frontal 0,5mg cx/30',       'Medicamento', 'Pfizer',     'Alprazolam',         22.00,  43.90, 'Alprazolam 0,5mg — 30 comprimidos'),
    -- Medicamentos comuns
    (7891234560004, 'Amoxicilina 500mg cx/21',   'Medicamento', 'EMS',        'Amoxicilina',        12.00,  24.90, 'Amoxicilina 500mg — 21 cápsulas'),
    (7891234560005, 'Dipirona 500mg cx/20',      'Medicamento', 'Medley',     'Dipirona Sódica',     4.50,   9.90, 'Dipirona Sódica 500mg — 20 comprimidos'),
    (7891234560006, 'Ibuprofeno 600mg cx/20',    'Medicamento', 'Cimed',      'Ibuprofeno',          6.00,  12.90, 'Ibuprofeno 600mg — 20 comprimidos'),
    (7891234560007, 'Omeprazol 20mg cx/28',      'Medicamento', 'Eurofarma',  'Omeprazol',           8.00,  16.90, 'Omeprazol 20mg — 28 cápsulas'),
    (7891234560008, 'Loratadina 10mg cx/12',     'Medicamento', 'Hypera',     'Loratadina',          5.00,  10.90, 'Loratadina 10mg — 12 comprimidos'),
    -- Cosméticos
    (7891234560009, 'Protetor Solar FPS50 120ml','Cosmético',   'Nivea',       NULL,                 18.00,  39.90, 'Protetor solar facial FPS50 — 120ml'),
    (7891234560010, 'Hidratante Corporal 400ml', 'Cosmético',   'Dove',        NULL,                 14.00,  29.90, 'Loção hidratante corporal — 400ml'),
    (7891234560011, 'Shampoo Anticaspa 400ml',   'Cosmético',   'Head&Shoulders', NULL,              12.00,  24.90, 'Shampoo anticaspa controle — 400ml'),
    (7891234560012, 'Condicionador 400ml',        'Cosmético',   'Pantene',    NULL,                 11.00,  22.90, 'Condicionador hidratação intensa — 400ml'),
    -- Higiene Pessoal
    (7891234560013, 'Escova Dental Macia',        'Higiene Pessoal', 'Colgate', NULL,                 2.50,   5.90, 'Escova dental cerdas macias'),
    (7891234560014, 'Creme Dental 90g',           'Higiene Pessoal', 'Colgate', NULL,                 3.00,   6.90, 'Creme dental flúor — 90g'),
    (7891234560015, 'Sabonete Antibacteriano 90g','Higiene Pessoal', 'Protex',  NULL,                 2.00,   4.90, 'Sabonete antibacteriano — 90g'),
    (7891234560016, 'Fio Dental 50m',             'Higiene Pessoal', 'Oral-B',  NULL,                 3.50,   7.90, 'Fio dental encerado menta — 50m'),
    -- Conveniência
    (7891234560017, 'Água Mineral 500ml',         'Conveniência', 'Crystal',   NULL,                  0.80,   2.50, 'Água mineral natural sem gás — 500ml'),
    (7891234560018, 'Barra de Cereal Integral',   'Conveniência', 'Trio',      NULL,                  1.50,   3.90, 'Barra de cereal integral frutas — 25g'),
    (7891234560019, 'Vitamina C 1g cx/10',        'Conveniência', 'Cimed',     'Ácido Ascórbico',     5.00,  11.90, 'Vitamina C efervescente 1g — 10 comprimidos'),
    (7891234560020, 'Máscara Descartável cx/50',  'Conveniência', 'Descarpack', NULL,                  8.00,  18.90, 'Máscara descartável tripla camada — cx com 50');
 
-- 7. Lote
-- 13 registros (um lote por produto estocado; id_lote segue a ordem abaixo)
-- id_fornecedor: fornecedor que abastece aquele produto (conforme as reposições).
INSERT INTO lote (id_produto, id_fornecedor, numero_lote, data_fabricacao, data_validade, quantidade) VALUES
    (1,  1, 10001, '2024-01-10', '2026-01-10', 100),  -- id_lote 1
    (2,  1, 10002, '2024-02-15', '2026-02-15', 150),  -- id_lote 2
    (3,  1, 10003, '2024-03-20', '2026-03-20', 200),  -- id_lote 3
    (4,  2, 10004, '2024-04-05', '2026-04-05', 100),  -- id_lote 4
    (5,  2, 10005, '2024-05-12', '2026-05-12', 300),  -- id_lote 5
    (6,  3, 10006, '2024-06-18', '2025-06-18',  80),  -- id_lote 6 — vence em 2025 — alerta
    (7,  1, 10007, '2024-07-22', '2025-07-22', 250),  -- id_lote 7 — vence em 2025 — alerta
    (8,  3, 10008, '2024-08-30', '2026-08-30', 120),  -- id_lote 8
    (9,  6, 10009, '2024-09-14', '2026-09-14', 500),  -- id_lote 9
    (10, 6, 10010, '2024-10-01', '2026-10-01', 200),  -- id_lote 10
    (13, 1, 10011, '2024-11-05', '2026-11-05', 150),  -- id_lote 11
    (17, 1, 10012, '2024-12-10', '2026-12-10', 300),  -- id_lote 12
    (19, 7, 10013, '2025-01-15', '2027-01-15', 200);  -- id_lote 13
 
-- 8. Medicamento
-- 8 registros
INSERT INTO medicamento (id_produto, controlado) VALUES
    (1, TRUE),   -- Ritalina — controlado
    (2, TRUE),   -- Rivotril — controlado
    (3, TRUE),   -- Frontal  — controlado
    (4, FALSE),  -- Amoxicilina — comum
    (5, FALSE),  -- Dipirona    — comum
    (6, FALSE),  -- Ibuprofeno  — comum
    (7, FALSE),  -- Omeprazol   — comum
    (8, FALSE);  -- Loratadina  — comum
 
-- 9. Prescrição
-- 5 registros
INSERT INTO prescricao (id_medico, numero_prescricao, data) VALUES
    (1, 20250001, '2025-01-10 09:00:00'),
    (2, 20250002, '2025-01-15 10:30:00'),
    (3, 20250003, '2025-02-01 14:00:00'),
    (5, 20250004, '2025-02-10 11:00:00'),
    (6, 20250005, '2025-03-05 09:30:00');
 
-- 10. Item_Prescricao
-- 8 registros
INSERT INTO item_prescricao (id_medicamento, id_prescricao, posologia) VALUES
    (1, 1, 'Tomar 1 comprimido pela manhã em jejum'),
    (2, 1, 'Tomar 1 comprimido à noite antes de dormir'),
    (3, 2, 'Tomar 1 comprimido 2x ao dia'),
    (1, 3, 'Tomar 1 comprimido pela manhã'),
    (4, 3, 'Tomar 1 cápsula de 8 em 8 horas por 7 dias'),
    (2, 4, 'Tomar 1 comprimido à noite'),
    (5, 5, 'Tomar 1 comprimido a cada 6 horas se dor'),
    (3, 5, 'Tomar 1 comprimido pela manhã e 1 à noite');
 
-- 11. Estoque
-- 15 registros
INSERT INTO estoque (id_lote, id_produto, id_filial,
                     estoque_maximo, estoque_minimo, quantidade) VALUES
    -- Filial 1 (Centro)
    (1,  1,  1, 100,  10,  45),   -- Ritalina
    (2,  2,  1, 100,  10,  30),   -- Rivotril
    (3,  3,  1, 100,  10,   8),   -- Frontal — abaixo do mínimo!
    (4,  4,  1, 200,  20,  80),   -- Amoxicilina
    (5,  5,  1, 300,  30, 150),   -- Dipirona
    (9,  9,  1, 150,  15,  12),   -- Protetor Solar — lote próximo vencimento
    (11, 13, 1, 200,  20,  90),   -- Escova Dental — lote próximo vencimento
    -- Filial 2 (Norte)
    (1,  1,  2, 100,  10,  20),   -- Ritalina
    (5,  5,  2, 300,  30,   5),   -- Dipirona — abaixo do mínimo!
    (6,  6,  2, 150,  15,  60),   -- Ibuprofeno
    (10, 10, 2, 100,  10,  35),   -- Hidratante
    (12, 17, 2, 500,  50, 200),   -- Água Mineral
    -- Filial 3 (Sul)
    (7,  7,  3, 150,  15,  70),   -- Omeprazol
    (8,  8,  3, 150,  15,  40),   -- Loratadina
    (13, 19, 3, 200,  20,   3);   -- Vitamina C — abaixo do mínimo!
 
-- 12. Reposicao_Estoque
-- 5 registros
INSERT INTO reposicao_estoque (id_fornecedor, id_filial_destino, numero_pedido,
                    data_pedido, status, valor_total) VALUES
    (1, 1, 2025001, '2025-01-05 09:00:00', 'RECEBIDO',   4950.00),
    (2, 1, 2025002, '2025-01-10 10:00:00', 'RECEBIDO',   1890.00),
    (3, 2, 2025003, '2025-02-01 09:00:00', 'RECEBIDO',    780.00),
    (6, 2, 2025004, '2025-02-15 14:00:00', 'PENDENTE',   2340.00),
    (7, 3, 2025005, '2025-03-01 11:00:00', 'APROVADO',   1560.00);
 
-- 13. Item_Reposicao
-- 10 registros
INSERT INTO item_reposicao (id_reposicao, id_produto, id_lote, quantidade, valor_unitario) VALUES
    -- Reposicao 1 (EMS — Filial Centro)
    (1, 1,  1, 50,  45.00),  -- Ritalina
    (1, 2,  2, 60,  28.00),  -- Rivotril
    (1, 3,  3, 30,  22.00),  -- Frontal
    -- Reposicao 2 (Medley — Filial Centro)
    (2, 4,  4, 100, 12.00),  -- Amoxicilina
    (2, 5,  5, 200,  4.50),  -- Dipirona
    -- Reposicao 3 (Hypera — Filial Norte)
    (3, 6,  6, 80,   6.00),  -- Ibuprofeno
    (3, 8,  8, 100,  5.00),  -- Loratadina
    -- Reposicao 4 (UniDistrib — Filial Norte — pendente)
    (4, 9,  9, 60,  18.00),  -- Protetor Solar
    (4, 10, 10, 70, 14.00),  -- Hidratante
    -- Reposicao 5 (DrogariaMax — Filial Sul — aprovada)
    (5, 19, 13, 120, 5.00);  -- Vitamina C
 
-- 14. Recebido
-- 3 registros (Reposicões com status RECEBIDO)
INSERT INTO recebido (id_reposicao, quantidade, divergência) VALUES
    (1, 140, NULL),
    (2, 300, NULL),
    (3, 175, '5 unidades de Loratadina com embalagem danificada');

-- Liga os itens das reposições já recebidas ao seu recebimento (id_recebido).
UPDATE item_reposicao ir
SET id_recebido = r.id_recebido
FROM recebido r
WHERE r.id_reposicao = ir.id_reposicao;
 
-- 15. Venda
-- 8 registros
INSERT INTO venda (id_filial, id_vendedor, id_cliente, cupom_fiscal,
                   data_hora, forma_pagamento, valor_total) VALUES
    (1, 1,  1,  100001, '2025-01-20 09:15:00', 'Pix',               134.70),
    (1, 2,  2,  100002, '2025-01-22 10:30:00', 'Cartão de Crédito', 144.60),
    (1, 4,  3,  100003, '2025-01-25 14:00:00', 'Cartão de Débito',   49.80),
    (2, 5,  4,  100004, '2025-02-01 09:00:00', 'Pix',                24.90),
    (2, 3,  5,  100005, '2025-02-05 11:00:00', 'Cartão de Crédito',  79.80),
    (2, 5,  6,  100006, '2025-02-10 15:30:00', 'Pix',                43.90),
    (3, 7,  7,  100007, '2025-02-15 10:00:00', 'Cartão de Débito',   33.80),
    (3, 9,  8,  100008, '2025-03-01 09:30:00', 'Pix',                89.90);
 
-- 16. Item_Venda 
-- 15 registros
INSERT INTO item_venda (id_venda, id_produto, id_prescricao, quantidade, preco_unitario, desconto) VALUES
    -- Venda 1 (Filial Centro — João — Ana Paula)
    (1,  1, 1,    1,  89.90, 0.00),   -- Ritalina  — controlada (prescrição 1)
    (1,  2, 1,    1,  54.90, 0.10),   -- Rivotril  — controlada (prescrição 1), 10% desconto
    -- Venda 2 (Filial Centro — Aline — Bruno)
    (2,  5, NULL, 5,   9.90, 0.00),   -- Dipirona
    (2,  9, NULL, 1,  39.90, 0.05),   -- Protetor Solar 5% desc
    (2, 14, NULL, 2,   6.90, 0.00),   -- Creme Dental
    -- Venda 3 (Filial Centro — Bruna — Carla)
    (3, 13, NULL, 2,   5.90, 0.00),   -- Escova Dental
    (3, 15, NULL, 4,   4.90, 0.00),   -- Sabonete
    (3, 16, NULL, 2,   7.90, 0.00),   -- Fio Dental
    -- Venda 4 (Filial Norte — Diego — Daniel)
    (4,  6, NULL, 2,  12.90, 0.00),   -- Ibuprofeno
    -- Venda 5 (Filial Norte — Rafael — Eduarda)
    (5, 10, NULL, 2,  29.90, 0.00),   -- Hidratante
    (5, 11, NULL, 1,  24.90, 0.00),   -- Shampoo
    -- Venda 6 (Filial Norte — Diego — Fábio)
    (6,  3, 2,    1,  43.90, 0.00),   -- Frontal — controlado (prescrição 2)
    -- Venda 7 (Filial Sul — Lucas — Gabriela)
    (7, 17, NULL, 4,   2.50, 0.00),   -- Água Mineral
    (7, 18, NULL, 3,   3.90, 0.00),   -- Barra de Cereal
    -- Venda 8 (Filial Sul — Thiago — Henrique)
    (8,  1, 3,    1,  89.90, 0.00);   -- Ritalina — controlado (prescrição 3)

-- 17. Devolucao 
-- 4 registros
INSERT INTO devolucao (id_venda, data_devolucao, motivo, tipo) VALUES
    (2, '2025-01-25 14:30:00', 'Produto com embalagem danificada',        'REEMBOLSO'),
    (3, '2025-01-28 10:00:00', 'Cliente comprou item errado',             'TROCA'),
    (5, '2025-02-08 16:00:00', 'Produto vencido identificado na entrega', 'REEMBOLSO'),
    (7, '2025-02-18 11:30:00', 'Cliente desistiu da reposicao_estoque',   'REEMBOLSO');

-- 18. Item_Devolucao 
-- 6 registros
INSERT INTO item_devolucao (id_devolucao, id_produto, quantidade) VALUES
    -- Devolução 1 (refere-se à Venda 2)
    (1,  9, 1),   -- Protetor Solar
    (1, 14, 1),   -- Creme Dental
    -- Devolução 2 (refere-se à Venda 3)
    (2, 15, 2),   -- Sabonete
    -- Devolução 3 (refere-se à Venda 5)
    (3, 10, 1),   -- Hidratante
    (3, 11, 1),   -- Shampoo
    -- Devolução 4 (refere-se à Venda 7)
    (4, 17, 2);   -- Água Mineral

COMMIT;
