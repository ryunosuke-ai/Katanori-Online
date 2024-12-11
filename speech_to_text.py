import pyaudio
import wave
import os
from google.cloud import speech
import io
import settings

# Google Cloudの認証ファイルへのパスを設定
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.G_AP

# 録音設定
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # サンプルレート（Google Speech-to-Textのデフォルト）
CHUNK = 1024
RECORD_SECONDS = 5  # 録音時間
WAVE_OUTPUT_FILENAME = "recorded.wav"

def record_audio():
    audio = pyaudio.PyAudio()

    # 録音の開始
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

    print("録音中...")

    frames = []

    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("録音終了")

    # 録音ストリームを閉じる
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # 録音したデータをWAV形式で保存
    with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

def transcribe_audio(file_path):
    client = speech.SpeechClient()

    with io.open(file_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ja-JP"  # 日本語の場合
    )

    response = client.recognize(config=config, audio=audio)

    # 文字起こしの結果を出力
    for result in response.results:
        print("Transcript: {}".format(result.alternatives[0].transcript))

if __name__ == "__main__":
    # 音声の録音
    record_audio()

    # 録音した音声の文字起こし
    transcribe_audio(WAVE_OUTPUT_FILENAME)
