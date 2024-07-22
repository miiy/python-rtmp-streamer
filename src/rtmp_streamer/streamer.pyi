import threading
import numpy as np
import multiprocessing as mp


class Streamer:
    FRAME_PIPE_PATH: str
    AUDIO_PIPE_PATH: str

    _packet_queue: mp.Queue
    _stop_event: threading.Event
    _push_url: str
    _frame_width: int
    _frame_height: int
    _fps: int

    def __init__(self, packet_queue: mp.Queue, stop_event: threading.Event,
                 push_url: str, frame_width: int, frame_height: int, fps: int = 25):
        """
        :param packet_queue: The maxsize of the queue should be set
        :param stop_event:
        :param push_url:
        :param frame_width:
        :param frame_height:
        :param fps:
        """
        ...

    def run(self) -> None: ...

    def ffmpeg_command(self) -> list[str]: ...
