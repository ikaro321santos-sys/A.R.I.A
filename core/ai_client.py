"""
ai_client.py — Integração de IA da A.R.I.A.

Único lugar do projeto que sabe como conversar com um modelo de IA.
Usa o Ollama local — sem API externa, sem cota, sem custo.

A interface (ui.py) só chama send_message(texto, callback) e recebe a
resposta em pedaços (streaming), o que faz a conversa parecer mais
rápida mesmo quando o tempo total de geração é o mesmo.
"""

import json

import requests

from . import config
from . import persona


def send_message(texto: str, ao_receber_pedaco=None) -> str:
    """Envia uma mensagem para o Ollama e retorna a resposta completa.

    Se ao_receber_pedaco for passado, é chamado a cada fragmento de
    texto que chega, permitindo mostrar a resposta sendo "digitada"
    em tempo real na interface.
    """
    resposta = _tentar_ollama(texto, ao_receber_pedaco)
    if resposta is not None:
        return resposta

    return (
        "Não consegui falar com o Ollama. Verifique se ele está instalado "
        "e rodando (comando: ollama serve)."
    )


def _tentar_ollama(texto: str, ao_receber_pedaco=None):
    """Tenta gerar uma resposta via streaming no Ollama. Retorna None se falhar."""
    try:
        resposta = requests.post(
            f"{config.OLLAMA_URL}/api/generate",
            json={
                "model": config.OLLAMA_MODEL,
                "prompt": texto,
                "system": persona.SYSTEM_PROMPT,
                "stream": True,
            },
            # (tempo de conexão, tempo de leitura) — conexão falha rápido se o
            # Ollama não estiver rodando; leitura tem mais folga pra IA gerar.
            timeout=(config.OLLAMA_TIMEOUT_SECONDS, 60),
            stream=True,
        )
        resposta.raise_for_status()

        texto_completo = ""
        for linha in resposta.iter_lines():
            if not linha:
                continue
            pedaco = json.loads(linha)
            fragmento = pedaco.get("response", "")
            if fragmento:
                texto_completo += fragmento
                if ao_receber_pedaco:
                    ao_receber_pedaco(fragmento)
            if pedaco.get("done"):
                break

        return texto_completo.strip() or None
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError, ValueError):
        return None
