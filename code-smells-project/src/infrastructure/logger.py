"""Logger estruturado — substitui os 19 print() do código legado."""
import logging


def configurar_logger(nivel="INFO"):
    logging.basicConfig(
        level=getattr(logging, nivel, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return logging.getLogger("loja")
