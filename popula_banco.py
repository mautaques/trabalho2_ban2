import datetime as dt

from database import ensure_indexes, get_db, test_connection

COLECOES = [
    "medicos", "filiais", "vendedores", "clientes", "fornecedores",
    "produtos", "lotes", "medicamentos", "prescricoes", "estoques",
    "reposicoes", "recebidos", "vendas", "devolucoes", "contadores",
]


def item_venda(seq, id_produto, id_prescricao, qtd, preco, desconto):
    bruto = qtd * preco
    return {
        "id_item_venda": seq,
        "id_produto": id_produto,
        "id_prescricao": id_prescricao,
        "quantidade": qtd,
        "preco_unitario": preco,
        "desconto": desconto,
        "valor_total": round(bruto - bruto * desconto, 2),
    }


def item_reposicao(seq, id_produto, id_lote, qtd, valor_unitario, id_recebido=None):
    return {
        "id_item_reposicao": seq,
        "id_produto": id_produto,
        "id_lote": id_lote,
        "id_recebido": id_recebido,
        "quantidade": qtd,
        "valor_unitario": valor_unitario,
        "valor_total": round(qtd * valor_unitario, 2),
    }


def main():
    if not test_connection():
        raise SystemExit("MongoDB indisponível — verifique se o servidor está rodando.")

    db = get_db()
    for colecao in COLECOES:
        db[colecao].drop()
    ensure_indexes()

    # 1. Médicos ------------------------------------------------------------
    db.medicos.insert_many([
        {"_id": i, "nome": nome, "crm": crm}
        for i, (nome, crm) in enumerate([
            ("Ricardo Almeida", "37545-SC"),
            ("Fernanda Souza", "3856-SC"),
            ("Marcelo Teixeira", "31229-PR"),
            ("Juliana Carvalho", "876486-RJ"),
            ("Paulo Mendes", "67583-SC"),
            ("Ana Beatriz Rocha", "36237-SC"),
            ("Carlos Eduardo Lima", "16534-SC"),
            ("Patrícia Nunes", "9743-SC"),
            ("Henrique Barbosa", "10342-SC"),
            ("Camila Ferreira", "4471-SC"),
        ], start=1)
    ])

    # 2. Filiais ------------------------------------------------------------
    db.filiais.insert_many([
        {"_id": 1, "codigo_filial": "FIL-001", "cnpj": "12.345.678/0001-01",
         "nome_fantasia": "FarmaJoinville Centro", "nome_gerente": "Roberto Mendes",
         "telefone": "(47) 3322-0001",
         "endereco": "Rua Princesa Isabel, 500, Centro, Joinville/SC"},
        {"_id": 2, "codigo_filial": "FIL-002", "cnpj": "12.345.678/0002-02",
         "nome_fantasia": "FarmaJoinville Norte", "nome_gerente": "Sandra Ferreira",
         "telefone": "(47) 3322-0002",
         "endereco": "Av. Santos Dumont, 1200, Boa Vista, Joinville/SC"},
        {"_id": 3, "codigo_filial": "FIL-003", "cnpj": "12.345.678/0003-03",
         "nome_fantasia": "FarmaJoinville Sul", "nome_gerente": "Marcos Andrade",
         "telefone": "(47) 3322-0003",
         "endereco": "Rua XV de Novembro, 800, Aventureiro, Joinville/SC"},
    ])

    # 3. Vendedores ----------------------------------------------------------
    db.vendedores.insert_many([
        {"_id": i, "id_filial": fil, "nome": nome, "cpf": cpf, "matricula": mat,
         "cargo": cargo, "data_admissao": dt.datetime.fromisoformat(adm),
         "comissao_percentual": com}
        for i, (fil, nome, cpf, mat, cargo, adm, com) in enumerate([
            (1, "João Pereira", "10122233344", 1001, "Atendente", "2021-03-10", 2.5),
            (1, "Aline Martins", "20233344455", 1002, "Atendente", "2020-07-15", 2.5),
            (2, "Rafael Costa", "30344455566", 1003, "Atendente", "2022-01-20", 2.5),
            (1, "Bruna Oliveira", "40455566677", 1004, "Farmacêutico", "2019-05-08", 3.0),
            (2, "Diego Nascimento", "50566677788", 1005, "Atendente", "2023-02-14", 2.5),
            (2, "Tatiane Rodrigues", "60677788899", 1006, "Farmacêutico", "2018-11-30", 3.0),
            (3, "Lucas Freitas", "70788899900", 1007, "Atendente", "2022-08-01", 2.5),
            (3, "Mariana Gomes", "80899900011", 1008, "Atendente", "2021-10-25", 2.5),
            (3, "Thiago Batista", "90900011122", 1009, "Farmacêutico", "2017-06-18", 3.0),
            (1, "Vanessa Cunha", "01011122233", 1010, "Atendente", "2023-09-05", 2.5),
        ], start=1)
    ])

    # 4. Clientes -----------------------------------------------------------
    db.clientes.insert_many([
        {"_id": i, "nome": nome, "cpf": cpf, "telefone": tel, "mail": mail,
         "data_nascimento": dt.datetime.fromisoformat(nasc)}
        for i, (nome, cpf, tel, mail, nasc) in enumerate([
            ("Ana Paula Ferreira", "11122233301", "(47) 99101-0001", "ana.ferreira@email.com", "1985-04-12"),
            ("Bruno Costa", "22233344402", "(47) 99101-0002", "bruno.costa@email.com", "1990-08-23"),
            ("Carla Menezes", "33344455503", "(47) 99101-0003", "carla.menezes@email.com", "1978-11-05"),
            ("Daniel Rocha", "44455566604", "(47) 99101-0004", "daniel.rocha@email.com", "1995-02-17"),
            ("Eduarda Lima", "55566677705", "(47) 99101-0005", "eduarda.lima@email.com", "2000-06-30"),
            ("Fábio Nascimento", "66677788806", "(47) 99101-0006", "fabio.nasc@email.com", "1982-09-14"),
            ("Gabriela Torres", "77788899907", "(47) 99101-0007", "gabi.torres@email.com", "1998-03-22"),
            ("Henrique Alves", "88899900008", "(47) 99101-0008", "henrique.alves@email.com", "1975-12-01"),
            ("Isabela Martins", "99900011109", "(47) 99101-0009", "isabela.m@email.com", "1993-07-19"),
            ("João Vitor Pires", "00011122210", "(47) 99101-0010", "joaovitor.p@email.com", "1988-05-08"),
            ("Larissa Cunha", "11133355511", "(47) 99101-0011", "larissa.cunha@email.com", "2001-01-25"),
            ("Marcos Oliveira", "22244466612", "(47) 99101-0012", "marcos.oliv@email.com", "1970-10-11"),
            ("Natália Sousa", "33355577713", "(47) 99101-0013", "natalia.sousa@email.com", "1996-08-03"),
            ("Otávio Gomes", "44466688814", "(47) 99101-0014", "otavio.gomes@email.com", "1983-04-27"),
            ("Patrícia Duarte", "55577799915", "(47) 99101-0015", "patricia.d@email.com", "1991-12-15"),
        ], start=1)
    ])

    # 5. Fornecedores ---------------------------------------------------------
    db.fornecedores.insert_many([
        {"_id": i, "cnpj": cnpj, "razao_social": razao, "nome_fantasia": fantasia,
         "mail": mail, "telefone": tel, "condicoes_pagamento": cond, "endereco": end}
        for i, (cnpj, razao, fantasia, mail, tel, cond, end) in enumerate([
            ("60.798.633/0001-78", "EMS S.A.", "EMS Pharma", "vendas@ems.com.br", "(11) 4196-9000", "30 dias", "Rodovia SP-101, Km 08, Hortolândia/SP"),
            ("44.734.671/0001-51", "Medley Farmacêutica Ltda", "Medley", "comercial@medley.com.br", "(11) 4133-6000", "30/60", "Av. Prefeito Luís Walter, Sumaré/SP"),
            ("02.932.074/0001-91", "Hypermarcas S.A.", "Hypera Pharma", "hypera@hypera.com.br", "(11) 3897-9797", "28 DDL", "Av. das Nações Unidas, 14401, São Paulo/SP"),
            ("61.190.096/0001-92", "Eurofarma Laboratórios S.A.", "Eurofarma", "contato@eurofarma.com.br", "(11) 3627-4500", "30/60/90", "Av. Vereador José Diniz, São Paulo/SP"),
            ("25.005.218/0001-94", "Cimed Indústria Farmac. Ltda", "Cimed", "cimed@cimed.com.br", "(35) 3829-9000", "À vista", "Av. Zuca Lino Ferreira, Poços de Caldas/MG"),
            ("12.345.001/0001-01", "Unimed Distribuidora Ltda", "UniDistrib", "unidistrib@ud.com.br", "(47) 3333-0001", "30 dias", "Rua XV de Novembro, 500, Joinville/SC"),
            ("12.345.002/0001-02", "DrogariaMax Distrib. ME", "DrogariaMax", "max@drogariamax.com.br", "(47) 3333-0002", "15 dias", "Rua Blumenau, 200, Joinville/SC"),
            ("12.345.003/0001-03", "Cosméticos Sul Ltda", "CosméticosSul", "sul@cosmeticossul.com.br", "(48) 3222-0001", "30/60", "Av. Beira Mar, 100, Florianópolis/SC"),
            ("12.345.004/0001-04", "HigieneTotal Eireli", "HigieneTotal", "total@higienatotal.com.br", "(41) 3111-0001", "28 DDL", "Rua das Flores, 300, Curitiba/PR"),
            ("12.345.005/0001-05", "Nutrição & Saúde Ltda", "NutriSaúde", "nutri@nutrisaude.com.br", "(11) 3000-0001", "30 dias", "Av. Paulista, 1000, São Paulo/SP"),
        ], start=1)
    ])

    # 6. Produtos (margem_lucro = preco_venda - preco_custo, calculada) -------
    db.produtos.insert_many([
        {"_id": i, "codigo_de_barras": cod, "nome_produto": nome, "categoria": cat,
         "fabricante": fab, "principio_ativo": pa, "preco_custo": custo,
         "preco_venda": venda, "margem_lucro": round(venda - custo, 2),
         "descricao": desc}
        for i, (cod, nome, cat, fab, pa, custo, venda, desc) in enumerate([
            (7891234560001, "Ritalina 10mg cx/30", "Medicamento", "Novartis", "Metilfenidato", 45.00, 89.90, "Metilfenidato 10mg — 30 comprimidos"),
            (7891234560002, "Rivotril 2mg cx/30", "Medicamento", "Roche", "Clonazepam", 28.00, 54.90, "Clonazepam 2mg — 30 comprimidos"),
            (7891234560003, "Frontal 0,5mg cx/30", "Medicamento", "Pfizer", "Alprazolam", 22.00, 43.90, "Alprazolam 0,5mg — 30 comprimidos"),
            (7891234560004, "Amoxicilina 500mg cx/21", "Medicamento", "EMS", "Amoxicilina", 12.00, 24.90, "Amoxicilina 500mg — 21 cápsulas"),
            (7891234560005, "Dipirona 500mg cx/20", "Medicamento", "Medley", "Dipirona Sódica", 4.50, 9.90, "Dipirona Sódica 500mg — 20 comprimidos"),
            (7891234560006, "Ibuprofeno 600mg cx/20", "Medicamento", "Cimed", "Ibuprofeno", 6.00, 12.90, "Ibuprofeno 600mg — 20 comprimidos"),
            (7891234560007, "Omeprazol 20mg cx/28", "Medicamento", "Eurofarma", "Omeprazol", 8.00, 16.90, "Omeprazol 20mg — 28 cápsulas"),
            (7891234560008, "Loratadina 10mg cx/12", "Medicamento", "Hypera", "Loratadina", 5.00, 10.90, "Loratadina 10mg — 12 comprimidos"),
            (7891234560009, "Protetor Solar FPS50 120ml", "Cosmético", "Nivea", None, 18.00, 39.90, "Protetor solar facial FPS50 — 120ml"),
            (7891234560010, "Hidratante Corporal 400ml", "Cosmético", "Dove", None, 14.00, 29.90, "Loção hidratante corporal — 400ml"),
            (7891234560011, "Shampoo Anticaspa 400ml", "Cosmético", "Head&Shoulders", None, 12.00, 24.90, "Shampoo anticaspa controle — 400ml"),
            (7891234560012, "Condicionador 400ml", "Cosmético", "Pantene", None, 11.00, 22.90, "Condicionador hidratação intensa — 400ml"),
            (7891234560013, "Escova Dental Macia", "Higiene Pessoal", "Colgate", None, 2.50, 5.90, "Escova dental cerdas macias"),
            (7891234560014, "Creme Dental 90g", "Higiene Pessoal", "Colgate", None, 3.00, 6.90, "Creme dental flúor — 90g"),
            (7891234560015, "Sabonete Antibacteriano 90g", "Higiene Pessoal", "Protex", None, 2.00, 4.90, "Sabonete antibacteriano — 90g"),
            (7891234560016, "Fio Dental 50m", "Higiene Pessoal", "Oral-B", None, 3.50, 7.90, "Fio dental encerado menta — 50m"),
            (7891234560017, "Água Mineral 500ml", "Conveniência", "Crystal", None, 0.80, 2.50, "Água mineral natural sem gás — 500ml"),
            (7891234560018, "Barra de Cereal Integral", "Conveniência", "Trio", None, 1.50, 3.90, "Barra de cereal integral frutas — 25g"),
            (7891234560019, "Vitamina C 1g cx/10", "Conveniência", "Cimed", "Ácido Ascórbico", 5.00, 11.90, "Vitamina C efervescente 1g — 10 comprimidos"),
            (7891234560020, "Máscara Descartável cx/50", "Conveniência", "Descarpack", None, 8.00, 18.90, "Máscara descartável tripla camada — cx com 50"),
        ], start=1)
    ])

    # 7. Lotes ---------------------------------------------------------------
    db.lotes.insert_many([
        {"_id": i, "id_produto": prod, "id_fornecedor": forn, "numero_lote": num,
         "data_fabricacao": dt.datetime.fromisoformat(fab),
         "data_validade": dt.datetime.fromisoformat(val), "quantidade": qtd}
        for i, (prod, forn, num, fab, val, qtd) in enumerate([
            (1, 1, 10001, "2024-01-10", "2026-01-10", 100),
            (2, 1, 10002, "2024-02-15", "2026-02-15", 150),
            (3, 1, 10003, "2024-03-20", "2026-03-20", 200),
            (4, 2, 10004, "2024-04-05", "2026-04-05", 100),
            (5, 2, 10005, "2024-05-12", "2026-05-12", 300),
            (6, 3, 10006, "2024-06-18", "2025-06-18", 80),
            (7, 1, 10007, "2024-07-22", "2025-07-22", 250),
            (8, 3, 10008, "2024-08-30", "2026-08-30", 120),
            (9, 6, 10009, "2024-09-14", "2026-09-14", 500),
            (10, 6, 10010, "2024-10-01", "2026-10-01", 200),
            (13, 1, 10011, "2024-11-05", "2026-11-05", 150),
            (17, 1, 10012, "2024-12-10", "2026-12-10", 300),
            (19, 7, 10013, "2025-01-15", "2027-01-15", 200),
        ], start=1)
    ])

    # 8. Medicamentos ----------------------------------------------------------
    db.medicamentos.insert_many([
        {"_id": i, "id_produto": i, "controlado": i <= 3} for i in range(1, 9)
    ])

    # 9. Prescrições (itens embutidos) ----------------------------------------
    db.prescricoes.insert_many([
        {"_id": 1, "id_medico": 1, "numero_prescricao": 20250001,
         "data": dt.datetime(2025, 1, 10, 9, 0),
         "itens": [
             {"id_medicamento": 1, "posologia": "Tomar 1 comprimido pela manhã em jejum"},
             {"id_medicamento": 2, "posologia": "Tomar 1 comprimido à noite antes de dormir"},
         ]},
        {"_id": 2, "id_medico": 2, "numero_prescricao": 20250002,
         "data": dt.datetime(2025, 1, 15, 10, 30),
         "itens": [
             {"id_medicamento": 3, "posologia": "Tomar 1 comprimido 2x ao dia"},
         ]},
        {"_id": 3, "id_medico": 3, "numero_prescricao": 20250003,
         "data": dt.datetime(2025, 2, 1, 14, 0),
         "itens": [
             {"id_medicamento": 1, "posologia": "Tomar 1 comprimido pela manhã"},
             {"id_medicamento": 4, "posologia": "Tomar 1 cápsula de 8 em 8 horas por 7 dias"},
         ]},
        {"_id": 4, "id_medico": 5, "numero_prescricao": 20250004,
         "data": dt.datetime(2025, 2, 10, 11, 0),
         "itens": [
             {"id_medicamento": 2, "posologia": "Tomar 1 comprimido à noite"},
         ]},
        {"_id": 5, "id_medico": 6, "numero_prescricao": 20250005,
         "data": dt.datetime(2025, 3, 5, 9, 30),
         "itens": [
             {"id_medicamento": 5, "posologia": "Tomar 1 comprimido a cada 6 horas se dor"},
             {"id_medicamento": 3, "posologia": "Tomar 1 comprimido pela manhã e 1 à noite"},
         ]},
    ])

    # 10. Estoques -------------------------------------------------------------
    db.estoques.insert_many([
        {"_id": i, "id_lote": lote, "id_produto": prod, "id_filial": fil,
         "estoque_maximo": emax, "estoque_minimo": emin, "quantidade": qtd}
        for i, (lote, prod, fil, emax, emin, qtd) in enumerate([
            (1, 1, 1, 100, 10, 45),
            (2, 2, 1, 100, 10, 30),
            (3, 3, 1, 100, 10, 8),      # Frontal — abaixo do mínimo!
            (4, 4, 1, 200, 20, 80),
            (5, 5, 1, 300, 30, 150),
            (9, 9, 1, 150, 15, 12),
            (11, 13, 1, 200, 20, 90),
            (1, 1, 2, 100, 10, 20),
            (5, 5, 2, 300, 30, 5),      # Dipirona — abaixo do mínimo!
            (6, 6, 2, 150, 15, 60),
            (10, 10, 2, 100, 10, 35),
            (12, 17, 2, 500, 50, 200),
            (7, 7, 3, 150, 15, 70),
            (8, 8, 3, 150, 15, 40),
            (13, 19, 3, 200, 20, 3),    # Vitamina C — abaixo do mínimo!
        ], start=1)
    ])

    # 11. Reposições (itens embutidos; valor_total = soma dos itens) -----------
    reposicoes = [
        {"_id": 1, "id_fornecedor": 1, "id_filial_destino": 1,
         "numero_pedido": 2025001, "data_pedido": dt.datetime(2025, 1, 5, 9, 0),
         "status": "RECEBIDO",
         "itens": [
             item_reposicao(1, 1, 1, 50, 45.00, id_recebido=1),
             item_reposicao(2, 2, 2, 60, 28.00, id_recebido=1),
             item_reposicao(3, 3, 3, 30, 22.00, id_recebido=1),
         ]},
        {"_id": 2, "id_fornecedor": 2, "id_filial_destino": 1,
         "numero_pedido": 2025002, "data_pedido": dt.datetime(2025, 1, 10, 10, 0),
         "status": "RECEBIDO",
         "itens": [
             item_reposicao(1, 4, 4, 100, 12.00, id_recebido=2),
             item_reposicao(2, 5, 5, 200, 4.50, id_recebido=2),
         ]},
        {"_id": 3, "id_fornecedor": 3, "id_filial_destino": 2,
         "numero_pedido": 2025003, "data_pedido": dt.datetime(2025, 2, 1, 9, 0),
         "status": "RECEBIDO",
         "itens": [
             item_reposicao(1, 6, 6, 80, 6.00, id_recebido=3),
             item_reposicao(2, 8, 8, 100, 5.00, id_recebido=3),
         ]},
        {"_id": 4, "id_fornecedor": 6, "id_filial_destino": 2,
         "numero_pedido": 2025004, "data_pedido": dt.datetime(2025, 2, 15, 14, 0),
         "status": "PENDENTE",
         "itens": [
             item_reposicao(1, 9, 9, 60, 18.00),
             item_reposicao(2, 10, 10, 70, 14.00),
         ]},
        {"_id": 5, "id_fornecedor": 7, "id_filial_destino": 3,
         "numero_pedido": 2025005, "data_pedido": dt.datetime(2025, 3, 1, 11, 0),
         "status": "APROVADO",
         "itens": [
             item_reposicao(1, 19, 13, 120, 5.00),
         ]},
    ]
    for rep in reposicoes:
        rep["valor_total"] = round(sum(i["valor_total"] for i in rep["itens"]), 2)
    db.reposicoes.insert_many(reposicoes)

    # 12. Recebidos --------------------------------------------------------------
    db.recebidos.insert_many([
        {"_id": 1, "id_reposicao": 1, "quantidade": 140,
         "data": dt.datetime(2025, 1, 8, 10, 0), "divergencia": None},
        {"_id": 2, "id_reposicao": 2, "quantidade": 300,
         "data": dt.datetime(2025, 1, 13, 9, 30), "divergencia": None},
        {"_id": 3, "id_reposicao": 3, "quantidade": 175,
         "data": dt.datetime(2025, 2, 4, 15, 0),
         "divergencia": "5 unidades de Loratadina com embalagem danificada"},
    ])

    # 13. Vendas (itens embutidos; valor_total = soma dos itens) ------------------
    vendas = [
        {"_id": 1, "id_filial": 1, "id_vendedor": 1, "id_cliente": 1,
         "cupom_fiscal": 100001, "data_hora": dt.datetime(2025, 1, 20, 9, 15),
         "forma_pagamento": "Pix",
         "itens": [
             item_venda(1, 1, 1, 1, 89.90, 0.00),
             item_venda(2, 2, 1, 1, 54.90, 0.10),
         ]},
        {"_id": 2, "id_filial": 1, "id_vendedor": 2, "id_cliente": 2,
         "cupom_fiscal": 100002, "data_hora": dt.datetime(2025, 1, 22, 10, 30),
         "forma_pagamento": "Cartão de Crédito",
         "itens": [
             item_venda(1, 5, None, 5, 9.90, 0.00),
             item_venda(2, 9, None, 1, 39.90, 0.05),
             item_venda(3, 14, None, 2, 6.90, 0.00),
         ]},
        {"_id": 3, "id_filial": 1, "id_vendedor": 4, "id_cliente": 3,
         "cupom_fiscal": 100003, "data_hora": dt.datetime(2025, 1, 25, 14, 0),
         "forma_pagamento": "Cartão de Débito",
         "itens": [
             item_venda(1, 13, None, 2, 5.90, 0.00),
             item_venda(2, 15, None, 4, 4.90, 0.00),
             item_venda(3, 16, None, 2, 7.90, 0.00),
         ]},
        {"_id": 4, "id_filial": 2, "id_vendedor": 5, "id_cliente": 4,
         "cupom_fiscal": 100004, "data_hora": dt.datetime(2025, 2, 1, 9, 0),
         "forma_pagamento": "Pix",
         "itens": [
             item_venda(1, 6, None, 2, 12.90, 0.00),
         ]},
        {"_id": 5, "id_filial": 2, "id_vendedor": 3, "id_cliente": 5,
         "cupom_fiscal": 100005, "data_hora": dt.datetime(2025, 2, 5, 11, 0),
         "forma_pagamento": "Cartão de Crédito",
         "itens": [
             item_venda(1, 10, None, 2, 29.90, 0.00),
             item_venda(2, 11, None, 1, 24.90, 0.00),
         ]},
        {"_id": 6, "id_filial": 2, "id_vendedor": 5, "id_cliente": 6,
         "cupom_fiscal": 100006, "data_hora": dt.datetime(2025, 2, 10, 15, 30),
         "forma_pagamento": "Pix",
         "itens": [
             item_venda(1, 3, 2, 1, 43.90, 0.00),
         ]},
        {"_id": 7, "id_filial": 3, "id_vendedor": 7, "id_cliente": 7,
         "cupom_fiscal": 100007, "data_hora": dt.datetime(2025, 2, 15, 10, 0),
         "forma_pagamento": "Cartão de Débito",
         "itens": [
             item_venda(1, 17, None, 4, 2.50, 0.00),
             item_venda(2, 18, None, 3, 3.90, 0.00),
         ]},
        {"_id": 8, "id_filial": 3, "id_vendedor": 9, "id_cliente": 8,
         "cupom_fiscal": 100008, "data_hora": dt.datetime(2025, 3, 1, 9, 30),
         "forma_pagamento": "Pix",
         "itens": [
             item_venda(1, 1, 3, 1, 89.90, 0.00),
         ]},
    ]
    for venda in vendas:
        venda["valor_total"] = round(sum(i["valor_total"] for i in venda["itens"]), 2)
    db.vendas.insert_many(vendas)

    # 14. Devoluções (itens embutidos) --------------------------------------------
    db.devolucoes.insert_many([
        {"_id": 1, "id_venda": 2, "data_devolucao": dt.datetime(2025, 1, 25, 14, 30),
         "motivo": "Produto com embalagem danificada", "tipo": "REEMBOLSO",
         "itens": [
             {"id_item_devolucao": 1, "id_produto": 9, "quantidade": 1},
             {"id_item_devolucao": 2, "id_produto": 14, "quantidade": 1},
         ]},
        {"_id": 2, "id_venda": 3, "data_devolucao": dt.datetime(2025, 1, 28, 10, 0),
         "motivo": "Cliente comprou item errado", "tipo": "TROCA",
         "itens": [
             {"id_item_devolucao": 1, "id_produto": 15, "quantidade": 2},
         ]},
        {"_id": 3, "id_venda": 5, "data_devolucao": dt.datetime(2025, 2, 8, 16, 0),
         "motivo": "Produto vencido identificado na entrega", "tipo": "REEMBOLSO",
         "itens": [
             {"id_item_devolucao": 1, "id_produto": 10, "quantidade": 1},
             {"id_item_devolucao": 2, "id_produto": 11, "quantidade": 1},
         ]},
        {"_id": 4, "id_venda": 7, "data_devolucao": dt.datetime(2025, 2, 18, 11, 30),
         "motivo": "Cliente desistiu da compra", "tipo": "REEMBOLSO",
         "itens": [
             {"id_item_devolucao": 1, "id_produto": 17, "quantidade": 2},
         ]},
    ])

    # 15. Contadores (próximo _id = seq + 1 para cada coleção) ---------------------
    db.contadores.insert_many([
        {"_id": "medicos", "seq": 10},
        {"_id": "filiais", "seq": 3},
        {"_id": "vendedores", "seq": 10},
        {"_id": "clientes", "seq": 15},
        {"_id": "fornecedores", "seq": 10},
        {"_id": "produtos", "seq": 20},
        {"_id": "lotes", "seq": 13},
        {"_id": "medicamentos", "seq": 8},
        {"_id": "prescricoes", "seq": 5},
        {"_id": "estoques", "seq": 15},
        {"_id": "reposicoes", "seq": 5},
        {"_id": "recebidos", "seq": 3},
        {"_id": "vendas", "seq": 8},
        {"_id": "devolucoes", "seq": 4},
    ])

    print("Banco populado com sucesso:")
    for colecao in sorted(c for c in COLECOES if c != "contadores"):
        print(f"  {colecao}: {db[colecao].count_documents({})} documentos")


if __name__ == "__main__":
    main()
