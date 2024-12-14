import os
import sounddevice as sd
import soundfile as sf
from google.cloud import texttospeech
import tempfile
import settings

# Google Cloud認証情報のパスを設定
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GP

def synthesize_speech(text):
    # Google Text-to-Speechクライアントを設定
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # 音声のパラメータ設定
    voice = texttospeech.VoiceSelectionParams(
        language_code="ja-JP",  # 日本語を使用
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16  # Wav形式で出力
    )

    # 音声の合成
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    
    # 一時ファイルに音声を書き込む
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        temp_file.write(response.audio_content)
        temp_filename = temp_file.name

    return temp_filename

def play_audio(file_path, device_name):
    # 音声ファイルを読み込み、仮想オーディオデバイスに再生
    data, fs = sf.read(file_path)
    sd.default.device = device_name  # 仮想オーディオデバイス名を設定（例: 'VB-Audio Cable'や'BlackHole'）
    sd.play(data, fs)
    sd.wait()  # 再生完了まで待機

if __name__ == "__main__":
    text_to_speak = "こんにちは、これはテストです。"  # 合成するテキスト
    device_name = "BlackHole"  # 仮想オーディオデバイス名（例: 'VB-Audio Cable'や'BlackHole'）

    # 合成音声を生成し、その一時ファイルパスを取得
    audio_file_path = synthesize_speech(text_to_speak)
    
    # 合成音声を仮想オーディオデバイス経由で再生
    play_audio(audio_file_path, device_name)
