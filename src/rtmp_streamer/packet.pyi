import numpy as np
from multiprocessing.shared_memory import SharedMemory


class Packet:
    _image_shape: tuple
    _image_dtype: np.dtype
    _image_size: int

    _audio_shape: tuple
    _audio_dtype: np.dtype
    _audio_size: int

    _shm: SharedMemory

    def __init__(self, image_shape: tuple, image_dtype: np.dtype, image_size: int,
                 audio_shape: tuple, audio_dtype: np.dtype, audio_size: int,
                 name: str | None = None) -> None: ...
    @classmethod
    def create(cls, image: np.ndarray, audio: np.ndarray) -> "Packet":
        ...

    def image(self) -> bytes: ...

    def audio(self) -> bytes: ...

    def image_numpy(self) -> np.ndarray: ...

    def audio_numpy(self) -> np.ndarray: ...

    def close(self) -> None: ...

    def unlink(self) -> None: ...


def create_empty_audio(fps: int, sr: int) -> np.ndarray: ...
