import os
import time
import queue
import logging
import threading


logger = logging.getLogger(__name__)


class PipeThread(threading.Thread):
    """ write stream to named pipe """
    def __init__(self, q: queue.Queue, pipe_name: str):
        super().__init__(daemon=True)

        self.q = q
        self.pipe_name = pipe_name
        self.last_time = time.time()

    def run(self) -> None:
        # create named pipes
        self.create_named_pipe(self.pipe_name)
        # open named pipe
        # Notice: if read not ready, open will block
        fd_pipe = os.open(self.pipe_name, os.O_WRONLY)
        logging.debug(f"fd opened: {self.pipe_name}")
        while True:
            # no blocking read queue
            try:
                frame = self.q.get(timeout=0.02)
            except queue.Empty:
                # if time > 1 second, break
                if time.time() - self.last_time > 1:
                    logging.debug(f"{self.pipe_name} queue empty over 1s.")
                    break
                # retry
                continue
            self.last_time = time.time()

            try:
                # Notice: if read pipe is full, write will block.
                #         close read pipe throw BrokenPipeError.
                os.write(fd_pipe, frame)
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
        self.remove_named_pipe(self.pipe_name)

    @classmethod
    def remove_named_pipe(cls, path: str):
        """ remove the "named pipes". """
        if os.path.exists(path):
            os.unlink(path)

    @classmethod
    def create_named_pipe(cls, path: str):
        """create named pipes"""
        cls.remove_named_pipe(path)
        os.mkfifo(path)
