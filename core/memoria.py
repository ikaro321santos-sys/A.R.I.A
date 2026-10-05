"""
memoria.py — Memória de longo prazo da A.R.I.A. (com suporte a vários chats)

Cada chat vira um arquivo JSON dentro da pasta "conversas/", guardando
um título (opcional, definido pelo usuário) e a lista de mensagens.
Arquivos antigos (formato de lista simples, sem título) continuam
funcionando — são lidos normalmente, só não têm título customizado
até o usuário renomear.
"""

import json
import os
from datetime import datetime

PASTA_CONVERSAS = os.path.join(os.path.dirname(__file__), "conversas")


def _caminho(chat_id: str) -> str:
    return os.path.join(PASTA_CONVERSAS, f"{chat_id}.json")


def novo_chat_id() -> str:
    """Gera um id novo baseado na data/hora atual."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def listar_chats() -> list:
    """Retorna os ids dos chats salvos, do mais recente para o mais antigo."""
    if not os.path.isdir(PASTA_CONVERSAS):
        return []
    arquivos = [nome[:-5] for nome in os.listdir(PASTA_CONVERSAS) if nome.endswith(".json")]
    return sorted(arquivos, reverse=True)


def _ler_arquivo(chat_id: str) -> dict:
    """Lê o arquivo de um chat, normalizando pro formato {titulo, mensagens}."""
    caminho = _caminho(chat_id)
    if not os.path.exists(caminho):
        return {"titulo": None, "mensagens": []}

    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (json.JSONDecodeError, OSError):
        return {"titulo": None, "mensagens": []}

    if isinstance(dados, list):
        # Formato antigo: só a lista de mensagens, sem título.
        return {"titulo": None, "mensagens": dados}

    return {"titulo": dados.get("titulo"), "mensagens": dados.get("mensagens", [])}


def _gravar_arquivo(chat_id: str, titulo, mensagens: list):
    os.makedirs(PASTA_CONVERSAS, exist_ok=True)
    with open(_caminho(chat_id), "w", encoding="utf-8") as arquivo:
        json.dump({"titulo": titulo, "mensagens": mensagens}, arquivo, ensure_ascii=False, indent=2)


def carregar_historico(chat_id: str) -> list:
    """Lê o histórico de um chat. Retorna lista vazia se não existir ainda."""
    return _ler_arquivo(chat_id)["mensagens"]


def salvar_mensagem(chat_id: str, remetente: str, texto: str):
    """Adiciona uma mensagem ao chat indicado e grava tudo no disco."""
    dados = _ler_arquivo(chat_id)
    dados["mensagens"].append({"remetente": remetente, "texto": texto})
    _gravar_arquivo(chat_id, dados["titulo"], dados["mensagens"])


def definir_titulo(chat_id: str, novo_titulo: str):
    """Define um título customizado para o chat (sobrepõe o automático)."""
    dados = _ler_arquivo(chat_id)
    _gravar_arquivo(chat_id, novo_titulo.strip() or None, dados["mensagens"])


def apagar_chat(chat_id: str):
    """Remove o arquivo do chat do disco, se existir."""
    caminho = _caminho(chat_id)
    if os.path.exists(caminho):
        os.remove(caminho)


def titulo_chat(chat_id: str) -> str:
    """Rótulo pro menu: título customizado, ou a primeira mensagem, ou o id."""
    dados = _ler_arquivo(chat_id)
    if dados["titulo"]:
        return dados["titulo"]

    for mensagem in dados["mensagens"]:
        if mensagem["remetente"] == "Você":
            texto = mensagem["texto"]
            return texto[:30] + ("..." if len(texto) > 30 else "")

    return chat_id
