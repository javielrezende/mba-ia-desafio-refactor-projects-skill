"""Entry point. Mantido na raiz para preservar `python app.py` do README."""
from src.app import create_app
from src.config.settings import carregar_settings

settings = carregar_settings()
app = create_app(settings=settings)

if __name__ == "__main__":
    app.extensions["logger"].info(
        "servidor iniciado em http://%s:%s", settings.HOST, settings.PORT
    )
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
