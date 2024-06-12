# python-rtmpstreamer

## Develop

install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Generate requirements.txt

```bash
pip freeze > requirements.txt
```

use ffmpeg

```bash
ffmpeg -i input.mp4 -vcodec libx264 -preset:v ultrafast -tune:v zerolatency -f flv -r 25 rtmp://127.0.0.1/live/livestream
```

```bash
docker run --rm --env CANDIDATE="192.168.110.78" -p 1935:1935 -p 8080:8080 -p 1985:1985 -p 8000:8000/udp registry.cn-hangzhou.aliyuncs.com/ossrs/srs:5 objs/srs -c conf/rtmp2rtc.conf
```

## Sample data

<https://file-examples.com/index.php/sample-audio-files/>

- file_example_MP4_1920_18MG.mp4
- file_example_WAV_1MG.wav

### docs

pip: <https://pip.pypa.io/en/stable/>

Setuptools: <https://setuptools.pypa.io/en/latest/index.html>

PyScaffold: <https://pyscaffold.org/en/stable/index.html>

Cython: <https://cython.readthedocs.io/en/latest/index.html>
