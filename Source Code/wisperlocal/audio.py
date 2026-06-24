"""Microphone capture via sounddevice.

Records mono float32 at 16 kHz (what Whisper expects) into an in-memory
buffer, so no temporary WAV file is needed.
"""

import threading

import numpy as np

SAMPLE_RATE = 16000


class Recorder:
    def __init__(self, samplerate: int = SAMPLE_RATE, device=None):
        self.samplerate = samplerate
        self.device = device  # sounddevice index or None for default
        self._frames: list[np.ndarray] = []
        self._stream = None
        self._level = 0.0
        self._lock = threading.Lock()

    def _callback(self, indata, frames, time_info, status):  # PortAudio thread
        # Peak level for the live waveform (cheap; float assignment is atomic).
        try:
            self._level = float(np.abs(indata).max())
        except Exception:
            pass
        # Copy: PortAudio reuses the buffer after the callback returns.
        with self._lock:
            self._frames.append(indata.copy())

    def start(self) -> None:
        import sounddevice as sd  # imported lazily so import errors surface clearly

        with self._lock:
            self._frames = []
        self._level = 0.0
        self._stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=1,
            dtype="float32",
            device=self.device,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        """Stop the stream and return the captured mono float32 samples."""
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            finally:
                self._stream = None
        with self._lock:
            if not self._frames:
                return np.zeros(0, dtype=np.float32)
            audio = np.concatenate(self._frames, axis=0).reshape(-1).astype(np.float32)
            self._frames = []
        return audio

    def get_level(self) -> float:
        """Latest mic peak level in 0..1 (for the live waveform); 0 when idle."""
        return self._level if self._stream is not None else 0.0

    @property
    def is_recording(self) -> bool:
        return self._stream is not None
