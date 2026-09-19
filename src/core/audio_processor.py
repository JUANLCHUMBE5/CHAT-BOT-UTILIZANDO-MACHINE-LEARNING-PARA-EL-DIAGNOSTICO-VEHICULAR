"""Procesador acústico y de audio para CarBot (FFT espectral + Transcripción de voz)."""

from __future__ import annotations

import base64
from typing import Optional, Tuple

import numpy as np
import requests

from src.config import settings


class AudioProcessor:
    """Clase encargada de procesar las señales de audio físicas (FFT y RMS) y transcripción."""

    def __init__(self, samplerate: int = 44100):
        self.samplerate = samplerate
        self.umbral_silencio = 0.01
        self.umbral_ruido_agudo = 15.0  # Porcentaje de agudos > 2000Hz

    def normalizar_audio(self, datos_audio: np.ndarray) -> np.ndarray:
        """Normaliza la amplitud del audio para evitar problemas de volumen."""
        maximo = np.max(np.abs(datos_audio))
        if maximo > 0:
            return datos_audio / maximo
        return datos_audio

    def bytes_a_vector(self, audio_bytes: bytes) -> np.ndarray:
        """Convierte bytes de audio crudo en un vector NumPy normalizado."""
        if not audio_bytes:
            return np.zeros(0, dtype=np.float32)
        try:
            arr = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
            return self.normalizar_audio(arr)
        except Exception:
            return np.zeros(0, dtype=np.float32)

    def analizar_audio(self, datos_audio_crudos: np.ndarray) -> Tuple[str, str]:
        """
        Analiza las propiedades físicas del audio.
        Retorna: (Tipo de entrada: 'Silencio'|'Ruido Mecánico'|'Voz Humana', Detalle/Diagnóstico)
        """
        if len(datos_audio_crudos) == 0:
            return "Silencio", "Señal de audio vacía."

        # Aplanar y normalizar
        datos_normalizados = self.normalizar_audio(datos_audio_crudos.flatten())

        # Calcular energía RMS (Root Mean Square)
        energia_rms = np.sqrt(np.mean(datos_normalizados**2))

        if energia_rms < self.umbral_silencio:
            return "Silencio", "No se detectaron niveles significativos de audio."

        # Aplicar Transformada Rápida de Fourier (FFT) para análisis espectral
        fft_resultado = np.abs(np.fft.rfft(datos_normalizados))
        frecuencias = np.fft.rfftfreq(len(datos_normalizados), d=1.0 / self.samplerate)

        # Encontrar frecuencia dominante
        indice_maximo = np.argmax(fft_resultado)
        frecuencia_dominante = frecuencias[indice_maximo]

        # Porcentaje de frecuencias agudas (> 2000 Hz) para aislar ruidos metálicos
        indices_agudos = np.where(frecuencias > 2000)[0]
        energia_aguda = np.sum(fft_resultado[indices_agudos])
        energia_total = np.sum(fft_resultado)
        ratio_agudo = (energia_aguda / energia_total) * 100 if energia_total > 0 else 0

        # Decidir según la firma acústica espectral
        if ratio_agudo > self.umbral_ruido_agudo:
            # Clasificación física simplificada basada en frecuencia dominante
            if 2000 <= frecuencia_dominante < 5000:
                diagnostico = "Desgaste en la faja del alternador (Chillido de faja)"
            elif frecuencia_dominante >= 5000:
                diagnostico = "Pastillas de freno cristalizadas o desgastadas (Fricción de metal)"
            else:
                diagnostico = "Cascabeleo / Golpeteo interno en los cilindros del motor"
            return "Ruido Mecánico", diagnostico
        else:
            # Audio con firma de voz humana
            return "Voz Humana", "Señal correspondiente a nota de voz hablada del mecánico o cliente."

    def transcribir_nota_de_voz(
        self,
        audio_id: str,
        audio_bytes: Optional[bytes] = None,
        mime_type: str = "audio/ogg",
        api_key: Optional[str] = None,
    ) -> str:
        """
        Transcribe una nota de voz a texto para ingresarla al clasificador ML y RAG.
        Transcribe bytes reales mediante la entrada multimodal de Gemini.
        """
        if not audio_id or not audio_bytes:
            raise ValueError("La nota de voz no contiene bytes de audio reales.")
        clave = api_key or settings.gemini_api_key
        if not clave:
            raise RuntimeError("GEMINI_API_KEY es obligatoria para transcribir audio.")
        if len(audio_bytes) > settings.audio_max_bytes:
            raise ValueError("El audio supera el tamaño máximo permitido.")

        modelo = settings.gemini_model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
        payload = {
            "contents": [{"parts": [
                {"text": "Transcribe literalmente esta nota de voz en español. Devuelve solo la transcripción, sin explicar ni diagnosticar."},
                {"inline_data": {
                    "mime_type": mime_type,
                    "data": base64.b64encode(audio_bytes).decode("ascii"),
                }},
            ]}]
        }
        response = requests.post(
            url,
            headers={"Content-Type": "application/json", "x-goog-api-key": clave},
            json=payload,
            timeout=30,
        )
        from src.core.gemini_queue import gemini_rate_limiter

        if response.status_code == 200:
            gemini_rate_limiter.registrar_estado_gemini(exitoso=True, codigo_http=200)
        else:
            espera = (
                gemini_rate_limiter.extraer_retry_after_segundos(response)
                if response.status_code == 429
                else 0
            )
            gemini_rate_limiter.registrar_estado_gemini(
                exitoso=False,
                codigo_http=response.status_code,
                error=f"Gemini audio HTTP {response.status_code}",
                retry_after_segundos=espera,
            )
        response.raise_for_status()
        data = response.json()
        try:
            texto = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Gemini no devolvió una transcripción utilizable.") from exc
        if not texto:
            raise RuntimeError("La transcripción de audio está vacía.")
        return texto
