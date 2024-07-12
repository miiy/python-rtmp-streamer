import numpy as np
from multiprocessing.shared_memory import SharedMemory


class Packet:
    def __init__(self, image_shape: tuple, image_dtype: np.dtype, image_size: int,
                 audio_shape: tuple, audio_dtype: np.dtype, audio_size: int,
                 name: str | None = None) -> None:

        self._image_shape = image_shape
        self._image_dtype = image_dtype
        self._image_size = image_size

        self._audio_shape = audio_shape
        self._audio_dtype = audio_dtype
        self._audio_size = audio_size

        if name:
            self._shm = SharedMemory(name=name, create=False)
        else:
            self._shm = SharedMemory(create=True, size=image_size + audio_size)

    @classmethod
    def create(cls, image: np.ndarray, audio: np.ndarray) -> "Packet":
        arr = cls(image.shape, image.dtype, image.nbytes, audio.shape, audio.dtype, audio.nbytes)
        arr._shm.buf[:image.nbytes] = image.tobytes()
        arr._shm.buf[image.nbytes:image.nbytes + audio.nbytes] = audio.tobytes()
        return arr

    def image(self) -> bytes:
        return bytes(self._shm.buf[:self._image_size])

    def audio(self) -> bytes:
        return bytes(self._shm.buf[self._image_size:self._image_size + self._audio_size])

    def image_numpy(self) -> np.ndarray:
        return np.ndarray(self._image_shape, dtype=self._image_dtype, buffer=self._shm.buf[:self._image_size])

    def audio_numpy(self) -> np.ndarray:
        return np.ndarray(self._audio_shape, dtype=self._audio_dtype,
                          buffer=self._shm.buf[self._image_size:self._image_size + self._audio_size])

    def close(self) -> None:
        self._shm.close()

    def unlink(self) -> None:
        self._shm.unlink()

    def __del__(self):
        self._shm.close()

    def __getstate__(self):
        return (self._image_shape, self._image_dtype, self._image_size,
                self._audio_shape, self._audio_dtype, self._audio_size,
                self._shm.name)

    def __setstate__(self, state):
        self.__init__(*state)


def create_empty_audio(fps: int, sr: int) -> np.ndarray:
    """
    create empty audio
    empty_audio = create_empty_audio(fps, sr)
    """
    wav_frame_num = int(sr / fps)
    audio = np.zeros(wav_frame_num, dtype=np.int16)
    return audio
