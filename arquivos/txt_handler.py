"""
txt_handler.py — Leitura de arquivos de texto puro.

Cobre os formatos que a A.R.I.A. já suporta: .txt, .md, .py, .csv,
.json, .log, .yaml/.yml — qualquer coisa que seja texto puro em UTF-8.
"""


def ler(caminho: str) -> str:
    """Lê o conteúdo de um arquivo de texto.

    Lança OSError ou UnicodeDecodeError se não conseguir — quem chama
    (manager.py) decide como tratar isso.
    """
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return arquivo.read()
