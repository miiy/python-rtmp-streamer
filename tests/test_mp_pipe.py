import time
import numpy as np
import multiprocessing as mp
import unittest


def producer(write_conn: mp.Pipe) -> None:
    # handle frame data
    frames = [np.zeros((1080, 1920, 3), dtype=np.uint8) for i in range(500)]

    fps = 25
    wav_frame_num = int(44100 / fps)
    aud_empty = np.zeros(wav_frame_num, dtype=np.int16)

    start_time = time.time()
    for i in range(len(frames)):
        frame = frames[i]
        packet = (frame, aud_empty)
        write_conn.send(packet)
        # send time
        if i % 25 == 0:
            total_time = time.time() - start_time
            start_time = time.time()
            print(f"send time: {total_time}")


def consumer(read_conn: mp.Pipe) -> None:
    i = 0
    start_time = time.time()
    while True:
        try:
            packet = read_conn.recv()
        except Exception as e:
            print(e)

        # receive time
        if i == 25:
            total_time = time.time() - start_time
            i = 0
            start_time = time.time()
            print(f"recv time: {total_time}")
        i += 1


class MPPipeTestCase(unittest.TestCase):

    def test_run(self):
        read_conn, write_conn = mp.Pipe()
        p_process = mp.Process(target=producer, args=(write_conn,))
        p_process.start()

        consumer(read_conn)

        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
