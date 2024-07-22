from setuptools import setup, find_packages

# cython
from Cython.Build import cythonize
from distutils.core import Extension

extensions = [
    Extension("rtmp_streamer.audio", ["src/rtmp_streamer/audio.py"]),
    Extension("rtmp_streamer.packet_thread", ["src/rtmp_streamer/packet_thread.py"]),
    Extension("rtmp_streamer.pipe_thread", ["src/rtmp_streamer/pipe_thread.py"]),
    Extension("rtmp_streamer.streamer", ["src/rtmp_streamer/streamer.py"]),
]

setup(
    name="rtmp_streamer",
    version="0.1.0",
    package_dir={"": "build"},
    packages=find_packages(where="src"),
    package_data={"rtmp_streamer": ["*.so", "*.pyi"]},
    # cython
    ext_modules=cythonize(extensions, language_level=3),
)
