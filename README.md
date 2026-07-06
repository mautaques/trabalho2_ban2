# trabalho2_ban2
O objetivo deste trabalho é integrar o sistema já implementado do trabalho 1, agora com o banco de dados NoSQL MongoDB.

## Como executar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Com o MongoDB rodando (padrão: `mongodb://localhost:27017`, banco `farmacia` —
   ajustável pelas variáveis de ambiente `MONGO_URL` e `MONGO_DB`), crie e
   popule o banco com os dados de exemplo:
   ```bash
   python popula_banco.py
   ```
3. Inicie a aplicação:
   ```bash
   python main.py
   ```

## Estrutura

- `database.py` — conexão com o MongoDB, contadores de ID sequencial e índices únicos.
- `models/` — wrapper `Documento` (documentos MongoDB com acesso por atributo).
- `services/` — regras de negócio e consultas (aggregation pipelines). A lógica
  que no PostgreSQL ficava em funções e gatilhos (baixa de estoque, cálculo de
  totais, validação vendedor × filial, transições de status da reposição) foi
  reimplementada aqui, pois o MongoDB não possui gatilhos.
- `ui/` — interface gráfica (PyQt6).
- `popula_banco.py` — criação/carga inicial do banco (equivalente NoSQL do `esquema_farmacia.sql`).
- `esquema_farmacia.sql` e `funcoes_gatilhos.sql` — referência do modelo
  relacional do Trabalho 1 (PostgreSQL).
