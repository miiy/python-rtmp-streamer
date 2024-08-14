import os
import time
import queue
import logging
import threading


logger = logging.getLogger(__name__)


class PipeThread(threading.Thread):
    """ write stream to named pipe """
    def __init__(self, q: queue.Queue, pipe_name: str, stop_event: threading.Event):
        super().__init__(daemon=True)

        self._q = q
        self._pipe_name = pipe_name
        self._stop_event = stop_event
        self._last_time = time.time()

    def run(self) -> None:
        # create named pipes
        self._create_named_pipe(self._pipe_name)
        # open named pipe
        # Notice: if read not ready, open will block
        fd_pipe = os.open(self._pipe_name, os.O_WRONLY)
        logger.debug(f"fd opened: {self._pipe_name}")

        while not self._stop_event.is_set():
            # no blocking read queue
            try:
                data = self._q.get(timeout=0.02)
            except queue.Empty:
                # if time > 1 second, break
                if time.time() - self._last_time > 2:
                    logger.debug(f"{self._pipe_name} queue empty over 2s.")
                    break
                # retry
                continue
            self._last_time = time.time()

            try:
                # Notice: if read pipe is full, write will block.
                #         close read pipe throw BrokenPipeError.
                os.write(fd_pipe, data)
            except BrokenPipeError as e:
                logger.exception(e)
                break
            except Exception as e:
                logger.error("An unexpected error occurred: %s", e)
                break

        # terminate
        # close named pipe
        if fd_pipe:
            os.close(fd_pipe)
        self._remove_named_pipe(self._pipe_name)

    @classmethod
    def _remove_named_pipe(cls, path: str):
        """ remove the "named pipes". """
        if os.path.exists(path):
            os.unlink(path)

    @classmethod
    def _create_named_pipe(cls, path: str):
        """create named pipes"""
        cls._remove_named_pipe(path)
        os.mkfifo(path)
