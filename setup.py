import os
import shutil
import requests
import tarfile
from setuptools import setup
from setuptools.command.install import install

class CustomInstall(install):
    """Custom installation class."""
    DOWNLOAD_URL = "https://freepats.zenvoid.org/Piano/SalamanderGrandPiano/SalamanderGrandPianoV3+20161209_48khz24bit.tar.xz"
    
    def run(self):
        """Override default run method."""
        install.run(self)
        self.download_and_extract()

    def download_and_extract(self):
        """Download and extract the tar file."""
        tar_file = os.path.join(self.build_lib, os.path.basename(self.DOWNLOAD_URL))
        
        # Download the file
        with requests.get(self.DOWNLOAD_URL, stream=True) as response:
            with open(tar_file, "wb") as f:
                shutil.copyfileobj(response.raw, f)

        with tarfile.open(tar_file, "r:xz") as tar:
            tar.extractall(path=self.build_lib)
            extracted_folder = tar.getnames()[0]

        folder_name = os.path.join(self.build_lib, extracted_folder)
        correct_folder_name = os.path.join(self.build_lib, "48khz24bit")
        shutil.move(os.path.join(folder_name, "48khz24bit"), correct_folder_name)
        os.remove(tar_file)
        shutil.rmtree(folder_name)

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
