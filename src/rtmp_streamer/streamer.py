import os
import time
import queue
import logging
import threading
import subprocess
import multiprocessing as mp
from .packet_thread import PacketThread
from .pipe_thread import PipeThread


logger = logging.getLogger(__name__)


class Streamer:
    """
    Class for streaming video and audio using ffmpeg and threads.

    run
        packet thread
        ffmpeg subprocess
        frame pipe thread
        audio pipe thread
    """

    # named pipes
    FRAME_PIPE_PATH = "frame_pipe"
    AUDIO_PIPE_PATH = "audio_pipe"

    def __init__(self, packet_queue: mp.Queue,
                 push_url: str, frame_width: int, frame_height: int, fps: int = 25):
        """ init """
        self._packet_queue = packet_queue
        self._packet_thread = None

        self._push_url = push_url
        self._frame_width = frame_width
        self._frame_height = frame_height
        self._fps = fps

        self._frame_queue = queue.Queue(maxsize=50)
        self._frame_thread = None
        self._audio_queue = queue.Queue(maxsize=50)
        self._audio_thread = None
        self._ffmpeg_process = None

        self._stop_task_event = threading.Event()
        self._stop_event = threading.Event()

    def run(self) -> None:
        """
        run
            packet_queue 需要设置队列最大数量
        task
        packet_queue 队列为空，0.5s后自动停止
        管道错误，立即停止
        停止1个，三个全部停止。
        如果packet_queue里有数据，重启开启
        """
        logger.debug("run")
        # packet thread
        self._packet_thread = PacketThread(self._packet_queue, self._frame_queue, self._audio_queue, self._stop_event)
        self._packet_thread.start()
        logger.debug("packet thread started")

        last_time = 0
        sleep = 1
        max_sleep = 5
        while not self._stop_event.is_set():
            if self._packet_queue.empty():
                logger.debug("packet_queue is empty")
                time.sleep(0.2)
                continue

            # start task
            self._packet_thread.clear_all_queue()
            self._start_task()
            last_time = time.time()

            # process status
            while not self._stop_task_event.is_set():
                # if packet thread is dead, stop all
                if self._ffmpeg_process.poll() is not None or not self._frame_thread.is_alive() or not self._audio_thread.is_alive():
                    break
                time.sleep(0.2)

            # stop task
            self._stop_task()

            if time.time() - last_time > 5:
                sleep = 1
            else:
                sleep = sleep + 1 if sleep < max_sleep else sleep
            time.sleep(sleep)

    def _start_task(self) -> None:
        """ start task """
        logger.debug("_start_task")
        self._stop_task_event.clear()
        # frame thread, audio_thread：创建两个线程，分别将视频流和音频流写入"named pipes"
        self._frame_thread = PipeThread(self._frame_queue, self.FRAME_PIPE_PATH, self._stop_task_event)
        self._audio_thread = PipeThread(self._audio_queue, self.AUDIO_PIPE_PATH, self._stop_task_event)
        self._frame_thread.start()
        logger.debug("frame thread started")
        self._audio_thread.start()
        logger.debug("audio thread started")

        # wait ready
        while not os.path.exists(self.FRAME_PIPE_PATH) or not os.path.exists(self.AUDIO_PIPE_PATH):
            time.sleep(0.01)

        # start ffmpeg command subprocess
        self._ffmpeg_process = subprocess.Popen(self.ffmpeg_command(), stdin=subprocess.PIPE, shell=False)
        logger.debug("ffmpeg subprocess started")

    def _stop_task(self) -> None:
        logger.debug("_stop_task")
        # set stop task event
        self._stop_task_event.set()

        # stop ffmpeg process
        self._ffmpeg_process.stdin.close()
        self._ffmpeg_process.terminate()
        # wait process exit
        try:
            self._ffmpeg_process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            logger.exception("ffmpeg didn't terminate in time, killing it.")
            self._ffmpeg_process.kill()

        # wait exit
        self._frame_thread.join()
        self._audio_thread.join()
        logger.debug("task stopped")


    def get_packet_queue_qsize(self) -> int:
        try:
            return self._packet_queue.qsize()
        except NotImplementedError:
            return 0

    def get_frame_queue_qsize(self) -> int:
        return self._frame_queue.qsize()

    def get_audio_queue_qsize(self) -> int:
        return self._audio_queue.qsize()

    def ffmpeg_command(self) -> list[str]:
        """
        ffmpeg command

        -i 输入
        -g 关键帧（I帧）间隔， 实时传输通常1-5之间
        """
        command = ['ffmpeg',
                   # '-thread_queue_size', '128',
                   '-thread_queue_size', '8',
                   # '-loglevel', 'info',
                   # '-loglevel', 'debug',
                   # '-y', '-an',
                   '-re',
                   # '-threads', '4',
                   '-threads', '4',
                   '-y',
                   '-f', 'rawvideo',
                   '-vcodec', 'rawvideo',
                   '-pix_fmt', 'bgr24',
                   '-s', "{}x{}".format(self._frame_width, self._frame_height),
                   '-i', self.FRAME_PIPE_PATH,
                   '-f', 's16le',
                   '-acodec', 'pcm_s16le',
                   '-i', self.AUDIO_PIPE_PATH,
                   '-c:v', "libx264",
                   '-pix_fmt', 'yuv420p',
                   '-preset', 'ultrafast',
                   # '-profile:v', 'main',
                   '-tune:v', 'zerolatency',
                   '-g', '2',
                   # '-b:v', "1000k",
                   '-ac', '1',
                   '-ar', '44100',
                   '-acodec', 'aac',
                   '-shortest',
                   '-f', 'flv',
                   '-r', str(self._fps),
                   self._push_url]
        return command

    def stop(self) -> None:
        self._stop_event.set()


def _mp_safe_qsize(q: mp.Queue) -> int:
    """
    https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing.Queue.qsize
    """
    try:
        return q.qsize()
    except NotImplementedError:
        return 0
