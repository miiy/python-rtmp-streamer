import time
import unittest
import numpy as np
import multiprocessing as mp

from rtmp_streamer.packet import Packet


class PacketTestCase(unittest.TestCase):

    def test_mp_queue_packet(self):
        mp.set_start_method('spawn')
        image_data = np.ones((1080, 1920, 3), dtype=np.uint8)

        q = mp.Queue()

        start_time = time.time()
        for i in range(250):
            q.put(image_data)

            # put time
            if i % 25 == 0:
                total_time = time.time() - start_time
                start_time = time.time()
                print(f"put time: {total_time}")

        start_time = time.time()
        for i in range(250):
            frame2 = q.get()
            # get time
            if i % 25 == 0:
                total_time = time.time() - start_time
                start_time = time.time()
                print(f"get time: {total_time}")

        self.assertTrue(True)

    def test_shared_packet(self):
        mp.set_start_method('spawn')
        image_data = np.ones((1080, 1920, 3), dtype=np.uint8)
        wav_frame_num = int(44100 / 25)
        audio_data = np.zeros(wav_frame_num, dtype=np.int16)

        q = mp.Queue()

        start_time = time.time()
        for i in range(250):
            shared_frame = Packet.create(image_data, audio_data)
            q.put(shared_frame)
            # put time
            if i % 25 == 0:
                total_time = time.time() - start_time
                start_time = time.time()
                print(f"put time: {total_time}")

        start_time = time.time()
        for i in range(250):
            frame2 = q.get()
            image_byte = frame2.image()
            audio_byte = frame2.audio()
            frame2.close()
            frame2.unlink()
            # get time
            if i % 25 == 0:
                total_time = time.time() - start_time
                start_time = time.time()
                print(f"get time: {total_time}")

        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
