"""Pacote voz — pipeline de fala da A.R.I.A., 100% local.

captura.py grava o microfone (push-to-talk). reconhecimento.py
transcreve o áudio com Whisper local (faster-whisper). fala.py lê a
resposta em voz alta com o motor de TTS do sistema operacional
(pyttsx3). Nenhum dos três depende de API externa."""
