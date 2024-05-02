from os import path

from setuptools import setup

DESCRIPTION_PATH = path.join(path.abspath(path.dirname(__file__)), "README.md")
with open(DESCRIPTION_PATH, encoding="utf-8") as f:
    long_description = f.read()

REQUIREMENTS_PATH = path.join(path.abspath(path.dirname(__file__)), "requirements.txt")
with open(REQUIREMENTS_PATH, encoding="utf-8") as f:
    requirements = f.read()


setup(
    name="PySynth",
    author="Martin C. Doege", # original author
    keywords=["music", "piano", "notes"],
    version="2.4.1",
    packages=["pysynth"],
    include_package_data=True,
    license="GNU General Public License v3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    description="A simple music synthesizer for Python 3",
    python_requires=">=3.10.0",
    install_requires=requirements,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Intended Audience :: Musicians",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: MIDI",
        "Topic :: Multimedia :: Sound/Audio :: Sound Synthesis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)