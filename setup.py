#!/usr/bin/env python

import os
import subprocess
import shutil
from setuptools import setup
from setuptools.command.install import install

class CustomInstall(install):
    def run(self):
        install.run(self)
        self.download_and_extract()

    def download_and_extract(self):
        download_url = "https://freepats.zenvoid.org/Piano/SalamanderGrandPiano/SalamanderGrandPianoV3+20161209_48khz24bit.tar.xz"
        tar_file = os.path.join(os.getcwd(), "SalamanderGrandPianoV3+20161209_48khz24bit.tar.xz")
        subprocess.run(["wget", download_url, "-O", tar_file])
        subprocess.run(["tar", "-xf", tar_file])
        extracted_folder = "SalamanderGrandPianoV3_48khz24bit"
        source_folder = os.path.join(extracted_folder, "48khz24bit")
        target_folder = os.path.join(os.getcwd(), "48khz24bit")
        shutil.move(source_folder, target_folder)


setup(
    name="PySynth",
    version="2.4",
    description="A simple music synthesizer for Python 3",
    author="Martin C. Doege",
    author_email="mdoege@compuserve.com",
    url="http://mdoege.github.io/PySynth/",
    py_modules=[
        "pysynth",
        "pysynth_b",
        "pysynth_c",
        "pysynth_d",
        "pysynth_e",
        "pysynth_p",
        "pysynth_s",
        "pysynth_beeper",
        "pysynth_samp",
        "play_wav",
        "mixfiles",
        "mkfreq",
        "demosongs",
    ],
    scripts=[
        "read_abc.py",
        "readmidi.py",
        "nokiacomposer2wav.py",
        "test_nokiacomposer2wav.py",
        "menv.py",
    ],
    requires=["numpy"],
    cmdclass={"install": CustomInstall},
)
