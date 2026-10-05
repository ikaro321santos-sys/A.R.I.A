"""
config.py — Configuração central da A.R.I.A.

Único lugar do projeto que lida com variáveis de ambiente.
Se no futuro a IA mudar, só este arquivo precisa ser tocado.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Ollama (IA local — único provedor usado agora, sem API externa)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Tempo (segundos) para considerar que o Ollama não está disponível.
# Vale só para a conexão inicial — depois que a resposta começa a
# chegar (streaming), o tempo de leitura é maior (veja ai_client.py).
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "3"))

# --- Voz (Speech-to-Text / Text-to-Speech) — tudo local, sem API externa ---
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
WHISPER_IDIOMA = os.getenv("WHISPER_IDIOMA", "pt")  # vazio = detectar idioma automaticamente
TTS_VELOCIDADE = int(os.getenv("TTS_VELOCIDADE", "170"))  # palavras por minuto, aprox.

# Voz — Speech-to-Text (Whisper local) e Text-to-Speech (motor do SO).
# Tudo local, sem API externa e sem cota.
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
WHISPER_IDIOMA = os.getenv("WHISPER_IDIOMA", "pt")  # vazio = detectar automaticamente
TTS_VELOCIDADE = int(os.getenv("TTS_VELOCIDADE", "170"))  # palavras por minuto, aprox.
