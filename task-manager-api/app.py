"""Entry point da aplicação.

Mantém o caminho de execução original (`python app.py`) documentado no README.
Toda a montagem está em src/app.py:create_app() — este arquivo só resolve a
configuração e sobe o servidor.
"""
from src.app import create_app
from src.config.settings import settings

app = create_app(settings)

if __name__ == '__main__':
    # debug e host vêm de variável de ambiente, com default seguro.
    # Antes era app.run(debug=True, host='0.0.0.0'), que expunha o console
    # interativo do Werkzeug na rede (finding 3 / AP-02).
    app.run(debug=settings.DEBUG, host=settings.HOST, port=settings.PORT)
