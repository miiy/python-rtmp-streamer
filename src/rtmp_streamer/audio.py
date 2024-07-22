import numpy as np


def create_empty_audio(fps: int, sr: int) -> np.ndarray:
    """
    create empty audio
    empty_audio = create_empty_audio(fps, sr)
    """
    wav_frame_num = int(sr / fps)
    audio = np.zeros(wav_frame_num, dtype=np.int16)
    return audio
