"""Wrapper genérico para documentos MongoDB.

Substitui os modelos ORM do SQLAlchemy: o PyMongo devolve dicionários, e a
classe ``Documento`` converte cada documento (inclusive subdocumentos e
listas) em um objeto com acesso por atributo — o formato que a camada de
interface espera (ex.: ``venda.filial.nome_fantasia``).
"""


def _converte(valor):
    if isinstance(valor, dict):
        return Documento(valor)
    if isinstance(valor, list):
        return [_converte(v) for v in valor]
    return valor


class Documento:
    """Objeto com acesso por atributo construído a partir de um dict."""

    def __init__(self, dados: dict):
        for chave, valor in dados.items():
            setattr(self, chave, _converte(valor))

    def __repr__(self) -> str:
        campos = ", ".join(f"{k}={v!r}" for k, v in vars(self).items())
        return f"<Documento({campos})>"
