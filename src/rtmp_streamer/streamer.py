import os
import time
import queue
import logging
import threading
import subprocess
from typing import Optional
import multiprocessing as mp

from .packet import PacketThread
from .pipe import PipeThread


logger = logging.getLogger(__name__)


class Streamer(mp.Process):
    """
    Streamer process
        packet thread
        ffmpeg sub process
        frame pipe thread
        audio pipe thread
    """

    # named pipes
    FRAME_PIPE_PATH = "frame_pipe"
    AUDIO_PIPE_PATH = "audio_pipe"

    # debug
    _debug_exclude = ['get_status']

    def __init__(self, packet_queue: mp.Queue,
                 fps: int = 25, sr: int = 44100, ffmpeg_cmd: list[str] = None):
        """ init """
        super().__init__()

        # config
        self.fps = fps
        self.sr = sr
        self.ffmpeg_cmd = ffmpeg_cmd

        # packet_queue 需要设置队列最大数量
        self.packet_queue = packet_queue
        self._frame_queue = queue.Queue(maxsize=50)
        self._audio_queue = queue.Queue(maxsize=50)
        self._packet_thread: Optional[PacketThread] = None

        # task
        # packet_queue 队列为空，1s后自动停止
        # 管道错误，立即停止
        # 停止1个，三个全部停止。
        # stop_task() 如果packet_queue里有数据，会自动再次开启任务
        # 推流服务器失败，最多重试3次
        self.ffmpeg_process: Optional[subprocess.Popen] = None
        self.frame_thread: Optional[PipeThread] = None
        self.audio_thread: Optional[PipeThread] = None
        self.stop_task_event = threading.Event()

    def run(self) -> None:
        """ run """
        # packet worker
        self._packet_thread = PacketThread(self.packet_queue, self._frame_queue, self._audio_queue, self.fps, self.sr)
        self._packet_thread.start()

        self.task_runer()

    def get_status(self) -> dict:
        """ get status """
        fp_is_alive = False if self.ffmpeg_process is None else self.ffmpeg_process.poll() is None
        ft_is_alive = False if self.frame_thread is None else self.frame_thread.is_alive()
        at_is_alive = False if self.audio_thread is None else self.audio_thread.is_alive()

        # https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing.Queue.qsize

        return {
            "packet_qsize": self._mp_safe_qsize(self.packet_queue),
            "frame_qsize": self._frame_queue.qsize(),
            "audio_qsize": self._audio_queue.qsize(),
            "fp_is_alive": fp_is_alive,
            "ft_is_alive": ft_is_alive,
            "at_is_alive": at_is_alive,
        }

    def task_runer(self) -> None:
        """ task runner """
        last_time = 0
        while True:
            status = self.get_status()
            # start task
            # 缓存8帧，防止数据传输慢，播放完后立即关闭
            # ffmpeg, frame pipe, audio pipe must alive
            if (status["frame_qsize"] > 8 or status["audio_qsize"] > 8) \
                    and not status["fp_is_alive"] and not status["ft_is_alive"] and not status["at_is_alive"]:

                if last_time > 0 and time.time()-last_time < 1:
                    logger.error("start task failed, retry after 10s")
                    time.sleep(10)

                self.start_task(self.ffmpeg_cmd)
                last_time = time.time()
                continue

            # stop task
            if (status["frame_qsize"] > 8 or status["audio_qsize"] > 8) \
                    and (not status["fp_is_alive"] or not status["ft_is_alive"] or not status["at_is_alive"]):
                self.stop_task()
            time.sleep(0.1)

    def start_task(self, ffmpeg_cmd: list[str]) -> None:
        """ start task """
        self._packet_thread.clear_queue()
        # 创建两个线程，分别将视频流和音频流写入"named pipes"
        self.frame_thread = PipeThread(self._frame_queue, self.FRAME_PIPE_PATH)
        self.audio_thread = PipeThread(self._audio_queue, self.AUDIO_PIPE_PATH)
        self.frame_thread.start()
        self.audio_thread.start()
        # ffmpeg command subprocess
        while not os.path.exists(self.FRAME_PIPE_PATH) or not os.path.exists(self.AUDIO_PIPE_PATH):
            time.sleep(0.01)
        # 如果非正常关闭，先释放资源
        if self.ffmpeg_process is not None:
            self.ffmpeg_process.stdin.close()
        self.ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, shell=False)


    def stop_task(self) -> None:
        """stop task"""
        if self.stop_task_event.is_set():
            return

        self.stop_task_event.set()

        # close ffmpeg process
        if self.ffmpeg_process is not None:
            # close stdin
            if self.ffmpeg_process.stdin:
                self.ffmpeg_process.stdin.close()
            self.ffmpeg_process.terminate()
            try:
                self.ffmpeg_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.ffmpeg_process.kill()
                self.ffmpeg_process.wait()
            self.ffmpeg_process = None
            logger.debug("ffmpeg_process stopped.")

        # close frame thread
        if self.frame_thread is not None:
            self.frame_thread.stop()
            if self.frame_thread.is_alive():
                self.frame_thread.join()
            self.frame_thread = None
            logger.debug("frame_thread stopped.")

        # close audio thread
        if self.audio_thread is not None:
            self.audio_thread.stop()
            if self.audio_thread.is_alive():
                self.audio_thread.join()
            self.audio_thread = None
            logger.debug("audio_thread stopped.")

        self.stop_task_event.clear()
    
    def terminate(self) -> None:
        self.ffmpeg_process.terminate()
        super().terminate()

    @classmethod
    def _mp_safe_qsize(cls, q: mp.Queue) -> int:
        """
        https://docs.python.org/zh-cn/3/library/multiprocessing.html#multiprocessing.Queue.qsize
        """
        try:
            return q.qsize()
        except NotImplementedError:
            return 0

    @classmethod
    def ffmpeg_command(cls, push_url: str, fps: int, frame_width: int, frame_height: int) -> list[str]:
        """
        ffmpeg command

        -i 输入
        -g 关键帧（I帧）间隔， 实时传输通常1-5之间
        """
        command = ['ffmpeg',
                   # '-thread_queue_size', '128',
                   '-thread_queue_size', '8',
                   # '-loglevel', 'info',
                   # '-y', '-an',
                   '-re',
                   # '-threads', '4',
                   '-threads', '4',
                   '-y',
                   '-f', 'rawvideo',
                   '-vcodec', 'rawvideo',
                   '-pix_fmt', 'bgr24',
                   '-s', "{}x{}".format(frame_width, frame_height),
                   '-i', cls.FRAME_PIPE_PATH,
                   '-f', 's16le',
                   '-acodec', 'pcm_s16le',
                   '-i', cls.AUDIO_PIPE_PATH,
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
                   '-r', str(fps),
                   push_url]
        logger.debug(f"ffmpeg command: {command}")
        return command

