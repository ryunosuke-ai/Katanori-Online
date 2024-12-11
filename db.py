import librosa
import wave
import soundfile as sf
import numpy as np

def wav_read(path):
    wave, fs = sf.read(path) #音データと周波数を読み込む
    return wave, fs

def get_db(db_filename):
    wave, fs = wav_read(db_filename)
    rms = librosa.feature.rms(y=wave) #音量の計算
    db = librosa.amplitude_to_db(rms)
    db_average =  np.average(db)

    return db_average
