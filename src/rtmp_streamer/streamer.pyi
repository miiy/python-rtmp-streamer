import queue
import subprocess
import threading
import numpy as np
import multiprocessing as mp


class Streamer:
    FRAME_PIPE_PATH: str
    AUDIO_PIPE_PATH: str

    _packet_queue: mp.Queue
    _packet_thread: threading.Thread

    _push_url: str
    _frame_width: int
    _frame_height: int
    _fps: int

    _frame_queue: queue.Queue
    _frame_thread: threading.Thread
    _audio_queue: queue.Queue
    _audio_thread: threading.Thread
    _ffmpeg_process: subprocess.Popen

    _stop_task_event: threading.Event
    _stop_event: threading.Event

    def __init__(self, packet_queue: mp.Queue,
                 push_url: str, frame_width: int, frame_height: int, fps: int = 25):
        """
        :param packet_queue: The maxsize of the queue should be set
        :param push_url:
        :param frame_width:
        :param frame_height:
        :param fps:
        """
        ...

    def run(self) -> None: ...

    def _start_task(self) -> None: ...

    def _stop_task(self) -> None: ...

    def get_packet_queue_qsize(self) -> int: ...

    def get_frame_queue_qsize(self) -> int: ...

    def get_audio_queue_qsize(self) -> int: ...

    def ffmpeg_command(self) -> list[str]: ...

    def stop(self) -> None: ...
