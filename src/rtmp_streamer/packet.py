import time
import queue
import logging
import threading
import numpy as np
import multiprocessing as mp

logger = logging.getLogger(__name__)


class PacketThread(threading.Thread):
    """ packet worker """
    def __init__(self, packet_queue: mp.Queue, frame_queue: queue.Queue, audio_queue: queue.Queue,
                 fps: int, sr: int):
        super().__init__(daemon=True)
        self.packet_queue = packet_queue
        self.frame_queue = frame_queue
        self.audio_queue = audio_queue
        self.fps = fps
        self.sr = sr
        self.pause_event = threading.Event()

    def run(self) -> None:
        i = 0
        start_time = time.time()
        empty_audio = self.create_empty_audio(self.fps, self.sr)
        while True:
            if self.pause_event.is_set():
                self.pause_event.wait()
            try:
                sh_frame, sh_audio = self.packet_queue.get(timeout=0.02)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error("get packet error", exc_info=e)
                break

            frame = sh_frame.array
            audio = sh_audio.array if sh_audio is not None else empty_audio

            self.frame_queue.put(frame.tobytes())
            self.audio_queue.put(audio.tobytes())

            sh_frame.close()
            sh_frame.unlink()
            if sh_audio is not None:
                sh_audio.close()
                sh_audio.unlink()

            # 帧率是否超时
            if i == 25:
                total_time = time.time() - start_time
                i = 0
                start_time = time.time()
                if total_time >= 1.02:
                    logger.warning(f"push time: {total_time}")
            i += 1

    def clear_queue(self) -> None:
        self.pause_event.set()
        try:
            while self.packet_queue.qsize() > 25:
                self.packet_queue.get()
        except NotImplementedError:
            pass
        while self.frame_queue.qsize() > 0:
            self.frame_queue.get()
        while self.audio_queue.qsize() > 0:
            self.audio_queue.get()
        self.pause_event.clear()

    @classmethod
    def create_empty_audio(cls, fps: int, sr: int) -> np.ndarray:
        wav_frame_num = int(sr / fps)
        audio = np.zeros(wav_frame_num, dtype=np.int16)
        return audio

