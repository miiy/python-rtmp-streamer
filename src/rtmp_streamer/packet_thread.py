import time
import queue
import logging
import threading
from typing import Union
import multiprocessing as mp
from .packet import Packet

logger = logging.getLogger(__name__)


class PacketThread(threading.Thread):
    """ packet worker """
    def __init__(self, packet_queue: mp.Queue, frame_queue: queue.Queue, audio_queue: queue.Queue):
        super().__init__(daemon=True)
        self._packet_queue = packet_queue
        self._frame_queue = frame_queue
        self._audio_queue = audio_queue
        self._clear_event = threading.Event()

    def run(self) -> None:
        i = 0
        start_time = time.time()
        while True:
            if self._clear_event.is_set():
                self._clear_event.wait()
            try:
                packet: Packet = self._packet_queue.get(timeout=0.01)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error("get packet error", exc_info=e)
                break

            image = packet.image()
            audio = packet.audio()
            self._frame_queue.put(image)
            self._audio_queue.put(audio)

            packet.close()
            packet.unlink()

            # 分割时间
            if i % 25 == 0:
                total_time = time.time() - start_time
                start_time = time.time()
                logger.debug(f"push time: {total_time}")
            i = i + 1 if i < 10000 else 0

    def clear_all_queue(self) -> None:
        self._clear_event.set()
        pt = threading.Thread(target=self.clear_queue, args=(self._packet_queue, True))
        pt.start()

        queues = [self._frame_queue, self._audio_queue]
        threads = []
        for q in queues:
            t = threading.Thread(target=self.clear_queue, args=(q,))
            t.start()
            threads.append(t)

        pt.join()
        for t in threads:
            t.join()

        self._clear_event.clear()

    @classmethod
    def clear_queue(cls, q: Union[queue.Queue, mp.Queue], is_free: bool = False) -> None:
        while not q.empty():
            if is_free:
                data = q.get()
                data.close()
                data.unlink()
            else:
                q.get()
