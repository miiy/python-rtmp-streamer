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


logging.basicConfig(level=logging.DEBUG)
logging.getLogger('numba').setLevel(logging.WARNING)


def load_audio(path: str):
    """load audio stream"""
    aud, sr = librosa.load(path, sr=44100)
    aud = (aud*32767).astype(np.int16)
    return aud


def producer(q: mp.Queue) -> None:
    # video picture
    cap = cv2.VideoCapture("../data/test.mp4")
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    frame_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    logging.info(f"cap: fps: {fps}, frame_width: {frame_width}, frame_height: {frame_height}, frame_count: {frame_count}")

    # audio
    aud = load_audio("../data/test.wav")
    wav_frame_num = int(44100 / fps)
    aud_len = len(aud)
    logging.info(f"aud: len: {aud_len}, wav_frame_num: {wav_frame_num}")

    # handle frame data
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            logging.info("Opening camera is failed")
            break
        frames.append(frame)

    logging.info("data loaded")

    # push
    aud_empty = np.zeros(wav_frame_num, dtype=np.int16)

    aud_idx = 0
    start_time = time.time()
    for i in range(len(frames)):
        audio_frame = aud_empty.copy()
        if aud_idx < aud_len:
            aud_end = aud_idx+wav_frame_num
            if aud_end > aud_len:
                aud_end = aud_len
            audio_frame = aud[aud_idx:aud_end]
            aud_idx = aud_end

        frame = frames[i]
        sh_frame = sn.from_numpy(frame)
        sh_audio = sn.from_numpy(audio_frame)
        packet = (sh_frame, sh_audio)
        q.put(packet)

        # send time
        if i % 25 == 0:
            total_time = time.time() - start_time
            start_time = time.time()
            print(f"send time: {total_time}")


def get_status(stop_monitor_event: threading.Event, obj):
    print(f"{obj.get_status()}")
    while not stop_monitor_event.is_set():
        status = obj.get_status()
        print(f"{status}")
        time.sleep(0.5)


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
        ffmpeg_cmd = Streamer.ffmpeg_command(push_url, fps, frame_width, frame_height)
        streamer = Streamer(packet_queue, fps, sr, ffmpeg_cmd)
        stop_monitor_event = threading.Event()
        status_thread = threading.Thread(target=get_status, args=(stop_monitor_event, streamer,))
        status_thread.start()
        streamer.run()
        print("stop monitor")
        stop_monitor_event.set()

        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
