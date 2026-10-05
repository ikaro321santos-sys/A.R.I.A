"""
captura.py — Gravação de áudio do microfone (push-to-talk).

Grava enquanto o botão do microfone estiver pressionado; ao soltar,
salva um .wav temporário que reconhecimento.py depois transcreve.
"""

import queue
import tempfile
import wave

import numpy as np
import sounddevice as sd

TAXA_AMOSTRAGEM = 16000  # Hz — o que o Whisper espera
CANAIS = 1


class Gravador:
    def __init__(self):
        self._fila = queue.Queue()
        self._stream = None

    def iniciar(self):
        self._fila = queue.Queue()

        def callback(indata, frames, tempo, status):
            self._fila.put(indata.copy())

        self._stream = sd.InputStream(
            samplerate=TAXA_AMOSTRAGEM, channels=CANAIS, dtype="int16", callback=callback
        )
        self._stream.start()

    def parar(self):
        """Para a gravação e salva um .wav temporário.

        Retorna o caminho do arquivo, ou None se nada foi gravado
        (ex.: clique rápido demais no botão).
        """
        if self._stream is None:
            return None

        self._stream.stop()
        self._stream.close()
        self._stream = None

        blocos = []
        while not self._fila.empty():
            blocos.append(self._fila.get())

        if not blocos:
            return None

        audio = np.concatenate(blocos, axis=0)

        arquivo_temp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(arquivo_temp.name, "wb") as wav:
            wav.setnchannels(CANAIS)
            wav.setsampwidth(2)  # int16 = 2 bytes por amostra
            wav.setframerate(TAXA_AMOSTRAGEM)
            wav.writeframes(audio.tobytes())

        return arquivo_temp.name
