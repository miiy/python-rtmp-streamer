import multiprocessing as mp


class Streamer(mp.Process):
    FRAME_PIPE_PATH = "frame_pipe"
    AUDIO_PIPE_PATH = "audio_pipe"

    fps: int
    sr: int
    ffmpeg_cmd: list
    packet_queue: mp.Queue

    def __init__(self, packet_queue: mp.Queue,
                 fps: int = 25, sr: int = 44100, ffmpeg_cmd: list[str] = None):
        """
        :param packet_queue: The maxsize of the queue should be set
        :param fps:
        :param sr:
        :param ffmpeg_cmd:
        """
        ...

    def run(self) -> None: ...

    def get_status(self) -> dict:
        """
        :return:
        {
            "packet_qsize": 0,
            "frame_qsize": 0,
            "audio_qsize": 0,
            "fp_is_alive": False,
            "ft_is_alive": False,
            "at_is_alive": False,
        }
        """
        ...

    def graceful_shutdown(self) -> None: ...

    @classmethod
    def ffmpeg_command(cls, push_url: str, fps: int, frame_width: int, frame_height: int) -> list[str]: ...
