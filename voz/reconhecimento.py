"""
reconhecimento.py — Speech-to-Text (fala → texto), Whisper local.

Usa faster-whisper: roda inteiramente na sua máquina, sem API externa
e sem cota. O modelo é baixado uma única vez (cache do próprio
faster-whisper) na primeira transcrição.

Trocar de modelo ou idioma é só mexer em WHISPER_MODEL / WHISPER_IDIOMA
no .env — nenhum outro arquivo do projeto depende disso.
"""

from faster_whisper import WhisperModel

from core import config

_modelo = None  # carregado sob demanda, na primeira transcrição


def _obter_modelo():
    global _modelo
    if _modelo is None:
        _modelo = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")
    return _modelo


def transcrever(caminho_wav: str) -> str:
    """Transcreve um arquivo .wav para texto. Retorna string vazia se falhar."""
    try:
        modelo = _obter_modelo()
        segmentos, _ = modelo.transcribe(caminho_wav, language=config.WHISPER_IDIOMA or None)
        return " ".join(segmento.text.strip() for segmento in segmentos).strip()
    except Exception:
        return ""
