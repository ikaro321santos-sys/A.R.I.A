"""
fala.py — Text-to-Speech (texto → fala), motor do sistema operacional.

pyttsx3 usa a voz já instalada no seu SO (espeak no Linux, SAPI5 no
Windows, NSSpeechSynthesizer no macOS) — sem API externa, sem
download de modelo, sem cota.
"""

import pyttsx3

from core import config

_motor = None  # inicializado sob demanda


def _obter_motor():
    global _motor
    if _motor is None:
        _motor = pyttsx3.init()
        _motor.setProperty("rate", config.TTS_VELOCIDADE)
    return _motor


def falar(texto: str):
    """Fala o texto em voz alta. Bloqueia até terminar — quem chamar
    deve rodar isso numa thread separada se não quiser travar a UI."""
    texto_limpo = texto.replace("**", "").strip()
    if not texto_limpo:
        return
    motor = _obter_motor()
    motor.say(texto_limpo)
    motor.runAndWait()
