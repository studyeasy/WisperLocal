"""End-to-end accuracy check: transcribe a synthesized-speech WAV through the
real default model. Run with the venv python from the project root."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faster_whisper.audio import decode_audio

from wisperlocal.transcriber import Transcriber

wav = sys.argv[1] if len(sys.argv) > 1 else "test_tts.wav"
audio = decode_audio(wav, sampling_rate=16000)
print(f"loaded {len(audio)} samples ({len(audio)/16000:.1f}s)")

tr = Transcriber(model="small.en", device="cpu", compute_type="int8")
text = tr.transcribe(audio, language="en", vad_filter=True)
print("TRANSCRIPT:", repr(text))
print("device/compute:", tr.active_device, tr.active_compute)
