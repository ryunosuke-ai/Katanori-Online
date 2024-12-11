from flask import Flask, request, render_template, jsonify
from google.cloud import speech
import io
import os
import logging
import settings

app = Flask(__name__)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.G_AP

client = speech.SpeechClient()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio_file" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files["audio_file"]
    audio_content = audio_file.read()

    # 音声データをGoogle Speech-to-Textに送信
    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ja-JP"
    )

    try:
        response = client.recognize(config=config, audio=audio)
        logging.debug("API Full Response: %s", response)

        if not response.results:
            return jsonify({"error": "No transcription result or unsupported audio format"}), 400

        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript + "\n"

        return jsonify({"transcript": transcript})
    except Exception as e:
        logging.error("API Error: %s", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True)
