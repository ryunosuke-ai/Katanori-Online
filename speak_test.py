import sounddevice as sd
import numpy as np
import wave
import time

DURATION = 10  # 最大録音時間（秒）
SILENCE_THRESHOLD = 800  # 無音判定の閾値（適切な値に調整）
SILENCE_DURATION = 3  # 無音が続いた場合の停止判定時間（秒）
RESTART_DELAY = 5  # 録音再開の遅延秒数
RATE = 44100
CHANNELS = 1
OUTPUT_FILENAME = "recorded_audio.wav"

def moving_average(data, window_size=5):
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

def is_silent(data, threshold=SILENCE_THRESHOLD):
    rms_value = np.sqrt(np.mean(np.square(data)))
    return rms_value < threshold

def record_audio():
    print("録音を開始します... 話してください")
    recording_started = False
    start_time = None

    # WAVファイルを開いて録音データを書き込む準備
    with wave.open(OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(RATE)

        with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype='int16', blocksize=None) as stream:
            silent_duration = 0
            while True:
                data = stream.read(int(RATE * 0.5))[0].flatten()

                # 平均処理を使ったデータの滑らかさ向上
                smoothed_data = moving_average(data)

                # 話し始めを待つ
                if not recording_started:
                    if not is_silent(smoothed_data):
                        print("録音中...")
                        recording_started = True
                        start_time = time.time()  # 話し始めたタイミングでカウントを開始
                    else:
                        continue  # 無音の場合は再度ループして待機

                # 録音中のデータをWAVファイルに直接書き込み
                wf.writeframes(data.tobytes())

                # 最大録音時間に達したら停止
                if recording_started and (time.time() - start_time > DURATION):
                    print("録音時間が上限に達したため、録音を停止します...")
                    break

                # 無音が続いた場合も停止
                if recording_started and is_silent(smoothed_data):
                    silent_duration += 0.5  # 無音の継続秒数をカウント
                    if silent_duration >= SILENCE_DURATION:
                        print("無音が続いたため、録音を停止します...")
                        break
                else:
                    silent_duration = 0  # 音声があれば無音カウントをリセット

    print(f"録音を保存しました: {OUTPUT_FILENAME}")
    time.sleep(RESTART_DELAY)
    print(f"{RESTART_DELAY}秒後に再度録音を開始します。")

while True:
    record_audio()
