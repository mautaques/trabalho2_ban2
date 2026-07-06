/*
Trabalho 1 Parte 3, Guilherme Lelinski e Mauricio Taques
Criação das funções e gatilhos do sistema

Revisão (Trabalho 2 — migração para MongoDB):
- O antigo Gatilho 4 (trg_alerta_estoque_minimo) foi REMOVIDO por ser
  redundante e inócuo: a aplicação já calcula e exibe a situação crítica do
  estoque (quantidade <= estoque_minimo) nas consultas da tela de Estoque, e
  o RAISE NOTICE não é visível para o usuário da interface gráfica. Além
  disso, o gatilho usava a comparação "<" enquanto o restante do sistema usa
  "<=", gerando resultados inconsistentes. Os comandos de remoção estão no
  fim deste arquivo.
- Corrigidas as assinaturas dos DROP FUNCTION, que não batiam com os
  parâmetros reais das funções.
- Como o MongoDB não possui gatilhos, a lógica das funções e dos gatilhos
  restantes foi reimplementada na camada de serviços da aplicação (services/).
  Este arquivo permanece como referência do modelo relacional do Trabalho 1.
*/


/* Função 1 
Inserir um pedido de reposição no sistema, atualizando as tabelas: 
reposicao_estoque e item_reposicao.
A FUNÇÃO SÓ PODE SER USADA COM PRODUTOS JÁ CADASTRADOS.
*/
DROP FUNCTION IF EXISTS insere_pedido_reposicao(INTEGER, INTEGER, JSONB, TIMESTAMP);
CREATE OR REPLACE FUNCTION insere_pedido_reposicao(
    p_id_fornecedor     INTEGER,
    p_id_filial_destino INTEGER,
    p_itens_reposicao   JSONB,
    p_data_pedido       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
RETURNS TEXT AS $$
DECLARE
    v_id_reposicao    INTEGER;
    v_numero_pedido   INTEGER;
    v_numero_lote     INTEGER;
    v_item            JSONB;
    v_id_produto      INTEGER;
    v_id_lote         INTEGER;
    v_quantidade      INTEGER;
    v_valor_unitario  NUMERIC(10,2);
BEGIN
    -- numero_pedido é gerado automaticamente (próximo número da sequência)
    SELECT COALESCE(MAX(numero_pedido), 0) + 1 INTO v_numero_pedido
    FROM reposicao_estoque;

    INSERT INTO reposicao_estoque (id_fornecedor, id_filial_destino, numero_pedido, data_pedido)
    VALUES (p_id_fornecedor, p_id_filial_destino, v_numero_pedido, p_data_pedido)
    RETURNING id_reposicao INTO v_id_reposicao;

    FOR v_item IN SELECT * FROM jsonb_array_elements(p_itens_reposicao)
    LOOP
        v_id_produto     := (v_item->>'id_produto')::INTEGER;
        v_quantidade     := (v_item->>'quantidade')::INTEGER;
        v_valor_unitario := (v_item->>'valor_unitario')::NUMERIC;

        -- O lote é resolvido automaticamente a partir do produto
        -- (lote daquele produto com a validade mais recente).
        SELECT id_lote INTO v_id_lote
        FROM lote
        WHERE id_produto = v_id_produto
        ORDER BY data_validade DESC
        LIMIT 1;

        -- Se o produto ainda não tem lote, cria um automaticamente, com
        -- numero_lote incremental (MAX(numero_lote) + 1).
        IF v_id_lote IS NULL THEN
            SELECT COALESCE(MAX(numero_lote), 0) + 1 INTO v_numero_lote FROM lote;
            INSERT INTO lote (id_produto, id_fornecedor, numero_lote, data_fabricacao, data_validade, quantidade)
            VALUES (
                v_id_produto,
                p_id_fornecedor,
                v_numero_lote,
                p_data_pedido::DATE,
                (p_data_pedido + INTERVAL '2 years')::DATE,
                0
            )
            RETURNING id_lote INTO v_id_lote;
        END IF;

        -- Apenas insere. O GATILHO trg_atualiza_total_reposicao soma o valor total
        INSERT INTO item_reposicao (id_reposicao, id_produto, id_lote, quantidade, valor_unitario)
        VALUES (v_id_reposicao, v_id_produto, v_id_lote, v_quantidade, v_valor_unitario);
    END LOOP;

    RETURN 'Pedido ' || v_numero_pedido || ' inserido com sucesso. Totais processados automaticamente.';
END;
$$ LANGUAGE plpgsql;


/* Função 2
Inserir um pedido de venda no sistema, atualizando as tabelas: venda, 
item_venda e estoque (via gatilho).
*/
DROP FUNCTION IF EXISTS insere_pedido_venda(INTEGER, INTEGER, INTEGER, VARCHAR, JSONB, TIMESTAMP);
CREATE OR REPLACE FUNCTION insere_pedido_venda(
    p_id_filial    INTEGER,
    p_vendedor     INTEGER,
    p_cliente      INTEGER,
    p_pagamento    VARCHAR,
    p_itens_venda  JSONB,
    p_data_cupom   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
RETURNS TEXT AS $$
DECLARE
    v_id_venda       INTEGER;
    v_cupom_fiscal   INTEGER;
    v_item           JSONB;
    v_id_produto     INTEGER;
    v_id_prescricao  INTEGER;
    v_quantidade     INTEGER;
    v_preco_unitario NUMERIC(10,2);
    v_desconto       NUMERIC(10,2);
BEGIN
    -- Cupom fiscal gerado aleatoriamente (6 dígitos) e único.
    LOOP
        v_cupom_fiscal := floor(random() * 900000 + 100000)::INTEGER;
        EXIT WHEN NOT EXISTS (SELECT 1 FROM venda WHERE cupom_fiscal = v_cupom_fiscal);
    END LOOP;

    INSERT INTO venda (id_filial, id_vendedor, id_cliente, cupom_fiscal, data_hora, forma_pagamento)
    VALUES (p_id_filial, p_vendedor, p_cliente, v_cupom_fiscal, p_data_cupom, p_pagamento)
    RETURNING id_venda INTO v_id_venda;

    FOR v_item IN SELECT * FROM jsonb_array_elements(p_itens_venda)
    LOOP
        v_id_produto     := (v_item->>'id_produto')::INTEGER;
        v_quantidade     := (v_item->>'quantidade')::INTEGER; 
        v_preco_unitario := (v_item->>'preco_unitario')::NUMERIC;
        v_desconto       := COALESCE((v_item->>'desconto')::NUMERIC, 0);
        v_id_prescricao  := NULLIF((v_item->>'id_prescricao'), '')::INTEGER;

        -- Os gatilhos trg_baixa_estoque_venda e trg_atualiza_total_venda fazem o resto
        INSERT INTO item_venda (id_venda, id_produto, id_prescricao, quantidade, preco_unitario, desconto) 
        VALUES (v_id_venda, v_id_produto, v_id_prescricao, v_quantidade, v_preco_unitario, v_desconto);
    END LOOP;

    RETURN 'Venda inserida com sucesso. Cupom fiscal gerado: ' || v_cupom_fiscal
           || '. Estoque baixado e totais calculados.';
END;
$$ LANGUAGE plpgsql;


/* Função 3
Recebe um pedido de reposição: entra TODOS os itens no estoque (cada item com
sua própria quantidade), atualizando ou criando a linha de estoque por produto.
Tabelas afetadas: recebido, estoque e reposicao_estoque.
*/
DROP FUNCTION IF EXISTS recebe_reposicao(INTEGER, TEXT);
CREATE OR REPLACE FUNCTION recebe_reposicao(
    p_id_reposicao INTEGER,
    p_divergencia  TEXT DEFAULT NULL
)
RETURNS TEXT AS $$
DECLARE
    v_id_filial    INTEGER;
    v_status_atual VARCHAR(20);
    v_item         RECORD;
    v_total        INTEGER := 0;
    v_id_recebido  INTEGER;
BEGIN
    -- Verifica o status atual: só recebe pedido APROVADO ou ENVIADO
    SELECT status, id_filial_destino INTO v_status_atual, v_id_filial
    FROM reposicao_estoque
    WHERE id_reposicao = p_id_reposicao;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Reposição % não encontrada.', p_id_reposicao;
    END IF;

    IF v_status_atual NOT IN ('APROVADO', 'ENVIADO') THEN
        RAISE EXCEPTION
            'Só é possível receber um pedido APROVADO ou ENVIADO (status atual: %).',
            v_status_atual;
    END IF;

    -- Atualiza o status para RECEBIDO
    UPDATE reposicao_estoque
    SET status = 'RECEBIDO'
    WHERE id_reposicao = p_id_reposicao;

    -- Entra CADA item no estoque, usando a quantidade do próprio item.
    FOR v_item IN
        SELECT id_produto, id_lote, quantidade
        FROM item_reposicao
        WHERE id_reposicao = p_id_reposicao
    LOOP
        UPDATE estoque
        SET quantidade = quantidade + v_item.quantidade
        WHERE id_produto = v_item.id_produto AND id_filial = v_id_filial;

        -- Produto sem linha de estoque na filial (produto novo): cria.
        IF NOT FOUND THEN
            INSERT INTO estoque (id_lote, id_produto, id_filial, quantidade)
            VALUES (v_item.id_lote, v_item.id_produto, v_id_filial, v_item.quantidade);
        END IF;

        v_total := v_total + v_item.quantidade;
    END LOOP;

    -- Registra o recebimento (quantidade total = soma dos itens)
    INSERT INTO recebido (id_reposicao, quantidade, divergência)
    VALUES (p_id_reposicao, v_total, p_divergencia)
    RETURNING id_recebido INTO v_id_recebido;

    -- Liga os itens da reposição a este recebimento.
    UPDATE item_reposicao
    SET id_recebido = v_id_recebido
    WHERE id_reposicao = p_id_reposicao;

    RETURN 'Reposição recebida: ' || v_total || ' unidades adicionadas ao estoque.';
END;
$$ LANGUAGE plpgsql;


/* Função 3.1
Altera o status de um pedido de reposição respeitando as transições válidas:
  PENDENTE -> APROVADO -> ENVIADO -> (RECEBIDO via recebe_reposicao)
  PENDENTE/APROVADO/ENVIADO -> CANCELADO
RECEBIDO e CANCELADO são estados finais.
*/
CREATE OR REPLACE FUNCTION altera_status_reposicao(
    p_id_reposicao INTEGER,
    p_novo_status  VARCHAR
)
RETURNS TEXT AS $$
DECLARE
    v_status_atual VARCHAR(20);
BEGIN
    SELECT status INTO v_status_atual
    FROM reposicao_estoque
    WHERE id_reposicao = p_id_reposicao;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Reposição % não encontrada.', p_id_reposicao;
    END IF;

    IF p_novo_status = 'APROVADO' THEN
        IF v_status_atual <> 'PENDENTE' THEN
            RAISE EXCEPTION 'Só é possível aprovar um pedido PENDENTE (status atual: %).', v_status_atual;
        END IF;
    ELSIF p_novo_status = 'ENVIADO' THEN
        IF v_status_atual <> 'APROVADO' THEN
            RAISE EXCEPTION 'Só é possível enviar um pedido APROVADO (status atual: %).', v_status_atual;
        END IF;
    ELSIF p_novo_status = 'CANCELADO' THEN
        IF v_status_atual IN ('RECEBIDO', 'CANCELADO') THEN
            RAISE EXCEPTION 'Não é possível cancelar um pedido com status %.', v_status_atual;
        END IF;
    ELSE
        RAISE EXCEPTION 'Status inválido para esta operação: %. Use APROVADO, ENVIADO ou CANCELADO.', p_novo_status;
    END IF;

    UPDATE reposicao_estoque
    SET status = p_novo_status
    WHERE id_reposicao = p_id_reposicao;

    RETURN FORMAT('Pedido %s: status alterado de %s para %s.',
                  p_id_reposicao, v_status_atual, p_novo_status);
END;
$$ LANGUAGE plpgsql;


/* Função 4
Registra a devolução de vendas de produtos nas tabelas devolucao e item_devolucao,
e atualiza a tabela estoque.
*/
CREATE OR REPLACE FUNCTION devolver_produtos(
    p_id_venda  INTEGER,
    p_itens     JSONB,    
    p_motivo    TEXT,
    p_tipo      VARCHAR   
)
RETURNS TEXT AS $$
DECLARE
    v_id_filial    INTEGER;
    v_id_devolucao INTEGER;
    v_item         JSONB;
    v_id_produto   INTEGER;
    v_quantidade   INTEGER;
    v_qtd_vendida  INTEGER;
    v_id_lote      INTEGER;
    v_total_itens  INTEGER := 0;
BEGIN
    SELECT id_filial INTO v_id_filial
    FROM venda
    WHERE id_venda = p_id_venda;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Venda % não encontrada.', p_id_venda;
    END IF;

    IF p_tipo NOT IN ('REEMBOLSO', 'TROCA') THEN
        RAISE EXCEPTION 'Tipo de devolução inválido: %. Use REEMBOLSO ou TROCA.', p_tipo;
    END IF;

    INSERT INTO devolucao (id_venda, motivo, tipo)
    VALUES (p_id_venda, p_motivo, p_tipo)
    RETURNING id_devolucao INTO v_id_devolucao;

    FOR v_item IN SELECT * FROM jsonb_array_elements(p_itens)
    LOOP
        v_id_produto := (v_item->>'id_produto')::INTEGER;
        v_quantidade := (v_item->>'quantidade')::INTEGER;

        SELECT quantidade INTO v_qtd_vendida
        FROM item_venda
        WHERE id_venda   = p_id_venda
          AND id_produto = v_id_produto;

        IF NOT FOUND THEN
            RAISE EXCEPTION
                'Produto % não consta na venda %. Não pode ser devolvido.',
                v_id_produto, p_id_venda;
        END IF;

        IF v_quantidade > v_qtd_vendida THEN
            RAISE EXCEPTION
                'Quantidade devolvida (%) maior que a vendida (%) para o produto %.',
                v_quantidade, v_qtd_vendida, v_id_produto;
        END IF;

        INSERT INTO item_devolucao (id_devolucao, id_produto, quantidade)
        VALUES (v_id_devolucao, v_id_produto, v_quantidade);

        SELECT id_lote INTO v_id_lote
        FROM estoque
        WHERE id_produto = v_id_produto
          AND id_filial  = v_id_filial
        LIMIT 1;

        IF FOUND THEN
            UPDATE estoque
            SET quantidade = quantidade + v_quantidade
            WHERE id_produto = v_id_produto
              AND id_filial  = v_id_filial
              AND id_lote    = v_id_lote;
        END IF;

        v_total_itens := v_total_itens + v_quantidade;
    END LOOP;

    RETURN FORMAT(
        'Devolução %s registrada. Venda: %s. Tipo: %s. Total de itens devolvidos: %s.',
        v_id_devolucao, p_id_venda, p_tipo, v_total_itens
    );
END;
$$ LANGUAGE plpgsql;


/* Gatilho 1
Atualiza o total de uma venda automaticamente sempre que um item é inserido,
atualizado ou removido.
*/
CREATE OR REPLACE FUNCTION func_atualiza_total_venda()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        UPDATE venda 
        SET valor_total = (
            SELECT COALESCE(SUM(valor_total), 0) 
            FROM item_venda 
            WHERE id_venda = OLD.id_venda
        ) 
        WHERE id_venda = OLD.id_venda;
        RETURN OLD;
    ELSE
        UPDATE venda 
        SET valor_total = (
            SELECT COALESCE(SUM(valor_total), 0) 
            FROM item_venda 
            WHERE id_venda = NEW.id_venda
        ) 
        WHERE id_venda = NEW.id_venda;
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_atualiza_total_venda ON item_venda;
CREATE TRIGGER trg_atualiza_total_venda
AFTER INSERT OR UPDATE OR DELETE ON item_venda
FOR EACH ROW EXECUTE FUNCTION func_atualiza_total_venda();


/* Gatilho 2
Atualiza o total de uma reposição (compra) automaticamente sempre que 
um item de reposição é inserido, atualizado ou removido.
*/
CREATE OR REPLACE FUNCTION func_atualiza_total_reposicao()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        UPDATE reposicao_estoque 
        SET valor_total = (
            SELECT COALESCE(SUM(valor_total), 0) 
            FROM item_reposicao 
            WHERE id_reposicao = OLD.id_reposicao
        ) 
        WHERE id_reposicao = OLD.id_reposicao;
        RETURN OLD;
    ELSE
        UPDATE reposicao_estoque 
        SET valor_total = (
            SELECT COALESCE(SUM(valor_total), 0) 
            FROM item_reposicao 
            WHERE id_reposicao = NEW.id_reposicao
        ) 
        WHERE id_reposicao = NEW.id_reposicao;
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_atualiza_total_reposicao ON item_reposicao;
CREATE TRIGGER trg_atualiza_total_reposicao
AFTER INSERT OR UPDATE OR DELETE ON item_reposicao
FOR EACH ROW EXECUTE FUNCTION func_atualiza_total_reposicao();


/* Gatilho 3
Altera a quantidade no estoque sempre que uma venda é realizada,
usando o lote com vencimento mais próximo (FIFO por validade).
*/
CREATE OR REPLACE FUNCTION func_baixa_estoque_venda()
RETURNS TRIGGER AS $$
DECLARE
    v_id_filial  INTEGER;
    v_id_estoque INTEGER;
BEGIN
    SELECT id_filial INTO v_id_filial 
    FROM venda 
    WHERE id_venda = NEW.id_venda;

    SELECT e.id_estoque INTO v_id_estoque
    FROM estoque e
    JOIN lote l ON e.id_lote = l.id_lote
    WHERE e.id_produto = NEW.id_produto 
      AND e.id_filial  = v_id_filial
      AND e.quantidade >= NEW.quantidade
    ORDER BY l.data_validade ASC
    LIMIT 1;

    IF v_id_estoque IS NULL THEN
        RAISE EXCEPTION 
            'Estoque insuficiente ou produto não encontrado para o ID % na filial %', 
            NEW.id_produto, v_id_filial;
    END IF;

    UPDATE estoque
    SET quantidade = quantidade - NEW.quantidade
    WHERE id_estoque = v_id_estoque;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_baixa_estoque_venda ON item_venda;
CREATE TRIGGER trg_baixa_estoque_venda
AFTER INSERT ON item_venda
FOR EACH ROW EXECUTE FUNCTION func_baixa_estoque_venda();


/* Gatilho 4 (antigo Gatilho 5)
Garante que o vendedor de uma venda pertence à filial da própria venda
(cada vendedor trabalha em uma única filial — vendedor.id_filial).
*/
CREATE OR REPLACE FUNCTION func_valida_vendedor_filial()
RETURNS TRIGGER AS $$
DECLARE
    v_id_filial_vendedor INTEGER;
BEGIN
    SELECT id_filial INTO v_id_filial_vendedor
    FROM vendedor
    WHERE id_vendedor = NEW.id_vendedor;

    IF v_id_filial_vendedor IS DISTINCT FROM NEW.id_filial THEN
        RAISE EXCEPTION
            'O vendedor % pertence à filial % e não pode vender na filial %.',
            NEW.id_vendedor, v_id_filial_vendedor, NEW.id_filial;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_valida_vendedor_filial ON venda;
CREATE TRIGGER trg_valida_vendedor_filial
BEFORE INSERT OR UPDATE ON venda
FOR EACH ROW EXECUTE FUNCTION func_valida_vendedor_filial();


/* Gatilho REMOVIDO — trg_alerta_estoque_minimo (antigo Gatilho 4)
Motivo: redundante e inócuo. A situação crítica do estoque já é calculada e
exibida pela aplicação na consulta da tela de Estoque (EstoqueService, com
quantidade <= estoque_minimo), e o RAISE NOTICE emitido pelo gatilho não é
visível na interface gráfica. O gatilho ainda usava "<" em vez de "<=",
divergindo do critério usado no restante do sistema. Os comandos abaixo
removem o gatilho de bancos onde ele já havia sido criado.
*/
DROP TRIGGER IF EXISTS trg_alerta_estoque_minimo ON estoque;
DROP FUNCTION IF EXISTS func_alerta_estoque_minimo();