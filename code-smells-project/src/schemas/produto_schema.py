"""Schema único de produto — o POST e o PUT usam exatamente as mesmas regras."""
from src.config.constants import (
    CATEGORIAS_VALIDAS,
    CATEGORIA_PADRAO,
    MAX_NOME_PRODUTO,
    MIN_NOME_PRODUTO,
)
from src.schemas.validators import (
    Campo,
    Schema,
    comprimento_maximo,
    comprimento_minimo,
    minimo,
    numero,
    texto,
    um_de,
)

CAMPOS_PRODUTO = [
    Campo("nome", obrigatorio=True, mensagem_obrigatorio="Nome é obrigatório",
          tipo=texto("Nome"),
          regras=(comprimento_minimo(MIN_NOME_PRODUTO, "Nome muito curto"),
                  comprimento_maximo(MAX_NOME_PRODUTO, "Nome muito longo"))),
    Campo("preco", obrigatorio=True, mensagem_obrigatorio="Preço é obrigatório",
          tipo=numero("Preço"),
          regras=(minimo(0, "Preço não pode ser negativo"),)),
    Campo("estoque", obrigatorio=True, mensagem_obrigatorio="Estoque é obrigatório",
          tipo=numero("Estoque"),
          regras=(minimo(0, "Estoque não pode ser negativo"),)),
    Campo("descricao", padrao="", tipo=texto("Descrição")),
    Campo("categoria", padrao=CATEGORIA_PADRAO, tipo=texto("Categoria"),
          regras=(um_de(CATEGORIAS_VALIDAS,
                        "Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS)),)),
]

produto_schema = Schema(CAMPOS_PRODUTO)
