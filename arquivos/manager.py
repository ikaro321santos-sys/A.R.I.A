"""
manager.py — Ponto único de entrada para ler anexos.

Identifica o tipo do arquivo pela extensão e encaminha pro handler
certo. Novos formatos entram aqui como uma nova entrada em
EXTENSOES_SUPORTADAS + um novo módulo "*_handler.py" — sem precisar
mexer na interface nem no restante do projeto.

Por enquanto só existe suporte a texto puro (txt_handler). PDF, DOCX,
planilhas e imagens ainda não têm handler — é o próximo passo natural
depois desta reorganização.
"""

import os

from . import txt_handler

EXTENSOES_TEXTO = {".txt", ".md", ".py", ".csv", ".json", ".log", ".yaml", ".yml"}


def ler_arquivo(caminho: str) -> str:
    """Lê um arquivo e retorna o conteúdo como texto.

    Lança ValueError se o formato ainda não tiver handler implementado,
    ou OSError/UnicodeDecodeError se o arquivo não puder ser lido.
    """
    extensao = os.path.splitext(caminho)[1].lower()

    if extensao in EXTENSOES_TEXTO or extensao == "":
        return txt_handler.ler(caminho)

    raise ValueError(f"formato '{extensao}' ainda não tem handler implementado")
