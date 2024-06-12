import time
import queue
import unittest
import numpy as np
import multiprocessing as mp
import shared_ndarray as sn


def producer(q: mp.Queue) -> None:
    # handle frame data
    frames = [np.zeros((1080, 1920, 3), dtype=np.uint8) for i in range(250)]

    start_time = time.time()
    print(f"begin: {start_time}")
    for i in range(len(frames)):
        frame = frames[i]
        sh_frame = sn.from_numpy(frame)
        q.put(sh_frame)
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
        except Exception as e:
            print(e)
            break

        frame_copy = frame.clone()
        frame.unlink()

        # receive time
        if i % 25 == 0:
            total_time = time.time() - start_time
            start_time = time.time()
            print(f"recv time: {total_time}")
        i += 1
        if i == 255:
            end_time = time.time()
            print(f"end: {end_time}")
            break


class MPSharedNDArrayTestCase(unittest.TestCase):

    def test_run(self):
        mp.set_start_method('spawn')

        q = mp.Queue()
        p_process = mp.Process(target=producer, args=(q,))
        p_process.start()
        c_process = mp.Process(target=consumer, args=(q,))
        c_process.start()

        p_process.join()
        c_process.join()

        # self.assertEqual(ret, True)


if __name__ == '__main__':
    unittest.main()
