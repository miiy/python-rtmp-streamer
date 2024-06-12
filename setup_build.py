from setuptools import setup

# cython
from Cython.Build import cythonize
from distutils.core import Extension

extensions = [
    Extension("rtmp_streamer.packet", ["src/rtmp_streamer/packet.py"]),
    Extension("rtmp_streamer.pipe", ["src/rtmp_streamer/pipe.py"]),
    Extension("rtmp_streamer.streamer", ["src/rtmp_streamer/streamer.py"]),
]

setup(
    name="rtmp_streamer",
    version="0.1.0",
    package_dir={"": "build"},
    packages=["rtmp_streamer"],
    package_data={"rtmp_streamer": ["*.so", "*.pyi"]},
    # cython
    ext_modules=cythonize(extensions, language_level=3),
)
