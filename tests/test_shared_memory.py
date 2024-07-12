import time
import unittest
import numpy as np
import multiprocessing.shared_memory as shared_memory


class SharedMemoryTestCase(unittest.TestCase):

    def test_shared_packet_demo(self):
        image_data = np.ones((1080, 1920, 3), dtype=np.uint8)
        wav_frame_num = int(44100 / 25)
        audio_data = np.zeros(wav_frame_num, dtype=np.int16)
        # image_data = np.random.randint(0, 256, (1080, 1920, 3), dtype=np.uint8)
        # audio_data = np.random.randint(-32768, 32767, (1764,), dtype=np.int16)

        # 计算所需的总字节数
        image_shape = image_data.shape
        audio_shape = audio_data.shape
        image_bytes = image_data.nbytes
        audio_bytes = audio_data.nbytes
        total_bytes = image_bytes + audio_bytes

        t1 = time.time()
        # 创建共享内存
        shm = shared_memory.SharedMemory(create=True, size=total_bytes)

        # 将图片和音频数据复制到共享内存
        shm.buf[:image_bytes] = image_data.tobytes()
        shm.buf[image_bytes:total_bytes] = audio_data.tobytes()
        t2 = time.time() - t1
        print(f"{t2}")

        # 重建数据
        shared_image = np.ndarray(image_shape, dtype=np.uint8, buffer=shm.buf[:image_bytes])
        shared_audio = np.ndarray(audio_shape, dtype=np.int16, buffer=shm.buf[image_bytes:image_bytes + audio_bytes])

        self.assertTrue(np.equal(image_data, shared_image).all())
        self.assertTrue(np.equal(audio_data, shared_audio).all())
        # # 使用完毕后，关闭共享内存
        shm.close()
        shm.unlink()  # 注意：只有在所有进程都不再使用共享内存时，才应该调用unlink

        t2 = time.time() - t1
        print(f"{t2}")
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
