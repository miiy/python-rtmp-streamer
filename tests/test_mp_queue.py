import time
import queue
import unittest
import numpy as np
import multiprocessing as mp


def producer(q: mp.Queue) -> None:
    # handle frame data
    frames = [np.zeros((1080, 1920, 3), dtype=np.uint8) for i in range(250)]

    start_time = time.time()
    for i in range(len(frames)):
        frame = frames[i]
        q.put(frame)
        # send time
        if i % 25 == 0:
            total_time = time.time() - start_time
            start_time = time.time()
            print(f"send time: {total_time}")


def consumer(q: mp.Queue) -> None:
    i = 0
    start_time = time.time()

    try:
        while q.qsize() == 0:
            time.sleep(0.001)
    except NotImplementedError:
        while q.empty():
            time.sleep(0.001)

    while True:
        try:
            frame = q.get(timeout=0.1)
        except queue.Empty:
            break

        # receive time
        if i == 25:
            total_time = time.time() - start_time
            i = 0
            start_time = time.time()
            print(f"recv time: {total_time}")
        i += 1


class MPQueueTestCase(unittest.TestCase):

    def test_run(self):
        q = mp.Queue()
        p_process = mp.Process(target=producer, args=(q,))
        p_process.start()

        consumer(q)

        # self.assertEqual(ret, True)


if __name__ == '__main__':
    unittest.main()
