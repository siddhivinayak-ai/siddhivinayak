"""
TTS Server
Supports Indian Male voice (en-IN-PrabhatNeural) and local Piper models.
"""

import asyncio
import io
import os
import wave
import edge_tts
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Primary voice: Indian Male voice
DEFAULT_VOICE = "en-IN-PrabhatNeural"
CURRENT_VOICE = DEFAULT_VOICE

# Optional Piper fallback
piper_voice = None
HINDI_ONNX = os.path.join(BASE_DIR, "hindi_accent.onnx")
HINDI_CONFIG = os.path.join(BASE_DIR, "hindi_accent.json")

try:
    if os.path.exists(HINDI_ONNX) and os.path.exists(HINDI_CONFIG):
        from piper.voice import PiperVoice
        piper_voice = PiperVoice.load(HINDI_ONNX, config_path=HINDI_CONFIG)
        print("[TTS] Piper backup voice loaded.")
except Exception as e:
    print(f"[TTS] Piper voice skipped: {e}")


async def synthesize_edge(text: str, voice_name: str) -> bytes:
    """Synthesize speech using high-fidelity Indian Male neural voice."""
    communicate = edge_tts.Communicate(text, voice=voice_name)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "voice": CURRENT_VOICE,
        "gender": "Male",
        "locale": "en-IN"
    })


@app.route("/api/speak", methods=["POST"])
def speak():
    """Convert text to speech with Indian Male voice."""
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    requested_voice = data.get("voice", CURRENT_VOICE)

    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        if requested_voice.startswith("piper") and piper_voice:
            buffer = io.BytesIO()
            with wave.open(buffer, "wb") as wav_file:
                piper_voice.synthesize_wav(text, wav_file)
            buffer.seek(0)
            return send_file(buffer, mimetype="audio/wav", as_attachment=False)

        # Synthesize with Indian Male Neural voice
        audio_bytes = asyncio.run(synthesize_edge(text, requested_voice))

        return send_file(
            io.BytesIO(audio_bytes),
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="speech.mp3",
        )
    except Exception as e:
        print(f"[TTS] Speech synthesis error: {e}")
        # Fallback to piper if edge fails
        if piper_voice:
            try:
                buffer = io.BytesIO()
                with wave.open(buffer, "wb") as wav_file:
                    piper_voice.synthesize_wav(text, wav_file)
                buffer.seek(0)
                return send_file(buffer, mimetype="audio/wav", as_attachment=False)
            except Exception as e2:
                print(f"[TTS] Fallback error: {e2}")

        return jsonify({"error": str(e)}), 500


@app.route("/api/voices", methods=["GET"])
def list_voices():
    return jsonify({
        "current": CURRENT_VOICE,
        "available": [
            {"id": "en-IN-PrabhatNeural", "name": "Prabhat (Indian Male - English)", "gender": "Male"},
            {"id": "hi-IN-MadhurNeural", "name": "Madhur (Indian Male - Hindi)", "gender": "Male"},
            {"id": "piper-hindi", "name": "Piper Hindi Accent", "gender": "Female"}
        ]
    })


if __name__ == "__main__":
    print(f"[TTS] Server running with Indian Male voice: {CURRENT_VOICE}")
    app.run(host="0.0.0.0", port=5050, debug=False)
