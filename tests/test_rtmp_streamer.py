import cv2
import time
import librosa
import logging
import threading
import unittest
import numpy as np
import multiprocessing as mp

import shared_ndarray as sn
from rtmp_streamer.streamer import Streamer
from rtmp_streamer import audio


logging.basicConfig(level=logging.DEBUG)
logging.getLogger('numba').setLevel(logging.WARNING)


def load_audio(path: str):
    """load audio stream"""
    aud, sr = librosa.load(path, sr=44100)
    aud = (aud*32767).astype(np.int16)
    return aud


def print_frame_info(cap) -> None:
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    frame_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    print(f"cap: fps: {fps}, frame_width: {frame_width}, frame_height: {frame_height}, frame_count: {frame_count}")


def producer(q: mp.Queue) -> None:
    # video picture
    cap = cv2.VideoCapture("../data/test.mp4")
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    print_frame_info(cap)

    # cap frame data
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Opening camera is failed")
            break
        frames.append(frame)
    cap.release()

    # audio
    aud = load_audio("../data/test.wav")
    sr = 44100
    wav_frame_num = int(sr / fps)
    aud_len = len(aud)
    print(f"aud: len: {aud_len}, wav_frame_num: {wav_frame_num}")
    aud_empty = audio.create_empty_audio(fps, sr)

    audios = []
    aud_idx = 0
    for i in range(len(frames)):
        audio_frame = aud_empty.copy()
        if aud_idx < aud_len:
            aud_end = aud_idx + wav_frame_num
            if aud_end > aud_len:
                aud_end = aud_len
            audio_frame = aud[aud_idx:aud_end]
            aud_idx = aud_end
        audios.append(audio_frame)

    print("data loaded")

    # push
    print(f"start time: {time.time()}")
    start_time = time.time()
    for i in range(len(frames)):
        packet = sn.from_numpy(arr=None, frame=frames[i], audio=audios[i])
        if q.full():
            start_time = time.time()
        q.put(packet)
        packet.close()

        # send time
        if i % 25 == 0:
            total_time = time.time() - start_time
            start_time = time.time()
            print(f"send time: {total_time}")
        # test stop
        # if i > 0 and i % 100 == 0:
        #     print(f"sleep: {i}")
        #     time.sleep(10)


class StreamerTestCase(unittest.TestCase):

    def test_run(self):
        mp.set_start_method('spawn')

        packet_queue = mp.Queue(maxsize=50)
        p_process = mp.Process(target=producer, args=(packet_queue,))
        p_process.start()

        push_url = "rtmp://127.0.0.1/live/livestream"
        fps = 25
        sr = 44100
        frame_width = 1080
        frame_height = 1920
        streamer = Streamer(packet_queue, push_url, frame_width, frame_height, fps=fps)

        streamer_thread = threading.Thread(target=streamer.run, daemon=True)
        streamer_thread.start()
        streamer_thread.join()


if __name__ == '__main__':
    unittest.main()
