import time
import queue
import logging
import threading
from typing import Union
import multiprocessing as mp

import shared_ndarray as sn


logger = logging.getLogger(__name__)


class PacketThread(threading.Thread):
    """ packet worker """
    def __init__(self, packet_queue: mp.Queue, frame_queue: queue.Queue, audio_queue: queue.Queue, stop_event: threading.Event):
        super().__init__(daemon=True)
        self._packet_queue = packet_queue
        self._frame_queue = frame_queue
        self._audio_queue = audio_queue

        self._clear_event = threading.Event()
        self._stop_event = stop_event

    def run(self) -> None:
        i = 0
        start_time = time.time()
        while not self._stop_event.is_set():
            if self._clear_event.is_set():
                self._clear_event.wait()
            try:
                packet: sn.SharedNDArray = self._packet_queue.get(timeout=0.01)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error("get packet error", exc_info=e)
                break

            frame = packet.get("frame")
            audio = packet.get("audio")
            self._frame_queue.put(frame)
            self._audio_queue.put(audio)

            packet.close()
            packet.unlink()

            # 分割时间
            if i % 25 == 0:
                total_time = time.time() - start_time
                start_time = time.time()
                if total_time > 1.01:
                    logger.warn(f"packet time: {total_time}")
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
    def clear_queue(cls, q: Union[queue.Queue, mp.Queue], is_shared: bool = False) -> None:
        while True:
            try:
                data = q.get(timeout=0.02)
            except queue.Empty:
                break

            if is_shared:
                data.close()
                data.unlink()
